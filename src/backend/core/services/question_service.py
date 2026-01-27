import asyncio
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ValidationError

from core.llm import get_llm_provider
from core.models import Question, Topic
from core.models.profiles import (
    ANALYSIS,
    GENERATION_BULK,
    GENERATION_SINGLE,
    REFINEMENT_BULK,
)
from core.monitoring.logger import get_logger
from core.repositories import QuestionRepository


class LLMTimeoutError(Exception):
    """Custom exception for LLM API timeouts."""

    pass


class QuestionServiceError(Exception):
    """Base exception for QuestionService."""

    pass


class QuestionGenerationError(QuestionServiceError):
    """Exception for failures during question generation."""

    pass


class QuestionService:
    def __init__(self):
        self.repository = QuestionRepository()
        self.llm_provider = get_llm_provider("default")
        self.fast_llm_provider = get_llm_provider("fast")
        self.logger = get_logger("question_service")

    def get_topic_questions(
        self, topic_id: str, user_uid: str, limit: Optional[int] = None, randomize: bool = False
    ) -> List[Question]:
        """Get questions for a topic from user's subcollection"""
        questions = self.repository.list_by_topic(topic_id, user_uid)

        if randomize:
            import random

            random.shuffle(questions)

        if limit and limit > 0:
            questions = questions[:limit]

        return questions

    async def generate_question_bank(self, topic: Topic) -> List[Question]:
        """
        Generate a bank of 10 high-quality questions using a single bulk generation
        prompt followed by one bulk refinement pass.
        """

        # Step 1: Bulk-generate diverse questions
        raw_items = await self._bulk_generate_questions(topic, count=10)

        # Step 2: One-pass refinement for quality (preserve type/difficulty)
        refined_map = await self._bulk_refine_questions(raw_items)

        # Step 3: Persist with deduplication
        saved_questions: List[Question] = []
        existing_question_texts: List[str] = []

        for idx, item in enumerate(raw_items):
            # Use refined text if available; otherwise fallback to original
            refined_text = refined_map.get(idx, item.get("text", "")).strip()
            if not refined_text:
                continue

            if self._is_too_similar(refined_text, existing_question_texts):
                continue

            q_type_raw = str(item.get("type", "short_answer"))
            q_type = self._coerce_question_type(q_type_raw)
            try:
                difficulty_val = int(item.get("difficulty", 2))
            except Exception:
                difficulty_val = 2
            difficulty_val = max(1, min(3, difficulty_val))

            tags: List[str] = []
            raw_tags = item.get("tags", [])
            if isinstance(raw_tags, list):
                tags = [str(t).strip() for t in raw_tags if str(t).strip()]

            question = Question(
                id=str(uuid.uuid4()),
                topicId=topic.id,
                text=refined_text,
                tags=tags,
                type=q_type,
                difficulty=difficulty_val,
                metadata={
                    "generated_by": "llm_bulk_refined",
                    "topic_name": topic.name,
                    "generation_version": "bulk_1.0",
                },
            )

            self.repository.create(question, topic.ownerUid)
            saved_questions.append(question)
            existing_question_texts.append(refined_text)

        return saved_questions

    async def generate_initial_questions(self, topic: Topic, user_uid: str) -> List[Question]:
        """
        Generate a set of questions (10 questions).
        """
        # Attempt bulk generation with retries only
        items: List[Dict[str, Any]] = []
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"Bulk generation attempt {attempt}/{max_attempts} for topic '{topic.name}'")
                items = await self._bulk_generate_questions(topic, count=10)
                if items:
                    break
            except Exception as e:
                self.logger.warning(
                    f"Bulk generation attempt {attempt} failed: {e}",
                )
                if attempt < max_attempts:
                    # Backoff before retrying
                    await asyncio.sleep(0.75 * attempt)

        if not items:
            raise QuestionGenerationError(
                f"Failed to bulk-generate initial questions for topic '{topic.name}' after {max_attempts} attempts"
            )

        questions: List[Question] = []
        existing_question_texts: List[str] = []
        for it in items:
            text = str(it.get("text", "")).strip()
            if not text:
                continue
            if self._is_too_similar(text, existing_question_texts):
                continue

            q_type_raw = str(it.get("type", "short_answer")) or "short_answer"
            q_type = self._coerce_question_type(q_type_raw)
            try:
                difficulty_val = int(it.get("difficulty", 2))
            except Exception:
                difficulty_val = 2
            difficulty_val = max(1, min(3, difficulty_val))

            tags: List[str] = []
            raw_tags = it.get("tags", [])
            if isinstance(raw_tags, list):
                tags = [str(t).strip() for t in raw_tags if str(t).strip()]

            question = Question(
                id=str(uuid.uuid4()),
                topicId=topic.id,
                text=text,
                tags=tags,
                type=q_type,
                difficulty=difficulty_val,
                metadata={
                    "generated_by": "llm_initial_bulk",
                    "topic_name": topic.name,
                    "generation_version": "initial_bulk_1.0",
                },
            )

            self.repository.create(question, user_uid)
            questions.append(question)
            existing_question_texts.append(text)

        if not questions:
            raise QuestionGenerationError(f"Failed to generate any initial questions for topic '{topic.name}'")

        return questions

    async def _generate_question(self, topic: Topic, template: str, difficulty: int) -> str:
        """Generate initial question with enhanced diversity"""
        # Add random perspective/context to increase variety
        import random

        perspectives = [
            "from a beginner's perspective",
            "from an advanced learner's perspective",
            "in a real-world context",
            "in a theoretical context",
            "from a practical application standpoint",
            "from a historical perspective",
            "in a modern context",
            "from a problem-solving angle",
            "from a critical thinking perspective",
            "in an interdisciplinary context",
        ]

        selected_perspective = random.choice(perspectives)

        prompt = template.format(topic=topic.name)
        prompt += f"\n\nTopic description: {topic.description}"
        prompt += f"\nDifficulty level: {difficulty}/3"
        prompt += f"\nContext: Consider this {selected_perspective}"
        prompt += """
Requirements:
- Create a clear, well-structured question
- Ensure it is relevant to the topic of {topic}
- The question should be answerable without external resources
- Do NOT include the answer to the question in your return
- Be creative and diverse - avoid common or obvious questions
- Focus on different aspects, perspectives, or applications of the topic
- Use varied vocabulary and phrasing to ensure uniqueness
- Incorporate the specified context/perspective naturally
"""

        return await self._call_llm(
            prompt,
            max_completion_tokens=GENERATION_SINGLE.max_completion_tokens,
        )

    async def _refine_question(self, initial_question: str, question_type: str, difficulty: int) -> str:
        """Refine a generated question for quality and clarity"""
        prompt = f"""
Original question about {question_type}:
"{initial_question}"

Critique this question based on:
- Clarity and conciseness
- Relevance to the topic
- Potential for ambiguity
- Would this question help someone learn the concept?

Return ONLY the improved question text. If the original is already excellent,
return it unchanged.
NEVER include the answer to the question in your return
NEVER include a heading like "improved question:" or "Question:" before the question in your return
ONLY return the question itself when you return and NOT EVER THE ANSWER DELETE ANYTHING THAT SAYS "ANSWER" and any follwing related text
"""
        return await self._call_llm(prompt, use_fast=True)

    async def _generate_basic_question(
        self, topic: Topic, template: str, difficulty: int, question_type: str
    ) -> Optional[Question]:
        """Fallback basic question generation"""
        try:
            prompt = template.format(topic=topic.name)
            prompt += f"\n\nTopic description: {topic.description}"
            prompt += f"\nDifficulty level: {difficulty}/3"
            prompt += "\n\nReturn only the question text, no additional formatting."

            response = await self._call_llm(prompt)

            question = Question(
                id=str(uuid.uuid4()),
                topicId=topic.id,
                text=response.strip(),
                type=question_type,
                difficulty=difficulty,
                metadata={"generated_by": "llm_basic", "topic_name": topic.name},
            )

            self.repository.create(question, topic.ownerUid)
            return question

        except Exception:
            return None

    async def _bulk_generate_questions(self, topic: Topic, count: int = 10) -> List[Dict[str, Any]]:
        """Generate many questions in one prompt and return structured items.

        Each item has keys: text (str), type (free-form str), tags (list[str]), difficulty (int 1..3)
        """
        import json

        prompt = f"""
You are generating exactly {count} diverse learning questions for the topic "{topic.name}".

Topic description:
{topic.description}

STRICT OUTPUT REQUIREMENTS:
- Output MUST be valid JSON parseable by Python json.loads.
- Output MUST be ONLY a JSON array of exactly {count} objects. No prose, no explanations, no comments.
- DO NOT include Markdown code fences (no ``` or ```json). DO NOT include any text before or after the array.
- The first character of your output MUST be '[' and the last character MUST be ']'.
- No trailing commas. Use double quotes for all strings.

Each object MUST contain these keys:
- "text": string (the question),
- "type": string (a short free-form descriptor),
- "difficulty": integer (1, 2, or 3).
- Optionally you MAY include "tags": array of strings.

Quality rules:
- Write clear, high-quality questions that do NOT include answers.
- Ensure diversity of question style and depth across the set.
- Avoid redundancy and overly similar phrasing.

Example JSON SHAPE (illustrative only):
[
  {{"text": "...", "type": "concept_check", "difficulty": 2, "tags": ["fundamentals"]}},
  {{"text": "...", "type": "why_how", "difficulty": 3, "tags": ["analysis"]}}
]
"""

        # Bulk generation needs a longer timeout and higher token budget
        response = await self._call_llm(
            prompt,
            max_completion_tokens=GENERATION_BULK.max_completion_tokens,
            timeout=40.0,
        )

        # Robust JSON array extraction
        start = response.find("[")
        end = response.rfind("]") + 1
        if start == -1 or end <= 0:
            raise QuestionGenerationError("LLM did not return a JSON array of questions")

        json_str = response[start:end]

        try:
            items = json.loads(json_str)
        except Exception as e:
            raise QuestionGenerationError(f"Failed to parse questions JSON: {e}")

        if not isinstance(items, list):
            raise QuestionGenerationError("Parsed questions payload was not a list")

        # Pydantic validation for structure
        class GeneratedQuestionItemModel(BaseModel):
            text: str
            type: str
            tags: Optional[List[str]] = []
            difficulty: int

        normalized: List[Dict[str, Any]] = []
        seen_texts: List[str] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            try:
                parsed = GeneratedQuestionItemModel(**it)
            except ValidationError:
                continue

            text = parsed.text.strip()
            if not text:
                continue
            # Cheap dedupe during generation phase
            if any(self._calculate_similarity(text, s) > 0.85 for s in seen_texts):
                continue

            q_type = self._coerce_question_type(parsed.type)

            try:
                diff = int(parsed.difficulty)
            except Exception:
                diff = 2
            diff = max(1, min(3, diff))

            tags: List[str] = []
            if parsed.tags:
                tags = [str(t).strip() for t in parsed.tags if str(t).strip()]

            normalized.append({"text": text, "type": q_type, "tags": tags, "difficulty": diff})
            seen_texts.append(text)

        return normalized

    async def _bulk_refine_questions(self, items: List[Dict[str, Any]]) -> Dict[int, str]:
        """Refine many questions in one pass. Returns map of index -> refined_text."""
        import json

        if not items:
            return {}

        # Build compact JSON array with index for alignment
        indexed_items = [
            {
                "index": i,
                "text": it.get("text", ""),
                "type": it.get("type", "short_answer"),
                "tags": it.get("tags", []),
                "difficulty": it.get("difficulty", 2),
            }
            for i, it in enumerate(items)
        ]

        input_json = json.dumps(indexed_items, ensure_ascii=False)

        prompt = f"""
Refine the clarity and learning value of each question below without changing its intent.
Do NOT add answers. Keep each question as a single sentence or concise prompt.

Input JSON (array of objects with index, text, type, difficulty):
{input_json}

Return STRICT JSON ONLY: an array of objects with keys "index" (int) and "text" (string), same order/length.
No explanations.
"""

        response = await self._call_llm(
            prompt,
            max_completion_tokens=REFINEMENT_BULK.max_completion_tokens,
            timeout=30.0,
            use_fast=True,
        )

        start = response.find("[")
        end = response.rfind("]") + 1
        if start == -1 or end <= 0:
            # If refinement fails, return original texts
            return {i: it.get("text", "") for i, it in enumerate(items)}

        try:
            refined_list = json.loads(response[start:end])
        except Exception:
            return {i: it.get("text", "") for i, it in enumerate(items)}

        refined_map: Dict[int, str] = {}
        for obj in refined_list if isinstance(refined_list, list) else []:
            try:
                idx = int(obj.get("index"))
                txt = str(obj.get("text", "")).strip()
                if txt:
                    refined_map[idx] = txt
            except Exception:
                continue

        # Ensure all indices present
        for i in range(len(items)):
            if i not in refined_map:
                refined_map[i] = items[i].get("text", "")

        return refined_map

    def _coerce_question_type(self, free_form_type: str) -> str:
        """Map free-form descriptors into our allowed enum. Defaults to short_answer."""
        t = (free_form_type or "").lower()
        if any(k in t for k in ["multiple", "choice", "mcq"]):
            return "multiple_choice"
        if any(k in t for k in ["explain", "explanation"]):
            return "explanation"
        if any(k in t for k in ["apply", "application", "scenario"]):
            return "application"
        if any(k in t for k in ["compare", "contrast", "versus", "vs."]):
            return "comparison"
        if any(k in t for k in ["analy", "why", "how"]):
            return "analysis"
        if any(k in t for k in ["synth", "combine", "integrate"]):
            return "synthesis"
        if any(k in t for k in ["predict", "forecast"]):
            return "prediction"
        return "short_answer"

    def _calculate_similarity(self, question1: str, question2: str) -> float:
        """Calculate similarity between two questions using simple heuristics."""
        # Convert to lowercase and remove punctuation for comparison
        import re

        q1_clean = re.sub(r"[^\w\s]", "", question1.lower())
        q2_clean = re.sub(r"[^\w\s]", "", question2.lower())

        # Split into words
        words1 = set(q1_clean.split())
        words2 = set(q2_clean.split())

        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        if union == 0:
            return 0.0

        return intersection / union

    def _is_too_similar(self, new_question: str, existing_questions: List[str], threshold: float = 0.6) -> bool:
        """Check if a new question is too similar to existing questions."""
        for existing in existing_questions:
            similarity = self._calculate_similarity(new_question, existing)
            if similarity > threshold:
                return True
        return False

    async def _call_llm(
        self,
        prompt: str,
        max_completion_tokens: int = GENERATION_SINGLE.max_completion_tokens,
        timeout: float = 15.0,
        use_fast: bool = False,
    ) -> str:
        """Make LLM API call with error handling and configurable timeout.

        Args:
            prompt: The prompt to send.
            max_completion_tokens: Maximum tokens in response.
            timeout: Request timeout in seconds.
            use_fast: If True, use the fast (Haiku) model for lighter tasks.

        Returns:
            The generated text response.
        """
        try:
            provider = self.fast_llm_provider if use_fast else self.llm_provider
            self.logger.info(
                "Preparing LLM request",
                extra={
                    "use_fast": use_fast,
                    "max_tokens": max_completion_tokens,
                    "timeout": timeout,
                    "prompt_preview": (prompt[:200] + ("…" if len(prompt) > 200 else "")),
                },
            )

            content = await provider.complete(
                prompt=prompt,
                system_prompt="You are an expert educator creating high-quality learning questions.",
                max_tokens=max_completion_tokens,
                timeout=timeout,
            )

            self.logger.info(
                "LLM response received",
                extra={
                    "content_len": len(content) if content else 0,
                    "content_preview": (content[:200] + ("…" if len(content) > 200 else "")) if content else None,
                },
            )

            if not content or not content.strip():
                raise Exception("LLM returned empty response")

            return content
        except asyncio.TimeoutError:
            raise LLMTimeoutError(f"LLM API call timed out after {timeout} seconds")
        except Exception as e:
            safe_error = str(e).replace("{", "{{").replace("}", "}}")
            raise Exception(f"LLM API error: {safe_error}")

    def get_question(self, question_id: str, user_uid: str, topic_id: str) -> Optional[Question]:
        """Get a specific question by ID from user's topic subcollection"""
        return self.repository.get_by_id(question_id, user_uid, topic_id)

    def get_diverse_questions(self, topic_id: str, user_uid: str, limit: int = 5) -> List[Question]:
        """Get a diverse set of questions with different types and difficulties"""
        all_questions = self.get_topic_questions(topic_id, user_uid)
        if not all_questions:
            return []

        # Group questions by type and difficulty
        questions_by_type = {}
        questions_by_difficulty = {}

        for q in all_questions:
            if q.type not in questions_by_type:
                questions_by_type[q.type] = []
            questions_by_type[q.type].append(q)

            if q.difficulty not in questions_by_difficulty:
                questions_by_difficulty[q.difficulty] = []
            questions_by_difficulty[q.difficulty].append(q)

        # Select diverse questions
        selected_questions = []
        import random

        # Ensure we get different types
        for question_type in questions_by_type:
            if questions_by_type[question_type]:
                selected_questions.append(random.choice(questions_by_type[question_type]))

        # Ensure we get different difficulties
        for difficulty in questions_by_difficulty:
            if questions_by_difficulty[difficulty]:
                diff_question = random.choice(questions_by_difficulty[difficulty])
                if diff_question not in selected_questions:
                    selected_questions.append(diff_question)

        # Fill remaining slots with random questions
        remaining_questions = [q for q in all_questions if q not in selected_questions]
        while len(selected_questions) < limit and remaining_questions:
            selected_questions.append(remaining_questions.pop(random.randint(0, len(remaining_questions) - 1)))

        return selected_questions[:limit]

    # New Phase 3 advanced features

    async def analyze_question_quality(self, question: Question) -> Dict[str, Any]:
        """Analyze the quality of a generated question"""
        analysis_prompt = f"""
Analyze this learning question for quality:

QUESTION: {question.text}
TYPE: {question.type}
DIFFICULTY: {question.difficulty}/3

Rate the question on these criteria (1-5 scale):
1. CLARITY: How clear and understandable is the question?
2. EDUCATIONAL_VALUE: How well does it test real understanding?
3. DIFFICULTY_MATCH: How well does it match the intended difficulty?
4. ENGAGEMENT: How engaging is it for learners?

Provide your analysis in this JSON format:
{{
    "clarity": 4,
    "educational_value": 3,
    "difficulty_match": 5,
    "engagement": 3,
    "overall_score": 3.75,
    "suggestions": "Brief suggestion for improvement",
    "strengths": "What works well about this question"
}}
"""

        try:
            response = await self._call_llm(
                analysis_prompt,
                max_completion_tokens=ANALYSIS.max_completion_tokens,
                use_fast=True,
            )

            # Try to parse JSON response
            import json

            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)

        except Exception as e:
            print(f"Question analysis failed: {e}")

        # Fallback analysis
        return {
            "clarity": 3,
            "educational_value": 3,
            "difficulty_match": 3,
            "engagement": 3,
            "overall_score": 3.0,
            "suggestions": "Analysis not available",
            "strengths": "Standard generated question",
        }

    async def get_question_bank_analytics(self, topic_id: str, user_uid: str) -> Dict[str, Any]:
        """Get analytics for a topic's question bank"""
        questions = self.get_topic_questions(topic_id, user_uid)

        if not questions:
            return {"error": "No questions found"}

        # Analyze distribution
        type_distribution = {}
        difficulty_distribution = {}

        for question in questions:
            type_distribution[question.type] = type_distribution.get(question.type, 0) + 1
            difficulty_distribution[question.difficulty] = difficulty_distribution.get(question.difficulty, 0) + 1

        return {
            "total_questions": len(questions),
            "type_distribution": type_distribution,
            "difficulty_distribution": difficulty_distribution,
            "average_difficulty": sum(q.difficulty for q in questions) / len(questions),
            "generation_methods": [q.metadata.get("generated_by", "unknown") for q in questions],
        }
