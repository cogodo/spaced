import 'package:flutter/material.dart';
import 'package:spaced/models/schedule_manager.dart';
import 'package:spaced/models/task_holder.dart';
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
    final isDesktop = MediaQuery.of(context).size.width > 600;

    todaysTasks.forEach((task) {
      _checkedState.putIfAbsent(task.task, () => false);
    });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Title section with stats
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 16.0),
          child: Row(
            children: [
              Text(
                'Today\'s Reviews',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              SizedBox(width: 16),
              Chip(
                label: Text(
                  '${todaysTasks.length} items',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                backgroundColor: Theme.of(context).colorScheme.primary,
                padding: EdgeInsets.symmetric(horizontal: 8),
              ),
              Spacer(),
              IconButton(
                icon: Icon(Icons.settings, size: 28),
                splashRadius: 28,
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
                        return FadeTransition(opacity: animation, child: child);
                      },
                    ),
                  );
                },
              ),
            ],
          ),
        ),

        // Empty state
        if (todaysTasks.isEmpty)
          Expanded(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.check_circle_outline,
                    size: 86,
                    color: Colors.grey.shade400,
                  ),
                  SizedBox(height: 24),
                  Text(
                    'No reviews due today',
                    style: TextStyle(fontSize: 24, color: Colors.grey.shade700),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Add new items from the "Add" tab',
                    style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
          ),

        // List of tasks
        if (todaysTasks.isNotEmpty)
          Expanded(
            child: ListView.builder(
              itemCount: todaysTasks.length,
              itemBuilder: (context, index) {
                final task = todaysTasks[index];
                final bool isChecked = _checkedState[task.task] ?? false;

                return Card(
                  margin: EdgeInsets.symmetric(vertical: 8),
                  elevation: 1,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(12),
                    onTap: () {
                      if (!isChecked) {
                        setState(() {
                          _checkedState[task.task] = true;
                        });
                        _showQualityPopup(context, task);
                      }
                    },
                    child: Padding(
                      padding: EdgeInsets.symmetric(
                        vertical: isDesktop ? 24.0 : 16.0,
                        horizontal: 16.0,
                      ),
                      child: Row(
                        children: [
                          // Checkbox - larger and more visible
                          Transform.scale(
                            scale: isDesktop ? 1.5 : 1.2,
                            child: Checkbox(
                              value: isChecked,
                              onChanged: (bool? newValue) {
                                if (newValue == true) {
                                  setState(() {
                                    _checkedState[task.task] = true;
                                  });
                                  _showQualityPopup(context, task);
                                }
                              },
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(4),
                              ),
                            ),
                          ),
                          SizedBox(width: isDesktop ? 16 : 8),

                          // Task text
                          Expanded(
                            child: Text(
                              task.task,
                              style: TextStyle(
                                fontSize: isDesktop ? 20 : 18,
                                decoration:
                                    isChecked
                                        ? TextDecoration.lineThrough
                                        : null,
                                color: isChecked ? Colors.grey : null,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
      ],
    );
  }

  Future<void> _showQualityPopup(BuildContext context, Task task) async {
    final isDesktop = MediaQuery.of(context).size.width > 600;
    int? selectedQuality = await showDialog<int>(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        int? groupValue;
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Rate Response Quality'),
                  SizedBox(height: 8),
                  Text(
                    '"${task.task}"',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.normal,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
              content: Container(
                width: isDesktop ? 500 : 300,
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children:
                        _qualityDescriptions.entries
                            .map(
                              (entry) => RadioListTile<int>(
                                title: Text(
                                  '${entry.key}: ${entry.value}',
                                  style: TextStyle(
                                    fontSize: isDesktop ? 18 : 16,
                                  ),
                                ),
                                value: entry.key,
                                groupValue: groupValue,
                                onChanged: (int? value) {
                                  setDialogState(() {
                                    groupValue = value;
                                  });
                                },
                                contentPadding: EdgeInsets.symmetric(
                                  vertical: isDesktop ? 12 : 8,
                                  horizontal: 16,
                                ),
                              ),
                            )
                            .toList()
                            .reversed
                            .toList(),
                  ),
                ),
              ),
              actions: <Widget>[
                TextButton(
                  child: Text(
                    'Cancel',
                    style: TextStyle(fontSize: isDesktop ? 16 : 14),
                  ),
                  onPressed: () => Navigator.of(context).pop(),
                ),
                ElevatedButton(
                  child: Text(
                    'Submit',
                    style: TextStyle(fontSize: isDesktop ? 16 : 14),
                  ),
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
              actionsPadding: EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 12,
              ),
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
