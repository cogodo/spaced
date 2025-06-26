import uuid
from openai import AsyncOpenAI
from typing import List, Optional, Dict, Any, Tuple
from core.models import Question, Topic
from core.repositories import QuestionRepository
from app.config import settings


class QuestionService:
    def __init__(self):
        self.repository = QuestionRepository()
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def get_topic_questions(self, topic_id: str, user_uid: str) -> List[Question]:
        """Get all questions for a topic from user's subcollection"""
        return await self.repository.list_by_topic(topic_id, user_uid)

    async def generate_question_bank(self, topic: Topic) -> List[Question]:
        """Generate a bank of 20 high-quality questions using generator + refiner loop"""
        
        question_templates = [
            ("multiple_choice", "Create a multiple choice question about {topic} with 4 options. Focus on key concepts."),
            ("short_answer", "Create a short answer question about {topic} that tests understanding."),
            ("explanation", "Create a question asking to explain a concept related to {topic}."),
        ]
        
        questions = []
        
        # Generate different types of questions with refinement
        for i in range(20):
            question_type, template = question_templates[i % len(question_templates)]
            difficulty = (i // 7) + 1  # Distribute difficulties 1-3
            
            try:
                # Step 1: Generate initial question
                generated_question = await self._generate_question(topic, template, difficulty)
                
                # Step 2: Refine the question for quality
                refined_question = await self._refine_question(generated_question, question_type, difficulty)
                
                question = Question(
                    id=str(uuid.uuid4()),
                    topicId=topic.id,
                    text=refined_question,
                    type=question_type,
                    difficulty=difficulty,
                    metadata={
                        "generated_by": "openai_refined",
                        "topic_name": topic.name,
                        "generation_version": "2.0"
                    }
                )
                
                # Save to database with user context
                await self.repository.create(question, topic.ownerUid)
                questions.append(question)
                
            except Exception as e:
                print(f"Failed to generate refined question {i+1}: {e}")
                # Fallback to basic generation
                try:
                    basic_question = await self._generate_basic_question(topic, template, difficulty, question_type)
                    if basic_question:
                        questions.append(basic_question)
                except Exception as e2:
                    print(f"Failed basic generation fallback: {e2}")
                    continue
        
        return questions

    async def generate_initial_questions(self, topic: Topic, user_uid: str) -> List[Question]:
        """Generate a small initial set of questions quickly (5 questions, no refinement)"""
        
        question_templates = [
            ("multiple_choice", "Create a multiple choice question about {topic} with 4 options. Focus on key concepts."),
            ("short_answer", "Create a short answer question about {topic} that tests understanding."),
            ("explanation", "Create a question asking to explain a concept related to {topic}."),
        ]
        
        questions = []
        
        # Generate 5 questions quickly without refinement
        for i in range(5):
            question_type, template = question_templates[i % len(question_templates)]
            difficulty = min(i // 2 + 1, 3)  # Distribute difficulties 1-3
            
            try:
                # Single step generation (no refinement for speed)
                generated_question = await self._generate_question(topic, template, difficulty)
                
                question = Question(
                    id=str(uuid.uuid4()),
                    topicId=topic.id,
                    text=generated_question,
                    type=question_type,
                    difficulty=difficulty,
                    metadata={
                        "generated_by": "openai_initial",
                        "topic_name": topic.name,
                        "generation_version": "initial_1.0"
                    }
                )
                
                # Save to database with user context
                await self.repository.create(question, user_uid)
                questions.append(question)
                
            except Exception as e:
                print(f"Failed to generate initial question {i+1}: {e}")
                continue
        
        return questions



    async def _generate_question(self, topic: Topic, template: str, difficulty: int) -> str:
        """Generate initial question"""
        prompt = template.format(topic=topic.name)
        prompt += f"\n\nTopic description: {topic.description}"
        prompt += f"\nDifficulty level: {difficulty}/3"
        prompt += """
        
Requirements:
- Create a clear, well-structured question
- Ensure it tests understanding, not just memorization
- Make it appropriate for the specified difficulty level
- Focus on practical application of concepts

Return only the question text, no additional formatting."""

        return await self._call_openai(prompt, max_tokens=250, temperature=0.8)

    async def _refine_question(self, initial_question: str, question_type: str, difficulty: int) -> str:
        """Refine the generated question for better quality"""
        
        refinement_prompt = f"""
You are an expert educator reviewing and improving learning questions.

INITIAL QUESTION: {initial_question}
QUESTION TYPE: {question_type}
DIFFICULTY: {difficulty}/3

Please review this question and improve it by:

1. CLARITY: Make the question clearer and more precise
2. EDUCATIONAL VALUE: Ensure it tests real understanding
3. ENGAGEMENT: Make it more engaging for learners
4. DIFFICULTY ALIGNMENT: Ensure it matches the {difficulty}/3 difficulty level

Quality checklist:
- Is the question clear and unambiguous?
- Does it test understanding rather than just recall?
- Is it at the appropriate difficulty level?
- Would this question help someone learn the concept?

Return ONLY the improved question text. If the original is already excellent, return it unchanged.
"""

        try:
            refined = await self._call_openai(
                refinement_prompt, 
                max_tokens=300, 
                temperature=0.3  # Lower temperature for refinement
            )
            
            # Validate the refinement actually improved something
            if len(refined.strip()) > 10 and refined.strip() != initial_question.strip():
                return refined.strip()
            else:
                return initial_question
                
        except Exception as e:
            print(f"Refinement failed, using original: {e}")
            return initial_question

    async def _generate_basic_question(self, topic: Topic, template: str, difficulty: int, question_type: str) -> Optional[Question]:
        """Fallback basic question generation"""
        try:
            prompt = template.format(topic=topic.name)
            prompt += f"\n\nTopic description: {topic.description}"
            prompt += f"\nDifficulty level: {difficulty}/3"
            prompt += "\n\nReturn only the question text, no additional formatting."
            
            response = await self._call_openai(prompt)
            
            question = Question(
                id=str(uuid.uuid4()),
                topicId=topic.id,
                text=response.strip(),
                type=question_type,
                difficulty=difficulty,
                metadata={"generated_by": "openai_basic", "topic_name": topic.name}
            )
            
            await self.repository.create(question, topic.ownerUid)
            return question
            
        except Exception:
            return None

    async def _call_openai(self, prompt: str, max_tokens: int = 200, temperature: float = 0.7) -> str:
        """Make OpenAI API call with error handling and timeout"""
        try:
            import asyncio
            
            # Add timeout to prevent hanging requests
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert educator creating high-quality learning questions."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                ),
                timeout=15.0  # 15 second timeout for individual API calls
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            raise Exception("OpenAI API call timed out after 15 seconds")
        except Exception as e:
            # Escape curly braces in error message to prevent f-string formatting errors
            safe_error = str(e).replace("{", "{{").replace("}", "}}")
            raise Exception(f"OpenAI API error: {safe_error}")

    async def get_question(self, question_id: str, user_uid: str, topic_id: str) -> Optional[Question]:
        """Get a specific question by ID from user's topic subcollection"""
        return await self.repository.get_by_id(question_id, user_uid, topic_id)

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
            response = await self._call_openai(analysis_prompt, max_tokens=400, temperature=0.2)
            
            # Try to parse JSON response
            import json
            start = response.find('{')
            end = response.rfind('}') + 1
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
            "strengths": "Standard generated question"
        }

    async def get_question_bank_analytics(self, topic_id: str, user_uid: str) -> Dict[str, Any]:
        """Get analytics for a topic's question bank"""
        questions = await self.get_topic_questions(topic_id, user_uid)
        
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
            "generation_methods": [q.metadata.get("generated_by", "unknown") for q in questions]
        } 