import 'package:flutter/material.dart';
import 'package:spaced/screens/all_review_items_screen.dart';
import 'home_screen.dart';
import 'add_screen.dart';
import 'chat_screen.dart';
import 'user_profile_screen.dart';
import 'package:spaced/models/schedule_manager.dart';
import 'package:provider/provider.dart';
import 'dart:async';
import '../widgets/theme_logo.dart';
import 'package:go_router/go_router.dart';
import '../routing/route_constants.dart';
import 'dart:html' as html;

class TabNavigationScreen extends StatefulWidget {
  final Widget child; // Child widget from router

  const TabNavigationScreen({super.key, required this.child});

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

  // Helper method to get selected navigation index from current route
  int _getSelectedIndex(String currentPath) {
    switch (currentPath) {
      case Routes.appHome:
        return 0; // app.getspaced.app/
      case Routes.appAdd:
        return 1; // app.getspaced.app/add
      case Routes.appAll:
        return 2; // app.getspaced.app/all
      case Routes.appChat:
        return 3; // app.getspaced.app/chat
      default:
        return 0;
    }
  }

  // Helper method to navigate to route by index
  void _navigateToIndex(BuildContext context, int index) {
    final routes = [
      Routes.appHome, // /
      Routes.appAdd, // /add
      Routes.appAll, // /all
      Routes.appChat, // /chat
    ];
    context.go(routes[index]);
  }

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 600;
    final currentPath = GoRouterState.of(context).matchedLocation;
    final selectedIndex = _getSelectedIndex(currentPath);

    return Scaffold(
      body: Column(
        children: [
          // Header with logo and profile
          _buildHeader(context),

          // Main content area
          Expanded(
            child: Row(
              children: [
                // Desktop navigation rail
                if (isDesktop)
                  Container(
                    width: 120,
                    height: double.infinity,
                    child: Center(
                      child: NavigationRail(
                        selectedIndex: selectedIndex,
                        onDestinationSelected:
                            (index) => _navigateToIndex(context, index),
                        labelType: NavigationRailLabelType.all,
                        backgroundColor:
                            Theme.of(context).scaffoldBackgroundColor,
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
                            icon: Icon(Icons.chat),
                            label: Text('Chat'),
                          ),
                        ],
                        minWidth: 120,
                        useIndicator: true,
                      ),
                    ),
                  ),

                // Main content from router
                Expanded(
                  child: Container(
                    padding: EdgeInsets.symmetric(
                      horizontal: isDesktop ? 80 : 20,
                      vertical: 20,
                    ),
                    child: widget.child, // Router provides the child
                  ),
                ),
              ],
            ),
          ),
        ],
      ),

      // Mobile bottom navigation
      bottomNavigationBar:
          !isDesktop
              ? BottomNavigationBar(
                currentIndex: selectedIndex,
                onTap: (index) => _navigateToIndex(context, index),
                backgroundColor: Theme.of(context).scaffoldBackgroundColor,
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
                    icon: Icon(Icons.chat),
                    label: 'Chat',
                  ),
                ],
                selectedFontSize: 14,
                iconSize: 28,
                type: BottomNavigationBarType.fixed,
              )
              : null,
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Container(
      height: 100,
      color: Theme.of(context).scaffoldBackgroundColor,
      padding: EdgeInsets.symmetric(horizontal: 30, vertical: 15),
      child: Row(
        children: [
          // Logo - now redirects to landing domain!
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Container(
              width: 100,
              height: 100,
              child: Tooltip(
                message: 'Return to landing page',
                child: MouseRegion(
                  cursor: SystemMouseCursors.click,
                  child: GestureDetector(
                    onTap: () {
                      final currentHost = html.window.location.host;
                      if (currentHost.contains('localhost') ||
                          currentHost.contains('127.0.0.1')) {
                        context.go(Routes.landing);
                      } else {
                        html.window.location.href =
                            'https://${Domains.landing}/';
                      }
                    },
                    child: Center(child: ThemeLogo(size: 60)),
                  ),
                ),
              ),
            ),
          ),

          const Spacer(),

          // Profile icon - simple app-domain routing!
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Container(
              width: 100,
              height: 100,
              child: Tooltip(
                message: 'Profile',
                child: MouseRegion(
                  cursor: SystemMouseCursors.click,
                  child: GestureDetector(
                    onTap: () => context.go(Routes.appProfile), // /profile
                    child: Center(
                      child: Icon(
                        Icons.account_circle,
                        size: 60,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    ),
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
