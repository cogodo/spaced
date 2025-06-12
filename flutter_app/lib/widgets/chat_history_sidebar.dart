import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../providers/auth_provider.dart';
import '../models/chat_session.dart';
import 'new_chat_button.dart';
import 'session_item.dart';

class ChatHistorySidebar extends StatefulWidget {
  final String? selectedSessionToken;

  const ChatHistorySidebar({super.key, this.selectedSessionToken});

  @override
  State<ChatHistorySidebar> createState() => _ChatHistorySidebarState();
}

class _ChatHistorySidebarState extends State<ChatHistorySidebar> {
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

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

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      width: 280,
      decoration: BoxDecoration(
        color: colorScheme.surface,
        border: Border(
          right: BorderSide(
            color: colorScheme.outline.withOpacity(
              0.15,
            ), // Slightly lighter border
            width: 1,
          ),
        ),
      ),
      child: Column(
        children: [
          // Header with new chat button - flush to top
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
            child: const NewChatButton(),
          ),

          // Search bar
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

          // User info panel at bottom
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
}
