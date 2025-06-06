import 'package:flutter/material.dart';
import 'package:spaced/screens/all_review_items_screen.dart';
import 'home_screen.dart';
import 'add_screen.dart';
import 'chat_screen.dart';
import 'user_profile_screen.dart';
import 'package:spaced/models/schedule_manager.dart';
import 'package:provider/provider.dart';
import 'dart:async';

class TabNavigationScreen extends StatefulWidget {
  final VoidCallback onNavigateToLanding;

  const TabNavigationScreen({super.key, required this.onNavigateToLanding});

  @override
  State<TabNavigationScreen> createState() => _TabNavigationScreenState();
}

class _TabNavigationScreenState extends State<TabNavigationScreen> {
  int _currentIndex = 0;
  bool _showConfirmation = false;
  String _confirmationText = "Review Added!";
  Timer? _confirmationTimer;

  @override
  void initState() {
    super.initState();
  }

  // Method to show a confirmation message
  void _showConfirmationMessage(String text) {
    // Cancel any existing timer to avoid conflicts
    _confirmationTimer?.cancel();

    setState(() {
      _confirmationText = text;
      _showConfirmation = true;
    });

    // Start a new timer
    _confirmationTimer = Timer(Duration(seconds: 3), () {
      if (mounted) {
        setState(() => _showConfirmation = false);
      }
    });
  }

  @override
  void dispose() {
    // Clean up timer when widget is disposed
    _confirmationTimer?.cancel();
    super.dispose();
  }

  // Method to handle adding a task
  Future<bool> _handleAddTask(String taskDescription) async {
    // Access ScheduleManager
    final scheduleManager = Provider.of<ScheduleManager>(
      context,
      listen: false,
    );
    final bool success = await scheduleManager.addTask(taskDescription);

    // Check if the widget is still mounted after the async operation
    if (!mounted) return success;

    if (success) {
      _showConfirmationMessage('Task "$taskDescription" added!');
    } else {
      _showConfirmationMessage('Task "$taskDescription" already exists!');
    }

    return success;
  }

  @override
  Widget build(BuildContext context) {
    // Get ScheduleManager instance
    final scheduleManager = Provider.of<ScheduleManager>(context);
    final isDesktop = MediaQuery.of(context).size.width > 600;

    // Create a list of screens that we'll display
    final screens = [
      HomeScreen(),
      AdderScreen(onAddTask: _handleAddTask),
      AllReviewItemsScreen(
        allTasks: scheduleManager.allTasks,
        onDeleteTask: scheduleManager.removeTask,
      ),
      UserProfileScreen(),
      ChatScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        elevation: 0,
        leading: Padding(
          padding: const EdgeInsets.all(8.0),
          child: GestureDetector(
            onTap: widget.onNavigateToLanding,
            child: Container(
              decoration: BoxDecoration(
                color: Theme.of(
                  context,
                ).colorScheme.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                Icons.psychology,
                color: Theme.of(context).colorScheme.primary,
                size: 32,
              ),
            ),
          ),
        ),
        automaticallyImplyLeading: false,
      ),
      body: Row(
        children: [
          // For desktop layouts, show the navigation rail
          if (isDesktop)
            NavigationRail(
              selectedIndex: _currentIndex,
              onDestinationSelected: (index) {
                setState(() {
                  _currentIndex = index;
                });
              },
              labelType: NavigationRailLabelType.all,
              backgroundColor: Theme.of(context).scaffoldBackgroundColor,
              destinations: [
                NavigationRailDestination(
                  icon: Icon(Icons.home),
                  label: Text('Today'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.add_circle_outline),
                  label: Text('Add'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.list),
                  label: Text('All Items'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.person),
                  label: Text('Profile'),
                ),
                NavigationRailDestination(
                  icon: Icon(Icons.chat),
                  label: Text('Chat'),
                ),
              ],
              // Make the rail wider for better visibility
              minWidth: 120,
              useIndicator: true,
            ),

          // Main content area
          Expanded(
            child: Stack(
              children: [
                // Main content
                Container(
                  padding: EdgeInsets.symmetric(
                    horizontal: isDesktop ? 80 : 20,
                    vertical: 20,
                  ),
                  child: screens[_currentIndex],
                ),

                // Confirmation message
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
                      color: Theme.of(context).colorScheme.primary,
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          vertical: 16.0,
                          horizontal: 24.0,
                        ),
                        child: Text(
                          _confirmationText,
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.onPrimary,
                            fontSize: 16,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),

      // Use a bottom navigation bar for mobile only
      bottomNavigationBar:
          !isDesktop
              ? BottomNavigationBar(
                currentIndex: _currentIndex,
                onTap: (index) {
                  setState(() {
                    _currentIndex = index;
                  });
                },
                backgroundColor: Theme.of(context).scaffoldBackgroundColor,
                // Use the text color for items to match theme
                selectedItemColor: Theme.of(context).colorScheme.primary,
                unselectedItemColor: Theme.of(
                  context,
                ).textTheme.bodyMedium?.color?.withAlpha(155),
                items: [
                  BottomNavigationBarItem(
                    icon: Icon(Icons.home),
                    label: 'Today',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.add_circle_outline),
                    label: 'Add',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.list),
                    label: 'All Items',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.person),
                    label: 'Profile',
                  ),
                  BottomNavigationBarItem(
                    icon: Icon(Icons.chat),
                    label: 'Chat',
                  ),
                ],
                // Ensure it's large enough for easy touch
                selectedFontSize: 14,
                iconSize: 28,
                type: BottomNavigationBarType.fixed, // Ensure all items fit
              )
              : null,
    );
  }
}
