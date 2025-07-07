import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../providers/chat_provider.dart';
import '../providers/auth_provider.dart';
import '../models/chat_session.dart';
import '../routing/route_constants.dart';
import '../widgets/theme_logo.dart';
import 'new_chat_button.dart';
import 'session_item.dart';

class ChatHistorySidebar extends StatefulWidget {
  final String? selectedSessionToken;
  final bool isCollapsed;
  final VoidCallback onToggleCollapse;

  const ChatHistorySidebar({
    super.key,
    this.selectedSessionToken,
    required this.isCollapsed,
    required this.onToggleCollapse,
  });

  @override
  State<ChatHistorySidebar> createState() => _ChatHistorySidebarState();
}

class _ChatHistorySidebarState extends State<ChatHistorySidebar> {
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';
  bool _isLogoHovered = false;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    setState(() {
      _searchQuery = query.toLowerCase().trim();
    });
  }

  List<ChatSessionSummary> _filterSessions(List<ChatSessionSummary> sessions) {
    if (_searchQuery.isEmpty) {
      return sessions;
    }

    return sessions.where((session) {
      return session.displayName.toLowerCase().contains(_searchQuery) ||
          session.topics.any(
            (topic) => topic.toLowerCase().contains(_searchQuery),
          );
    }).toList();
  }

  // Helper method to get selected navigation index from current route
  int _getSelectedIndex(String currentPath) {
    // Handle chat routes with tokens (e.g., /app/chat/abc123)
    if (currentPath.startsWith('/app/chat')) {
      return 2;
    }

    switch (currentPath) {
      case Routes.appTodays:
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
      Routes.appTodays, // /app/today
      Routes.appAll, // /app/all
      Routes.appChat, // /app/chat
    ];
    context.go(routes[index]);
  }

  Widget _buildNavigationTabs() {
    final currentPath = GoRouterState.of(context).matchedLocation;
    final selectedIndex = _getSelectedIndex(currentPath);
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    final navigationItems = [
      {'icon': Icons.home, 'label': 'Today', 'index': 0},
      {'icon': Icons.list, 'label': 'All Items', 'index': 1},
      {'icon': Icons.chat, 'label': 'Chat', 'index': 2},
    ];

    if (widget.isCollapsed) {
      // Show vertical icon-only navigation
      return Column(
        children:
            navigationItems.map((item) {
              final isSelected = selectedIndex == item['index'];
              return Tooltip(
                message: item['label'] as String,
                child: Container(
                  margin: const EdgeInsets.symmetric(vertical: 4),
                  child: InkWell(
                    onTap:
                        () => _navigateToIndex(context, item['index'] as int),
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color:
                            isSelected
                                ? colorScheme.primaryContainer.withOpacity(0.3)
                                : Colors.transparent,
                        borderRadius: BorderRadius.circular(8),
                        border:
                            isSelected
                                ? Border.all(
                                  color: colorScheme.primary.withOpacity(0.3),
                                  width: 1,
                                )
                                : null,
                      ),
                      child: Icon(
                        item['icon'] as IconData,
                        size: 24,
                        color:
                            isSelected
                                ? colorScheme.primary
                                : colorScheme.onSurface,
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
      );
    } else {
      // Show full navigation tabs
      return Column(
        children:
            navigationItems.map((item) {
              final isSelected = selectedIndex == item['index'];
              return Container(
                margin: const EdgeInsets.symmetric(vertical: 2),
                child: InkWell(
                  onTap: () => _navigateToIndex(context, item['index'] as int),
                  borderRadius: BorderRadius.circular(8),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    decoration: BoxDecoration(
                      color:
                          isSelected
                              ? colorScheme.primaryContainer.withOpacity(0.3)
                              : Colors.transparent,
                      borderRadius: BorderRadius.circular(8),
                      border:
                          isSelected
                              ? Border.all(
                                color: colorScheme.primary.withOpacity(0.3),
                                width: 1,
                              )
                              : null,
                    ),
                    child: Row(
                      children: [
                        Icon(
                          item['icon'] as IconData,
                          size: 20,
                          color:
                              isSelected
                                  ? colorScheme.primary
                                  : colorScheme.onSurface,
                        ),
                        const SizedBox(width: 12),
                        Text(
                          item['label'] as String,
                          style: TextStyle(
                            color:
                                isSelected
                                    ? colorScheme.primary
                                    : colorScheme.onSurface,
                            fontWeight:
                                isSelected ? FontWeight.w600 : FontWeight.w500,
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      width: widget.isCollapsed ? 72 : 280,
      decoration: BoxDecoration(
        color: colorScheme.surface,
        border: Border(
          right: BorderSide(
            color: colorScheme.outline.withOpacity(0.15),
            width: 1,
          ),
        ),
      ),
      child: Column(
        children: [
          // Header with logo and toggle button
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: colorScheme.surface,
              border: Border(
                bottom: BorderSide(
                  color: colorScheme.outline.withOpacity(0.1),
                  width: 1,
                ),
              ),
            ),
            child:
                widget.isCollapsed
                    ? _buildCollapsedHeader(colorScheme)
                    : _buildExpandedHeader(colorScheme),
          ),

          // Navigation tabs (above new chat button)
          Container(
            padding: const EdgeInsets.all(8),
            child: _buildNavigationTabs(),
          ),

          // New chat button (only show when expanded)
          if (!widget.isCollapsed) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: const NewChatButton(),
            ),
          ],

          // Divider
          if (!widget.isCollapsed) ...[
            Container(
              margin: const EdgeInsets.symmetric(vertical: 8),
              height: 1,
              color: colorScheme.outline.withOpacity(0.1),
            ),
          ],

          if (!widget.isCollapsed) ...[
            // Search bar (only when expanded)
            Container(
              padding: const EdgeInsets.all(12),
              child: TextField(
                controller: _searchController,
                onChanged: _onSearchChanged,
                decoration: InputDecoration(
                  hintText: 'Search sessions...',
                  prefixIcon: const Icon(Icons.search, size: 20),
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 8,
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: BorderSide(
                      color: colorScheme.outline.withOpacity(0.3),
                    ),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: BorderSide(
                      color: colorScheme.outline.withOpacity(0.3),
                    ),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: BorderSide(
                      color: colorScheme.primary,
                      width: 1.5,
                    ),
                  ),
                ),
                style: const TextStyle(fontSize: 14),
              ),
            ),

            // Session history list
            Expanded(
              child: Consumer<ChatProvider>(
                builder: (context, chatProvider, child) {
                  if (chatProvider.isLoadingHistory) {
                    return const Center(child: CircularProgressIndicator());
                  }

                  final filteredSessions = _filterSessions(
                    chatProvider.sessionHistory,
                  );

                  if (filteredSessions.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            _searchQuery.isNotEmpty
                                ? Icons.search_off
                                : Icons.chat_bubble_outline,
                            size: 48,
                            color: colorScheme.outline.withOpacity(0.5),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            _searchQuery.isNotEmpty
                                ? 'No sessions found'
                                : 'No chat sessions yet',
                            style: TextStyle(
                              color: colorScheme.onSurface.withOpacity(0.6),
                              fontSize: 16,
                            ),
                          ),
                          if (_searchQuery.isEmpty) ...[
                            const SizedBox(height: 8),
                            Text(
                              'Start a new chat to begin',
                              style: TextStyle(
                                color: colorScheme.onSurface.withOpacity(0.4),
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ],
                      ),
                    );
                  }

                  // Simple list of all sessions
                  return ListView.builder(
                    padding: const EdgeInsets.only(bottom: 16),
                    itemCount: filteredSessions.length,
                    itemBuilder: (context, index) {
                      final session = filteredSessions[index];
                      final isSelected =
                          session.token == widget.selectedSessionToken;
                      return SessionItem(
                        session: session,
                        isSelected: isSelected,
                      );
                    },
                  );
                },
              ),
            ),
          ] else ...[
            // Collapsed view - align new chat button with navigation
            Container(
              padding: const EdgeInsets.all(8),
              child: Tooltip(
                message: 'New Chat',
                child: Container(
                  margin: const EdgeInsets.symmetric(vertical: 4),
                  child: InkWell(
                    onTap: () {
                      Provider.of<ChatProvider>(
                        context,
                        listen: false,
                      ).startNewChatFlow();
                    },
                    borderRadius: BorderRadius.circular(8),
                    child: Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: colorScheme.primary,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        Icons.add,
                        size: 24,
                        color: colorScheme.onPrimary,
                      ),
                    ),
                  ),
                ),
              ),
            ),
            const Spacer(),
          ],

          // User info panel at bottom (only when expanded)
          if (!widget.isCollapsed)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: colorScheme.surface,
                border: Border(
                  top: BorderSide(
                    color: colorScheme.outline.withOpacity(0.1),
                    width: 1,
                  ),
                ),
              ),
              child: Consumer<AuthProvider>(
                builder: (context, authProvider, child) {
                  final user = authProvider.user;
                  if (user == null) return const SizedBox.shrink();

                  return Row(
                    children: [
                      // User avatar
                      CircleAvatar(
                        radius: 16,
                        backgroundColor: colorScheme.primary,
                        child:
                            user.photoURL != null
                                ? ClipOval(
                                  child: Image.network(
                                    user.photoURL!,
                                    width: 32,
                                    height: 32,
                                    fit: BoxFit.cover,
                                    errorBuilder: (context, error, stackTrace) {
                                      return Icon(
                                        Icons.person,
                                        size: 20,
                                        color: colorScheme.onPrimary,
                                      );
                                    },
                                  ),
                                )
                                : Icon(
                                  Icons.person,
                                  size: 20,
                                  color: colorScheme.onPrimary,
                                ),
                      ),

                      const SizedBox(width: 12),

                      // User info
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              user.displayName ?? 'User',
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            Text(
                              user.email ?? '',
                              style: TextStyle(
                                fontSize: 12,
                                color: colorScheme.onSurface.withOpacity(0.6),
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),

                      // Settings/logout button
                      PopupMenuButton<String>(
                        onSelected: (value) {
                          switch (value) {
                            case 'logout':
                              authProvider.signOut();
                              break;
                          }
                        },
                        itemBuilder:
                            (context) => [
                              const PopupMenuItem<String>(
                                value: 'logout',
                                child: Row(
                                  children: [
                                    Icon(Icons.logout, size: 16),
                                    SizedBox(width: 8),
                                    Text('Sign Out'),
                                  ],
                                ),
                              ),
                            ],
                        child: Icon(
                          Icons.more_vert,
                          size: 20,
                          color: colorScheme.outline,
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildCollapsedHeader(ColorScheme colorScheme) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isLogoHovered = true),
      onExit: (_) => setState(() => _isLogoHovered = false),
      child: Container(
        width: 56,
        height: 40,
        alignment: Alignment.center,
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 200),
          child:
              _isLogoHovered
                  ? IconButton(
                    key: const ValueKey('expand_button'),
                    onPressed: widget.onToggleCollapse,
                    icon: const Icon(Icons.menu, size: 20),
                    tooltip: 'Expand Sidebar',
                    style: IconButton.styleFrom(
                      backgroundColor: colorScheme.primary,
                      foregroundColor: colorScheme.onPrimary,
                      minimumSize: const Size(40, 40),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                  )
                  : Padding(
                    key: const ValueKey('logo'),
                    padding: const EdgeInsets.all(4.0),
                    child: ThemeLogo(size: 24),
                  ),
        ),
      ),
    );
  }

  Widget _buildExpandedHeader(ColorScheme colorScheme) {
    return Row(
      children: [
        // Logo (always visible)
        Padding(padding: const EdgeInsets.all(4.0), child: ThemeLogo(size: 28)),

        const Expanded(child: SizedBox.shrink()),

        // Toggle button
        IconButton(
          onPressed: widget.onToggleCollapse,
          icon: const Icon(Icons.menu_open, size: 24),
          tooltip: 'Collapse Sidebar',
          style: IconButton.styleFrom(
            backgroundColor: colorScheme.surface,
            foregroundColor: colorScheme.onSurface,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
      ],
    );
  }
}
