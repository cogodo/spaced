import 'package:flutter/material.dart';
import 'package:spaced/screens/all_review_items_screen.dart';
import 'home_screen.dart';
import 'add_screen.dart';
// import 'package:spaced/models/task_holder.dart'; // No longer needed directly here
import 'package:spaced/models/schedule_manager.dart';
// import 'package:spaced/utils/algorithm.dart'; // No longer used
import 'package:provider/provider.dart';
// Import main.dart to access the global key

class SwipeNavigationScreen extends StatefulWidget {
  const SwipeNavigationScreen({super.key});

  @override
  State<SwipeNavigationScreen> createState() => _SwipeNavigationScreenState();
}

class _SwipeNavigationScreenState extends State<SwipeNavigationScreen> {
  final PageController _pageController = PageController(initialPage: 0);
  bool _showConfirmation = false;
  String _confirmationText = "Review Added!";

  void _showBottomConfirmation(String text) {
    setState(() {
      _confirmationText = text;
      _showConfirmation = true;
    });

    Future.delayed(Duration(seconds: 2), () {
      if (mounted) {
        setState(() => _showConfirmation = false);
      }
    });
  }

  // Method to handle adding a task
  Future<bool> _handleAddTask(String taskDescription) async {
    // Access ScheduleManager here
    final scheduleManager = Provider.of<ScheduleManager>(
      context,
      listen: false,
    );
    final bool success = await scheduleManager.addTask(taskDescription);

    // Check if the widget is still mounted after the async operation
    if (!mounted) return success;

    if (success) {
      _showBottomConfirmation(
        'Task "$taskDescription" added!',
      ); // Use confirmation
    } else {
      // Add a small shake animation to indicate error
      // Consider showing the error via _showBottomConfirmation too
      _showBottomConfirmation(
        'Task "$taskDescription" already exists!',
      ); // Or use a different style
      _pageController
          .animateTo(
            _pageController.offset + 10.0,
            duration: Duration(milliseconds: 100),
            curve: Curves.easeInOut,
          )
          .then((_) {
            _pageController
                .animateTo(
                  _pageController.offset - 20.0,
                  duration: Duration(milliseconds: 100),
                  curve: Curves.easeInOut,
                )
                .then((_) {
                  _pageController.animateTo(
                    _pageController.offset + 10.0,
                    duration: Duration(milliseconds: 100),
                    curve: Curves.easeInOut,
                  );
                });
          });
    }
    return success; // Return the result to AdderScreen
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Get ScheduleManager instance (can still be used elsewhere if needed)
    final scheduleManager = Provider.of<ScheduleManager>(context);

    return Scaffold(
      body: Stack(
        children: [
          PageView(
            controller: _pageController,
            children: [
              HomeScreen(),
              AdderScreen(
                // Pass the reference to the handler method
                onAddTask: _handleAddTask,
              ),
              AllReviewItemsScreen(
                allTasks: scheduleManager.allTasks,
                onDeleteTask:
                    scheduleManager.removeTask, // Pass the removeTask method
              ),
            ],
          ),
          Positioned(
            bottom: 20,
            left: 20,
            right: 20,
            child: AnimatedOpacity(
              duration: Duration(milliseconds: 300),
              opacity: _showConfirmation ? 1.0 : 0.0,
              child: Material(
                borderRadius: BorderRadius.circular(12),
                elevation: 6,
                color: Colors.black87,
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    vertical: 12.0,
                    horizontal: 16.0,
                  ),
                  child: Text(
                    _confirmationText,
                    style: TextStyle(color: Colors.white),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
