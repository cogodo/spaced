import 'dart:convert'; // For JSON encoding/decoding
import 'package:flutter/foundation.dart'; // For ChangeNotifier
import 'package:lr_scheduler/models/task_holder.dart'; // Assuming Task is here
import 'package:lr_scheduler/utils/algorithm.dart'; // Assuming generateSchedule, scheduleTask are here
import 'package:shared_preferences/shared_preferences.dart';

// Make ScheduleManager a ChangeNotifier to notify listeners of updates
class ScheduleManager with ChangeNotifier {
  // Keep the singleton pattern if preferred, or rely solely on Provider
  static final ScheduleManager _instance = ScheduleManager._internal();
  factory ScheduleManager() {
    return _instance;
  }

  List<List<Task>> _schedule = [];
  DateTime? _lastOpenedDate;

  static const String _scheduleKey = 'schedule';
  static const String _lastOpenedKey = 'lastOpenedDate';

  List<List<Task>> get schedule => _schedule;

  // Private constructor for singleton
  ScheduleManager._internal() {
    // Load data when the instance is created
    _loadData();
  }

  // --- Core Logic Methods ---

  void addTask(Task task) {
    // Add the task using your scheduling algorithm
    scheduleTask(
      _schedule,
      task,
      5, // Example quality score
    );
    _saveSchedule(); // Save after modification
    notifyListeners(); // Notify UI
  }

  void advanceSchedule() {
    if (_schedule.isNotEmpty) {
      _schedule.removeAt(0);
      // Increment daysSinceInit or handle task rescheduling based on your algorithm
      for (var dayTasks in _schedule) {
        for (var task in dayTasks) {
          // Update task properties as needed for the next day
          task.daysSinceInit += 1; // Example increment
        }
      }
      _saveSchedule(); // Save after modification
      notifyListeners(); // Notify UI
    }
  }

  // --- Persistence Methods ---

  Future<void> _loadData() async {
    final prefs = await SharedPreferences.getInstance();

    // Load last opened date
    final lastOpenedMillis = prefs.getInt(_lastOpenedKey);
    if (lastOpenedMillis != null) {
      _lastOpenedDate = DateTime.fromMillisecondsSinceEpoch(lastOpenedMillis);
    }

    // Load schedule
    final String? scheduleJson = prefs.getString(_scheduleKey);
    if (scheduleJson != null) {
      try {
        final List<dynamic> decodedOuterList = jsonDecode(scheduleJson);
        _schedule =
            decodedOuterList.map((dayList) {
              final List<dynamic> decodedInnerList = dayList;
              return decodedInnerList
                  .map(
                    (taskMap) => Task.fromJson(taskMap as Map<String, dynamic>),
                  ) // Assuming Task has fromJson
                  .toList();
            }).toList();
      } catch (e) {
        print("Error decoding schedule: $e");
        _schedule = generateSchedule([]); // Fallback to default
      }
    } else {
      _schedule = generateSchedule([]); // Default if nothing saved
    }

    // --- Handle Day Advancement ---
    _handleDayChange();

    notifyListeners(); // Notify after loading and potential advancement
  }

  Future<void> _saveSchedule() async {
    final prefs = await SharedPreferences.getInstance();
    try {
      // Assuming Task has toJson method
      final String scheduleJson = jsonEncode(
        _schedule
            .map((dayList) => dayList.map((task) => task.toJson()).toList())
            .toList(),
      );
      await prefs.setString(_scheduleKey, scheduleJson);
    } catch (e) {
      print("Error encoding schedule: $e");
    }
  }

  Future<void> _saveLastOpenedDate(DateTime date) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_lastOpenedKey, date.millisecondsSinceEpoch);
    _lastOpenedDate = date; // Update local state
  }

  // --- Date Handling ---

  void _handleDayChange() {
    final now = DateTime.now();
    final today = DateTime(
      now.year,
      now.month,
      now.day,
    ); // Normalize to midnight

    if (_lastOpenedDate != null) {
      final lastOpenedDay = DateTime(
        _lastOpenedDate!.year,
        _lastOpenedDate!.month,
        _lastOpenedDate!.day,
      );
      final difference = today.difference(lastOpenedDay).inDays;

      if (difference > 0) {
        print("Advancing schedule by $difference days.");
        for (int i = 0; i < difference; i++) {
          if (_schedule.isEmpty) break; // Stop if schedule becomes empty
          // Call the core logic to advance one day
          // This internal call avoids extra saves/notifications if advanceSchedule handles them
          if (_schedule.isNotEmpty) {
            _schedule.removeAt(0);
            for (var dayTasks in _schedule) {
              for (var task in dayTasks) {
                task.daysSinceInit += 1;
              }
            }
          }
        }
        // Save schedule only once after all advancements
        _saveSchedule();
      }
    }

    // Update last opened date to today
    _saveLastOpenedDate(today);
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
