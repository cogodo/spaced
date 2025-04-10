import 'package:flutter/material.dart';
// import 'package:lr_scheduler/models/task_holder.dart'; // No longer needed here

class AdderScreen extends StatefulWidget {
  // Change callback signature to expect Future<bool>
  final Future<bool> Function(String) onAddTask;

  AdderScreen({required this.onAddTask});

  @override
  _AdderScreenState createState() => _AdderScreenState();
}

class _AdderScreenState extends State<AdderScreen> {
  final _taskController = TextEditingController();
  bool _isAdding = false; // Prevent double submission

  @override
  void dispose() {
    _taskController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Add Review')
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _taskController,
              decoration: InputDecoration(labelText: 'Review Description'),
              onSubmitted:
                  (_) =>
                      _isAdding
                          ? null
                          : _submitTask(), // Submit on keyboard action
            ),
            SizedBox(height: 16),
            // Disable button while adding
            ElevatedButton(
              onPressed: _isAdding ? null : _submitTask,
              child: _isAdding ? CircularProgressIndicator() : Text('Add Review'),
            ),
          ],
        ),
      ),
    );
  }

  // Make _submitTask async to await the callback result
  Future<void> _submitTask() async {
    final taskDescription = _taskController.text.trim();
    if (taskDescription.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please enter a review description.')),
      );
      return;
    }

    // Prevent multiple submissions while waiting
    setState(() {
      _isAdding = true;
    });

    try {
      final bool success = await widget.onAddTask(taskDescription);

      // Check the result from the callback
      if (success) {
        _taskController.clear();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Review "$taskDescription" added!')),
        );
        // Navigation is handled by the parent (SwipeNavigationScreen)
      }
    } finally {
      // Always re-enable the button
      if (mounted) {
        // Check if the widget is still in the tree
        setState(() {
          _isAdding = false;
        });
      }
    }
  }
}
