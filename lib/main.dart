import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lr_scheduler/models/task_holder.dart';
import 'package:lr_scheduler/utils/algorithm.dart';
import 'package:lr_scheduler/screens/swipe_navigation_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [ChangeNotifierProvider(create: (_) => ScheduleProvider())],
      child: MyApp(),
    ),
  );
}

class ScheduleProvider with ChangeNotifier {
  List<List<Task>> schedule = generateSchedule([]);

  void addTask(Task task) {
    scheduleTask(schedule, task, 5);
    notifyListeners();
  }
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Review App',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: SwipeNavigationScreen(), // Set HomeScreen as the initial screen
    );
  }
}
