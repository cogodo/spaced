class Task {
  late int responseQuality; // Quality of the last response (0-5 scale)
  final int daysSinceInit; // Days since the task was initialized
  int repetition; // Number of repetitions (initially 1)
  int previousInterval; // Previous interval (initially 1 for the first repetition)
  double eFactor; // E-Factor (initially 2.5 for new items)
  String task; // The task description

  // Constructor to initialize the task with default values
  Task(this.task, this.daysSinceInit, {this.repetition = 1, this.previousInterval = 1, this.eFactor = 2.5});

  // Method to set the response quality
  void setResponseQuality(int quality) {
    responseQuality = quality;
  }
}