import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../widgets/chat_history_sidebar.dart';

class ChatScreen extends StatefulWidget {
  final String? sessionToken;

  const ChatScreen({super.key, this.sessionToken});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

enum SessionState {
  initial, // No session started yet
  collectingTopics, // Waiting for user to provide topics
  active, // Session running, asking questions
  completed, // Session finished, showing scores
  error, // Error state
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _textFieldFocusNode = FocusNode();

  @override
  void initState() {
    super.initState();

    // Load session based on token or start new session
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);

      if (widget.sessionToken != null) {
        // Load specific session by token
        _loadSessionByToken(widget.sessionToken!);
      } else if (!chatProvider.hasActiveSession) {
        // Start a new session if there's no active session
        chatProvider.startNewSession();
      }
    });
  }

  @override
  void didUpdateWidget(ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Handle token changes when navigating between sessions
    if (widget.sessionToken != oldWidget.sessionToken) {
      if (widget.sessionToken != null) {
        _loadSessionByToken(widget.sessionToken!);
      } else {
        // Navigate to default chat - start new session if needed
        final chatProvider = Provider.of<ChatProvider>(context, listen: false);
        if (!chatProvider.hasActiveSession) {
          chatProvider.startNewSession();
        }
      }
    }
  }

  Future<void> _loadSessionByToken(String token) async {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);

    try {
      await chatProvider.loadSessionByToken(token);
    } catch (e) {
      // Handle session not found or error
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Session not found: $token'),
            action: SnackBarAction(
              label: 'Start New',
              onPressed: () => chatProvider.startNewSession(),
            ),
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    _textFieldFocusNode.dispose();
    super.dispose();
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    if (chatProvider.isLoading) return;

    chatProvider.sendMessage(text);
    _messageController.clear();

    // Keep focus on text field for better UX
    if (!_textFieldFocusNode.hasFocus) {
      _textFieldFocusNode.requestFocus();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        // Left sidebar for session history
        ChatHistorySidebar(selectedSessionToken: widget.sessionToken),

        // Vertical divider
        const VerticalDivider(width: 1),

        // Main chat area
        Expanded(child: _buildChatMainArea()),
      ],
    );
  }

  Widget _buildChatMainArea() {
    return GestureDetector(
      // Dismiss keyboard when tapping outside interactive elements
      onTap: () {
        final FocusScopeNode currentScope = FocusScope.of(context);
        if (!currentScope.hasPrimaryFocus && currentScope.hasFocus) {
          FocusManager.instance.primaryFocus?.unfocus();
        }
      },
      behavior: HitTestBehavior.translucent,
      child: Column(
        children: [
          // Session status bar
          _buildSessionStatusBar(),
          // Chat messages area
          Expanded(child: _buildMessagesArea()),
          // Input area - with bottom margin to move it up a bit
          Container(
            margin: const EdgeInsets.only(bottom: 24),
            child: _buildInputArea(),
          ),
        ],
      ),
    );
  }

  Widget _buildSessionStatusBar() {
    return Consumer<ChatProvider>(
      builder: (context, chatProvider, child) {
        if (chatProvider.sessionState == SessionState.initial ||
            chatProvider.sessionState == SessionState.collectingTopics) {
          return const SizedBox.shrink();
        }

        String statusText;
        Color statusColor;

        switch (chatProvider.sessionState) {
          case SessionState.active:
            statusText = "Learning Session Active";
            statusColor = Colors.green;
            break;
          case SessionState.completed:
            statusText = "Session Completed";
            statusColor = Colors.blue;
            break;
          case SessionState.error:
            statusText = "Session Error";
            statusColor = Colors.red;
            break;
          default:
            return const SizedBox.shrink();
        }

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: statusColor.withValues(alpha: 0.1),
            border: Border(
              bottom: BorderSide(
                color: Theme.of(context).dividerColor,
                width: 1,
              ),
            ),
          ),
          child: Row(
            children: [
              Icon(
                chatProvider.sessionState == SessionState.active
                    ? Icons.psychology
                    : chatProvider.sessionState == SessionState.completed
                    ? Icons.check_circle
                    : Icons.error,
                color: statusColor,
                size: 16,
              ),
              const SizedBox(width: 8),
              Text(
                statusText,
                style: TextStyle(
                  color: statusColor,
                  fontWeight: FontWeight.w500,
                  fontSize: 14,
                ),
              ),
              const Spacer(),
              if (chatProvider.sessionState == SessionState.active)
                TextButton(
                  onPressed: () {
                    showDialog(
                      context: context,
                      builder:
                          (context) => AlertDialog(
                            title: const Text('Start New Session'),
                            content: const Text(
                              'Are you sure you want to start a new learning session? This will end the current session.',
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(context),
                                child: const Text('Cancel'),
                              ),
                              TextButton(
                                onPressed: () {
                                  Navigator.pop(context);
                                  chatProvider.startNewSession();
                                },
                                child: const Text('Start New'),
                              ),
                            ],
                          ),
                    );
                  },
                  child: const Text('Start New'),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMessagesArea() {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
      ),
      child: Consumer<ChatProvider>(
        builder: (context, chatProvider, child) {
          // Scroll to bottom when messages change
          if (chatProvider.messages.isNotEmpty) {
            _scrollToBottom();
          }

          return ListView.builder(
            controller: _scrollController,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            itemCount:
                chatProvider.messages.length + (chatProvider.isLoading ? 1 : 0),
            itemBuilder: (context, index) {
              if (index == chatProvider.messages.length &&
                  chatProvider.isLoading) {
                return _buildLoadingIndicator(chatProvider);
              }
              return _buildMessageBubble(chatProvider.messages[index]);
            },
          );
        },
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    final isUser = message.isUser;
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      // Add horizontal padding to keep all messages within the same area
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              decoration: BoxDecoration(
                color:
                    message.isSystem
                        ? theme.colorScheme.secondaryContainer
                        : isUser
                        ? theme.colorScheme.primary
                        : theme.cardColor,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(20),
                  topRight: const Radius.circular(20),
                  bottomLeft: Radius.circular(isUser ? 20 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 20),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.1),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    message.text,
                    style: TextStyle(
                      color:
                          isUser
                              ? theme.colorScheme.onPrimary
                              : message.isSystem
                              ? theme.colorScheme.onSecondaryContainer
                              : theme.textTheme.bodyLarge?.color,
                      fontSize: 16,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _formatTimestamp(message.timestamp),
                    style: TextStyle(
                      color: (message.isSystem
                              ? theme.colorScheme.onSecondaryContainer
                              : isUser
                              ? theme.colorScheme.onPrimary
                              : theme.textTheme.bodyLarge?.color)
                          ?.withValues(alpha: 0.7),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingIndicator(ChatProvider chatProvider) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
                bottomRight: Radius.circular(20),
                bottomLeft: Radius.circular(4),
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  _getLoadingText(chatProvider.sessionState),
                  style: TextStyle(
                    color: Theme.of(context).textTheme.bodyMedium?.color,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getLoadingText(SessionState sessionState) {
    switch (sessionState) {
      case SessionState.collectingTopics:
        return "Starting your session...";
      case SessionState.active:
        return "Processing your answer...";
      case SessionState.completed:
      case SessionState.error:
        return "Thinking...";
      default:
        return "Loading...";
    }
  }

  Widget _buildInputArea() {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.symmetric(
        horizontal: 20,
      ), // Add horizontal margins to make it narrower
      child: SafeArea(
        child: Consumer<ChatProvider>(
          builder: (context, chatProvider, child) {
            return Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    enabled: !chatProvider.isLoading,
                    focusNode: _textFieldFocusNode,
                    decoration: InputDecoration(
                      hintText: _getInputHint(chatProvider.sessionState),
                      hintStyle: TextStyle(
                        color: theme.textTheme.bodyMedium?.color?.withValues(
                          alpha: 0.6,
                        ),
                        fontSize: 16,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      filled: true,
                      fillColor: theme.scaffoldBackgroundColor,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 14,
                      ),
                      // Add focus border for better visual feedback
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide(
                          color: theme.colorScheme.primary,
                          width: 2,
                        ),
                      ),
                      isDense: false,
                    ),
                    maxLines: 5,
                    minLines: 1,
                    textCapitalization: TextCapitalization.sentences,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) {
                      if (!chatProvider.isLoading) {
                        _sendMessage();
                      }
                    },
                    // Auto-focus on certain states for better UX
                    autofocus:
                        chatProvider.sessionState ==
                        SessionState.collectingTopics,
                    // Ensure text field captures all tap events
                    onTap: () {
                      if (!_textFieldFocusNode.hasFocus) {
                        _textFieldFocusNode.requestFocus();
                      }
                    },
                  ),
                ),
                const SizedBox(width: 12),
                // Send button
                IconButton(
                  onPressed: chatProvider.isLoading ? null : _sendMessage,
                  style: IconButton.styleFrom(
                    backgroundColor:
                        chatProvider.isLoading
                            ? theme.colorScheme.primary.withValues(alpha: 0.5)
                            : theme.colorScheme.primary,
                    foregroundColor: theme.colorScheme.onPrimary,
                    disabledBackgroundColor: theme.colorScheme.primary
                        .withValues(alpha: 0.5),
                    disabledForegroundColor: theme.colorScheme.onPrimary
                        .withValues(alpha: 0.7),
                    fixedSize: const Size(56, 56), // Consistent size
                    shape: const CircleBorder(),
                    elevation: chatProvider.isLoading ? 0 : 2,
                    shadowColor: theme.colorScheme.primary.withValues(
                      alpha: 0.3,
                    ),
                  ),
                  icon: const Icon(Icons.arrow_upward, size: 24),
                  tooltip: 'Send message',
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  String _getInputHint(SessionState sessionState) {
    switch (sessionState) {
      case SessionState.initial:
      case SessionState.collectingTopics:
        return 'Enter topics to study (e.g., "Flutter, Dart")...';
      case SessionState.active:
        return 'Type your answer...';
      case SessionState.completed:
        return 'Ask for new session or review scores...';
      case SessionState.error:
        return 'Type "try again" or "restart"...';
    }
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else {
      return '${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')}';
    }
  }
}

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final bool isSystem;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.isSystem = false,
  });
}
