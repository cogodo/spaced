import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/chat_session.dart';
import '../providers/chat_provider.dart';
import '../widgets/chat_progress_widget.dart';
import '../widgets/typing_indicator_widget.dart';
import '../widgets/topic_selection_widget.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter/services.dart';
import '../widgets/chat_bubble.dart';
import '../services/session_api.dart';

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
  Set<ChatSessionSummary> _selectedSessions = {};

  // Prevent duplicate sends
  bool _isSending = false;

  // Map to store self-evaluation scores for each message
  final Map<int, int> _selfEvaluationScores = {};

  // Sidebar collapse state
  bool _isSidebarCollapsed = false;

  late final ChatProvider _chatProvider;

  @override
  void initState() {
    super.initState();
    _chatProvider = Provider.of<ChatProvider>(context, listen: false);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      // If a session token is in the URL, try to load it, but only if it's
      // not already the active session in the provider. This prevents redundant
      // loading when navigating back to an already active chat.
      if (widget.sessionToken != null) {
        if (_chatProvider.currentSession?.token != widget.sessionToken) {
          _chatProvider.loadSessionByToken(widget.sessionToken!);
        }
      }
      // If there's no token in the URL and no session is active, ensure
      // we are in the initial state to start a new chat.
      else if (!_chatProvider.hasActiveSession) {
        _chatProvider.setSessionState(SessionState.initial);
      }
    });
  }

  @override
  void didUpdateWidget(ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Handle token changes when navigating between sessions
    if (widget.sessionToken != oldWidget.sessionToken) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (widget.sessionToken != null) {
          final chatProvider = Provider.of<ChatProvider>(
            context,
            listen: false,
          );
          // Also check here to prevent redundant loading on navigation.
          if (chatProvider.currentSession?.token == widget.sessionToken) {
            return;
          }
          _chatProvider.loadSessionByToken(widget.sessionToken!);
        }
      });
    }
  }

  void _startNewItemsSession() {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    chatProvider.setSessionState(SessionState.collectingTopics);
  }

  void _startPastReviewsSession() {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    chatProvider.setSessionState(SessionState.selectingDueTopics);
  }

  void _startDueTopicsSession() {
    if (_selectedSessions.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select at least one session to review'),
        ),
      );
      return;
    }

    final topics =
        _selectedSessions.expand<String>((s) => s.topics).toSet().toList();
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    chatProvider.startNewSession(topics);
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

    setState(() {
      _isSending = true;
    });

    try {
      chatProvider.sendMessage(text).whenComplete(() {
        if (mounted) {
          setState(() {
            _isSending = false;
          });
        }
      });

      _messageController.clear();
      if (!_textFieldFocusNode.hasFocus) {
        _textFieldFocusNode.requestFocus();
      }
    } catch (e) {
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
      child: Container(
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
              if (chatProvider.sessionState ==
                  SessionState.selectingDueTopics) {
                return _buildDueTopicsSelection(chatProvider);
              }

              // Show normal chat interface
              return Column(
                children: [
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
                        return _buildMessageBubble(
                          chatProvider.messages[index],
                          index,
                        );
                      },
                    ),
                  ),
                  // Action buttons for active sessions
                  if (chatProvider.sessionState == SessionState.active)
                    _buildActionButtons(),
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
                await chatProvider.startNewSession(topics);
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDueTopicsSelection(ChatProvider chatProvider) {
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
                color: theme.colorScheme.outline.withOpacity(0.2),
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
                          'Choose which past sessions you\'d like to review topics from',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onSurface.withOpacity(0.7),
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
              chatProvider.isLoadingHistory
                  ? const Center(child: CircularProgressIndicator())
                  : chatProvider.sessionHistory.isEmpty
                  ? _buildNoSessionsMessage()
                  : _buildSessionsList(chatProvider.sessionHistory),
        ),

        // Bottom action bar
        if (chatProvider.sessionHistory.isNotEmpty)
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              border: Border(
                top: BorderSide(
                  color: theme.colorScheme.outline.withOpacity(0.2),
                ),
              ),
            ),
            child: Row(
              children: [
                Text(
                  '${_selectedSessions.length} session${_selectedSessions.length == 1 ? '' : 's'} selected',
                  style: theme.textTheme.bodyMedium,
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed:
                      _selectedSessions.isEmpty ? null : _startDueTopicsSession,
                  child: const Text('Start Review Session'),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildNoSessionsMessage() {
    final theme = Theme.of(context);

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 400),
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.history_toggle_off,
              size: 80,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 24),
            Text(
              'No Past Sessions',
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onSurface,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Text(
              'You don\'t have any past sessions to review. Complete a session first!',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.7),
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

  Widget _buildSessionsList(List<ChatSessionSummary> sessions) {
    final theme = Theme.of(context);

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: sessions.length,
      itemBuilder: (context, index) {
        final session = sessions[index];
        final isSelected = _selectedSessions.contains(session);

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: CheckboxListTile(
            value: isSelected,
            onChanged: (bool? value) {
              setState(() {
                if (value == true) {
                  _selectedSessions.add(session);
                } else {
                  _selectedSessions.remove(session);
                }
              });
            },
            title: Text(
              session.displayName,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            subtitle: Text(
              'Topics: ${session.topics.join(', ')}',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
            controlAffinity: ListTileControlAffinity.trailing,
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

          return Column(
            children: [
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
                    return _buildMessageBubble(
                      chatProvider.messages[index],
                      index,
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message, int messageIndex) {
    if (message.text ==
        "Please use the buttons below to evaluate your answer.") {
      return Column(
        children: [
          ChatBubble(message: message, formatTimestamp: _formatTimestamp),
          _buildSelfEvaluationButtons(
            messageIndex - 1,
          ), // Associate with user's message
        ],
      );
    }
    return ChatBubble(message: message, formatTimestamp: _formatTimestamp);
  }

  Widget _buildSelfEvaluationButtons(int messageIndex) {
    return Container(); // Disabled for now
  }

  Color _getScoreColor(int score) {
    switch (score) {
      case 1:
        return Colors.red;
      case 2:
        return Colors.orangeAccent;
      case 3:
        return Colors.yellow;
      case 4:
        return Colors.lightGreen;
      case 5:
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  Future<void> _submitSelfEvaluation(int messageIndex, int score) async {
    // Disabled
  }

  Widget _buildActionButtons() {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      child: SafeArea(
        child: Consumer<ChatProvider>(
          builder: (context, chatProvider, child) {
            return Row(
              children: [
                // Skip Question Button
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed:
                        (chatProvider.isLoading ||
                                chatProvider.isTyping ||
                                _isSending)
                            ? null
                            : () async {
                              await chatProvider.skipCurrentQuestion();
                            },
                    icon: const Icon(Icons.skip_next, size: 18),
                    label: const Text('Skip Question'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 10,
                      ),
                      side: BorderSide(
                        color: theme.colorScheme.outline,
                        width: 1,
                      ),
                      foregroundColor: theme.colorScheme.onSurface,
                      disabledForegroundColor: theme.colorScheme.onSurface
                          .withOpacity(0.4),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                // End Session Button
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed:
                        (chatProvider.isLoading ||
                                chatProvider.isTyping ||
                                _isSending)
                            ? null
                            : () async {
                              // Show confirmation dialog
                              final confirmed = await showDialog<bool>(
                                context: context,
                                builder:
                                    (context) => AlertDialog(
                                      title: const Text('End Session?'),
                                      content: const Text(
                                        'Are you sure you want to end this learning session early? '
                                        'Your progress will be saved.',
                                      ),
                                      actions: [
                                        TextButton(
                                          onPressed:
                                              () => Navigator.of(
                                                context,
                                              ).pop(false),
                                          child: const Text('Cancel'),
                                        ),
                                        TextButton(
                                          onPressed:
                                              () => Navigator.of(
                                                context,
                                              ).pop(true),
                                          child: const Text('End Session'),
                                        ),
                                      ],
                                    ),
                              );

                              if (confirmed == true) {
                                await chatProvider.endCurrentSession();
                              }
                            },
                    icon: const Icon(Icons.stop, size: 18),
                    label: const Text('End Session'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 10,
                      ),
                      side: BorderSide(
                        color: theme.colorScheme.error,
                        width: 1,
                      ),
                      foregroundColor: theme.colorScheme.error,
                      disabledForegroundColor: theme.colorScheme.error
                          .withOpacity(0.4),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                  ),
                ),
              ],
            );
          },
        ),
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
                        !_isSending &&
                        chatProvider.sessionState != SessionState.error &&
                        chatProvider.sessionState != SessionState.completed,
                    focusNode: _textFieldFocusNode,
                    style: theme.textTheme.bodyLarge?.copyWith(
                      height: 1.4,
                      letterSpacing: 0.2,
                    ),
                    decoration: InputDecoration(
                      hintText: _getInputHint(chatProvider.sessionState),
                      hintStyle: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.textTheme.bodyMedium?.color?.withAlpha(
                          0.6.toInt(),
                        ),
                        letterSpacing: 0.2,
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
                          !_isSending &&
                          chatProvider.sessionState != SessionState.error &&
                          chatProvider.sessionState != SessionState.completed) {
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
                              _isSending ||
                              chatProvider.sessionState == SessionState.error ||
                              chatProvider.sessionState ==
                                  SessionState.completed)
                          ? null
                          : _sendMessage,
                  style: IconButton.styleFrom(
                    backgroundColor:
                        (chatProvider.isLoading ||
                                chatProvider.isTyping ||
                                _isSending)
                            ? theme.colorScheme.primary.withAlpha(0.5.toInt())
                            : theme.colorScheme.primary,
                    foregroundColor: theme.colorScheme.onPrimary,
                    disabledBackgroundColor: theme.colorScheme.primary
                        .withAlpha(0.5.toInt()),
                    disabledForegroundColor: theme.colorScheme.onPrimary
                        .withAlpha(0.7.toInt()),
                    fixedSize: const Size(56, 56), // Consistent size
                    shape: const CircleBorder(),
                    elevation:
                        (chatProvider.isLoading ||
                                chatProvider.isTyping ||
                                _isSending)
                            ? 0
                            : 2,
                    shadowColor: theme.colorScheme.primary.withAlpha(
                      0.3.toInt(),
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
        return 'Session completed';
      case SessionState.error:
        return 'Input disabled due to error';
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
  int? evaluation;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.isSystem = false,
    this.evaluation,
  });
}
