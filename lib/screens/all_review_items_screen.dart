import 'package:flutter/material.dart';
import 'package:lr_scheduler/models/task_holder.dart';

class AllReviewItemsScreen extends StatefulWidget {
  final List<List<Task>> schedule;

  const AllReviewItemsScreen({super.key, required this.schedule});

  @override
  _AllReviewItemsScreenState createState() => _AllReviewItemsScreenState();
}

class _AllReviewItemsScreenState extends State<AllReviewItemsScreen> {
  List<Task> _getUniqueItems() {
    final uniqueTasks = <String>{};
    final uniqueTaskList = <Task>[];

    for (var daySchedule in widget.schedule) {
      for (var task in daySchedule) {
        if (!uniqueTasks.contains(task.task)) {
          uniqueTasks.add(task.task);
          uniqueTaskList.add(task);
        }
      }
    }

    return uniqueTaskList;
  }

  @override
  Widget build(BuildContext context) {
    final uniqueItems = _getUniqueItems();

    return Scaffold(
      appBar: AppBar(title: Text('All Review Items')),
      body: ListView.builder(
        itemCount: uniqueItems.length,
        itemBuilder: (context, index) {
          final task = uniqueItems[index];
          return ListTile(
            title: Text(task.task),
            subtitle: Text('Days since start: ${task.daysSinceInit}'),
            leading: Icon(Icons.assignment),
          );
        },
      ),
    );
  }
}
