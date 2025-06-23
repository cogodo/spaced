import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../routing/route_constants.dart';
import '../widgets/theme_logo.dart';
import 'package:flutter/foundation.dart';

class TopNavigationBar extends StatelessWidget implements PreferredSizeWidget {
  const TopNavigationBar({super.key});

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);

  // Helper method to get selected navigation index from current route
  int _getSelectedIndex(String currentPath) {
    // Handle chat routes with tokens (e.g., /app/chat/abc123)
    if (currentPath.startsWith('/app/chat')) {
      return 2;
    }

    switch (currentPath) {
      case Routes.appHome:
        return 0;
      case Routes.appAll:
        return 1;
      case Routes.appChat:
        return 2;
      default:
        return 0;
    }
  }

  // Helper method to navigate to route by index
  void _navigateToIndex(BuildContext context, int index) {
    final routes = [
      Routes.appHome, // /app
      Routes.appAll, // /app/all
      Routes.appChat, // /app/chat
    ];
    context.go(routes[index]);
  }

  void _navigateToLanding(BuildContext context) {
    // For web, navigate to landing page
    if (kIsWeb) {
      // Check if we're on localhost for development
      final currentUrl = Uri.base.toString();
      if (currentUrl.contains('localhost') ||
          currentUrl.contains('127.0.0.1')) {
        context.go(Routes.landing);
      } else {
        // Production: Use go router to navigate to landing
        context.go(Routes.landing);
      }
    } else {
      // For non-web platforms, just go to landing route
      context.go(Routes.landing);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentPath = GoRouterState.of(context).matchedLocation;
    final selectedIndex = _getSelectedIndex(currentPath);
    final isDesktop = MediaQuery.of(context).size.width > 800;
    final isTablet = MediaQuery.of(context).size.width > 600;

    // Create a slightly darker color than the scaffold background
    final scaffoldColor = Theme.of(context).scaffoldBackgroundColor;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final navBarColor =
        isDark
            ? Color.fromARGB(
              (scaffoldColor.a * 255.0).round() & 0xff,
              (scaffoldColor.r * 255.0 * 0.85).round() & 0xff,
              (scaffoldColor.g * 255.0 * 0.85).round() & 0xff,
              (scaffoldColor.b * 255.0 * 0.85).round() & 0xff,
            )
            : Color.fromARGB(
              (scaffoldColor.a * 255.0).round() & 0xff,
              (scaffoldColor.r * 255.0 * 0.95).round() & 0xff,
              (scaffoldColor.g * 255.0 * 0.95).round() & 0xff,
              (scaffoldColor.b * 255.0 * 0.95).round() & 0xff,
            );

    return AppBar(
      backgroundColor: navBarColor,
      elevation: 1,
      shadowColor: Theme.of(context).dividerColor,
      leading: Padding(
        padding: const EdgeInsets.all(8.0),
        child: Tooltip(
          message: 'Return to landing page',
          child: MouseRegion(
            cursor: SystemMouseCursors.click,
            child: GestureDetector(
              onTap: () => _navigateToLanding(context),
              child: const ThemeLogo(size: 32),
            ),
          ),
        ),
      ),
      title: isDesktop ? null : null, // Keep title empty to save space
      actions: [
        // Navigation tabs - responsive design
        if (isDesktop) ...[
          // Desktop: Show all navigation as buttons
          _NavigationTab(
            icon: Icons.home,
            label: 'Today',
            isSelected: selectedIndex == 0,
            onTap: () => _navigateToIndex(context, 0),
          ),
          _NavigationTab(
            icon: Icons.list,
            label: 'All Items',
            isSelected: selectedIndex == 1,
            onTap: () => _navigateToIndex(context, 1),
          ),
          _NavigationTab(
            icon: Icons.chat,
            label: 'Chat',
            isSelected: selectedIndex == 2,
            onTap: () => _navigateToIndex(context, 2),
          ),
          const SizedBox(width: 16),
        ] else if (isTablet) ...[
          // Tablet: Show icons only
          _NavigationTab(
            icon: Icons.home,
            isSelected: selectedIndex == 0,
            onTap: () => _navigateToIndex(context, 0),
            showLabel: false,
          ),
          _NavigationTab(
            icon: Icons.list,
            isSelected: selectedIndex == 1,
            onTap: () => _navigateToIndex(context, 1),
            showLabel: false,
          ),
          _NavigationTab(
            icon: Icons.chat,
            isSelected: selectedIndex == 2,
            onTap: () => _navigateToIndex(context, 2),
            showLabel: false,
          ),
          const SizedBox(width: 16),
        ] else ...[
          // Mobile: Use hamburger menu
          _buildMobileMenu(context, selectedIndex),
          const SizedBox(width: 8),
        ],

        // Profile button - always visible
        Tooltip(
          message: 'Profile',
          child: IconButton(
            onPressed: () => context.go(Routes.appProfile),
            icon: Icon(
              Icons.account_circle,
              size: 28,
              color:
                  currentPath == Routes.appProfile
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).iconTheme.color,
            ),
          ),
        ),
        const SizedBox(width: 8),
      ],
    );
  }

  Widget _buildMobileMenu(BuildContext context, int selectedIndex) {
    return PopupMenuButton<int>(
      icon: const Icon(Icons.menu),
      onSelected: (index) => _navigateToIndex(context, index),
      itemBuilder:
          (context) => [
            PopupMenuItem(
              value: 0,
              child: Row(
                children: [
                  Icon(
                    Icons.home,
                    color:
                        selectedIndex == 0
                            ? Theme.of(context).colorScheme.primary
                            : null,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Today',
                    style: TextStyle(
                      color:
                          selectedIndex == 0
                              ? Theme.of(context).colorScheme.primary
                              : null,
                      fontWeight: selectedIndex == 0 ? FontWeight.bold : null,
                    ),
                  ),
                ],
              ),
            ),
            PopupMenuItem(
              value: 1,
              child: Row(
                children: [
                  Icon(
                    Icons.list,
                    color:
                        selectedIndex == 1
                            ? Theme.of(context).colorScheme.primary
                            : null,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'All Items',
                    style: TextStyle(
                      color:
                          selectedIndex == 1
                              ? Theme.of(context).colorScheme.primary
                              : null,
                      fontWeight: selectedIndex == 1 ? FontWeight.bold : null,
                    ),
                  ),
                ],
              ),
            ),
            PopupMenuItem(
              value: 2,
              child: Row(
                children: [
                  Icon(
                    Icons.chat,
                    color:
                        selectedIndex == 2
                            ? Theme.of(context).colorScheme.primary
                            : null,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Chat',
                    style: TextStyle(
                      color:
                          selectedIndex == 2
                              ? Theme.of(context).colorScheme.primary
                              : null,
                      fontWeight: selectedIndex == 2 ? FontWeight.bold : null,
                    ),
                  ),
                ],
              ),
            ),
          ],
    );
  }
}

class _NavigationTab extends StatelessWidget {
  final IconData icon;
  final String? label;
  final bool isSelected;
  final VoidCallback onTap;
  final bool showLabel;

  const _NavigationTab({
    required this.icon,
    this.label,
    required this.isSelected,
    required this.onTap,
    this.showLabel = true,
  });

  @override
  Widget build(BuildContext context) {
    final color =
        isSelected
            ? Theme.of(context).colorScheme.primary
            : Theme.of(context).iconTheme.color;

    return Tooltip(
      message: label ?? '',
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: EdgeInsets.symmetric(
            horizontal: showLabel ? 16 : 12,
            vertical: 8,
          ),
          decoration:
              isSelected
                  ? BoxDecoration(
                    color: Theme.of(context).colorScheme.primary.withAlpha(20),
                    borderRadius: BorderRadius.circular(8),
                  )
                  : null,
          child:
              showLabel && label != null
                  ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(icon, size: 20, color: color),
                      const SizedBox(width: 8),
                      Text(
                        label!,
                        style: TextStyle(
                          color: color,
                          fontWeight:
                              isSelected ? FontWeight.w600 : FontWeight.w500,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  )
                  : Icon(icon, size: 24, color: color),
        ),
      ),
    );
  }
}
