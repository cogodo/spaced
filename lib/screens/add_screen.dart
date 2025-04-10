import 'package:flutter/material.dart';
// import 'package:lr_scheduler/models/task_holder.dart'; // No longer needed here

class AdderScreen extends StatefulWidget {
  final Function(String)
  onAddTask; // Changed callback signature to accept String

  AdderScreen({required this.onAddTask});

  @override
  _AdderScreenState createState() => _AdderScreenState();
}

class _AdderScreenState extends State<AdderScreen> {
  final _taskController = TextEditingController();

  @override
  void dispose() {
    _taskController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Add Task')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _taskController,
              decoration: InputDecoration(labelText: 'Task Description'),
              onSubmitted:
                  (_) => _submitTask(), // Allow submitting with keyboard action
            ),
            SizedBox(height: 16),
            ElevatedButton(onPressed: _submitTask, child: Text('Add Task')),
          ],
        ),
      ),
    );
  }

  void _submitTask() {
    final taskDescription = _taskController.text.trim();
    if (taskDescription.isNotEmpty) {
      // Pass the task description string directly
      widget.onAddTask(taskDescription);
      _taskController.clear();
      // Optional: Show feedback like a Snackbar
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Task "$taskDescription" added!')));
      // Navigation is handled by the parent (SwipeNavigationScreen)
    } else {
      // Optional: Show feedback if field is empty
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please enter a task description.')),
      );
    }
  }
}
