import 'package:lr_scheduler/models/task_holder.dart';
import 'dart:math';

List<List<Task>> generateSchedule(List<Task> tasks) {
  var schedule = List<List<Task>>.generate(
    10000, // Number of days in the schedule
    (int index) => [],
  );
  return schedule; // Return the empty schedule for now, to be filled in later
}

List<List<Task>> addTask(
  List<List<Task>> schedule,
  Task task,
  int index,
  int maxDaysSinceInit,
) {
  Task newTask = Task(
    task.task,
    task.daysSinceInit + index,
  ); // Create a new instance to avoid mutating the original task
  if (index < schedule.length && task.daysSinceInit <= maxDaysSinceInit) {
    // Ensure the index is within the bounds of the schedule
    schedule[index].add(newTask); // Add to the specified indices as well
  }

  return schedule;
}

int calculateNextInterval(Task task, int quality) {
  // Default E-Factor for new items
  double eFactor = task.eFactor;

  // Update E-Factor based on quality of response
  eFactor = eFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  if (eFactor < 1.3) {
    eFactor = 1.3; // Minimum E-Factor
  }

  // Calculate the next interval
  int interval;
  if (task.repetition == 1) {
    interval = 1; // First repetition interval
  } else if (task.repetition == 2) {
    interval = 6; // Second repetition interval
  } else {
    interval = (task.previousInterval * eFactor).ceil(); // Subsequent intervals
  }

  // Update task properties
  task.eFactor = eFactor;
  task.previousInterval = interval;
  task.repetition += 1;

  return interval;
}

void scheduleTask(
  List<List<Task>> schedule,
  Task task,
  int quality,
) {
  // Calculate the next interval
  int nextInterval = calculateNextInterval(task, quality);

  // Add the task to the schedule at the calculated index
  int nextIndex = task.daysSinceInit + nextInterval;
  if (nextIndex < schedule.length) {
    schedule[nextIndex].add(task);
  }
}