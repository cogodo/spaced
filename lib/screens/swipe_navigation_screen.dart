import 'package:flutter/material.dart';
import 'package:lr_scheduler/screens/all_review_items_screen.dart';
import 'home_screen.dart';
import 'add_screen.dart';
// import 'package:lr_scheduler/models/task_holder.dart'; // No longer needed directly here
import 'package:lr_scheduler/models/schedule_manager.dart';
// import 'package:lr_scheduler/utils/algorithm.dart'; // No longer used
import 'package:provider/provider.dart';

class SwipeNavigationScreen extends StatefulWidget {
  @override
  _SwipeNavigationScreenState createState() => _SwipeNavigationScreenState();
}

class _SwipeNavigationScreenState extends State<SwipeNavigationScreen> {
  final PageController _pageController = PageController(initialPage: 0);

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Get ScheduleManager instance
    final scheduleManager = Provider.of<ScheduleManager>(context);

    return PageView(
      controller: _pageController,
      children: [
        // HomeScreen fetches its own data
        HomeScreen(),
        AdderScreen(
          // Pass the correct callback signature (String)
          onAddTask: (String taskDescription) {
            scheduleManager.addTask(taskDescription);
            _pageController.jumpToPage(0); // Jump back after adding
          },
        ),
        // Pass the flat list of all tasks using the correct parameter name
        AllReviewItemsScreen(allTasks: scheduleManager.allTasks),
      ],
    );
  }
}
