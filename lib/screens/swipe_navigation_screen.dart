import 'package:flutter/material.dart';
import 'package:lr_scheduler/screens/all_review_items_screen.dart';
import 'home_screen.dart';
import 'add_screen.dart';
import 'package:lr_scheduler/models/task_holder.dart';
import 'package:lr_scheduler/models/schedule_manager.dart';
import 'package:lr_scheduler/utils/algorithm.dart';
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
    final scheduleManager = Provider.of<ScheduleManager>(context);

    List<String> currentReviewItems = [];
    if (scheduleManager.schedule.isNotEmpty) {
      currentReviewItems =
          scheduleManager.schedule[0].map((task) => task.task).toList();
    }

    return PageView(
      controller: _pageController,
      children: [
        HomeScreen(reviewItems: currentReviewItems),
        AdderScreen(
          onAddTask: (task) {
            scheduleManager.addTask(task);
            _pageController.jumpToPage(0);
          },
        ),
        AllReviewItemsScreen(schedule: scheduleManager.schedule),
      ],
    );
  }
}
