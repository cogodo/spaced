import json
from openai import AsyncOpenAI
from typing import Dict, Any
from core.models import Question
from app.config import settings


class ScoringService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def score_response(self, question: Question, answer: str) -> Dict[str, Any]:
        """
        Score a user's response using LLM evaluation
        Returns score (0-5), feedback, and explanation
        """
        if not answer.strip():
            return {
                "score": 0,
                "feedback": "No answer provided",
                "explanation": "Empty responses receive a score of 0",
                "correct": False
            }

        # Create scoring prompt based on question type
        prompt = self._create_scoring_prompt(question, answer)
        
        try:
            response = await self._call_openai_for_scoring(prompt)
            result = self._parse_scoring_response(response)
            
            # Ensure score is in valid range
            result["score"] = max(0, min(5, result["score"]))
            result["correct"] = result["score"] >= 3
            
            return result
            
        except Exception as e:
            # Fallback to basic scoring if LLM fails
            return self._fallback_scoring(answer)

    def _create_scoring_prompt(self, question: Question, answer: str) -> str:
        """Create a scoring prompt based on question type"""
        
        base_prompt = f"""
You are an expert educator evaluating a student's response to a learning question.

QUESTION: {question.text}
QUESTION TYPE: {question.type}
DIFFICULTY: {question.difficulty}/3
STUDENT ANSWER: {answer}

Please evaluate this response and provide:
1. A score from 0-5 (where 0=no understanding, 3=adequate, 5=excellent)
2. Brief feedback explaining the score
3. What the student got right or wrong

Scoring Guidelines:
- 0: No answer or completely incorrect
- 1: Shows minimal understanding, major errors
- 2: Some understanding but significant gaps
- 3: Adequate understanding, minor errors
- 4: Good understanding, well explained
- 5: Excellent understanding, comprehensive answer

Return your response in this JSON format:
{
    "score": 3,
    "feedback": "Your explanation covers the main concept but misses...",
    "explanation": "The answer demonstrates understanding of..."
}
"""

        # Add question-type specific guidance
        if question.type == "multiple_choice":
            base_prompt += "\nFor multiple choice: Score 5 if correct choice with good reasoning, 0 if wrong choice."
        elif question.type == "short_answer":
            base_prompt += "\nFor short answer: Focus on accuracy and completeness of key concepts."
        elif question.type == "explanation":
            base_prompt += "\nFor explanation: Evaluate depth of understanding, clarity, and examples used."

        return base_prompt

    async def _call_openai_for_scoring(self, prompt: str) -> str:
        """Make OpenAI API call for scoring"""
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert educator who provides fair, constructive feedback on student responses."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3  # Lower temperature for more consistent scoring
        )
        return response.choices[0].message.content

    def _parse_scoring_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Try to extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                result = json.loads(json_str)
                
                # Validate required fields
                if "score" in result and "feedback" in result:
                    return {
                        "score": int(result["score"]),
                        "feedback": str(result["feedback"]),
                        "explanation": str(result.get("explanation", ""))
                    }
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        
        # Fallback parsing if JSON fails
        return self._extract_score_from_text(response)

    def _extract_score_from_text(self, response: str) -> Dict[str, Any]:
        """Extract score from non-JSON response"""
        import re
        
        # Look for score patterns
        score_match = re.search(r'score[:\s]*([0-5])', response.lower())
        score = int(score_match.group(1)) if score_match else 3
        
        return {
            "score": score,
            "feedback": response[:200] + "..." if len(response) > 200 else response,
            "explanation": "Automated scoring from response text"
        }

    def _fallback_scoring(self, answer: str) -> Dict[str, Any]:
        """Fallback scoring method if LLM fails"""
        answer_length = len(answer.strip())
        
        if answer_length < 5:
            score = 1
            feedback = "Answer is too brief to demonstrate understanding"
        elif answer_length < 20:
            score = 2
            feedback = "Shows some understanding but needs more detail"
        elif answer_length < 50:
            score = 3
            feedback = "Adequate response with room for improvement"
        elif answer_length < 100:
            score = 4
            feedback = "Good detailed response"
        else:
            score = 5
            feedback = "Comprehensive and detailed answer"
        
        return {
            "score": score,
            "feedback": feedback,
            "explanation": "Fallback scoring based on response length",
            "correct": score >= 3
        } 