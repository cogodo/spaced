import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../widgets/chat_history_sidebar.dart';
import '../routing/route_constants.dart';
import '../screens/all_review_items_screen.dart';

class TabNavigationScreen extends StatefulWidget {
  final Widget child;

  const TabNavigationScreen({super.key, required this.child});

  @override
  State<TabNavigationScreen> createState() => _TabNavigationScreenState();
}

class _TabNavigationScreenState extends State<TabNavigationScreen> {
  bool _isSidebarCollapsed = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Main layout with sidebar
          SizedBox(
            height: double.infinity,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Left sidebar
                ChatHistorySidebar(
                  selectedSessionToken: _getCurrentSessionToken(),
                  isCollapsed: _isSidebarCollapsed,
                  onToggleCollapse: () {
                    setState(() {
                      _isSidebarCollapsed = !_isSidebarCollapsed;
                    });
                  },
                ),

                // Main content area
                Expanded(child: widget.child),
              ],
            ),
          ),

          // Floating profile icon in top right
          Positioned(top: 16, right: 20, child: _buildFloatingProfileIcon()),
        ],
      ),
    );
  }

  String? _getCurrentSessionToken() {
    final currentPath = GoRouterState.of(context).matchedLocation;
    // Extract session token from chat routes like /app/chat/abc123
    if (currentPath.startsWith('/app/chat/') &&
        currentPath.length > '/app/chat/'.length) {
      return currentPath.substring('/app/chat/'.length);
    }
    return null;
  }

  Widget _buildFloatingProfileIcon() {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        final user = authProvider.user;
        if (user == null) return const SizedBox.shrink();

        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor.withOpacity(0.9),
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: IconButton(
            onPressed: () => context.go(Routes.appProfile),
            icon: CircleAvatar(
              radius: 18,
              backgroundColor: Theme.of(context).colorScheme.primary,
              child:
                  user.photoURL != null
                      ? ClipOval(
                        child: Image.network(
                          user.photoURL!,
                          width: 36,
                          height: 36,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) {
                            return Icon(
                              Icons.person,
                              size: 20,
                              color: Theme.of(context).colorScheme.onPrimary,
                            );
                          },
                        ),
                      )
                      : Icon(
                        Icons.person,
                        size: 20,
                        color: Theme.of(context).colorScheme.onPrimary,
                      ),
            ),
            tooltip: 'Profile',
          ),
        );
      },
    );
  }
}
