from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    from fsrs import FSRS as FSRSScheduler
    from fsrs import Card, Rating, State
except ImportError:
    # Fallback if FSRS library is not available or API is different
    Card = None
    Rating = None
    State = None
    FSRSScheduler = None

from core.models import FSRSParams


class FSRSService:
    def __init__(self):
        if FSRSScheduler:
            self.fsrs = FSRSScheduler()
        else:
            self.fsrs = None

    def calculate_next_review(
        self,
        current_params: FSRSParams,
        performance_score: int,
        last_review: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Calculate next review date using FSRS algorithm or fallback

        Args:
            current_params: Current FSRS parameters
            performance_score: User performance (0-5 scale)
            last_review: When the topic was last reviewed

        Returns:
            Dictionary with next review date and updated parameters
        """

        if not self.fsrs or not Card:
            # Fallback to simple calculation if FSRS not available
            return self._fallback_calculation(
                current_params, performance_score, last_review
            )

        try:
            # Convert our performance score (0-5) to FSRS Rating
            rating = self._score_to_rating(performance_score)

            # Create FSRS Card from our parameters
            card = Card(
                due=last_review or datetime.now(),
                stability=current_params.ease,
                difficulty=max(
                    1, min(10, 11 - current_params.ease)
                ),  # Invert ease to difficulty
                elapsed_days=current_params.interval,
                scheduled_days=current_params.interval,
                reps=current_params.repetition,
                lapses=0,
                state=self._determine_card_state(current_params.repetition),
            )

            # Calculate next review using FSRS
            now = datetime.now()
            scheduling_cards = self.fsrs.repeat(card, now)

            # Get the appropriate scheduling based on rating
            if hasattr(scheduling_cards, "__getitem__"):
                # Handle different FSRS API versions
                if rating == Rating.Again:
                    next_card = scheduling_cards[Rating.Again]
                elif rating == Rating.Hard:
                    next_card = scheduling_cards[Rating.Hard]
                elif rating == Rating.Good:
                    next_card = scheduling_cards[Rating.Good]
                else:  # Rating.Easy
                    next_card = scheduling_cards[Rating.Easy]
            else:
                # Fallback if API is different
                next_card = scheduling_cards

            # Convert back to our FSRSParams format
            updated_params = FSRSParams(
                ease=getattr(next_card, "stability", current_params.ease),
                interval=getattr(
                    next_card, "scheduled_days", current_params.interval + 1
                ),
                repetition=getattr(next_card, "reps", current_params.repetition + 1),
            )

            return {
                "nextReviewAt": getattr(
                    next_card,
                    "due",
                    datetime.now() + timedelta(days=updated_params.interval),
                ),
                "updatedParams": updated_params,
                "intervalDays": updated_params.interval,
                "stability": updated_params.ease,
                "difficulty": 11 - updated_params.ease,
            }

        except Exception as e:
            print(f"FSRS calculation failed, using fallback: {e}")
            return self._fallback_calculation(
                current_params, performance_score, last_review
            )

    def _fallback_calculation(
        self,
        current_params: FSRSParams,
        performance_score: int,
        last_review: Optional[datetime],
    ) -> Dict[str, Any]:
        """Fallback calculation if FSRS library is not available"""

        # Simple spaced repetition logic
        if performance_score >= 4:
            # Good performance - increase interval
            new_interval = min(current_params.interval * 2, 30)
            new_ease = min(current_params.ease * 1.1, 5.0)
        elif performance_score >= 3:
            # Adequate performance - slight increase
            new_interval = max(current_params.interval + 1, 1)
            new_ease = current_params.ease
        else:
            # Poor performance - reset or decrease
            new_interval = 1
            new_ease = max(current_params.ease * 0.9, 1.3)

        updated_params = FSRSParams(
            ease=new_ease,
            interval=new_interval,
            repetition=current_params.repetition + 1,
        )

        next_review = datetime.now() + timedelta(days=new_interval)

        return {
            "nextReviewAt": next_review,
            "updatedParams": updated_params,
            "intervalDays": new_interval,
            "stability": new_ease,
            "difficulty": 11 - new_ease,
        }

    def _score_to_rating(self, score: int):
        """Convert 0-5 performance score to FSRS Rating"""
        if not Rating:
            return score  # Return score directly if Rating not available

        if score <= 1:
            return Rating.Again  # Need to review again soon
        elif score == 2:
            return Rating.Hard  # Difficult, shorter interval
        elif score in [3, 4]:
            return Rating.Good  # Standard interval
        else:  # score == 5
            return Rating.Easy  # Longer interval

    def _determine_card_state(self, repetitions: int):
        """Determine FSRS card state based on repetitions"""
        if not State:
            return repetitions  # Return repetitions directly if State not available

        if repetitions == 0:
            return State.New
        elif repetitions == 1:
            return State.Learning
        else:
            return State.Review

    def get_optimal_review_time(self, params: FSRSParams) -> datetime:
        """Get the optimal time for next review based on current parameters"""
        return datetime.now() + timedelta(days=params.interval)

    def calculate_retention_probability(
        self, params: FSRSParams, days_since_review: int
    ) -> float:
        """Calculate probability that user remembers the topic"""

        # Simple retention calculation based on FSRS principles
        stability = params.ease

        if stability <= 0:
            return 0.0

        # Exponential decay formula similar to FSRS
        retention = (0.9) ** (days_since_review / stability)
        return max(0.0, min(1.0, retention))

    def should_review_now(self, params: FSRSParams, last_review: datetime) -> bool:
        """Determine if a topic should be reviewed now"""
        days_since = (datetime.now() - last_review).days
        retention = self.calculate_retention_probability(params, days_since)

        # Review if retention drops below 90%
        return retention < 0.9

    def get_difficulty_adjustment(self, recent_scores: list) -> float:
        """
        Calculate difficulty adjustment based on recent performance

        Args:
            recent_scores: List of recent performance scores (0-5)

        Returns:
            Adjustment factor for difficulty
        """
        if not recent_scores:
            return 1.0

        avg_score = sum(recent_scores) / len(recent_scores)

        # If consistently performing well, reduce difficulty
        if avg_score >= 4.0:
            return 0.8  # Make easier
        elif avg_score <= 2.0:
            return 1.2  # Make harder
        else:
            return 1.0  # Keep same

    def bulk_calculate_reviews(self, topics_with_params: list) -> Dict[str, datetime]:
        """
        Calculate next review dates for multiple topics efficiently

        Args:
            topics_with_params: List of (topic_id, FSRSParams, last_score) tuples

        Returns:
            Dictionary mapping topic_id to next_review_date
        """
        review_schedule = {}

        for topic_id, params, score in topics_with_params:
            result = self.calculate_next_review(params, score)
            review_schedule[topic_id] = result["nextReviewAt"]

        return review_schedule
