import 'dart:convert'; // For JSON encoding/decoding
import 'package:flutter/foundation.dart'; // For ChangeNotifier
import 'package:lr_scheduler/models/task_holder.dart'; // Assuming Task is here
// Removed algorithm import as SM-2 logic is now in Task
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:math'; // For max()

// Make ScheduleManager a ChangeNotifier to notify listeners of updates
class ScheduleManager with ChangeNotifier {
  // Keep the singleton pattern if preferred, or rely solely on Provider
  static final ScheduleManager _instance = ScheduleManager._internal();
  factory ScheduleManager() {
    return _instance;
  }

  List<Task> _allTasks = []; // Changed from List<List<Task>> _schedule
  int maxRepetitions = 10; // Default max repetitions

  // TODO: Implement actual pro user check (e.g., via in-app purchase status)
  bool userIsPro = true; // Default to true for now

  // Removed _lastOpenedDate as day advancement logic changes

  static const String _tasksKey = 'allTasks'; // Renamed key
  static const String _maxRepetitionsKey =
      'maxRepetitions'; // Key for persistence

  // Getter for all tasks (optional, maybe only expose today's tasks?)
  List<Task> get allTasks => _allTasks;

  // Private constructor for singleton
  ScheduleManager._internal() {
    print("[ScheduleManager._internal] Constructor called.");
    // Load data when the instance is created
    // _loadData(); // DO NOT CALL ASYNC from constructor
  }

  // --- Core Logic Methods ---

  // Gets tasks due today or earlier
  List<Task> getTodaysTasks() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    print("[getTodaysTasks] Getting tasks for date: $today");

    return _allTasks.where((task) {
      // Include tasks never reviewed (nextReviewDate is null)
      // or tasks scheduled for today or earlier.
      return task.nextReviewDate == null ||
          task.nextReviewDate!.isBefore(today) ||
          task.nextReviewDate!.isAtSameMomentAs(today);
    }).toList();
  }

  // Adds a new task if no task with the same description exists.
  // Returns true if the task was added successfully, false otherwise.
  Future<bool> addTask(String taskDescription) async {
    // Check for duplicates (case-insensitive comparison)
    final descriptionLower = taskDescription.toLowerCase().trim();
    if (descriptionLower.isEmpty) {
      print("[addTask] Attempted to add an empty task.");
      return false; // Don't add empty tasks
    }

    final exists = _allTasks.any(
      (task) => task.task.toLowerCase().trim() == descriptionLower,
    );

    if (exists) {
      return false; // Indicate task was not added
    }

    // Create and add the new task
    final newTask = Task(task: taskDescription.trim()); // Trim whitespace
    _allTasks.add(newTask);
    await _saveTasks(); // Save after modification
    notifyListeners(); // Notify UI
    return true; // Indicate task was added successfully
  }

  // Method to update task after review
  Future<void> updateTaskReview(Task taskToUpdate, int quality) async {
    print(
      "[updateTaskReview] Updating task: ${taskToUpdate.task} with quality: $quality",
    );
    // Find the task instance in our list
    final taskIndex = _allTasks.indexWhere(
      (t) => t.task == taskToUpdate.task,
    ); // Assuming task string is unique ID for now
    if (taskIndex != -1) {
      // Calculate the next interval and update nextReviewDate within the task object
      _allTasks[taskIndex].calculateNextInterval(quality);
      print(
        "[updateTaskReview] Task ${taskToUpdate.task} next review date: ${_allTasks[taskIndex].nextReviewDate}",
      );

      await _saveTasks(); // Save the updated list of all tasks
      notifyListeners(); // Notify listeners that data has changed
    } else {
      print(
        "[updateTaskReview] Warning: Task ${taskToUpdate.task} not found in _allTasks list.",
      );
      // Handle error or log appropriately
    }
  }

  // --- Persistence Methods ---

  /// Initializes the ScheduleManager by loading data from storage.
  /// Must be called awaited after creating the instance and before using it.
  Future<void> init() async {
    print("[init] Starting data load...");
    try {
      print("[init] Getting SharedPreferences instance...");
      final prefs = await SharedPreferences.getInstance();
      print("[init] SharedPreferences instance obtained.");

      // Load max repetitions setting
      maxRepetitions =
          prefs.getInt(_maxRepetitionsKey) ?? 10; // Load with default
      print("[init] Max repetitions loaded: $maxRepetitions");

      // Load all tasks
      print("[init] Loading tasks...");
      final String? tasksJson = prefs.getString(_tasksKey);
      if (tasksJson != null) {
        print("[init] Found saved tasks JSON. Decoding...");
        try {
          final List<dynamic> decodedList = jsonDecode(tasksJson);
          _allTasks =
              decodedList
                  .map(
                    (taskMap) => Task.fromJson(taskMap as Map<String, dynamic>),
                  )
                  .toList();
          print(
            "[init] Tasks decoded successfully. Count: ${_allTasks.length}",
          );
        } catch (e, s) {
          print("Error decoding tasks JSON: $e\n$s");
          print("[init] Falling back to default empty task list.");
          _allTasks = []; // Fallback to empty list
        }
      } else {
        print("[init] No saved tasks found. Starting with empty list.");
        _allTasks = []; // Default if nothing saved
      }

      // Removed day change handling logic as it's implicitly handled by getTodaysTasks filter

      print("[init] Notifying listeners...");
      notifyListeners(); // Notify after loading
      print("[init] Data load completed successfully.");
    } catch (e, s) {
      print("[init] CRITICAL ERROR during data load: $e\n$s");
      _allTasks = []; // Ensure task list is empty on critical failure
      // Consider re-throwing or notifying error state
    }
  }

  Future<void> _saveTasks() async {
    // Renamed from _saveSchedule
    print("[_saveTasks] Saving tasks...");
    try {
      final prefs = await SharedPreferences.getInstance();
      // Ensure all tasks have necessary fields for toJson
      final String tasksJson = jsonEncode(
        _allTasks.map((task) => task.toJson()).toList(),
      );
      await prefs.setString(_tasksKey, tasksJson);
      print(
        "[_saveTasks] Tasks saved successfully. Count: ${_allTasks.length}",
      );
    } catch (e, s) {
      print("Error encoding/saving tasks: $e\n$s");
    }
  }

  // Removed _saveLastOpenedDate
  // Removed _handleDayChange

  // Add a method to remove a task (useful for testing/management)
  Future<void> removeTask(Task taskToRemove) async {
    print("[removeTask] Removing task: ${taskToRemove.task}");
    _allTasks.removeWhere(
      (t) => t.task == taskToRemove.task,
    ); // Assumes task string is unique ID
    await _saveTasks();
    notifyListeners();
    print("[removeTask] Task removed.");
  }

  // Add a method to clear all tasks (useful for testing/reset)
  Future<void> clearAllTasks() async {
    print("[clearAllTasks] Clearing all tasks.");
    _allTasks.clear();
    await _saveTasks();
    notifyListeners();
    print("[clearAllTasks] All tasks cleared.");
  }

  // Method to set the maximum repetitions and save it
  Future<void> setMaxRepetitions(int newValue) async {
    if (newValue < 1) newValue = 1; // Ensure at least 1 repetition

    // Check if the value actually changed
    if (newValue == maxRepetitions) {
      print("[setMaxRepetitions] Value unchanged ($newValue).");
      return; // No need to update or check tasks
    }

    maxRepetitions = newValue;
    print("[setMaxRepetitions] Setting max repetitions to: $maxRepetitions");
    bool tasksRemoved = false;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_maxRepetitionsKey, maxRepetitions);
      print("[setMaxRepetitions] Max repetitions saved successfully.");

      // Now check existing tasks against the new threshold
      final initialTaskCount = _allTasks.length;
      _allTasks.removeWhere((task) {
        final shouldRemove = task.repetition >= maxRepetitions;
        if (shouldRemove) {
          print(
            "[setMaxRepetitions] Removing task '${task.task}' (reps: ${task.repetition} >= max: $maxRepetitions)",
          );
        }
        return shouldRemove;
      });

      if (_allTasks.length < initialTaskCount) {
        tasksRemoved = true;
        print(
          "[setMaxRepetitions] Removed ${initialTaskCount - _allTasks.length} tasks exceeding the new max repetition threshold.",
        );
        await _saveTasks(); // Save the modified task list
      }
    } catch (e, s) {
      print("Error saving max repetitions or removing tasks: $e\n$s");
    } finally {
      // Notify listeners if the setting changed or tasks were removed
      notifyListeners();
    }
  }
}

// --- Add to your Task model ---
// You NEED `fromJson` and `toJson` methods in your Task class for persistence

/* Example in lib/models/task_holder.dart (or wherever Task is defined)
class Task {
  String task;
  int daysSinceInit;
  // Add other relevant fields (e.g., interval, easeFactor)

  Task({required this.task, this.daysSinceInit = 0 /*, other fields */});

  // Factory constructor to create a Task from JSON
  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      task: json['task'] as String,
      daysSinceInit: json['daysSinceInit'] as int? ?? 0,
      // Deserialize other fields
    );
  }

  // Method to convert a Task instance to JSON
  Map<String, dynamic> toJson() {
    return {
      'task': task,
      'daysSinceInit': daysSinceInit,
      // Serialize other fields
    };
  }
}
*/
