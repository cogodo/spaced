import 'package:flutter/material.dart';
import 'package:lr_scheduler/screens/all_review_items_screen.dart';
import 'home_screen.dart';
import 'add_screen.dart';
import 'package:lr_scheduler/models/task_holder.dart';
import 'package:lr_scheduler/utils/algorithm.dart';

class SwipeNavigationScreen extends StatefulWidget {
  @override
  _SwipeNavigationScreenState createState() => _SwipeNavigationScreenState();
}

class _SwipeNavigationScreenState extends State<SwipeNavigationScreen> {
  final PageController _pageController = PageController(initialPage: 0);

  // Shared schedule for tasks
  List<List<Task>> schedule = generateSchedule([]);

  // Shared list of review items for display
  List<String> reviewItems = [
    'Review Chapter 1',
    'Review Lecture Notes',
    'Practice Problems',
  ];

  void _addTask(Task task) {
    setState(() {
      // Add the task to the schedule
      scheduleTask(
        schedule,
        task,
        5,
      ); // Assume perfect response for the first addition

      // Add the task description to the reviewItems for display
      reviewItems.add(task.task);

      // Navigate back to the home screen
      _pageController.jumpToPage(0);
    });
  }

  void _advanceDay() {
    setState(() {
    });
  }

  @override
  Widget build(BuildContext context) {
    return PageView(
      controller: _pageController,
      children: [
        HomeScreen(reviewItems: reviewItems),
        AdderScreen(
          onAddTask: (task) {
            _addTask(task);
            // Use jumpToPage instead of animateToPage to avoid navigation stack issues
          },
        ),
        AllReviewItemsScreen(schedule: schedule),
      ],
    );
  }
}
