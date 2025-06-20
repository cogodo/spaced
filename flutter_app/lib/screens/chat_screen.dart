import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../providers/auth_provider.dart';
import '../widgets/chat_history_sidebar.dart';
import '../widgets/chat_progress_widget.dart';
import '../widgets/typing_indicator_widget.dart';
import '../widgets/topic_selection_widget.dart';
import '../models/schedule_manager.dart';
import '../models/task_holder.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter/services.dart';

class ChatScreen extends StatefulWidget {
  final String? sessionToken;

  const ChatScreen({super.key, this.sessionToken});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

enum SessionState {
  initial, // No session started yet
  selectingSessionType, // Choosing between new items or past reviews
  selectingDueTopics, // Selecting which due topics to review
  collectingTopics, // Waiting for user to provide topics
  active, // Session running, asking questions
  completed, // Session finished, showing scores
  error, // Error state
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _textFieldFocusNode = FocusNode();

  // For due topics selection
  List<Task> _dueTasks = [];
  Set<String> _selectedTopics = {};
  bool _isLoadingDueTasks = false;

  // Prevent duplicate sends
  bool _isSending = false;

  @override
  void initState() {
    super.initState();

    // Load session based on token, but don't auto-start new sessions
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);

      if (widget.sessionToken != null) {
        // Load specific session by token
        _loadSessionByToken(widget.sessionToken!);
      } else {
        // Check if there's an active session and redirect to its token URL
        final currentToken = chatProvider.currentSessionToken;
        if (currentToken != null) {
          // Redirect to the active session's token URL
          context.go('/app/chat/$currentToken');
        } else {
          // No session token and no active session - reset to initial state for session selection
          chatProvider.resetToInitialState();
        }
      }
      // Don't auto-start new sessions - wait for user input
    });
  }

  @override
  void didUpdateWidget(ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Handle token changes when navigating between sessions
    if (widget.sessionToken != oldWidget.sessionToken) {
      if (widget.sessionToken != null) {
        _loadSessionByToken(widget.sessionToken!);
      }
      // Don't auto-start new sessions when navigating to default chat
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

  Future<void> _loadDueTasks() async {
    setState(() {
      _isLoadingDueTasks = true;
    });

    try {
      final scheduleManager = Provider.of<ScheduleManager>(
        context,
        listen: false,
      );
      final dueTasks = scheduleManager.getTodaysTasks();
      setState(() {
        _dueTasks = dueTasks;
        _selectedTopics.clear();
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error loading due tasks: $e')));
      }
    } finally {
      setState(() {
        _isLoadingDueTasks = false;
      });
    }
  }

  void _startNewItemsSession() {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    chatProvider.startNewSession(sessionType: 'custom_topics');
  }

  void _startPastReviewsSession() {
    _loadDueTasks();
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    chatProvider.setSessionState(SessionState.selectingDueTopics);
  }

  void _startDueTopicsSession() {
    if (_selectedTopics.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select at least one topic to review'),
        ),
      );
      return;
    }

    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    chatProvider.startNewSession(
      sessionType: 'due_items',
      selectedTopics: _selectedTopics.toList(),
    );
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
    if (text.isEmpty || _isSending) return;

    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    if (chatProvider.isLoading) return;

    // Set sending state to prevent duplicates
    setState(() {
      _isSending = true;
    });

    try {
      // If no active session exists, start a new one first
      if (!chatProvider.hasActiveSession) {
        chatProvider
            .startNewSession()
            .then((_) {
              // Send the message after the session is started
              chatProvider.sendMessage(text);
            })
            .whenComplete(() {
              if (mounted) {
                setState(() {
                  _isSending = false;
                });
              }
            });
      } else {
        chatProvider.sendMessage(text).whenComplete(() {
          if (mounted) {
            setState(() {
              _isSending = false;
            });
          }
        });
      }

      _messageController.clear();

      // Keep focus on text field for better UX
      if (!_textFieldFocusNode.hasFocus) {
        _textFieldFocusNode.requestFocus();
      }
    } catch (e) {
      // Reset sending state on error
      if (mounted) {
        setState(() {
          _isSending = false;
        });
      }
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
    return SelectableRegion(
      focusNode: FocusNode(),
      selectionControls: materialTextSelectionControls,
      child: SizedBox(
        height: double.infinity, // Ensure full height
        child: Row(
          crossAxisAlignment:
              CrossAxisAlignment.stretch, // Make sidebar full height
          children: [
            // Left sidebar for session history
            ChatHistorySidebar(selectedSessionToken: widget.sessionToken),

            // Main chat area (no divider)
            Expanded(child: _buildChatMainArea()),
          ],
        ),
      ),
    );
  }

  Widget _buildChatMainArea() {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
      ),
      child: GestureDetector(
        // Dismiss keyboard when tapping outside interactive elements
        onTap: () {
          final FocusScopeNode currentScope = FocusScope.of(context);
          if (!currentScope.hasPrimaryFocus && currentScope.hasFocus) {
            FocusManager.instance.primaryFocus?.unfocus();
          }
        },
        behavior: HitTestBehavior.translucent,
        child: Consumer<ChatProvider>(
          builder: (context, chatProvider, child) {
            // Show session type selection if no active session and in initial state
            if (!chatProvider.hasActiveSession &&
                chatProvider.sessionState == SessionState.initial) {
              return _buildSessionTypeSelection();
            }

            // Show topic selection for new items
            if (chatProvider.sessionState == SessionState.collectingTopics) {
              return _buildTopicSelectionScreen();
            }

            // Show due topics selection
            if (chatProvider.sessionState == SessionState.selectingDueTopics) {
              return _buildDueTopicsSelection();
            }

            // Show normal chat interface
            return Column(
              children: [
                // Chat messages area - removed session status bar
                Expanded(child: _buildMessagesArea()),
                // Input area - with bottom margin to move it up a bit
                Container(
                  margin: const EdgeInsets.only(bottom: 24),
                  child: _buildInputArea(),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _buildSessionTypeSelection() {
    final theme = Theme.of(context);

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 600),
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.psychology, size: 80, color: theme.colorScheme.primary),
            const SizedBox(height: 24),
            Text(
              'Start Your Learning Session',
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              'Choose how you\'d like to learn today',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 48),

            // New Items Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _startNewItemsSession,
                icon: const Icon(Icons.add_circle_outline, size: 24),
                label: const Text('New Items'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    vertical: 20,
                    horizontal: 24,
                  ),
                  backgroundColor: theme.colorScheme.primary,
                  foregroundColor: theme.colorScheme.onPrimary,
                  textStyle: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Past Reviews Button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _startPastReviewsSession,
                icon: const Icon(Icons.history, size: 24),
                label: const Text('Past Reviews'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    vertical: 20,
                    horizontal: 24,
                  ),
                  foregroundColor: theme.colorScheme.primary,
                  side: BorderSide(color: theme.colorScheme.primary, width: 2),
                  textStyle: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 32),

            Text(
              'New Items: Learn completely new topics\nPast Reviews: Review topics you\'ve studied before',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTopicSelectionScreen() {
    final theme = Theme.of(context);

    return Column(
      children: [
        // Header
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            border: Border(
              bottom: BorderSide(
                color: theme.colorScheme.outline.withValues(alpha: 0.2),
              ),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  IconButton(
                    onPressed: () {
                      final chatProvider = Provider.of<ChatProvider>(
                        context,
                        listen: false,
                      );
                      chatProvider.setSessionState(SessionState.initial);
                    },
                    icon: const Icon(Icons.arrow_back),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Select Topics to Learn',
                          style: theme.textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Choose which topics you\'d like to learn today',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(
                              alpha: 0.7,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Topic Selection Widget
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(24),
            child: TopicSelectionWidget(
              onTopicsSelected: (topics) async {
                final chatProvider = Provider.of<ChatProvider>(
                  context,
                  listen: false,
                );
                // Use existing session and handle topics input instead of creating new session
                await chatProvider.handleTopicsInput(topics);
              },
              onPopularTopicSelected: (topic) async {
                final chatProvider = Provider.of<ChatProvider>(
                  context,
                  listen: false,
                );
                // Use existing session and handle the popular topic
                await chatProvider.handleTopicsInput([topic.name]);
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDueTopicsSelection() {
    final theme = Theme.of(context);

    return Column(
      children: [
        // Header
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            border: Border(
              bottom: BorderSide(
                color: theme.colorScheme.outline.withValues(alpha: 0.2),
              ),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  IconButton(
                    onPressed: () {
                      final chatProvider = Provider.of<ChatProvider>(
                        context,
                        listen: false,
                      );
                      chatProvider.setSessionState(SessionState.initial);
                    },
                    icon: const Icon(Icons.arrow_back),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Select Topics to Review',
                          style: theme.textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Choose which topics you\'d like to review today',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(
                              alpha: 0.7,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Content
        Expanded(
          child:
              _isLoadingDueTasks
                  ? const Center(child: CircularProgressIndicator())
                  : _dueTasks.isEmpty
                  ? _buildNoDueTasksMessage()
                  : _buildDueTasksList(),
        ),

        // Bottom action bar
        if (_dueTasks.isNotEmpty)
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              border: Border(
                top: BorderSide(
                  color: theme.colorScheme.outline.withValues(alpha: 0.2),
                ),
              ),
            ),
            child: Row(
              children: [
                Text(
                  '${_selectedTopics.length} topic${_selectedTopics.length == 1 ? '' : 's'} selected',
                  style: theme.textTheme.bodyMedium,
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed:
                      _selectedTopics.isEmpty ? null : _startDueTopicsSession,
                  child: const Text('Start Review Session'),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildNoDueTasksMessage() {
    final theme = Theme.of(context);

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 400),
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.check_circle_outline,
              size: 80,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 24),
            Text(
              'All Caught Up!',
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              'You don\'t have any topics due for review right now. Great job staying on top of your learning!',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _startNewItemsSession,
              child: const Text('Learn New Topics Instead'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDueTasksList() {
    final theme = Theme.of(context);

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _dueTasks.length,
      itemBuilder: (context, index) {
        final task = _dueTasks[index];
        final isSelected = _selectedTopics.contains(task.task);

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: CheckboxListTile(
            value: isSelected,
            onChanged: (bool? value) {
              setState(() {
                if (value == true) {
                  _selectedTopics.add(task.task);
                } else {
                  _selectedTopics.remove(task.task);
                }
              });
            },
            title: Text(
              task.task,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Row(
                  children: [
                    _buildTaskChip(
                      'Difficulty: ${(task.difficulty * 100).round()}%',
                      theme.colorScheme.secondary,
                    ),
                    const SizedBox(width: 8),
                    _buildTaskChip(
                      'Repetition: ${task.repetition}',
                      theme.colorScheme.tertiary,
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  _getTaskDueText(task),
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: _getTaskDueColor(task, theme),
                  ),
                ),
              ],
            ),
            controlAffinity: ListTileControlAffinity.trailing,
          ),
        );
      },
    );
  }

  Widget _buildTaskChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          color: color,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  String _getTaskDueText(Task task) {
    if (task.nextReviewDate == null) {
      return 'Never reviewed';
    }

    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final reviewDate = DateTime(
      task.nextReviewDate!.year,
      task.nextReviewDate!.month,
      task.nextReviewDate!.day,
    );

    final daysDifference = today.difference(reviewDate).inDays;

    if (daysDifference > 0) {
      return '$daysDifference day${daysDifference == 1 ? '' : 's'} overdue';
    } else if (daysDifference == 0) {
      return 'Due today';
    } else {
      return 'Due in ${-daysDifference} day${daysDifference == -1 ? '' : 's'}';
    }
  }

  Color _getTaskDueColor(Task task, ThemeData theme) {
    if (task.nextReviewDate == null) {
      return theme.colorScheme.primary;
    }

    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final reviewDate = DateTime(
      task.nextReviewDate!.year,
      task.nextReviewDate!.month,
      task.nextReviewDate!.day,
    );

    final daysDifference = today.difference(reviewDate).inDays;

    if (daysDifference > 0) {
      return theme.colorScheme.error; // Overdue
    } else if (daysDifference == 0) {
      return theme.colorScheme.primary; // Due today
    } else {
      return theme.colorScheme.onSurface.withValues(alpha: 0.6); // Future
    }
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

          return Column(
            children: [
              // Progress indicator for active sessions
              ChatProgressWidget(),

              // Messages list
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  itemCount:
                      chatProvider.messages.length +
                      (chatProvider.isTyping ? 1 : 0),
                  itemBuilder: (context, index) {
                    if (index == chatProvider.messages.length &&
                        chatProvider.isTyping) {
                      return SmartTypingIndicator(
                        sessionState: chatProvider.sessionState.toString(),
                        isGeneratingQuestions:
                            chatProvider.isGeneratingQuestions,
                        isProcessingAnswer: chatProvider.isProcessingAnswer,
                      );
                    }
                    return _buildMessageBubble(chatProvider.messages[index]);
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    final isUser = message.isUser;
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            // AI avatar
            Container(
              width: 32,
              height: 32,
              margin: const EdgeInsets.only(right: 12),
              decoration: BoxDecoration(
                color:
                    message.isSystem
                        ? theme.colorScheme.secondaryContainer
                        : theme.colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                message.isSystem ? Icons.info : Icons.smart_toy,
                size: 18,
                color:
                    message.isSystem
                        ? theme.colorScheme.onSecondaryContainer
                        : theme.colorScheme.onPrimaryContainer,
              ),
            ),
          ],
          Flexible(
            child: Container(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              child: Column(
                crossAxisAlignment:
                    isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
                children: [
                  // Message content without background bubble
                  SelectableText(
                    message.text,
                    style: TextStyle(
                      color: theme.textTheme.bodyLarge?.color,
                      fontSize: 16,
                      height: 1.4,
                    ),
                    textAlign: isUser ? TextAlign.right : TextAlign.left,
                    contextMenuBuilder: (context, editableTextState) {
                      final List<ContextMenuButtonItem> buttonItems =
                          <ContextMenuButtonItem>[
                            ContextMenuButtonItem(
                              label: 'Copy',
                              onPressed: () {
                                Clipboard.setData(
                                  ClipboardData(text: message.text),
                                );
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(
                                    content: Text(
                                      'Message copied to clipboard',
                                    ),
                                    duration: Duration(seconds: 2),
                                  ),
                                );
                                ContextMenuController.removeAny();
                              },
                            ),
                            ContextMenuButtonItem(
                              label: 'Select All',
                              onPressed: () {
                                editableTextState.selectAll(
                                  SelectionChangedCause.toolbar,
                                );
                                ContextMenuController.removeAny();
                              },
                            ),
                          ];

                      return AdaptiveTextSelectionToolbar.buttonItems(
                        anchors: editableTextState.contextMenuAnchors,
                        buttonItems: buttonItems,
                      );
                    },
                  ),
                  const SizedBox(height: 4),
                  // Timestamp
                  Text(
                    _formatTimestamp(message.timestamp),
                    style: TextStyle(
                      color: theme.textTheme.bodySmall?.color?.withOpacity(0.6),
                      fontSize: 12,
                    ),
                    textAlign: isUser ? TextAlign.right : TextAlign.left,
                  ),
                ],
              ),
            ),
          ),
          if (isUser) ...[
            // User avatar
            Container(
              width: 32,
              height: 32,
              margin: const EdgeInsets.only(left: 12),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                Icons.person,
                size: 18,
                color: theme.colorScheme.onPrimary,
              ),
            ),
          ],
        ],
      ),
    );
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
                    enabled:
                        !chatProvider.isLoading &&
                        !chatProvider.isTyping &&
                        !_isSending,
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
                      // Show typing indicator in input when AI is thinking
                      suffixIcon:
                          chatProvider.isTyping
                              ? Padding(
                                padding: const EdgeInsets.only(right: 12),
                                child: CompactTypingIndicator(),
                              )
                              : null,
                    ),
                    maxLines: 5,
                    minLines: 1,
                    textCapitalization: TextCapitalization.sentences,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) {
                      if (!chatProvider.isLoading &&
                          !chatProvider.isTyping &&
                          !_isSending) {
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
                  onPressed:
                      (chatProvider.isLoading ||
                              chatProvider.isTyping ||
                              _isSending)
                          ? null
                          : _sendMessage,
                  style: IconButton.styleFrom(
                    backgroundColor:
                        (chatProvider.isLoading ||
                                chatProvider.isTyping ||
                                _isSending)
                            ? theme.colorScheme.primary.withValues(alpha: 0.5)
                            : theme.colorScheme.primary,
                    foregroundColor: theme.colorScheme.onPrimary,
                    disabledBackgroundColor: theme.colorScheme.primary
                        .withValues(alpha: 0.5),
                    disabledForegroundColor: theme.colorScheme.onPrimary
                        .withValues(alpha: 0.7),
                    fixedSize: const Size(56, 56), // Consistent size
                    shape: const CircleBorder(),
                    elevation:
                        (chatProvider.isLoading ||
                                chatProvider.isTyping ||
                                _isSending)
                            ? 0
                            : 2,
                    shadowColor: theme.colorScheme.primary.withValues(
                      alpha: 0.3,
                    ),
                  ),
                  icon:
                      _isSending
                          ? SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: theme.colorScheme.onPrimary,
                            ),
                          )
                          : const Icon(Icons.arrow_upward, size: 24),
                  tooltip: _isSending ? 'Sending...' : 'Send message',
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
      case SessionState.selectingSessionType:
      case SessionState.selectingDueTopics:
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
