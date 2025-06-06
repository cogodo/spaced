// For JSON encoding/decoding
import 'package:flutter/foundation.dart'; // For ChangeNotifier
import 'package:spaced/models/task_holder.dart'; // Assuming Task is here
import '../services/logger_service.dart'; // Import our logger service
// Removed algorithm import as SM-2 logic is now in Task
// For max()
import '../services/storage_interface.dart'; // Import storage interface

// Make ScheduleManager a ChangeNotifier to notify listeners of updates
class ScheduleManager with ChangeNotifier {
  // Create a logger instance for this class
  final _logger = getLogger('ScheduleManager');

  final String userId; // Each instance is tied to a user
  final StorageInterface _storage; // Abstract storage interface

  List<Task> _allTasks = []; // Changed from List<List<Task>> _schedule
  int maxRepetitions = 10; // Default value

  // Storage references
  late final StorageDocumentReference _userDocRef;
  late final StorageCollectionReference _tasksCollectionRef;

  // Sync management
  StorageInterface? _cloudStorage; // Reference to Firestore for syncing
  bool _isSyncing = false;

  // Constructor now requires UID and StorageInterface instance
  ScheduleManager({required this.userId, required StorageInterface storage})
    : _storage = storage {
    _logger.info("Constructor called with userId: $userId");
    if (userId.isEmpty) {
      throw ArgumentError("User ID cannot be empty for ScheduleManager");
    }
    _userDocRef = _storage.getUserDocument(userId);
    _tasksCollectionRef = _storage.getUserTasksCollection(userId);
    _logger.info("Initialized for user: $userId");
    // Don't block constructor with async call
    Future.microtask(() => _loadUserData());
  }

  /// Set cloud storage for syncing (call this when Firestore becomes available)
  void setCloudStorage(StorageInterface cloudStorage) {
    _cloudStorage = cloudStorage;
    _logger.info('Cloud storage set, triggering sync...');
    _attemptSync();
  }

  /// Check if there are pending sync operations
  Future<bool> hasPendingSync() async {
    if (_storage.supportsSync) return false; // Already synced
    final pending = await _storage.getPendingSyncOperations(userId);
    return pending.isNotEmpty;
  }

  /// Manually trigger sync (useful for retry buttons or connectivity restored)
  Future<void> triggerSync() async {
    if (_cloudStorage != null && !_isSyncing) {
      await _attemptSync();
    }
  }

  /// Attempt to sync pending operations to cloud storage
  Future<void> _attemptSync() async {
    if (_isSyncing || _cloudStorage == null || _storage.supportsSync) return;

    _isSyncing = true;
    _logger.info('Starting sync process...');

    try {
      final pendingOps = await _storage.getPendingSyncOperations(userId);
      _logger.info('Found ${pendingOps.length} pending sync operations');

      for (final operation in pendingOps) {
        await _syncOperation(operation);
      }

      _logger.info('Sync completed successfully');
    } catch (e, s) {
      _logger.severe('Sync failed: $e', e, s);
    } finally {
      _isSyncing = false;
    }
  }

  /// Sync a single operation to cloud storage
  Future<void> _syncOperation(SyncOperation operation) async {
    if (_cloudStorage == null) return;

    try {
      final cloudUserDoc = _cloudStorage!.getUserDocument(userId);
      final cloudTasksCollection = _cloudStorage!.getUserTasksCollection(
        userId,
      );

      switch (operation.type) {
        case SyncOperationType.create:
        case SyncOperationType.update:
          if (operation.collection == 'users') {
            await cloudUserDoc.set(
              operation.data!,
              options: UniversalSetOptions.mergeOption,
            );
          } else if (operation.collection == 'tasks') {
            await cloudTasksCollection
                .doc(operation.documentId)
                .set(operation.data!);
          }
          break;
        case SyncOperationType.delete:
          if (operation.collection == 'tasks') {
            await cloudTasksCollection.doc(operation.documentId).delete();
          }
          break;
      }

      // Mark as synced
      await _storage.markAsSynced(userId, operation.id);
      _logger.info('Synced operation: ${operation.id}');
    } catch (e) {
      _logger.warning('Failed to sync operation ${operation.id}: $e');
      rethrow; // Re-throw to stop sync process on error
    }
  }

  /// Add pending sync operation (for local storage)
  Future<void> _addPendingSync(
    SyncOperationType type,
    String collection,
    String documentId, [
    Map<String, dynamic>? data,
  ]) async {
    if (_storage.supportsSync) return; // No need to track for Firestore

    final operation = SyncOperation(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      type: type,
      collection: collection,
      documentId: documentId,
      data: data,
      timestamp: DateTime.now(),
    );

    await _storage.addPendingSyncOperation(userId, operation);
  }

  // Getter for all tasks (optional, maybe only expose today's tasks?)
  List<Task> get allTasks => _allTasks;

  // Getter for storage interface (to check sync capabilities)
  StorageInterface get storage => _storage;

  // --- Load User Data --- (Called internally)
  Future<void> _loadUserData() async {
    _logger.info("Loading data for user: $userId");
    try {
      // Load user settings (maxRepetitions, etc.)
      final userDoc = await _userDocRef.get();
      if (userDoc.exists && userDoc.data() != null) {
        final data = userDoc.data()!;
        maxRepetitions = data['maxRepetitions'] as int? ?? 10;
        _logger.info("Loaded maxRepetitions: $maxRepetitions");
        // Load other settings like theme, pro status if stored here
      } else {
        // User document doesn't exist yet (first login?), use defaults
        // Optionally create the document with defaults here
        _logger.info("User document not found, using defaults.");
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
      _logger.info("Loaded ${_allTasks.length} tasks.");

      notifyListeners(); // Notify after loading all data
    } catch (e, s) {
      _logger.severe("ERROR loading user data", e, s);
      _allTasks = []; // Reset state on critical failure
      maxRepetitions = 10;
      notifyListeners(); // Notify about the error state
    }
  }

  // --- Save User Settings --- (Separate from saving tasks)
  Future<void> _saveUserSettings() async {
    _logger.info("Saving settings for user: $userId");
    try {
      // Use set with merge option to create or update
      await _userDocRef.set({
        'maxRepetitions': maxRepetitions,
        // Add other settings like theme preference, pro status etc.
      }, options: UniversalSetOptions.mergeOption);
      _logger.info("Settings saved.");
    } catch (e, s) {
      _logger.severe("Error saving user settings", e, s);
    }
  }

  // --- Persistence for Tasks (Uses local storage) ---

  // --- Core Logic Methods (Modified for local storage) ---

  // Gets tasks due today or earlier
  List<Task> getTodaysTasks() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    _logger.info("Getting tasks for date: $today");

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
    _logger.info("Starting addTask for user $userId: $taskDescription");

    final descriptionLower = taskDescription.toLowerCase().trim();
    if (descriptionLower.isEmpty) {
      _logger.warning("Empty task description provided");
      return false;
    }

    final exists = _allTasks.any(
      (task) => task.task.toLowerCase().trim() == descriptionLower,
    );
    if (exists) {
      _logger.info("Task already exists for user $userId: $taskDescription");
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

    // Add locally first for immediate UI update
    _allTasks.add(newTask);
    _logger.info("Added task locally for user $userId: ${newTask.task}");
    notifyListeners(); // Notify UI immediately

    try {
      // Try to save to storage (Firestore or Local)
      _logger.info("Attempting to save task to storage...");
      await _tasksCollectionRef.doc(newTask.task).set(newTask.toJson());
      _logger.info("Successfully saved task to storage for user $userId");
      return true;
    } catch (e, s) {
      _logger.severe("Error saving task to storage for user $userId: $e", e, s);

      // Add to pending sync if using local storage
      await _addPendingSync(
        SyncOperationType.create,
        'tasks',
        newTask.task,
        newTask.toJson(),
      );

      // Don't revert the local change - let the user keep the task even if save fails
      // This prevents data loss and provides better UX
      _logger.warning(
        "Task saved locally but failed to sync to storage. Will retry later.",
      );

      // Return true because the task was added locally successfully
      return true;
    }
  }

  // Method to update task after review
  Future<void> updateTaskReview(Task taskToUpdate, int quality) async {
    final taskIndex = _allTasks.indexWhere((t) => t.task == taskToUpdate.task);
    if (taskIndex != -1) {
      _allTasks[taskIndex].calculateNextInterval(quality);
      final updatedTask = _allTasks[taskIndex];
      _logger.info(
        "Updated task locally for user $userId: ${updatedTask.task}",
      );
      notifyListeners(); // Update UI immediately

      try {
        // Update the specific task document in local storage
        await _tasksCollectionRef
            .doc(updatedTask.task)
            .update(updatedTask.toJson());
        _logger.info("Updated task in local storage for user $userId.");
      } catch (e, s) {
        _logger.severe("Error updating task in local storage", e, s);

        // Add to pending sync if using local storage
        await _addPendingSync(
          SyncOperationType.update,
          'tasks',
          updatedTask.task,
          updatedTask.toJson(),
        );
      }
    } else {
      _logger.warning(
        "Task ${taskToUpdate.task} not found locally for user $userId.",
      );
    }
  }

  // Method to remove a task (useful for testing/management)
  Future<void> removeTask(Task taskToRemove) async {
    final initialLength = _allTasks.length;
    _allTasks.removeWhere((t) => t.task == taskToRemove.task);
    if (_allTasks.length < initialLength) {
      _logger.info(
        "Removed task locally for user $userId: ${taskToRemove.task}",
      );
      notifyListeners(); // Update UI immediately

      try {
        // Delete the specific task document from local storage
        await _tasksCollectionRef.doc(taskToRemove.task).delete();
        _logger.info("Deleted task from local storage for user $userId.");
      } catch (e, s) {
        _logger.severe("Error deleting task from local storage", e, s);

        // Add to pending sync if using local storage
        await _addPendingSync(
          SyncOperationType.delete,
          'tasks',
          taskToRemove.task,
        );
      }
    } else {
      _logger.warning(
        "Task not found locally for user $userId: ${taskToRemove.task}",
      );
    }
  }

  // Add a method to clear all tasks (useful for testing/reset)
  Future<void> clearAllTasks() async {
    _logger.info("Clearing all tasks locally for user $userId.");
    _allTasks.clear();
    notifyListeners();

    // Delete all tasks from local storage
    try {
      final currentDocs = await _tasksCollectionRef.get();
      for (var doc in currentDocs.docs) {
        await _tasksCollectionRef.doc(doc.id).delete();
      }
      _logger.info("Cleared tasks from local storage for user $userId.");
    } catch (e, s) {
      _logger.severe("Error clearing tasks from local storage", e, s);
    }
  }

  // Method to set the maximum repetitions and save it
  Future<void> setMaxRepetitions(int newValue) async {
    if (newValue < 1) newValue = 1;
    if (newValue == maxRepetitions) return;

    maxRepetitions = newValue;
    _logger.info(
      "Set max repetitions locally to: $maxRepetitions for user $userId",
    );
    notifyListeners(); // Update UI immediately for setting change

    await _saveUserSettings(); // Save setting to user document

    // Check tasks locally first
    List<Task> tasksToDelete = [];
    _allTasks.removeWhere((task) {
      final shouldRemove = task.repetition >= maxRepetitions;
      if (shouldRemove) {
        _logger.info("Marking task for removal: '${task.task}'");
        tasksToDelete.add(task); // Keep track for local storage deletion
      }
      return shouldRemove;
    });

    if (tasksToDelete.isNotEmpty) {
      _logger.info(
        "Removed ${tasksToDelete.length} tasks locally for user $userId.",
      );
      notifyListeners(); // Update UI for task removal

      // Delete tasks from local storage
      try {
        for (var task in tasksToDelete) {
          await _tasksCollectionRef.doc(task.task).delete();
        }
        _logger.info("Deleted tasks from local storage for user $userId.");
      } catch (e, s) {
        _logger.severe("Error deleting tasks in local storage", e, s);
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
