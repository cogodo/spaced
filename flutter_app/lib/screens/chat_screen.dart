import 'package:flutter/material.dart';
import 'package:markdown_widget/markdown_widget.dart';
import '../services/logger_service.dart';
import '../services/langgraph_api.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

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
  final _logger = getLogger('ChatScreen');
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _textFieldFocusNode = FocusNode();
  final List<ChatMessage> _messages = [];

  // LangGraph API integration
  late final LangGraphApi _api;
  SessionState _sessionState = SessionState.initial;
  String? _currentSessionId;
  bool _isLoading = false;
  Map<String, int>? _finalScores;

  // Session configuration
  final int _maxTopics = 3;
  final int _maxQuestions = 7;

  @override
  void initState() {
    super.initState();

    // Initialize API client
    _api = LangGraphApi(
      baseUrl:
          'https://spaced-x2o1.onrender.com', // Production backend on Render
    );

    // Add welcome message and prompt for topics
    _addSystemMessage(
      "Welcome to your personalized spaced repetition learning session! 🧠✨\n\n"
      "I'll help you learn and retain information using scientifically-proven spaced repetition techniques.\n\n"
      "To get started, please tell me what topics you'd like to study today. "
      "You can list multiple topics separated by commas.\n\n"
      "For example: 'Flutter widgets, Dart programming, Mobile development'",
    );

    _sessionState = SessionState.collectingTopics;
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    _textFieldFocusNode.dispose();
    super.dispose();
  }

  void _addSystemMessage(String text) {
    setState(() {
      _messages.add(
        ChatMessage(
          text: text,
          isUser: false,
          timestamp: DateTime.now(),
          isSystem: true,
        ),
      );
    });
    _scrollToBottom();
  }

  void _addUserMessage(String text) {
    setState(() {
      _messages.add(
        ChatMessage(text: text, isUser: true, timestamp: DateTime.now()),
      );
    });
    _scrollToBottom();
  }

  void _addAIMessage(String text) {
    setState(() {
      _messages.add(
        ChatMessage(text: text, isUser: false, timestamp: DateTime.now()),
      );
    });
    _scrollToBottom();
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty || _isLoading) return;

    _addUserMessage(text);
    _messageController.clear();

    // Keep focus on text field for better UX
    if (!_textFieldFocusNode.hasFocus) {
      _textFieldFocusNode.requestFocus();
    }

    _handleUserInput(text);
  }

  Future<void> _handleUserInput(String userInput) async {
    setState(() {
      _isLoading = true;
    });

    try {
      switch (_sessionState) {
        case SessionState.initial:
        case SessionState.collectingTopics:
          await _handleTopicsInput(userInput);
          break;

        case SessionState.active:
          await _handleAnswerInput(userInput);
          break;

        case SessionState.completed:
          await _handleCompletedState(userInput);
          break;

        case SessionState.error:
          await _handleErrorState(userInput);
          break;
      }
    } catch (e) {
      _logger.severe('Error handling user input: $e');
      await _handleError(e);
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _handleTopicsInput(String input) async {
    // Parse topics from user input
    List<String> topics =
        input
            .split(',')
            .map((topic) => topic.trim())
            .where((topic) => topic.isNotEmpty)
            .toList();

    if (topics.isEmpty) {
      _addAIMessage(
        "I couldn't find any topics in your message. Please list the topics you'd like to study, separated by commas.\n\n"
        "For example: 'Machine Learning, Python, Data Science'",
      );
      return;
    }

    if (topics.length > 10) {
      _addAIMessage(
        "That's quite a lot of topics! For the best learning experience, I recommend starting with 3-5 topics. "
        "Could you please select your most important topics?",
      );
      return;
    }

    // Start the session
    try {
      _addAIMessage(
        "Great! I'll create a learning session for: ${topics.join(', ')}\n\nStarting your session...",
      );

      final response = await _api.startSession(
        topics: topics,
        maxTopics: _maxTopics,
        maxQuestions: _maxQuestions,
      );

      _currentSessionId = response.sessionId;
      _sessionState = SessionState.active;

      await Future.delayed(
        const Duration(milliseconds: 500),
      ); // Brief pause for UX

      _addAIMessage(
        "📚 **Session Started!**\n\n"
        "I'll ask you up to $_maxQuestions questions per topic to assess your knowledge. "
        "Answer as best as you can - this helps me understand what you know and what needs more practice.\n\n"
        "**Question 1:**\n${response.nextQuestion}",
      );
    } on LangGraphApiException catch (e) {
      _sessionState = SessionState.error;
      _addAIMessage(
        "Sorry, I encountered an error starting your session: ${e.message}\n\n"
        "Would you like to try again with different topics?",
      );
    }
  }

  Future<void> _handleAnswerInput(String answer) async {
    if (_currentSessionId == null) {
      _addAIMessage("Session error: No active session ID. Let's start over.");
      _resetSession();
      return;
    }

    try {
      final response = await _api.answer(
        sessionId: _currentSessionId!,
        userInput: answer,
      );

      if (response.isDone) {
        // Session completed
        _sessionState = SessionState.completed;
        _finalScores = response.scores;

        _addAIMessage(_buildCompletionMessage(response.scores!));
      } else {
        // Continue with next question
        _addAIMessage("**Next Question:**\n${response.nextQuestion!}");
      }
    } on LangGraphApiException catch (e) {
      if (e.statusCode == 404) {
        _addAIMessage(
          "Your session has expired or is no longer valid. Let's start a new one!\n\n"
          "Please tell me what topics you'd like to study.",
        );
        _resetSession();
      } else {
        _sessionState = SessionState.error;
        _addAIMessage(
          "I encountered an error: ${e.message}\n\n"
          "Would you like to try answering again, or start a new session?",
        );
      }
    }
  }

  Future<void> _handleCompletedState(String input) async {
    final lowerInput = input.toLowerCase();

    if (lowerInput.contains('new') ||
        lowerInput.contains('again') ||
        lowerInput.contains('restart')) {
      _addAIMessage(
        "Starting a new session! What topics would you like to study this time?",
      );
      _resetSession();
    } else if (lowerInput.contains('score') || lowerInput.contains('result')) {
      if (_finalScores != null) {
        _addAIMessage(_buildCompletionMessage(_finalScores!));
      }
    } else {
      _addAIMessage(
        "Your learning session is complete! 🎉\n\n"
        "Would you like to:\n"
        "• Start a **new session** with different topics\n"
        "• **Review** your scores again\n"
        "• Ask me anything about spaced repetition learning",
      );
    }
  }

  Future<void> _handleErrorState(String input) async {
    final lowerInput = input.toLowerCase();

    if (lowerInput.contains('try') ||
        lowerInput.contains('again') ||
        lowerInput.contains('restart')) {
      _addAIMessage("Let's start fresh! What topics would you like to study?");
      _resetSession();
    } else {
      _addAIMessage(
        "I'm still having issues. Would you like to **try again** or **restart** with new topics?",
      );
    }
  }

  Future<void> _handleError(dynamic error) async {
    _sessionState = SessionState.error;
    String errorMessage = "I encountered an unexpected error.";

    if (error is LangGraphApiException) {
      errorMessage = "API Error: ${error.message}";
    } else {
      errorMessage = "Error: ${error.toString()}";
    }

    _addAIMessage(
      "$errorMessage\n\n"
      "Would you like to try again or start a new session?",
    );
  }

  String _buildCompletionMessage(Map<String, int> scores) {
    final buffer = StringBuffer();
    buffer.writeln("🎉 **Session Complete!**");
    buffer.writeln();
    buffer.writeln("Here are your learning scores (0-5 scale):");
    buffer.writeln();

    scores.forEach((topic, score) {
      String emoji;
      String feedback;

      if (score >= 4) {
        emoji = "🌟";
        feedback = "Excellent!";
      } else if (score >= 3) {
        emoji = "✅";
        feedback = "Good progress";
      } else if (score >= 2) {
        emoji = "📚";
        feedback = "Needs practice";
      } else {
        emoji = "🔄";
        feedback = "Review recommended";
      }

      buffer.writeln("$emoji **$topic**: $score/5 - $feedback");
    });

    buffer.writeln();
    buffer.writeln("**Spaced Repetition Recommendations:**");

    final lowScores = scores.entries.where((e) => e.value < 3).toList();
    if (lowScores.isNotEmpty) {
      buffer.writeln(
        "• Review these topics in 1 day: ${lowScores.map((e) => e.key).join(', ')}",
      );
    }

    final mediumScores =
        scores.entries.where((e) => e.value >= 3 && e.value < 4).toList();
    if (mediumScores.isNotEmpty) {
      buffer.writeln(
        "• Review these topics in 3 days: ${mediumScores.map((e) => e.key).join(', ')}",
      );
    }

    final highScores = scores.entries.where((e) => e.value >= 4).toList();
    if (highScores.isNotEmpty) {
      buffer.writeln(
        "• Review these topics in 1 week: ${highScores.map((e) => e.key).join(', ')}",
      );
    }

    buffer.writeln();
    buffer.writeln(
      "Would you like to start a **new session** with different topics?",
    );

    return buffer.toString();
  }

  void _resetSession() {
    setState(() {
      _sessionState = SessionState.collectingTopics;
      _currentSessionId = null;
      _finalScores = null;
    });
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
    return GestureDetector(
      // Dismiss keyboard when tapping outside interactive elements
      onTap: () {
        // Only unfocus if the tap isn't on the text field or button
        final FocusScopeNode currentScope = FocusScope.of(context);
        if (!currentScope.hasPrimaryFocus && currentScope.hasFocus) {
          FocusManager.instance.primaryFocus?.unfocus();
        }
      },
      // Make sure this doesn't interfere with child interactions
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
    if (_sessionState == SessionState.initial ||
        _sessionState == SessionState.collectingTopics) {
      return const SizedBox.shrink();
    }

    String statusText;
    Color statusColor;

    switch (_sessionState) {
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
          bottom: BorderSide(color: Theme.of(context).dividerColor, width: 1),
        ),
      ),
      child: Row(
        children: [
          Icon(
            _sessionState == SessionState.active
                ? Icons.psychology
                : _sessionState == SessionState.completed
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
          if (_sessionState == SessionState.active)
            TextButton(
              onPressed: () {
                showDialog(
                  context: context,
                  builder:
                      (context) => AlertDialog(
                        title: const Text('End Session'),
                        content: const Text(
                          'Are you sure you want to end the current learning session?',
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(context),
                            child: const Text('Cancel'),
                          ),
                          TextButton(
                            onPressed: () {
                              Navigator.pop(context);
                              _resetSession();
                              _addSystemMessage(
                                'Session ended. What topics would you like to study next?',
                              );
                            },
                            child: const Text('End Session'),
                          ),
                        ],
                      ),
                );
              },
              child: const Text('End Session'),
            ),
        ],
      ),
    );
  }

  Widget _buildMessagesArea() {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(
          bottom: BorderSide(color: Theme.of(context).dividerColor, width: 1),
        ),
      ),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        itemCount: _messages.length + (_isLoading ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _messages.length && _isLoading) {
            return _buildLoadingIndicator();
          }
          return _buildMessageBubble(_messages[index]);
        },
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    final isUser = message.isUser;
    final theme = Theme.of(context);

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[_buildAvatar(false), const SizedBox(width: 12)],
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
                  // Use markdown rendering for AI/system messages, plain text for user messages
                  if (isUser)
                    Text(
                      message.text,
                      style: TextStyle(
                        color: theme.colorScheme.onPrimary,
                        fontSize: 16,
                        height: 1.4,
                      ),
                    )
                  else
                    // Simple MarkdownWidget with basic theme-aware styling
                    MarkdownWidget(
                      data: message.text,
                      config: _buildMarkdownConfig(theme, message.isSystem),
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
          if (isUser) ...[const SizedBox(width: 12), _buildAvatar(true)],
        ],
      ),
    );
  }

  Widget _buildAvatar(bool isUser) {
    final theme = Theme.of(context);
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: isUser ? theme.colorScheme.primary : theme.colorScheme.secondary,
        shape: BoxShape.circle,
      ),
      child: Icon(
        isUser ? Icons.person : Icons.smart_toy,
        color: Colors.white,
        size: 20,
      ),
    );
  }

  Widget _buildLoadingIndicator() {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          _buildAvatar(false),
          const SizedBox(width: 12),
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
                  _getLoadingText(),
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

  String _getLoadingText() {
    switch (_sessionState) {
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
      decoration: BoxDecoration(
        color: theme.cardColor,
        border: Border(top: BorderSide(color: theme.dividerColor, width: 1)),
      ),
      child: SafeArea(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: _messageController,
                enabled: !_isLoading,
                focusNode: _textFieldFocusNode,
                decoration: InputDecoration(
                  hintText: _getInputHint(),
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
                  // Ensure hint doesn't interfere with touch
                  isDense: false,
                ),
                maxLines: 5,
                minLines: 1,
                textCapitalization: TextCapitalization.sentences,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) {
                  if (!_isLoading) {
                    _sendMessage();
                  }
                },
                // Auto-focus on certain states for better UX
                autofocus: _sessionState == SessionState.collectingTopics,
                // Ensure text field captures all tap events
                onTap: () {
                  if (!_textFieldFocusNode.hasFocus) {
                    _textFieldFocusNode.requestFocus();
                  }
                },
              ),
            ),
            const SizedBox(width: 12),
            // Use IconButton for better integration and accessibility
            IconButton(
              onPressed: _isLoading ? null : _sendMessage,
              style: IconButton.styleFrom(
                backgroundColor:
                    _isLoading
                        ? theme.colorScheme.primary.withValues(alpha: 0.5)
                        : theme.colorScheme.primary,
                foregroundColor: theme.colorScheme.onPrimary,
                disabledBackgroundColor: theme.colorScheme.primary.withValues(
                  alpha: 0.5,
                ),
                disabledForegroundColor: theme.colorScheme.onPrimary.withValues(
                  alpha: 0.7,
                ),
                fixedSize: const Size(56, 56), // Consistent size
                shape: const CircleBorder(),
                elevation: _isLoading ? 0 : 2,
                shadowColor: theme.colorScheme.primary.withValues(alpha: 0.3),
              ),
              icon: const Icon(Icons.send_rounded, size: 24),
              tooltip: 'Send message',
            ),
          ],
        ),
      ),
    );
  }

  String _getInputHint() {
    switch (_sessionState) {
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

  MarkdownConfig _buildMarkdownConfig(ThemeData theme, bool isSystem) {
    final baseConfig =
        isSystem ? MarkdownConfig.darkConfig : MarkdownConfig.defaultConfig;

    // Copy the base config but with theme-appropriate text colors
    return baseConfig.copy(
      configs: [
        PConfig(
          textStyle: TextStyle(
            color:
                isSystem
                    ? theme.colorScheme.onSecondaryContainer
                    : theme.textTheme.bodyLarge?.color,
            fontSize: 16,
            height: 1.4,
          ),
        ),
      ],
    );
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
