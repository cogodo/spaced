import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:lr_scheduler/models/schedule_manager.dart';
import 'package:lr_scheduler/models/task_holder.dart'; // Assuming Task is defined here
// Import your scheduling algorithm if it's separate
// import 'package:lr_scheduler/utils/algorithm.dart';
import 'package:shared_preferences/shared_preferences.dart';

// --- Helper Extensions/Methods for Testing Persistence ---
// Moved extensions to the top

// Option 1: Add static getters for keys in ScheduleManager
extension ScheduleManagerTestKeys on ScheduleManager {
  // Use the actual keys directly from ScheduleManager if possible,
  // otherwise define them here matching the manager's implementation.
  static String scheduleKeyForTest() => 'schedule';
  static String lastOpenedKeyForTest() => 'lastOpenedDate';
}

// Option 2: Add a method to ScheduleManager to get the JSON representation
extension ScheduleManagerJsonExport on ScheduleManager {
  String scheduleToJsonForTest() {
    // Replicate the JSON encoding logic used in _saveSchedule
    // This assumes Task has toJson()
    try {
      // Access the private _schedule if possible, or use the public getter
      return jsonEncode(
        schedule // Use the public getter 'schedule'
            .map((dayList) => dayList.map((task) => task.toJson()).toList())
            .toList(),
      );
    } catch (e) {
      print("Error encoding schedule for test: $e");
      return '[]'; // Return empty list on error
    }
  }
}

// Helper function to check if a specific task exists on a given day index
bool taskExistsOnDay(ScheduleManager manager, int dayIndex, String taskName) {
  if (dayIndex < 0 || dayIndex >= manager.schedule.length) {
    return false; // Day index out of bounds
  }
  return manager.schedule[dayIndex].any((task) => task.task == taskName);
}

void main() {
  // --- Test Setup ---

  // Use late initialization for the manager
  late ScheduleManager scheduleManager;

  // Mock SharedPreferences before each test
  setUp(() async {
    // Use in-memory implementation for SharedPreferences
    SharedPreferences.setMockInitialValues({});
    // Create a new instance for each test to ensure isolation
    // Note: If ScheduleManager relies heavily on async loading in its constructor or an init method,
    // you might need to make setUp async and await its initialization.
    // Assuming ScheduleManager._internal() calls _loadData synchronously or we handle async later.
    scheduleManager = ScheduleManager();
    // If _loadData is async and not called in constructor, you might need:
    // await scheduleManager._loadData(); // Or expose an init method
  });

  // --- Test Groups ---

  group('ScheduleManager Task Placement Tests', () {
    testWidgets('Newly added task appears on the expected initial day(s)', (
      WidgetTester tester,
    ) async {
      // Arrange: Create a task
      final task1 = Task(task: 'Learn Flutter Testing');

      // Act: Add the task
      scheduleManager.addTask(task1);
      // You might need await if addTask involves async operations like saving
      // await scheduleManager.addTask(task1);

      // Assert: Verify task placement based on your algorithm's initial scheduling
      // Example: Assuming a new task appears on day 0 and day 2 initially
      expect(
        taskExistsOnDay(scheduleManager, 0, 'Learn Flutter Testing'),
        isTrue,
        reason: "Task should be on day 0",
      );
      expect(
        taskExistsOnDay(scheduleManager, 1, 'Learn Flutter Testing'),
        isFalse,
        reason: "Task should NOT be on day 1",
      );
      expect(
        taskExistsOnDay(scheduleManager, 2, 'Learn Flutter Testing'),
        isTrue,
        reason: "Task should be on day 2",
      );
      // Add more checks for other days if necessary
    });

    testWidgets(
      'Task scheduled for a future day appears after advancing schedule',
      (WidgetTester tester) async {
        // Arrange: Add a task known to appear later
        final taskFuture = Task(task: 'Review Advanced Concepts');
        // Assume your algorithm schedules this for day 3 initially (relative to addition)
        scheduleManager.addTask(taskFuture);

        // Act: Advance the schedule twice
        scheduleManager.advanceSchedule(); // Now day 0 is original day 1
        scheduleManager.advanceSchedule(); // Now day 0 is original day 2

        // Assert: The task should now be on the *new* day 0 (which was original day 2)
        // or day 1 (original day 3) depending on how your algorithm places it.
        // Let's assume it should appear on original day 3.
        expect(
          taskExistsOnDay(scheduleManager, 0, 'Review Advanced Concepts'),
          isFalse,
          reason: "Task should not be on current day 0 (original day 2)",
        );
        expect(
          taskExistsOnDay(scheduleManager, 1, 'Review Advanced Concepts'),
          isTrue,
          reason: "Task should be on current day 1 (original day 3)",
        );
      },
    );

    testWidgets(
      'Multiple tasks added appear on their respective correct days',
      (WidgetTester tester) async {
        // Arrange: Add multiple tasks with potentially different schedules
        final taskA = Task(task: 'Task A'); // Assume appears day 0, 2
        final taskB = Task(task: 'Task B'); // Assume appears day 1, 4

        // Act
        scheduleManager.addTask(taskA);
        scheduleManager.addTask(taskB);

        // Assert: Check initial placement
        expect(
          taskExistsOnDay(scheduleManager, 0, 'Task A'),
          isTrue,
          reason: "A on day 0",
        );
        expect(
          taskExistsOnDay(scheduleManager, 0, 'Task B'),
          isFalse,
          reason: "B NOT on day 0",
        );

        expect(
          taskExistsOnDay(scheduleManager, 1, 'Task A'),
          isFalse,
          reason: "A NOT on day 1",
        );
        expect(
          taskExistsOnDay(scheduleManager, 1, 'Task B'),
          isTrue,
          reason: "B on day 1",
        );

        expect(
          taskExistsOnDay(scheduleManager, 2, 'Task A'),
          isTrue,
          reason: "A on day 2",
        );
        expect(
          taskExistsOnDay(scheduleManager, 2, 'Task B'),
          isFalse,
          reason: "B NOT on day 2",
        );

        expect(
          taskExistsOnDay(scheduleManager, 3, 'Task A'),
          isFalse,
          reason: "A NOT on day 3",
        );
        expect(
          taskExistsOnDay(scheduleManager, 3, 'Task B'),
          isFalse,
          reason: "B NOT on day 3",
        );

        expect(
          taskExistsOnDay(scheduleManager, 4, 'Task A'),
          isFalse,
          reason: "A NOT on day 4",
        );
        expect(
          taskExistsOnDay(scheduleManager, 4, 'Task B'),
          isTrue,
          reason: "B on day 4",
        );
      },
    );

    testWidgets(
      'Advancing schedule removes past days and shifts future tasks correctly',
      (WidgetTester tester) async {
        // Arrange: Add tasks
        final taskA = Task(task: 'Task A'); // Assume day 0, 2
        final taskB = Task(task: 'Task B'); // Assume day 1, 4
        scheduleManager.addTask(taskA);
        scheduleManager.addTask(taskB);

        final initialDayCount = scheduleManager.schedule.length;

        // Act: Advance one day
        scheduleManager.advanceSchedule();

        // Assert:
        // 1. Schedule length might decrease or stay same depending on generation logic
        //    expect(scheduleManager.schedule.length, lessThanOrEqualTo(initialDayCount)); // Or specific length if known
        // 2. Day 0 (original day 1) should now have Task B
        expect(
          taskExistsOnDay(scheduleManager, 0, 'Task A'),
          isFalse,
          reason: "A should be gone from current day 0",
        );
        expect(
          taskExistsOnDay(scheduleManager, 0, 'Task B'),
          isTrue,
          reason: "B should be on current day 0",
        );
        // 3. Day 1 (original day 2) should now have Task A
        expect(
          taskExistsOnDay(scheduleManager, 1, 'Task A'),
          isTrue,
          reason: "A should be on current day 1",
        );
        expect(
          taskExistsOnDay(scheduleManager, 1, 'Task B'),
          isFalse,
          reason: "B should NOT be on current day 1",
        );
        // 4. Day 3 (original day 4) should now have Task B
        expect(
          taskExistsOnDay(scheduleManager, 3, 'Task B'),
          isTrue,
          reason: "B should be on current day 3",
        );
      },
    );

    testWidgets(
      'Persistence: Advancing schedule across multiple days works correctly after reload',
      (WidgetTester tester) async {
        // Arrange:
        // Simulate app closing and reopening days later by manipulating the mock values *before* creating the manager

        // 1. Set up initial state and save it
        final initialPrefs = <String, Object>{};
        final initialScheduleManager =
            ScheduleManager(); // Temporary instance for setup
        final task1 = Task(task: 'Persistent Task'); // Assume appears day 0, 3
        initialScheduleManager.addTask(task1);
        // Manually simulate saving (get the JSON representation)
        final scheduleJson =
            initialScheduleManager
                .scheduleToJsonForTest(); // Need to expose this or replicate logic
        final lastOpened = DateTime.now().subtract(
          const Duration(days: 2),
        ); // Simulate last opened 2 days ago
        initialPrefs[ScheduleManagerTestKeys.scheduleKeyForTest()] =
            scheduleJson; // Need static keys or expose them
        initialPrefs[ScheduleManagerTestKeys.lastOpenedKeyForTest()] =
            lastOpened.millisecondsSinceEpoch;

        // 2. Set mock values for the *actual* test instance
        SharedPreferences.setMockInitialValues(initialPrefs);

        // Act: Create the manager for the test - it should load and handle the day change
        scheduleManager = ScheduleManager();
        // If loading is async, await it: await scheduleManager.ensureInitialized();

        // Assert: Check schedule after loading and automatic advancement (2 days passed)
        // Original day 0, 1 are gone. Original day 2 is now day 0. Original day 3 is now day 1.
        expect(
          taskExistsOnDay(scheduleManager, 0, 'Persistent Task'),
          isFalse,
          reason: "Task should not be on current day 0 (original day 2)",
        );
        expect(
          taskExistsOnDay(scheduleManager, 1, 'Persistent Task'),
          isTrue,
          reason: "Task should be on current day 1 (original day 3)",
        );
      },
    );
  });
}
