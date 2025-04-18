import 'package:flutter/material.dart';
import 'package:lr_scheduler/models/schedule_manager.dart';
import 'package:lr_scheduler/models/task_holder.dart';
import 'package:provider/provider.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, bool> _checkedState = {};

  final Map<int, String> _qualityDescriptions = {
    5: 'Perfect response',
    4: 'Correct response after hesitation',
    3: 'Correct response with difficulty',
    2: 'Incorrect response, seemed easy',
    1: 'Incorrect response, remembered correct',
    0: 'Complete blackout',
  };

  @override
  Widget build(BuildContext context) {
    final scheduleManager = Provider.of<ScheduleManager>(context);
    final List<Task> todaysTasks = scheduleManager.getTodaysTasks();

    todaysTasks.forEach((task) {
      _checkedState.putIfAbsent(task.task, () => false);
    });

    return Scaffold(
      appBar: AppBar(
        title: Text("today"),
        actions: [
          IconButton(
            icon: Icon(Icons.settings),
            onPressed: () {
              Navigator.of(context).push(
                PageRouteBuilder(
                  pageBuilder:
                      (context, animation, secondaryAnimation) =>
                          SettingsScreen(),
                  transitionsBuilder: (
                    context,
                    animation,
                    secondaryAnimation,
                    child,
                  ) {
                    // Example: Scale and Fade from center
                    return ScaleTransition(
                      scale: CurvedAnimation(
                        parent: animation,
                        curve: Curves.fastOutSlowIn,
                      ),
                      child: FadeTransition(opacity: animation, child: child),
                    );
                  },
                  transitionDuration: Duration(
                    milliseconds: 400,
                  ), // Adjust duration
                ),
              );
            },
          ),
        ],
      ),
      body:
          todaysTasks.isEmpty
              ? Center(child: Text("NO REVIEWS DUE"))
              : ListView.builder(
                itemCount: todaysTasks.length,
                itemBuilder: (context, index) {
                  final task = todaysTasks[index];
                  final bool isChecked = _checkedState[task.task] ?? false;

                  return CheckboxListTile(
                    title: Text(task.task),
                    value: isChecked,
                    onChanged: (bool? newValue) {
                      if (newValue == true) {
                        setState(() {
                          _checkedState[task.task] = true;
                        });
                        _showQualityPopup(context, task);
                      } else {
                        setState(() {
                          _checkedState[task.task] = false;
                        });
                      }
                    },
                  );
                },
              ),
    );
  }

  Future<void> _showQualityPopup(BuildContext context, Task task) async {
    int? selectedQuality = await showDialog<int>(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        int? groupValue;
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: Text('Rate Response Quality for: "${task.task}"'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children:
                      _qualityDescriptions.entries
                          .map(
                            (entry) => RadioListTile<int>(
                              title: Text('${entry.key}: ${entry.value}'),
                              value: entry.key,
                              groupValue: groupValue,
                              onChanged: (int? value) {
                                setDialogState(() {
                                  groupValue = value;
                                });
                              },
                            ),
                          )
                          .toList()
                          .reversed
                          .toList(),
                ),
              ),
              actions: <Widget>[
                TextButton(
                  child: Text('Submit'),
                  onPressed: () {
                    if (groupValue != null) {
                      Navigator.of(context).pop(groupValue);
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text("Please select a quality score."),
                        ),
                      );
                    }
                  },
                ),
              ],
            );
          },
        );
      },
    );

    final scheduleManager = Provider.of<ScheduleManager>(
      context,
      listen: false,
    );
    if (selectedQuality != null) {
      print("Selected quality: $selectedQuality for task: ${task.task}");
      await scheduleManager.updateTaskReview(task, selectedQuality);
      setState(() {
        _checkedState.remove(task.task);
      });
      print("Task update called. List should refresh.");
    } else {
      print("Quality selection cancelled for task: ${task.task}");
      setState(() {
        _checkedState[task.task] = false;
      });
    }
  }
}
