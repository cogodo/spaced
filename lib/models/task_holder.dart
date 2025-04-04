class Task {
  late int responseQuality; // Quality of the last response (0-5 scale)
  int daysSinceInit; // Days since the task was initialized
  int repetition; // Number of repetitions (initially 1)
  int
  previousInterval; // Previous interval (initially 1 for the first repetition)
  double eFactor; // E-Factor (initially 2.5 for new items)
  String task; // The task description

  // Constructor to initialize the task with default values
  Task({
    required this.task,
    this.daysSinceInit = 0,
    this.repetition = 1,
    this.previousInterval = 1,
    this.eFactor = 2.5,
  });

  // Method to set the response quality
  void setResponseQuality(int quality) {
    responseQuality = quality;
  }

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      task: json['task'] as String,
      daysSinceInit: json['daysSinceInit'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {'task': task, 'daysSinceInit': daysSinceInit};
  }
}
