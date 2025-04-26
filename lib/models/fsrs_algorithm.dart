import 'dart:math';

/// FSRS Algorithm implementation based on Free Spaced Repetition Scheduler
///
/// This algorithm is based on the FSRS model, which is an improvement over
/// SM-2 and provides better retention predictions.
///
/// Reference: https://github.com/open-spaced-repetition/fsrs4anki/
class FSRSAlgorithm {
  // Default parameters - can be tuned for better performance
  // These parameters are derived from optimal values in research
  static const double _w = 1.0; // Weight parameter
  static const double _initialStability = 1.0; // Initial stability
  static const double _initialDifficulty =
      0.3; // Initial difficulty (ranges 0-1)
  static const double _difficultyDecay =
      0.1; // How quickly difficulty is updated

  // Public constants for initial values that can be used in default parameters
  static const double INITIAL_STABILITY = _initialStability;
  static const double INITIAL_DIFFICULTY = _initialDifficulty;

  // Public getters for initial values (keep for backward compatibility if needed)
  static double get initialStability => _initialStability;
  static double get initialDifficulty => _initialDifficulty;

  // Forgetting curve parameters
  static const Map<String, double> _forgettingCurve = {
    'requestRetention': 0.9, // Target retention (90%)
    'timeFactor': 0.1, // Time weighting factor
  };

  // Rating boundaries for mapping 0-5 scale to FSRS internal ratings
  static const Map<int, String> _ratingMap = {
    0: 'again',
    1: 'again',
    2: 'hard',
    3: 'good',
    4: 'good',
    5: 'easy',
  };

  // Stability multipliers based on rating
  static const Map<String, double> _stabilityMultipliers = {
    'again': 0.2, // Significant stability decrease
    'hard': 0.8, // Moderate stability decrease
    'good': 1.0, // Maintain stability
    'easy': 1.5, // Increase stability
  };

  // Constants for first-time intervals
  static const int _firstReviewInterval = 1; // First correct review -> 1 day
  static const int _secondReviewInterval = 6; // Second correct review -> 6 days

  /// Calculate stability based on previous stability, difficulty, and rating
  static double _calculateStability(
    double previousStability,
    double difficulty,
    String rating,
    int repetition,
  ) {
    // On first review, use initial stability
    if (repetition == 0) {
      return _initialStability * _stabilityMultipliers[rating]!;
    }

    // Calculate retrievability decay
    double retrievability =
        pow(e, -_w * difficulty * previousStability).toDouble();

    // Apply stability multiplier based on rating
    double stabilityMultiplier = _stabilityMultipliers[rating]!;

    // Formula based on FSRS model - stability increases as function of
    // previous stability, retrievability, and difficulty
    return previousStability *
        (1 +
            stabilityMultiplier *
                (1 - retrievability) *
                previousStability /
                _w);
  }

  /// Update difficulty based on performance
  static double _updateDifficulty(double currentDifficulty, String rating) {
    double difficultyDelta = 0;

    switch (rating) {
      case 'again':
        difficultyDelta = 0.15;
        break;
      case 'hard':
        difficultyDelta = 0.05;
        break;
      case 'good':
        difficultyDelta = -0.05;
        break;
      case 'easy':
        difficultyDelta = -0.15;
        break;
    }

    // Apply difficulty decay to make changes less dramatic over time
    double newDifficulty =
        currentDifficulty + difficultyDelta * _difficultyDecay;

    // Clamp to valid range [0.1, 1.0]
    return newDifficulty.clamp(0.1, 1.0);
  }

  /// Calculate interval (days until next review) based on stability
  static int _calculateInterval(double stability, int repetition) {
    if (repetition == 0) {
      return _firstReviewInterval;
    } else if (repetition == 1) {
      return _secondReviewInterval;
    } else {
      // Interval formula based on stability and target retention
      // This is a simplified version of the FSRS formula
      double interval =
          stability *
          _forgettingCurve['timeFactor']! *
          (-log(_forgettingCurve['requestRetention']!) / _w);

      // Ensure minimum interval of 1 day
      return max(1, interval.round());
    }
  }

  /// Calculate next review parameters based on current state and rating
  ///
  /// Returns a map with:
  /// - nextInterval: days until next review
  /// - newStability: updated stability value
  /// - newDifficulty: updated difficulty value
  /// - wasSuccessful: whether the rating was a successful recall
  static Map<String, dynamic> calculateNext({
    required int quality,
    required double stability,
    required double difficulty,
    required int repetition,
  }) {
    // Ensure quality is in valid range
    final safeQuality = quality.clamp(0, 5);

    // Map SM-2 quality rating (0-5) to FSRS rating
    final rating = _ratingMap[safeQuality]!;

    // Determine if successful recall (SM-2 considers 3+ successful)
    final wasSuccessful = safeQuality >= 3;

    // Calculate new repetition count
    int newRepetition = wasSuccessful ? repetition + 1 : 0;

    // Calculate new stability
    final newStability = _calculateStability(
      stability,
      difficulty,
      rating,
      repetition,
    );

    // Update difficulty
    final newDifficulty = _updateDifficulty(difficulty, rating);

    // Calculate next interval
    final nextInterval = _calculateInterval(newStability, newRepetition);

    return {
      'nextInterval': nextInterval,
      'newStability': newStability,
      'newDifficulty': newDifficulty,
      'newRepetition': newRepetition,
      'wasSuccessful': wasSuccessful,
    };
  }
}
