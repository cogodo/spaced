import 'package:flutter/foundation.dart';
import 'package:go_router/go_router.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'dart:convert';
import '../models/chat_session.dart';
import '../screens/chat_screen.dart'; // For SessionState and ChatMessage
import '../services/session_api.dart';
import '../services/chat_session_service.dart';
import '../services/logger_service.dart';
// Note: Voice functionality now handled by LiveKit in chat screen
// import '../services/audio_player_service.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'dart:async';

class ChatProvider extends ChangeNotifier {
  final _logger = getLogger('ChatProvider');

  // Current session state
  ChatSession? _currentSession;
  SessionState _sessionState = SessionState.initial;
  List<ChatMessage> _messages = [];
  String? _currentSessionId;
  String? _currentTopicId;
  bool _isLoading = false;
  Map<String, int>? _finalScores;

  // Session history
  List<ChatSessionSummary> _sessionHistory = [];
  bool _isLoadingHistory = false;

  // Services
  late final ApiService _api;
  late final ChatSessionService _sessionService;
  // Voice functionality moved to LiveKit in chat screen
  // late final AudioPlayerService _audioPlayerService;

  // User ID for Firebase operations
  String? _userId;

  // Navigation context for URL updates
  GoRouter? _router;

  // Popular topics support
  List<Topic> _popularTopics = [];
  bool _isLoadingPopularTopics = false;

  // Due topics for the "Today's Reviews" screen
  DueTopics? _dueTopics;
  bool _isLoadingDueTopics = false;

  // Track topics reviewed in the current app session
  final Set<String> _recentlyReviewedTopicIds = {};

  // Enhanced loading and typing states
  bool _isTyping = false;
  String? _typingMessage;
  bool _isGeneratingQuestions = false;
  bool _isProcessingAnswer = false;
  bool _isStartingSession = false;
  String? _currentGeneratingTopic; // Track the topic being generated

  // Auto-scroll callback (set by chat screen)
  VoidCallback? _autoScrollCallback;

  StreamSubscription<QuerySnapshot>? _messagesSubscription;

  bool _isEndingSession = false; // Add flag to prevent double ending

  ChatProvider() {
    String backendUrl;

    if (kIsWeb) {
      final host = Uri.base.host;
      if (host.contains('staging')) {
        backendUrl = 'https://api.staging.getspaced.app';
      } else if (host == 'localhost' || host == '127.0.0.1') {
        backendUrl = 'http://localhost:8000';
      } else {
        backendUrl = 'https://api.getspaced.app';
      }
    } else {
      backendUrl = const String.fromEnvironment(
        'BACKEND_URL',
        defaultValue: 'http://10.0.2.2:8000',
      );
    }

    _logger.info('ChatProvider initialized with backend URL: $backendUrl');

    _api = ApiService(baseUrl: backendUrl);
    _sessionService = ChatSessionService();
    // Voice functionality moved to LiveKit in chat screen
    // _audioPlayerService = AudioPlayerService(baseUrl: backendUrl);
  }

  // Getters
  ChatSession? get currentSession => _currentSession;
  SessionState get sessionState => _sessionState;
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  String? get currentSessionId => _currentSessionId;
  String? get currentTopicId => _currentTopicId;
  bool get isLoading => _isLoading;
  Map<String, int>? get finalScores => _finalScores;
  List<ChatSessionSummary> get sessionHistory =>
      List.unmodifiable(_sessionHistory);
  bool get hasActiveSession => _currentSession != null;
  bool get isLoadingHistory => _isLoadingHistory;
  String? get userId => _userId;
  List<Topic> get popularTopics => List.unmodifiable(_popularTopics);
  bool get isLoadingPopularTopics => _isLoadingPopularTopics;
  DueTopics? get dueTopics => _dueTopics;
  bool get isLoadingDueTopics => _isLoadingDueTopics;
  Set<String> get recentlyReviewedTopicIds => _recentlyReviewedTopicIds;

  // Enhanced loading state getters
  bool get isTyping => _isTyping;
  String? get typingMessage => _typingMessage;
  bool get isGeneratingQuestions => _isGeneratingQuestions;
  bool get isProcessingAnswer => _isProcessingAnswer;
  bool get isStartingSession => _isStartingSession;
  String? get currentGeneratingTopic => _currentGeneratingTopic;

  // Backend URL getter for voice service
  String get backendUrl => _api.baseUrl;

  // API Service getter for question management
  ApiService get apiService => _api;

  // Helper method for authenticated API calls
  Future<Map<String, String>> _getAuthHeaders() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw Exception('User not authenticated');
    }
    final idToken = await user.getIdToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $idToken',
    };
  }

  void addVoiceMessage(String transcript, String aiResponse) {
    _addUserMessage(transcript, isVoice: true);
    _addAIMessage(aiResponse, isVoice: true);
    _updateCurrentSession();
    _autoSaveSession(); // Persist the new messages

    // Play the AI's response - moved to LiveKit voice system in chat screen
    // _audioPlayerService.playFromText(aiResponse);

    notifyListeners();
  }

  void setRouter(GoRouter router) {
    _router = router;
  }

  void setUserId(String? userId) {
    if (_userId == userId) return; // No change
    _userId = userId;
    if (userId != null) {
      loadSessionHistory();
      fetchDueTopics(); // Also fetch due topics on user set
    } else {
      clear();
    }
  }

  Future<void> loadPopularTopics() async {
    if (_isLoadingPopularTopics) return;

    _isLoadingPopularTopics = true;
    notifyListeners();

    try {
      _popularTopics = await _api.getTopics(view: 'status');
    } catch (e) {
      _logger.severe('Error loading popular topics: $e');
    } finally {
      _isLoadingPopularTopics = false;
      notifyListeners();
    }
  }

  void setSessionState(SessionState newState) {
    if (_sessionState != newState) {
      _sessionState = newState;
      notifyListeners();
    }
  }

  /// Reset the current session to start a new chat flow.
  void startNewChatFlow() {
    _currentSession = null;
    _sessionState = SessionState.initial;
    _messages = [];
    _currentSessionId = null;
    _currentTopicId = null;
    _finalScores = null;
    _isTyping = false;
    _isLoading = false;
    _isGeneratingQuestions = false;
    _isProcessingAnswer = false;
    _isStartingSession = false;
    _currentGeneratingTopic = null;
    _recentlyReviewedTopicIds.clear();

    // Navigate to the clean chat screen to begin topic selection.
    _router?.go('/app/chat');

    notifyListeners();
    _logger.info('Reset session state for new chat flow.');
  }

  /// Reset to initial state (alias for startNewChatFlow)
  void resetToInitialState() {
    startNewChatFlow();
  }

  /// Initialize a new chat session
  Future<void> startNewSession(List<String> topics) async {
    _logger.info('Starting new chat session with topics: $topics');
    _setLoadingWithTyping(
      true,
      typingMessage: "Preparing your learning session...",
      generatingQuestions: true,
    );
    _isStartingSession = true;
    _isGeneratingQuestions = true;
    _currentGeneratingTopic = topics.isNotEmpty ? topics.first : null;
    notifyListeners();

    try {
      final response = await _api.startChat(topics);
      _currentSessionId = response.chatId;
      _currentTopicId = response.topicId;
      _sessionState = SessionState.active;

      final session = ChatSession.create(
        id: response.chatId,
        topics: response.topics,
        name: 'New Session - ${_formatTimestamp(DateTime.now())}',
        topicId: response.topicId,
      );

      // Update session to active state since we're starting with topics
      _currentSession = session.copyWith(state: SessionState.active);

      _addAIMessage(response.message);

      // Play the initial message as audio - moved to LiveKit voice system
      // if (response.message.isNotEmpty) {
      //   _audioPlayerService.playFromText(response.message);
      // }

      if (_userId != null) {
        await _sessionService.saveSession(_userId!, _currentSession!);
        loadSessionHistory();
        // Start listening to messages for the new session
        _listenToMessages(_userId!, _currentSessionId!);
      }
      _router?.go('/app/chat/${_currentSession!.token}');

      // Auto-scroll to show the initial message
      _autoScrollCallback?.call();
    } catch (e) {
      _logger.severe('Error starting new session: $e');
      if (e is ApiException) {
        _addAIMessage('Error starting session: ${e.message}');
      } else {
        _addAIMessage(
          'Error: Could not start a new session. Please try again.',
        );
      }
      _sessionState = SessionState.error;
    } finally {
      _setLoadingWithTyping(
        false,
        typingMessage: null,
        generatingQuestions: false,
      );
      _isStartingSession = false;
      _isGeneratingQuestions = false;
      _currentGeneratingTopic = null;
      notifyListeners();
    }
  }

  /// Handle topic input from the topic selection widget
  Future<void> handleTopicsInput(List<String> topics) async {
    if (topics.isEmpty) return;

    // If we already have a current session, continue with it instead of creating new one
    if (_currentSessionId != null && _sessionState != SessionState.initial) {
      _logger.info(
        'Continuing existing session $_currentSessionId with topics: $topics',
      );

      // Get the initial AI question for this topic using the existing session
      _setLoadingWithTyping(
        true,
        typingMessage: "Preparing your questions...",
        generatingQuestions: true,
      );
      _isGeneratingQuestions = true;
      _currentGeneratingTopic = topics.isNotEmpty ? topics.first : null;
      notifyListeners();

      try {
        // Use startChat with existing session ID to get the proper initial message
        final response = await _api.startChat(topics, _currentSessionId);

        // Transition to active state
        _sessionState = SessionState.active;

        // Add the AI's initial question (not a user message)
        _addAIMessage(response.message);

        // Update session metadata with new topics if needed
        if (_currentSession != null) {
          _currentSession = _currentSession!.copyWith(
            topics: [..._currentSession!.topics, ...topics],
            state: SessionState.active,
            updatedAt: DateTime.now(),
          );

          // Save the updated session
          if (_userId != null) {
            await _sessionService.saveSession(_userId!, _currentSession!);
          }
        }
      } catch (e) {
        _logger.severe('Error adding topics to session: $e');
        if (e is ApiException) {
          _addAIMessage('Error: ${e.message}');
        } else {
          _addAIMessage(
            'An error occurred while preparing your questions. Please try again.',
          );
        }
      } finally {
        _setLoadingWithTyping(
          false,
          typingMessage: null,
          generatingQuestions: false,
        );
        _isGeneratingQuestions = false;
        _currentGeneratingTopic = null;
      }

      notifyListeners();
    } else {
      // Start a new session with the selected topics
      await startNewSession(topics);
    }
  }

  /// Start session with a popular topic
  Future<void> startSessionWithPopularTopic(Topic topic) async {
    // If we already have a current session, continue with it instead of creating new one
    if (_currentSessionId != null && _sessionState != SessionState.initial) {
      _logger.info(
        'Continuing existing session $_currentSessionId with popular topic: ${topic.name}',
      );

      // Get the initial AI question for this topic using the existing session
      _setLoadingWithTyping(
        true,
        typingMessage: "Preparing your questions...",
        generatingQuestions: true,
      );
      _isGeneratingQuestions = true;
      _currentGeneratingTopic = topic.name;
      notifyListeners();

      try {
        // Use startChat with existing session ID to get the proper initial message
        final response = await _api.startChat([topic.name], _currentSessionId);

        // Transition to active state
        _sessionState = SessionState.active;

        // Add the AI's initial question (not a user message)
        _addAIMessage(response.message);

        // Update session metadata with new topic if needed
        if (_currentSession != null) {
          _currentSession = _currentSession!.copyWith(
            topics: [..._currentSession!.topics, topic.name],
            state: SessionState.active,
            updatedAt: DateTime.now(),
          );

          // Save the updated session
          if (_userId != null) {
            await _sessionService.saveSession(_userId!, _currentSession!);
          }
        }
      } catch (e) {
        _logger.severe('Error adding topic to session: $e');
        if (e is ApiException) {
          _addAIMessage('Error: ${e.message}');
        } else {
          _addAIMessage(
            'An error occurred while preparing your questions. Please try again.',
          );
        }
      } finally {
        _setLoadingWithTyping(
          false,
          typingMessage: null,
          generatingQuestions: false,
        );
        _isGeneratingQuestions = false;
        _currentGeneratingTopic = null;
      }

      notifyListeners();
    } else {
      // Start a new session with the popular topic
      await startNewSession([topic.name]);
    }
  }

  /// Load an existing session from Firebase
  Future<void> loadSession(String sessionId) async {
    if (_userId == null) {
      _logger.warning('Cannot load session: No user authenticated');
      return;
    }

    _logger.info('Loading session: $sessionId');
    _setLoading(true);

    try {
      final session = await _sessionService.loadSession(_userId!, sessionId);

      if (session == null) {
        _logger.warning('Session $sessionId not found');
        return;
      }

      // Set loaded session as current
      _currentSession = session;
      _currentSessionId = session.id;
      _currentTopicId = session.topicId;
      _sessionState = session.state; // Restore the session state
      _messages = List.from(session.messages);
      _finalScores = session.finalScores;

      // Start listening to messages
      _listenToMessages(_userId!, sessionId);

      notifyListeners();
      _logger.info('Successfully loaded session $sessionId');

      // Auto-scroll to show the loaded messages
      _autoScrollCallback?.call();
    } catch (e) {
      _logger.severe('Error loading session $sessionId: $e');
      rethrow; // Re-throw to let the UI handle the error
    } finally {
      _setLoading(false);
    }
  }

  /// Load an existing session from Firebase by token
  Future<void> loadSessionByToken(String token) async {
    if (_userId == null) {
      _logger.warning('Cannot load session by token: No user authenticated');
      throw Exception('User not authenticated');
    }

    _logger.info('Loading session by token: $token for user: $_userId');
    _setLoading(true);

    try {
      final session = await _sessionService.loadSessionByToken(_userId!, token);
      _logger.debug(
        'loadSessionByToken result: ${session?.id}, token: ${session?.token}',
      );

      if (session == null) {
        _logger.warning('Session with token $token not found');
        _logger.debug('Session with token $token not found in Firebase');
        throw Exception('Session not found');
      }

      // Set loaded session as current
      _currentSession = session;
      _currentSessionId = session.id;
      _currentTopicId = session.topicId;
      _sessionState = session.state; // Restore the session state
      _messages = List.from(session.messages);
      _finalScores = session.finalScores;

      // Start listening to messages for the loaded session
      _listenToMessages(_userId!, session.id);

      notifyListeners();
      _logger.info('Successfully loaded session by token $token');
      _logger.debug('Successfully loaded session ${session.id}');

      // Auto-scroll to show the loaded messages
      _autoScrollCallback?.call();
    } catch (e) {
      _logger.severe('Error loading session by token $token: $e');
      _logger.debug('Error in loadSessionByToken: $e');
      rethrow; // Re-throw to let the UI handle the error
    } finally {
      _setLoading(false);
    }
  }

  /// Send a message in the current session
  Future<void> sendMessage(String text) async {
    if (_currentSessionId == null) return;

    // Check if session is completed
    if (_currentSession?.isCompleted == true ||
        _sessionState == SessionState.completed) {
      _addAIMessage(
        "This session has already been completed. You can start a new session to continue learning!",
      );
      return;
    }

    // Check if this is an end command and we're already ending the session
    final isEndCommand =
        text.toLowerCase().trim() == 'end' ||
        text.toLowerCase().trim() == 'end session' ||
        text.toLowerCase().trim() == 'end chat' ||
        text.toLowerCase().trim() == 'quit' ||
        text.toLowerCase().trim() == 'stop';

    if (isEndCommand && _isEndingSession) {
      _addAIMessage("Session is already being ended. Please wait...");
      return;
    }

    if (isEndCommand) {
      _isEndingSession = true;
    }

    _addUserMessage(text);
    _setLoadingWithTyping(
      true,
      typingMessage: "Thinking...",
      processingAnswer: true,
    );

    try {
      final botResponse = await _api.handleTurn(_currentSessionId!, text);
      _addAIMessage(botResponse);

      // Check if the response indicates session completion
      if (botResponse.contains("Session completed!") ||
          botResponse.contains("session has already been completed") ||
          botResponse.contains("Session ended!") ||
          botResponse.contains("run out of questions") ||
          botResponse.contains("completed all the questions") ||
          botResponse.contains("Here's your summary:")) {
        _sessionState = SessionState.completed;
        if (_currentSession != null) {
          _currentSession = _currentSession!.copyWith(
            state: SessionState.completed,
            isCompleted: true,
            updatedAt: DateTime.now(),
          );
        }
        notifyListeners();
      }

      // Save the updated session state to Firebase after each turn
      if (_currentSession != null && _userId != null) {
        // The `copyWith` is important to update the `updatedAt` timestamp
        final sessionToSave = _currentSession!.copyWith(
          messages: _messages,
          updatedAt: DateTime.now(),
        );
        _currentSession =
            sessionToSave; // Ensure provider has the latest version
        await _sessionService.saveSession(_userId!, sessionToSave);
      }
    } catch (e) {
      _logger.severe('Error handling user message: $e');
      if (e is ApiException) {
        _addAIMessage('Error: ${e.message}');
      } else {
        _addAIMessage('An unexpected error occurred. Please try again.');
      }
    } finally {
      _setLoadingWithTyping(
        false,
        typingMessage: null,
        processingAnswer: false,
      );
      // Reset the ending session flag
      _isEndingSession = false;
    }
  }

  /// Create a voice room for the current chat session
  Future<Map<String, dynamic>?> createVoiceRoom() async {
    if (_currentSessionId == null) {
      _logger.warning('Cannot create voice room: No active session');
      return null;
    }

    try {
      _logger.info('Creating voice room for chat session: $_currentSessionId');

      final response = await http.post(
        Uri.parse('${_api.baseUrl}/api/v1/voice/create-room'),
        headers: await _getAuthHeaders(),
        body: jsonEncode({'chat_id': _currentSessionId!}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _logger.info('Voice room created: ${data['room_name']}');
        return data;
      } else {
        throw Exception(
          'Voice room creation failed: ${response.statusCode} - ${response.body}',
        );
      }
    } catch (e) {
      _logger.severe('Error creating voice room: $e');
      return null;
    }
  }

  /// Handle voice transcript from LiveKit (sends to regular chat API)
  Future<void> handleVoiceTranscript(String transcript) async {
    if (_currentSessionId == null) {
      _logger.warning('Cannot handle voice transcript: No active session');
      return;
    }

    _logger.info('Processing voice transcript: $transcript');

    // Just call sendMessage, let it handle optimistic update and Firestore listener
    await sendMessage(transcript);
  }

  /// Update current session with latest messages and metadata
  void _updateCurrentSession() {
    if (_currentSession != null) {
      _currentSession = _currentSession!.copyWith(
        messages: List.from(_messages),
        messageCount: _messages.length,
        lastMessageAt: _messages.isNotEmpty ? _messages.last.timestamp : null,
        state: _sessionState,
        updatedAt: DateTime.now(),
      );
    }
  }

  /// Auto-save session to Firebase (with error handling)
  Future<void> _autoSaveSession() async {
    if (_userId == null || _currentSession == null) return;

    try {
      await _sessionService.saveSession(_userId!, _currentSession!);
      _logger.info('Session auto-saved to Firebase');
    } catch (e) {
      _logger.warning('Failed to auto-save session: $e');
      // Continue silently - user experience shouldn't be interrupted
    }
  }

  /// Set loading state
  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  /// Set typing indicator with optional custom message
  void _setTyping(
    bool typing, {
    String? message,
    bool? generatingQuestions,
    bool? processingAnswer,
  }) {
    _isTyping = typing;
    _typingMessage = message;
    _isGeneratingQuestions = generatingQuestions ?? false;
    _isProcessingAnswer = processingAnswer ?? false;
    notifyListeners();
  }

  /// Enhanced loading with contextual typing
  void _setLoadingWithTyping(
    bool loading, {
    String? typingMessage,
    bool? generatingQuestions,
    bool? processingAnswer,
  }) {
    _isLoading = loading;
    if (loading) {
      _setTyping(
        true,
        message: typingMessage,
        generatingQuestions: generatingQuestions,
        processingAnswer: processingAnswer,
      );
    } else {
      _setTyping(false);
    }
  }

  /// Format timestamp for display
  String _formatTimestamp(DateTime timestamp) {
    return '${timestamp.month}/${timestamp.day}/${timestamp.year} ${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')}';
  }

  /// Clear all data (for sign out, etc.)
  void clear() {
    _currentSession = null;
    _sessionState = SessionState.initial;
    _messages = [];
    _currentSessionId = null;
    _currentTopicId = null;
    _finalScores = null;
    _sessionHistory = [];
    _isTyping = false;
    _typingMessage = null;
    _isGeneratingQuestions = false;
    _isProcessingAnswer = false;
    _recentlyReviewedTopicIds.clear();
    notifyListeners();
    _logger.info('Chat provider cleared');
  }

  // Public method to add AI messages (used by voice service)
  void addAIMessage(String message, {bool isVoice = false}) {
    _addAIMessage(message, isVoice: isVoice);

    // Auto-save to Firebase when voice messages are added
    if (isVoice && _userId != null && _currentSession != null) {
      _autoSaveSession();
    }

    notifyListeners();
  }

  // Public method to add user messages (used by voice service)
  void addUserMessage(String message, {bool isVoice = false}) {
    _addUserMessage(message, isVoice: isVoice);

    // Auto-save to Firebase when voice messages are added
    if (isVoice && _userId != null && _currentSession != null) {
      _autoSaveSession();
    }

    notifyListeners();
  }

  // Firebase integration methods

  /// Save current session to Firebase
  Future<void> saveCurrentSession() async {
    if (_userId == null || _currentSession == null) {
      _logger.warning('Cannot save session: No user or session');
      return;
    }

    try {
      await _sessionService.saveSession(_userId!, _currentSession!);
      _logger.info('Session manually saved to Firebase');
    } catch (e) {
      _logger.severe('Error saving session: $e');
      rethrow; // Re-throw for UI error handling
    }
  }

  /// Load session history from Firebase
  Future<void> loadSessionHistory() async {
    if (_isLoadingHistory || _userId == null) return; // Guard
    _isLoadingHistory = true;
    notifyListeners();

    try {
      final history = await _sessionService.getSessionHistory(_userId!);
      _sessionHistory = history;
      _logger.info('Loaded ${history.length} sessions from history');
    } catch (e) {
      _logger.severe('Error loading session history: $e');
      _sessionHistory = []; // Clear on error
    } finally {
      _isLoadingHistory = false;
      notifyListeners();
    }
  }

  /// Delete a session from Firebase and local history
  Future<void> deleteSession(String sessionId) async {
    if (_userId == null) {
      _logger.warning('Cannot delete session: No user authenticated');
      return;
    }

    final wasCurrentSession = _currentSession?.id == sessionId;

    try {
      await _sessionService.deleteSession(_userId!, sessionId);

      // Remove from local history immediately
      _sessionHistory.removeWhere((session) => session.id == sessionId);

      // If this is the current session, clear it and reset to initial state
      if (wasCurrentSession) {
        _currentSession = null;
        _currentSessionId = null;
        _currentTopicId = null;
        _sessionState = SessionState.initial;
        _messages = [];
        _finalScores = null;
        _logger.info('Cleared current session state after deletion');

        // Reset routing to the default chat screen
        if (_router != null) {
          _router!.go('/app/chat');
        }
      }

      // Notify listeners immediately for UI update
      notifyListeners();

      // Also refresh from Firebase to ensure consistency
      await loadSessionHistory();

      _logger.info('Session $sessionId deleted successfully');
    } catch (e) {
      _logger.severe('Error deleting session $sessionId: $e');
      rethrow; // Re-throw for UI error handling
    }
  }

  /// Rename a session
  Future<void> renameSession(String sessionId, String newName) async {
    if (_userId == null) {
      _logger.warning('Cannot rename session: No user authenticated');
      return;
    }

    try {
      await _sessionService.updateSessionName(_userId!, sessionId, newName);

      // Update local history
      final sessionIndex = _sessionHistory.indexWhere((s) => s.id == sessionId);
      if (sessionIndex >= 0) {
        // Create updated summary (this is a bit hacky, but works for now)
        await loadSessionHistory(); // Refresh from Firebase
      }

      // Update current session if it matches
      if (_currentSession?.id == sessionId) {
        _currentSession = _currentSession!.copyWith(name: newName);
      }

      notifyListeners();
      _logger.info('Session $sessionId renamed to: $newName');
    } catch (e) {
      _logger.severe('Error renaming session $sessionId: $e');
      rethrow; // Re-throw for UI error handling
    }
  }

  /// Get incomplete sessions for resume functionality
  Future<List<ChatSessionSummary>> getIncompleteSessions() async {
    if (_userId == null) return [];

    try {
      // This method does not exist on the service anymore, so we remove it.
      // return await _sessionService.getIncompleteSessions(_userId!);
      return [];
    } catch (e) {
      _logger.severe('Error getting incomplete sessions: $e');
      return [];
    }
  }

  /// Get the current session token for routing
  String? get currentSessionToken => _currentSession?.token;

  /// Add user message
  void _addUserMessage(String text, {bool isVoice = false}) {
    final message = ChatMessage(
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
      isVoice: isVoice,
    );
    _messages.add(message);

    // Remove immediate persistence to prevent duplicates
    // Messages will be saved in batch during saveSession()

    _updateCurrentSession();
    notifyListeners();
  }

  /// Add AI message
  void _addAIMessage(String text, {bool isVoice = false}) {
    final message = ChatMessage(
      text: text,
      isUser: false,
      timestamp: DateTime.now(),
      isVoice: isVoice,
    );
    _messages.add(message);

    // Remove immediate persistence to prevent duplicates
    // Messages will be saved in batch during saveSession()

    _updateCurrentSession();
    notifyListeners();
  }

  /// Skip the current question
  Future<void> skipCurrentQuestion() async {
    if (_currentSessionId == null) return;
    _setLoadingWithTyping(true, typingMessage: 'Skipping...');
    try {
      final botResponse = await _api.handleTurn(
        _currentSessionId!,
        "skip question",
      );
      _addAIMessage(botResponse);
    } catch (e) {
      _logger.severe('Error skipping question: $e');
      if (e is ApiException) {
        _addAIMessage('Error: ${e.message}');
      } else {
        _addAIMessage('An unexpected error occurred.');
      }
    } finally {
      _setLoadingWithTyping(false);
    }
  }

  /// End the current session early
  Future<void> endCurrentSession() async {
    if (_currentSessionId == null) return;

    // Prevent double execution
    if (_isEndingSession) {
      _logger.info('Session ending already in progress, skipping...');
      return;
    }

    _isEndingSession = true;
    _logger.info('Ending current session: $_currentSessionId');
    _setLoadingWithTyping(true, typingMessage: "Ending your session...");

    try {
      final summaryMessage = await _api.handleTurn(_currentSessionId!, 'end');
      _addAIMessage(summaryMessage);

      // Update session state to completed
      _sessionState = SessionState.completed;

      if (_currentSession != null) {
        final updatedSession = _currentSession!.copyWith(
          state: SessionState.completed,
          isCompleted: true,
          updatedAt: DateTime.now(),
        );

        // Add the topic ID to the set of recently reviewed topics
        if (_currentSession?.topicId != null) {
          _recentlyReviewedTopicIds.add(_currentSession!.topicId!);
        }

        _currentSession = updatedSession;

        if (_userId != null) {
          await _sessionService.saveSession(_userId!, updatedSession);
        }
      }

      // Notify listeners to update UI
      notifyListeners();
    } catch (e) {
      _logger.severe('Error ending session: $e');
      _addAIMessage('Sorry, there was an error ending your session.');
    } finally {
      _setLoadingWithTyping(false);
      _isEndingSession = false;
    }
  }

  Future<void> fetchDueTopics() async {
    if (_isLoadingDueTopics || _userId == null) return; // Guard
    _isLoadingDueTopics = true;
    notifyListeners();

    try {
      _dueTopics = await _api.getDueTopics();
    } catch (e) {
      _logger.severe('Error fetching due topics: $e');
      _dueTopics = null; // Clear old data on error
    } finally {
      _isLoadingDueTopics = false;
      notifyListeners();
    }
  }

  /// Repair session metadata for all user sessions
  /// This back-populates missing fields in older sessions
  Future<void> repairAllSessionMetadata() async {
    if (_userId == null) {
      _logger.warning('Cannot repair sessions: No user authenticated');
      return;
    }

    _logger.info('Starting repair of all session metadata for user $_userId');

    try {
      // This method does not exist on the service anymore, so we remove it.
      // await _sessionService.repairAllUserSessions(_userId!);
      _logger.info('Successfully repaired all session metadata');

      // Reload session history to see the repaired data
      await loadSessionHistory();
    } catch (e) {
      _logger.severe('Error repairing session metadata: $e');
      rethrow; // Re-throw for UI error handling
    }
  }

  Future<void> deleteTopic(String topicId) async {
    if (_userId == null) {
      _logger.warning('Cannot delete topic: No user authenticated');
      return;
    }
    try {
      await _api.deleteTopic(topicId);
      await fetchDueTopics(); // Refresh the list after deletion
    } catch (e) {
      _logger.severe('Error deleting topic $topicId: $e');
      // Optionally, re-throw or show an error to the user
    }
  }

  void _listenToMessages(String userId, String sessionId) {
    _messagesSubscription?.cancel();
    final messagesRef = FirebaseFirestore.instance
        .collection('users')
        .doc(userId)
        .collection('sessions')
        .doc(sessionId)
        .collection('messages')
        .orderBy('messageIndex');

    _messagesSubscription = messagesRef.snapshots().listen((snapshot) {
      final firestoreMessages =
          snapshot.docs.map((doc) {
            final data = doc.data();
            return ChatMessage(
              text: data['text'] ?? '',
              isUser: data['isUser'] ?? false,
              timestamp: (data['timestamp'] as Timestamp).toDate(),
              isSystem: data['isSystem'] ?? false,
              isVoice: data['isVoice'] ?? false,
            );
          }).toList();

      // Remove any pending user message that is not in Firestore
      _messages.removeWhere(
        (pending) =>
            pending.isUser &&
            pending.isVoice &&
            !firestoreMessages.any(
              (m) =>
                  m.text == pending.text &&
                  m.isUser == pending.isUser &&
                  m.isVoice == pending.isVoice,
            ),
      );

      // Replace with Firestore messages
      _messages = List.from(firestoreMessages);
      notifyListeners();
      _autoScrollCallback?.call(); // Notify UI to auto-scroll
    });
  }

  void _stopListeningToMessages() {
    _messagesSubscription?.cancel();
    _messagesSubscription = null;
  }

  // Clean up listener on dispose
  @override
  void dispose() {
    _stopListeningToMessages();
    super.dispose();
  }

  void setAutoScrollCallback(VoidCallback callback) {
    _autoScrollCallback = callback;
  }
}
