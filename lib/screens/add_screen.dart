import 'package:flutter/material.dart';
import 'package:lr_scheduler/models/task_holder.dart';

class AdderScreen extends StatefulWidget {
  final Function(Task) onAddTask; // Callback to pass the task to the schedule

  AdderScreen({required this.onAddTask});

  @override
  _AdderScreenState createState() => _AdderScreenState();
}

class _AdderScreenState extends State<AdderScreen> {
  final _taskController = TextEditingController();

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
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                // Create a new Task object
                final newTask = Task(
                  _taskController.text,
                  0, // daysSinceInit starts at 0 for new tasks
                );

                // Pass the task to the parent widget
                widget.onAddTask(newTask);

                // Clear the input field and navigate back
                _taskController.clear();
              },
              child: Text('Add Task'),
            ),
          ],
        ),
      ),
    );
  }
}