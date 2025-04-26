import 'dart:math';
import 'fsrs_algorithm.dart';

class Task {
  late int responseQuality; // Keep for backward compatibility
  int
  daysSinceInit; // Days since the task was initialized - might still be useful for stats
  int repetition; // Number of successful repetitions
  int previousInterval; // Previous interval in days

  // Keep eFactor for backward compatibility and display purposes
  double eFactor;

  // New FSRS fields
  double stability; // Memory stability
  double difficulty; // Item difficulty (0.1 to 1.0)

  String task; // The task description
  DateTime? nextReviewDate; // When to review next
  DateTime? lastReviewDate; // When the item was last reviewed - useful for FSRS

  // Constructor - now includes FSRS parameters with defaults
  Task({
    required this.task,
    this.daysSinceInit = 0,
    this.repetition = 0,
    this.previousInterval = 0,
    this.eFactor = 2.5,
    this.stability = FSRSAlgorithm.INITIAL_STABILITY, // Use constant
    this.difficulty = FSRSAlgorithm.INITIAL_DIFFICULTY, // Use constant
    this.nextReviewDate,
    this.lastReviewDate,
  });

  // Method to set the response quality - keeping this for backward compatibility
  void setResponseQuality(int quality) {
    responseQuality = quality;
  }

  /// Calculates the next review interval in days using the FSRS algorithm.
  /// Updates the task's repetition count, stability, difficulty, and dates.
  /// Sets the nextReviewDate based on the calculated interval.
  /// Returns the calculated interval in days.
  int calculateNextInterval(int quality) {
    if (quality < 0 || quality > 5) {
      throw ArgumentError("Quality must be between 0 and 5.");
    }

    responseQuality = quality;

    // Calculate next parameters using FSRS algorithm
    final fsrsResult = FSRSAlgorithm.calculateNext(
      quality: quality,
      stability: stability,
      difficulty: difficulty,
      repetition: repetition,
    );

    // Extract values from result
    final int nextInterval = fsrsResult['nextInterval'];
    final bool wasSuccessful = fsrsResult['wasSuccessful'];

    // Update task properties
    stability = fsrsResult['newStability'];
    difficulty = fsrsResult['newDifficulty'];

    // Update repetition - this aligns with SM-2 behavior
    if (wasSuccessful) {
      repetition = fsrsResult['newRepetition'];
    } else {
      repetition = 0; // Reset on failure
    }

    // Update eFactor approximation for backward compatibility
    // This keeps the UI showing something sensible for eFactor
    // The eFactor in SM-2 is roughly the expansion rate of intervals
    // In FSRS this is approximated by stability growth rate
    eFactor = max(1.3, 2.5 - (difficulty * 1.5));

    // Store the calculated interval
    previousInterval = nextInterval;

    // Update review dates
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    lastReviewDate = today;
    nextReviewDate = today.add(Duration(days: nextInterval));

    return nextInterval;
  }

  // --- JSON Serialization ---
  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      task: json['task'] as String,
      daysSinceInit: json['daysSinceInit'] as int? ?? 0,
      repetition: json['repetition'] as int? ?? 0,
      previousInterval: json['previousInterval'] as int? ?? 0,
      eFactor: (json['eFactor'] as num?)?.toDouble() ?? 2.5,
      // Handle new FSRS fields with defaults if they don't exist in older data
      stability:
          (json['stability'] as num?)?.toDouble() ??
          FSRSAlgorithm.INITIAL_STABILITY,
      difficulty:
          (json['difficulty'] as num?)?.toDouble() ??
          FSRSAlgorithm.INITIAL_DIFFICULTY,
      nextReviewDate:
          json['nextReviewDate'] != null
              ? DateTime.parse(json['nextReviewDate'] as String)
              : null,
      lastReviewDate:
          json['lastReviewDate'] != null
              ? DateTime.parse(json['lastReviewDate'] as String)
              : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'task': task,
      'daysSinceInit': daysSinceInit,
      'repetition': repetition,
      'previousInterval': previousInterval,
      'eFactor': eFactor,
      // Include new FSRS fields
      'stability': stability,
      'difficulty': difficulty,
      'nextReviewDate': nextReviewDate?.toIso8601String(),
      'lastReviewDate': lastReviewDate?.toIso8601String(),
    };
  }
}
