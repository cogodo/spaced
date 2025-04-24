import 'dart:convert'; // For JSON encoding/decoding
import 'package:flutter/foundation.dart'; // For ChangeNotifier
import 'package:spaced/models/task_holder.dart'; // Assuming Task is here
// Removed algorithm import as SM-2 logic is now in Task
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:math'; // For max()
import '../services/local_storage_service.dart'; // Import local storage instead of Firestore

// Make ScheduleManager a ChangeNotifier to notify listeners of updates
class ScheduleManager with ChangeNotifier {
  final String userId; // Each instance is tied to a user
  final LocalStorageService _storage; // Local storage instead of Firestore

  List<Task> _allTasks = []; // Changed from List<List<Task>> _schedule
  int maxRepetitions = 10; // Default value

  // Local Storage Paths references
  late final LocalDocumentReference _userDocRef;
  late final LocalCollectionReference _tasksCollectionRef;

  // Constructor now requires UID and LocalStorageService instance
  ScheduleManager({required this.userId, required LocalStorageService storage})
    : _storage = storage {
    print("[ScheduleManager] Constructor called with userId: $userId");
    if (userId.isEmpty) {
      throw ArgumentError("User ID cannot be empty for ScheduleManager");
    }
    _userDocRef = _storage.getUserDocument(userId);
    _tasksCollectionRef = _storage.getUserTasksCollection(userId);
    print("[ScheduleManager] Initialized for user: $userId");
    // Don't block constructor with async call
    Future.microtask(() => _loadUserData());
  }

  // Getter for all tasks (optional, maybe only expose today's tasks?)
  List<Task> get allTasks => _allTasks;

  // --- Load User Data --- (Called internally)
  Future<void> _loadUserData() async {
    print("[_loadUserData] Loading data for user: $userId");
    try {
      // Load user settings (maxRepetitions, etc.)
      final userDoc = await _userDocRef.get();
      if (userDoc.exists && userDoc.data() != null) {
        final data = userDoc.data()!;
        maxRepetitions = data['maxRepetitions'] as int? ?? 10;
        print("[_loadUserData] Loaded maxRepetitions: $maxRepetitions");
        // Load other settings like theme, pro status if stored here
      } else {
        // User document doesn't exist yet (first login?), use defaults
        // Optionally create the document with defaults here
        print("[_loadUserData] User document not found, using defaults.");
        await _saveUserSettings(); // Save defaults if doc doesn't exist
      }

      // Load tasks
      final tasksSnapshot = await _tasksCollectionRef.get();
      _allTasks =
          tasksSnapshot.docs
              .map((doc) {
                final data = doc.data();
                if (data != null) {
                  return Task.fromJson(data);
                }
                return null;
              })
              .whereType<Task>() // Filter out nulls
              .toList();
      print("[_loadUserData] Loaded ${_allTasks.length} tasks.");

      notifyListeners(); // Notify after loading all data
    } catch (e, s) {
      print("[_loadUserData] ERROR loading user data: $e\n$s");
      _allTasks = []; // Reset state on critical failure
      maxRepetitions = 10;
      notifyListeners(); // Notify about the error state
    }
  }

  // --- Save User Settings --- (Separate from saving tasks)
  Future<void> _saveUserSettings() async {
    print("[_saveUserSettings] Saving settings for user: $userId");
    try {
      // Use set with merge option to create or update
      await _userDocRef.set({
        'maxRepetitions': maxRepetitions,
        // Add other settings like theme preference, pro status etc.
      }, options: LocalSetOptions(merge: true));
      print("[_saveUserSettings] Settings saved.");
    } catch (e, s) {
      print("Error saving user settings: $e\n$s");
    }
  }

  // --- Persistence for Tasks (Uses local storage) ---
  Future<void> _saveTasks() async {
    print("[_saveTasks] Saving all tasks for user $userId");
    try {
      // Delete all existing tasks
      final currentDocs = await _tasksCollectionRef.get();
      for (var doc in currentDocs.docs) {
        await _tasksCollectionRef.doc(doc.id).delete();
      }

      // Add all current tasks
      for (var task in _allTasks) {
        await _tasksCollectionRef.doc(task.task).set(task.toJson());
      }

      print("[_saveTasks] Tasks saved for user $userId.");
    } catch (e, s) {
      print("Error saving tasks: $e\n$s");
    }
  }

  // --- Core Logic Methods (Modified for local storage) ---

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
    final descriptionLower = taskDescription.toLowerCase().trim();
    if (descriptionLower.isEmpty) return false;
    final exists = _allTasks.any(
      (task) => task.task.toLowerCase().trim() == descriptionLower,
    );
    if (exists) {
      print(
        "[addTask] Task already exists locally for user $userId: $taskDescription",
      );
      return false;
    }

    final newTask = Task(task: taskDescription.trim());
    final now = DateTime.now();
    final tomorrow = DateTime(
      now.year,
      now.month,
      now.day,
    ).add(Duration(days: 1));
    newTask.nextReviewDate = tomorrow;
    _allTasks.add(newTask); // Add locally first for immediate UI update

    print("[addTask] Added task locally for user $userId: ${newTask.task}");
    notifyListeners(); // Notify UI immediately

    try {
      // Save specifically this task to local storage
      await _tasksCollectionRef.doc(newTask.task).set(newTask.toJson());
      print("[addTask] Saved new task to local storage for user $userId.");
      return true;
    } catch (e, s) {
      print("Error saving new task to local storage: $e\n$s");
      // Revert local change if save fails
      _allTasks.removeWhere((t) => t.task == newTask.task);
      notifyListeners();
      return false;
    }
  }

  // Method to update task after review
  Future<void> updateTaskReview(Task taskToUpdate, int quality) async {
    final taskIndex = _allTasks.indexWhere((t) => t.task == taskToUpdate.task);
    if (taskIndex != -1) {
      _allTasks[taskIndex].calculateNextInterval(quality);
      final updatedTask = _allTasks[taskIndex];
      print(
        "[updateTaskReview] Updated task locally for user $userId: ${updatedTask.task}",
      );
      notifyListeners(); // Update UI immediately

      try {
        // Update the specific task document in local storage
        await _tasksCollectionRef
            .doc(updatedTask.task)
            .update(updatedTask.toJson());
        print(
          "[updateTaskReview] Updated task in local storage for user $userId.",
        );
      } catch (e, s) {
        print("Error updating task in local storage: $e\n$s");
      }
    } else {
      print(
        "[updateTaskReview] Warning: Task ${taskToUpdate.task} not found locally for user $userId.",
      );
    }
  }

  // Method to remove a task (useful for testing/management)
  Future<void> removeTask(Task taskToRemove) async {
    final initialLength = _allTasks.length;
    _allTasks.removeWhere((t) => t.task == taskToRemove.task);
    if (_allTasks.length < initialLength) {
      print(
        "[removeTask] Removed task locally for user $userId: ${taskToRemove.task}",
      );
      notifyListeners(); // Update UI immediately

      try {
        // Delete the specific task document from local storage
        await _tasksCollectionRef.doc(taskToRemove.task).delete();
        print("[removeTask] Deleted task from local storage for user $userId.");
      } catch (e, s) {
        print("Error deleting task from local storage: $e\n$s");
      }
    } else {
      print(
        "[removeTask] Task not found locally for user $userId: ${taskToRemove.task}",
      );
    }
  }

  // Add a method to clear all tasks (useful for testing/reset)
  Future<void> clearAllTasks() async {
    print("[clearAllTasks] Clearing all tasks locally for user $userId.");
    _allTasks.clear();
    notifyListeners();

    // Delete all tasks from local storage
    try {
      final currentDocs = await _tasksCollectionRef.get();
      for (var doc in currentDocs.docs) {
        await _tasksCollectionRef.doc(doc.id).delete();
      }
      print(
        "[clearAllTasks] Cleared tasks from local storage for user $userId.",
      );
    } catch (e, s) {
      print("Error clearing tasks from local storage: $e\n$s");
    }
  }

  // Method to set the maximum repetitions and save it
  Future<void> setMaxRepetitions(int newValue) async {
    if (newValue < 1) newValue = 1;
    if (newValue == maxRepetitions) return;

    maxRepetitions = newValue;
    print(
      "[setMaxRepetitions] Set max repetitions locally to: $maxRepetitions for user $userId",
    );
    notifyListeners(); // Update UI immediately for setting change

    await _saveUserSettings(); // Save setting to user document

    // Check tasks locally first
    final initialTaskCount = _allTasks.length;
    List<Task> tasksToDelete = [];
    _allTasks.removeWhere((task) {
      final shouldRemove = task.repetition >= maxRepetitions;
      if (shouldRemove) {
        print("[setMaxRepetitions] Marking task for removal: '${task.task}'");
        tasksToDelete.add(task); // Keep track for local storage deletion
      }
      return shouldRemove;
    });

    if (tasksToDelete.isNotEmpty) {
      print(
        "[setMaxRepetitions] Removed ${tasksToDelete.length} tasks locally for user $userId.",
      );
      notifyListeners(); // Update UI for task removal

      // Delete tasks from local storage
      try {
        for (var task in tasksToDelete) {
          await _tasksCollectionRef.doc(task.task).delete();
        }
        print(
          "[setMaxRepetitions] Deleted tasks from local storage for user $userId.",
        );
      } catch (e, s) {
        print("Error deleting tasks in local storage: $e\n$s");
      }
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
