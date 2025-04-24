import 'dart:math';

class Task {
  late int responseQuality; // Quality of the last response (0-5 scale)
  int
  daysSinceInit; // Days since the task was initialized - might need review if this is still relevant
  int
  repetition; // Number of repetitions (initially 0 or 1?) - Let's assume it starts at 0 before first review
  int
  previousInterval; // Previous interval in days (initially 0 or 1?) - Let's assume 0 before first review
  double eFactor; // E-Factor (initially 2.5 for new items)
  String task; // The task description
  DateTime? nextReviewDate; // Add a field to store the next review date

  // Constructor - adjust initial values if needed
  Task({
    required this.task,
    this.daysSinceInit = 0, // Consider if this is still needed
    this.repetition = 0, // Start repetitions at 0
    this.previousInterval = 0, // Start interval at 0
    this.eFactor = 2.5,
    this.nextReviewDate, // Initialize potentially
  });

  // Method to set the response quality - keeping this separate might be redundant now
  void setResponseQuality(int quality) {
    responseQuality = quality;
  }

  /// Calculates the next review interval in days based on the SM-2 algorithm.
  /// Updates the task's repetition count, E-Factor, and previous interval.
  /// Sets the nextReviewDate based on the calculated interval.
  /// Returns the calculated interval in days.
  int calculateNextInterval(int quality) {
    if (quality < 0 || quality > 5) {
      throw ArgumentError("Quality must be between 0 and 5.");
    }

    responseQuality = quality;
    int nextInterval;

    if (quality < 3) {
      // Incorrect response - reset repetition
      repetition = 0;
      nextInterval = 1; // Review again tomorrow
    } else {
      // Correct response
      // Calculate new E-Factor
      eFactor = eFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
      if (eFactor < 1.3) {
        eFactor = 1.3; // E-Factor should not go below 1.3
      }

      // Calculate next interval based on repetition number
      if (repetition == 0) {
        nextInterval = 1; // First review success -> 1 day
      } else if (repetition == 1) {
        nextInterval = 6; // Second review success -> 6 days
      } else {
        // Use max(1, ...) ensures interval doesn't become 0 for very low eFactor
        nextInterval = max(1, (previousInterval * eFactor).round());
      }

      repetition++; // Increment repetition count only on success
    }

    previousInterval =
        nextInterval; // Store the calculated interval for the next iteration

    // Calculate the actual next review date from today
    final now = DateTime.now();
    // Set time to midnight to ensure consistent date comparison
    final today = DateTime(now.year, now.month, now.day);
    nextReviewDate = today.add(Duration(days: nextInterval));

    return nextInterval; // Return the interval in days
  }

  // --- JSON Serialization ---
  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      task: json['task'] as String,
      daysSinceInit: json['daysSinceInit'] as int? ?? 0, // Retain for now
      repetition: json['repetition'] as int? ?? 0,
      previousInterval: json['previousInterval'] as int? ?? 0,
      eFactor: (json['eFactor'] as num?)?.toDouble() ?? 2.5,
      nextReviewDate:
          json['nextReviewDate'] != null
              ? DateTime.parse(json['nextReviewDate'] as String)
              : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'task': task,
      'daysSinceInit': daysSinceInit, // Retain for now
      'repetition': repetition,
      'previousInterval': previousInterval,
      'eFactor': eFactor,
      'nextReviewDate': nextReviewDate?.toIso8601String(),
    };
  }
}
