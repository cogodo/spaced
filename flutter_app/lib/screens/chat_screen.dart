import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/typing_indicator_widget.dart';
import '../widgets/topic_selection_widget.dart';
import '../widgets/session_type_selection_widget.dart';
import '../widgets/due_topics_selection_widget.dart';
import 'package:go_router/go_router.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/voice_button.dart';
import '../widgets/stt_button.dart';
import '../services/audio_player_service.dart';
import '../services/stt_service.dart';
import '../services/auth_service.dart';
import '../services/logger_service.dart';

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
  final _logger = getLogger('ChatScreen');

  // For due topics selection (kept for backwards compatibility)
  List<dynamic> _dueTasks = []; // Changed from List<Task> to List<dynamic>
  final Set<String> _selectedTopics = {};
  bool _isLoadingDueTasks = false;

  // Prevent duplicate sends
  bool _isSending = false;

  // Voice chat state
  LiveKitVoiceService? _voiceService;
  bool _isVoiceConnecting = false;
  bool _isVoiceConnected = false;
  bool _isSpeaking = false;
  String? _currentTranscript;

  // STT service
  SttService? _sttService;

  @override
  void initState() {
    super.initState();

    // Initialize voice service
    _initializeVoiceService();

    // Initialize STT service
    _initializeSttService();

    // Load session based on token, but don't auto-start new sessions
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);

      // Set up auto-scroll callback
      chatProvider.setAutoScrollCallback(_scrollToBottomWithDelay);

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

  void _initializeVoiceService() {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    _voiceService = LiveKitVoiceService(baseUrl: chatProvider.backendUrl);

    // Set up voice event callbacks
    _voiceService!.onTranscriptReceived = (transcript) {
      _logger.info('Interim transcript: $transcript');
      setState(() {
        _currentTranscript = transcript;
        _messageController.text = transcript;
      });
    };

    _voiceService!.onFinalTranscriptReceived = (transcript) {
      _logger.info('Final transcript: $transcript');
      _currentTranscript = null;
      _messageController.clear();

      if (transcript.isNotEmpty && mounted) {
        final chatProvider = Provider.of<ChatProvider>(context, listen: false);

        // Send transcript through regular chat flow (not voice-specific)
        chatProvider.handleVoiceTranscript(transcript);

        // Auto-scroll with delay for consistency
        _scrollToBottomWithDelay();

        _logger.info('Voice transcript sent to regular chat API');
      }
    };

    // Note: onAgentResponse may not be used in new flow since voice agent handles TTS directly

    _voiceService!.onConnected = () {
      _logger.info('Voice connected');
      if (mounted) {
        setState(() {
          _isVoiceConnected = true;
          _isVoiceConnecting = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Voice chat connected! You can now speak.'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    };

    _voiceService!.onDisconnected = () {
      _logger.info('Voice disconnected');
      if (mounted) {
        setState(() {
          _isVoiceConnected = false;
          _isSpeaking = false;
        });
      }
    };

    _voiceService!.onError = (error) {
      _logger.severe('Voice error: $error');
      if (mounted) {
        setState(() {
          _isVoiceConnecting = false;
          _isVoiceConnected = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Voice error: $error'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    };

    _voiceService!.onLocalSpeakingChanged = (isSpeaking) {
      if (mounted) {
        setState(() {
          _isSpeaking = isSpeaking;
        });
        _logger.info('Speaking status changed: $isSpeaking');
      }
    };
  }

  void _initializeSttService() {
    _sttService = SttService();
    _sttService!.initialize();
    _logger.info('STT service initialized');
  }

  void _handleSttTranscript(String transcript) {
    _logger.info('STT transcript received: $transcript');
    setState(() {
      _messageController.text = transcript;
    });
  }

  Future<void> _toggleVoiceChat() async {
    if (_isVoiceConnecting) return;

    if (_isVoiceConnected) {
      // Disconnect voice
      await _voiceService?.disconnect();
      setState(() {
        _isVoiceConnected = false;
        _isSpeaking = false;
      });
    } else {
      // Connect to voice
      setState(() {
        _isVoiceConnecting = true;
      });

      // Get current chat session ID and capture context
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      String? chatId = chatProvider.currentSessionId;
      final mounted = this.mounted;
      final scaffoldMessenger = ScaffoldMessenger.of(context);
      final theme = Theme.of(context);

      try {
        // Get user ID
        final authService = AuthService();
        final user = authService.currentUser;
        if (user == null) {
          throw Exception('User not authenticated');
        }

        // Request microphone permission
        final hasMicPermission =
            await _voiceService!.requestMicrophonePermission();
        if (!hasMicPermission) {
          throw Exception('Microphone permission denied');
        }

        // Require a valid chat ID for voice
        if (chatId == null || chatId.isEmpty) {
          throw Exception(
            'No active session found. Please start a chat session first.',
          );
        }

        // Check voice service health before starting
        final isHealthy = await _voiceService!.checkVoiceServiceHealth();
        if (!mounted) return;
        if (!isHealthy) {
          throw Exception(
            'Voice service is not healthy. Please try again later.',
          );
        }

        // Start voice session with chat ID only
        await _voiceService!.startVoiceSession(chatId, user.uid);

        // Unlock audio playback on web after user gesture
        if (mounted) {
          await _voiceService!.startAudioPlayback();
        }
      } catch (e) {
        _logger.severe('Failed to start voice chat: $e');
        if (mounted) {
          setState(() {
            _isVoiceConnecting = false;
            _isVoiceConnected = false;
          });
          scaffoldMessenger.showSnackBar(
            SnackBar(
              content: Text('Failed to start voice chat: $e'),
              backgroundColor: theme.colorScheme.error,
            ),
          );
        }
      }
    }
  }

  @override
  void didUpdateWidget(ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Handle token changes when navigating between sessions
    if (widget.sessionToken != oldWidget.sessionToken) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (widget.sessionToken != null) {
          _loadSessionByToken(widget.sessionToken!);
        }
      });
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
              onPressed: () => chatProvider.startNewSession(['General']),
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
      // Since we removed the old task system, just set empty tasks
      setState(() {
        _dueTasks = [];
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
    chatProvider.setSessionState(SessionState.collectingTopics);
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
    chatProvider.startNewSession(_selectedTopics.toList());
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    _textFieldFocusNode.dispose();
    _voiceService?.dispose();
    _sttService?.dispose();
    super.dispose();
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _isSending) return;

    setState(() {
      _isSending = true;
    });

    _messageController.clear();
    FocusScope.of(context).unfocus();

    try {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      await chatProvider.sendMessage(text);

      // Auto-scroll with delay for consistency
      _scrollToBottomWithDelay();
    } catch (e) {
      _logger.severe('Error sending message: $e');
      // Handle error (maybe show a snackbar)
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
        });
      }
    }
  }

  void _scrollToBottomWithDelay() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (mounted && _scrollController.hasClients) {
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
                return SessionTypeSelectionWidget(
                  onNewItemsPressed: _startNewItemsSession,
                  onPastReviewsPressed: _startPastReviewsSession,
                );
              }

              // Show topic selection for new items
              if (chatProvider.sessionState == SessionState.collectingTopics) {
                return _buildTopicSelectionScreen();
              }

              // Show due topics selection
              if (chatProvider.sessionState ==
                  SessionState.selectingDueTopics) {
                return DueTopicsSelectionWidget(
                  dueTasks: _dueTasks,
                  selectedTopics: _selectedTopics,
                  isLoadingDueTasks: _isLoadingDueTasks,
                  onBackPressed: () {
                    final chatProvider = Provider.of<ChatProvider>(
                      context,
                      listen: false,
                    );
                    chatProvider.setSessionState(SessionState.initial);
                  },
                  onStartSession: _startDueTopicsSession,
                  onTopicToggled: (topicId) {
                    setState(() {
                      if (_selectedTopics.contains(topicId)) {
                        _selectedTopics.remove(topicId);
                      } else {
                        _selectedTopics.add(topicId);
                      }
                    });
                  },
                );
              }

              // Show normal chat interface
              return Stack(
                children: [
                  Column(
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
                                sessionState:
                                    chatProvider.sessionState.toString(),
                                isGeneratingQuestions:
                                    chatProvider.isGeneratingQuestions,
                                isProcessingAnswer:
                                    chatProvider.isProcessingAnswer,
                              );
                            }
                            return _buildMessageBubble(
                              chatProvider.messages[index],
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
                  ),
                ],
              );
            },
          ),
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
                // Use the proper method that handles state transitions
                await chatProvider.startSessionWithPopularTopic(topic);
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    return ChatBubble(message: message, formatTimestamp: _formatTimestamp);
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
                          .withValues(alpha: 0.4),
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
                          .withValues(alpha: 0.4),
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
            return Consumer<SettingsProvider>(
              builder: (context, settingsProvider, child) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    // Voice-to-voice button - Disabled due to RAM constraints
                    // if (chatProvider.sessionState == SessionState.active &&
                    //     settingsProvider.voiceEnabled) ...[
                    //   VoiceButton(
                    //     isConnecting: _isVoiceConnecting,
                    //     isVoiceConnected: _isVoiceConnected,
                    //     isSpeaking: _isSpeaking,
                    //     onTap: _toggleVoiceChat,
                    //     size: 56.0, // Match the send button size
                    //   ),
                    //   const SizedBox(width: 12),
                    // ],

                    // STT button (only show when session is active AND STT is enabled)
                    if (chatProvider.sessionState == SessionState.active &&
                        settingsProvider.sttEnabled &&
                        _sttService != null &&
                        _sttService!.isInitialized) ...[
                      SttButton(
                        sttService: _sttService!,
                        onTranscriptReceived: _handleSttTranscript,
                        size: 56.0, // Match the send button size
                      ),
                      const SizedBox(width: 12),
                    ],
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
                            color: theme.textTheme.bodyMedium?.color
                                ?.withValues(alpha: 0.6),
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
                                  : _currentTranscript != null
                                  ? Padding(
                                    padding: const EdgeInsets.only(right: 12),
                                    child: Icon(
                                      Icons.mic,
                                      color: theme.colorScheme.primary,
                                      size: 20,
                                    ),
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
                              chatProvider.sessionState !=
                                  SessionState.completed) {
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
                                  chatProvider.sessionState ==
                                      SessionState.error ||
                                  chatProvider.sessionState ==
                                      SessionState.completed)
                              ? null
                              : _sendMessage,
                      style: IconButton.styleFrom(
                        backgroundColor:
                            (chatProvider.isLoading ||
                                    chatProvider.isTyping ||
                                    _isSending)
                                ? theme.colorScheme.primary.withValues(
                                  alpha: 0.5,
                                )
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
        return 'Type your answer or use voice...';
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
  final bool isVoice;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.isSystem = false,
    this.isVoice = false,
  });
}
