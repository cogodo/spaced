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
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:async';
import 'dart:typed_data';
import 'dart:developer' as developer;
import 'package:logging/logging.dart';

// Centralize the WebSocket URL
const String _kWebSocketUrl = 'ws://127.0.0.1:8000/api/v1/voice/ws/voice';

/// A simple DTO for parsing WebSocket messages from the server.
class VoiceWsMessage {
  final String type;
  final String? text;

  VoiceWsMessage.fromJson(Map<String, dynamic> json)
    : type = json['type'],
      text = json['text'];
}

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

  // For WebSocket streaming
  WebSocketChannel? _channel;
  bool _isWebSocketConnected = false;
  StreamSubscription? _wsSubscription;

  // Map to store self-evaluation scores for each message
  final Map<int, int> _selfEvaluationScores = {};

  // Sidebar collapse state
  bool _isSidebarCollapsed = false;

  late final ChatProvider _chatProvider;
  FlutterSoundRecorder? _recorder;
  StreamController<Uint8List>? _recordingDataController;
  StreamSubscription? _recorderSubscription;

  String _transcript = ''; // To hold the live transcript
  Timer? _speechTimer; // To detect end of speech

  @override
  void initState() {
    super.initState();
    _chatProvider = Provider.of<ChatProvider>(context, listen: false);
    _recorder = FlutterSoundRecorder();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // This is a better place for this logic than initState/didUpdateWidget.
    // It runs when the widget's dependencies change, like when navigating.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (widget.sessionToken != null) {
        if (_chatProvider.currentSession?.token != widget.sessionToken) {
          _chatProvider.loadSessionByToken(widget.sessionToken!);
        }
      } else if (!_chatProvider.hasActiveSession) {
        _chatProvider.setSessionState(SessionState.initial);
      }
    });
  }

  @override
  void didUpdateWidget(ChatScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    // The logic is now primarily handled in didChangeDependencies,
    // but we can keep this as a secondary check if needed, though it's
    // often redundant if the provider handles state correctly.
    if (widget.sessionToken != oldWidget.sessionToken) {
      // This logic is now in didChangeDependencies and can likely be removed
      // to avoid redundant loads, but keeping it for safety for now.
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
    _speechTimer?.cancel();
    _disconnectWebSocket();
    _recorder?.closeRecorder();
    _recorder = null;
    _recordingDataController?.close();
    _recorderSubscription?.cancel();
    super.dispose();
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isEmpty || _isSending) return;

    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    if (chatProvider.isLoading) return;

    setState(() {
      _isSending = true;
      _transcript = ''; // Clear transcript on send
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

  Future<void> _startRecording() async {
    if (_recorder == null) return;
    try {
      await _recorder!.openRecorder();
      _recordingDataController = StreamController<Uint8List>();
      _recorderSubscription = _recordingDataController!.stream.listen((
        pcmChunk,
      ) {
        if (_channel != null && _isWebSocketConnected) {
          _channel!.sink.add(pcmChunk);
        }
      });
      await _recorder!.startRecorder(
        toStream: _recordingDataController!.sink,
        codec: Codec.pcm16,
        sampleRate: 16000,
        numChannels: 1,
      );
      developer.log("Recording started.", name: 'VoiceChat');
    } catch (e) {
      developer.log("Failed to start recorder:", name: 'VoiceChat', error: e);
    }
  }

  Future<void> _stopRecording() async {
    if (_recorder == null) return;
    try {
      await _recorder!.stopRecorder();
      await _recorderSubscription?.cancel();
      _recorderSubscription = null;
      await _recordingDataController?.close();
      _recordingDataController = null;
      developer.log("Recording stopped.", name: 'VoiceChat');
    } catch (e) {
      developer.log("Failed to stop recorder:", name: 'VoiceChat', error: e);
    }
  }

  void _handleServerMessage(dynamic message) {
    try {
      final wsMessage = VoiceWsMessage.fromJson(json.decode(message));
      if (wsMessage.type == 'transcript' && wsMessage.text != null) {
        setState(() {
          _transcript += " ${wsMessage.text!}"; // Append transcript
          _messageController.text = _transcript.trim();
          _messageController.selection = TextSelection.fromPosition(
            TextPosition(offset: _messageController.text.length),
          );
        });
        _resetSpeechTimer(); // Reset timer on new transcript
        developer.log('Transcript: "${wsMessage.text}"', name: 'VoiceChat');
      } else if (wsMessage.type == 'chat_response') {
        if (wsMessage.text != null) {
          final chatProvider = Provider.of<ChatProvider>(
            context,
            listen: false,
          );
          // Use the provider to add the user's transcript and the AI's response to the chat
          chatProvider.addVoiceMessage(_transcript, wsMessage.text!);

          // Clear the transcript and the input field
          setState(() {
            _transcript = '';
            _messageController.clear();
          });
        }
      }
    } catch (e) {
      developer.log('Received non-JSON message: $message', name: 'VoiceChat');
    }
  }

  void _handleSocketError(Object error, StackTrace stackTrace) {
    developer.log(
      'WebSocket error: $error',
      name: 'VoiceChat',
      stackTrace: stackTrace,
    );
    _disconnectWebSocket(); // Disconnect on error
  }

  Future<void> _connectWebSocket() async {
    developer.log("Connecting to WebSocket...", name: 'VoiceChat');

    // The browser will prompt for permission automatically on startRecorder.
    // No need to call a manual request here.

    try {
      final wsUrl = Uri.parse(_kWebSocketUrl);
      _channel = WebSocketChannel.connect(wsUrl);

      _wsSubscription = _channel!.stream.listen(
        _handleServerMessage,
        onError: _handleSocketError,
        onDone: () {
          developer.log(
            'WebSocket connection done (code=${_channel?.closeCode})',
            name: 'VoiceChat',
          );
          _disconnectWebSocket();
        },
        cancelOnError: true,
      );

      setState(() {
        _isWebSocketConnected = true;
        _transcript = ''; // Clear previous transcript
      });
      _startRecording();
      _resetSpeechTimer(); // Start timer
      developer.log("WebSocket connected.", name: 'VoiceChat');
    } catch (e) {
      developer.log("Failed to connect to WebSocket: $e", name: 'VoiceChat');
    }
  }

  Future<void> _disconnectWebSocket() async {
    if (!_isWebSocketConnected) return;

    developer.log("Disconnecting WebSocket...", name: 'VoiceChat');
    _speechTimer?.cancel(); // Cancel timer on disconnect
    await _stopRecording();

    // Defensive cleanup
    try {
      await _wsSubscription?.cancel();
    } catch (_) {}
    try {
      await _channel?.sink.close();
    } catch (_) {}

    _wsSubscription = null;
    _channel = null;

    if (mounted) {
      setState(() => _isWebSocketConnected = false);
    }
  }

  Future<void> _toggleWebSocketConnection() async {
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);
    if (chatProvider.isLoading) {
      developer.log("Chat is busy, ignoring voice input.", name: 'VoiceChat');
      return;
    }

    if (_isWebSocketConnected) {
      await _disconnectWebSocket();
    } else {
      await _connectWebSocket();
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

  void _resetSpeechTimer() {
    _speechTimer?.cancel();
    _speechTimer = Timer(const Duration(milliseconds: 1500), () {
      developer.log("End of speech detected.", name: 'VoiceChat');
      if (_isWebSocketConnected) {
        _toggleWebSocketConnection();
        // A short delay to ensure the UI updates before sending.
        Future.delayed(const Duration(milliseconds: 100), () {
          if (_messageController.text.isNotEmpty) {
            _sendMessage();
          }
        });
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
                    margin: const EdgeInsets.only(
                      bottom: 24,
                      left: 16,
                      right: 16,
                    ),
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
    // Add a Key for better performance
    return ChatBubble(
      key: ValueKey(messageIndex),
      message: message,
      formatTimestamp: _formatTimestamp,
    );
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
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);

    return _ChatInputBar(
      messageController: _messageController,
      focusNode: _textFieldFocusNode,
      onSendMessage: _sendMessage,
      onToggleVoice: _toggleWebSocketConnection,
      isWebSocketConnected: _isWebSocketConnected,
      isLoading: chatProvider.isLoading,
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

/// A dedicated widget for the chat input text field and action buttons.
class _ChatInputBar extends StatelessWidget {
  const _ChatInputBar({
    super.key,
    required this.messageController,
    required this.focusNode,
    required this.onSendMessage,
    required this.onToggleVoice,
    required this.isWebSocketConnected,
    required this.isLoading,
  });

  final TextEditingController messageController;
  final FocusNode focusNode;
  final VoidCallback onSendMessage;
  final VoidCallback onToggleVoice;
  final bool isWebSocketConnected;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final bool isEnabled = !isLoading;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(30),
        boxShadow: const [
          BoxShadow(
            color: Color.fromRGBO(0, 0, 0, 0.05),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: messageController,
              focusNode: focusNode,
              enabled: isEnabled,
              onSubmitted: (_) => onSendMessage(),
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                hintText: 'Type your message or use the mic...',
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(horizontal: 8),
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.send),
            onPressed: isEnabled ? onSendMessage : null,
          ),
          IconButton(
            icon: Icon(
              isWebSocketConnected ? Icons.mic_off : Icons.mic,
              color: theme.colorScheme.primary,
            ),
            onPressed: onToggleVoice,
          ),
        ],
      ),
    );
  }
}
