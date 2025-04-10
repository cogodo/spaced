import 'package:flutter/material.dart';
import 'package:lr_scheduler/models/task_holder.dart';
import 'package:intl/intl.dart'; // For date formatting

class AllReviewItemsScreen extends StatefulWidget {
  final List<Task> allTasks;
  final Function(Task) onDeleteTask;

  const AllReviewItemsScreen({
    super.key,
    required this.allTasks,
    required this.onDeleteTask,
  });

  @override
  _AllReviewItemsScreenState createState() => _AllReviewItemsScreenState();
}

class _AllReviewItemsScreenState extends State<AllReviewItemsScreen> {
  String _formatDate(DateTime? date) {
    if (date == null) {
      return 'Not reviewed yet';
    }
    return DateFormat.yMd().format(date); // Example format: 7/10/2024
  }

  @override
  Widget build(BuildContext context) {
    final allItems = widget.allTasks;

    allItems.sort((a, b) => a.task.compareTo(b.task));

    return Scaffold(
      appBar: AppBar(title: Text('All Review Items (${allItems.length})')),
      body:
          allItems.isEmpty
              ? Center(child: Text("No tasks added yet."))
              : ListView.builder(
                itemCount: allItems.length,
                itemBuilder: (context, index) {
                  final task = allItems[index];
                  return ListTile(
                    title: Text(task.task),
                    subtitle: Text(
                      'Next Review: ${_formatDate(task.nextReviewDate)}\nE-Factor: ${task.eFactor.toStringAsFixed(2)} | Reps: ${task.repetition}',
                    ),
                    leading: Icon(Icons.assignment),
                    trailing: IconButton(
                      icon: Icon(Icons.delete, color: Colors.red),
                      onPressed: () {
                        final taskToDelete = task; // Capture task variable
                        // Call the callback passed from the parent
                        widget.onDeleteTask(taskToDelete);

                        // Remove any existing snackbar first
                        ScaffoldMessenger.of(context).removeCurrentSnackBar();
                        // Then show the new one immediately
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(
                              'Task "${taskToDelete.task}" deleted.',
                            ),
                            duration: Duration(
                              seconds: 2,
                            ), // Keep duration, but it gets replaced
                          ),
                        );
                      },
                    ),
                    isThreeLine: true, // Allow more space for subtitle
                  );
                },
              ),
    );
  }
}
