import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/logger_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _logger = getLogger('ChatScreen');
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _isTyping = false;

  @override
  void initState() {
    super.initState();
    // Add a welcome message
    _messages.add(
      ChatMessage(
        text:
            "Hello! I'm your AI assistant. How can I help you with your spaced repetition learning today?",
        isUser: false,
        timestamp: DateTime.now(),
      ),
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    // Add user message
    setState(() {
      _messages.add(
        ChatMessage(text: text, isUser: true, timestamp: DateTime.now()),
      );
      _isTyping = true;
    });

    _messageController.clear();
    _scrollToBottom();

    // Simulate AI response
    _simulateAIResponse(text);
  }

  Future<void> _simulateAIResponse(String userMessage) async {
    // Simulate typing delay
    await Future.delayed(const Duration(milliseconds: 1500));

    if (!mounted) return;

    // Generate a mock response based on user input
    String response = _generateMockResponse(userMessage);

    setState(() {
      _messages.add(
        ChatMessage(text: response, isUser: false, timestamp: DateTime.now()),
      );
      _isTyping = false;
    });

    _scrollToBottom();
  }

  String _generateMockResponse(String userMessage) {
    final lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.contains('spaced repetition') ||
        lowerMessage.contains('learning')) {
      return "Spaced repetition is a highly effective learning technique! It's based on the psychological spacing effect, where information is reviewed at increasing intervals. This helps move knowledge from short-term to long-term memory more efficiently.";
    } else if (lowerMessage.contains('memory') ||
        lowerMessage.contains('remember')) {
      return "Memory formation involves three key processes: encoding, storage, and retrieval. Spaced repetition optimizes all three by:\n\n1. **Encoding**: Active recall strengthens neural pathways\n2. **Storage**: Spaced intervals prevent forgetting\n3. **Retrieval**: Regular practice improves access to memories";
    } else if (lowerMessage.contains('help') || lowerMessage.contains('how')) {
      return "I'm here to help you optimize your learning! I can assist with:\n\n• Understanding spaced repetition principles\n• Tips for effective review sessions\n• Memory techniques and mnemonics\n• Study scheduling strategies\n• Learning psychology insights\n\nWhat specific aspect would you like to explore?";
    } else if (lowerMessage.contains('difficulty') ||
        lowerMessage.contains('hard')) {
      return "Finding something challenging? That's actually good for learning! Research shows that 'desirable difficulties' strengthen memory formation. Try breaking complex topics into smaller chunks and review them more frequently initially.";
    } else {
      return "That's an interesting question! Based on cognitive science research, effective learning often involves active recall, spaced practice, and connecting new information to existing knowledge. Could you tell me more about what specific learning challenge you're facing?";
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
    return Column(
      children: [
        // Chat messages area
        Expanded(child: _buildMessagesArea()),
        // Input area
        _buildInputArea(),
      ],
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
        itemCount: _messages.length + (_isTyping ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _messages.length && _isTyping) {
            return _buildTypingIndicator();
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
                color: isUser ? theme.colorScheme.primary : theme.cardColor,
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
                              : theme.textTheme.bodyLarge?.color,
                      fontSize: 16,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _formatTimestamp(message.timestamp),
                    style: TextStyle(
                      color: (isUser
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

  Widget _buildTypingIndicator() {
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
                _buildTypingDot(0),
                const SizedBox(width: 4),
                _buildTypingDot(1),
                const SizedBox(width: 4),
                _buildTypingDot(2),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTypingDot(int index) {
    return TweenAnimationBuilder<double>(
      duration: const Duration(milliseconds: 600),
      tween: Tween(begin: 0.4, end: 1.0),
      builder: (context, value, child) {
        return AnimatedContainer(
          duration: Duration(milliseconds: 300 + (index * 150)),
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: Theme.of(
              context,
            ).textTheme.bodyMedium?.color?.withValues(alpha: value),
            shape: BoxShape.circle,
          ),
        );
      },
    );
  }

  Widget _buildInputArea() {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.cardColor,
        border: Border(top: BorderSide(color: theme.dividerColor, width: 1)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _messageController,
              decoration: InputDecoration(
                hintText: 'Ask me anything about learning and memory...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
                filled: true,
                fillColor: theme.scaffoldBackgroundColor,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 12,
                ),
              ),
              maxLines: null,
              textCapitalization: TextCapitalization.sentences,
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: _sendMessage,
            child: Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: theme.colorScheme.primary,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.send,
                color: theme.colorScheme.onPrimary,
                size: 24,
              ),
            ),
          ),
        ],
      ),
    );
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

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
  });
}
