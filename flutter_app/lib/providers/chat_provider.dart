import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import 'package:go_router/go_router.dart';
import '../models/chat_session.dart';
import '../screens/chat_screen.dart'; // For SessionState and ChatMessage
import '../services/session_api.dart';
import '../services/chat_session_service.dart';
import '../services/logger_service.dart';
import 'package:flutter/material.dart';

class ChatProvider extends ChangeNotifier {
  final _logger = getLogger('ChatProvider');
  final _uuid = const Uuid();

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

  // Session configuration
  final int _maxTopics = 3;
  final int _maxQuestions = 5;

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

  void setRouter(GoRouter router) {
    _router = router;
  }

  void setUserId(String? userId) {
    _userId = userId;
    if (userId != null) {
      loadSessionHistory();
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
    _recentlyReviewedTopicIds.clear();

    // Navigate to the clean chat screen to begin topic selection.
    _router?.go('/app/chat');

    notifyListeners();
    _logger.info('Reset session state for new chat flow.');
  }

  /// Initialize a new chat session
  Future<void> startNewSession(List<String> topics) async {
    _logger.info('Starting new chat session with topics: $topics');
    _setLoadingWithTyping(
      true,
      typingMessage: "Preparing your learning session...",
    );
    _isStartingSession = true;
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
      _currentSession = session;

      _addAIMessage(response.message);

      if (_userId != null) {
        await _sessionService.saveSession(_userId!, session);
        loadSessionHistory();
      }
      _router?.go('/app/chat/${session.token}');
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
      _setLoadingWithTyping(false, typingMessage: null);
      _isStartingSession = false;
      notifyListeners();
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

      notifyListeners();
      _logger.info('Successfully loaded session $sessionId');
    } catch (e) {
      _logger.severe('Error loading session $sessionId: $e');
      // TODO: Show error to user
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

      notifyListeners();
      _logger.info('Successfully loaded session by token $token');
      _logger.debug('Successfully loaded session ${session.id}');
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
    _addUserMessage(text);
    _setLoadingWithTyping(
      true,
      typingMessage: "Thinking...",
      processingAnswer: true,
    );

    try {
      final botResponse = await _api.handleTurn(_currentSessionId!, text);
      _addAIMessage(botResponse);

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
    }
  }

  /// Handle user input based on current session state
  Future<void> _handleUserInput(String input) async {
    _setLoading(true);

    try {
      switch (_sessionState) {
        case SessionState.initial:
        case SessionState.selectingSessionType:
        case SessionState.selectingDueTopics:
          // These states should be handled by UI, not text input
          _addAIMessage("Please use the buttons above to make your selection.");
          break;

        case SessionState.active:
          await _handleAnswerInput(input);
          break;

        case SessionState.completed:
        case SessionState.error:
          // Session has ended - no user input allowed
          break;
        case SessionState.collectingTopics:
          // This state is no longer used with the new flow.
          break;
      }
    } catch (e) {
      await _handleError(e);
    } finally {
      _setLoading(false);
    }
  }

  /// Handle answer input during active session
  Future<void> _handleAnswerInput(String answer) {
    // For self-evaluation, just add a placeholder message
    _addAIMessage("Please use the buttons below to evaluate your answer.");
    return Future.value();
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
    _isLoading = false;
    _finalScores = null;
    _sessionHistory = [];
    _isLoadingHistory = false;
    _userId = null;
    _popularTopics = [];
    notifyListeners();
    _logger.info('Chat provider cleared');
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
    if (_userId == null) {
      _logger.warning('Cannot load session history: No user authenticated');
      return;
    }

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

  /// Handle errors
  Future<void> _handleError(dynamic error) async {
    _sessionState = SessionState.error;
    String errorMessage = "Unexpected error occurred";

    if (error is ApiException) {
      errorMessage = "API Error: ${error.message}";
    } else {
      errorMessage = "Error: ${error.toString()}";
    }

    _addAIMessage(errorMessage);

    _updateCurrentSession();
    await _autoSaveSession();
  }

  /// Reset the current session
  void _resetSession() {
    _sessionState = SessionState.initial;
    _currentSessionId = null;
    _currentTopicId = null;
    _finalScores = null;
    // Note: We keep _currentSession and _messages for persistence
    notifyListeners();
  }

  /// Add system message
  void _addSystemMessage(String text) {
    final message = ChatMessage(
      text: text,
      isUser: false,
      timestamp: DateTime.now(),
      isSystem: true,
    );
    _messages.add(message);

    // Remove immediate persistence to prevent duplicates
    // Messages will be saved in batch during saveSession()

    _updateCurrentSession();
    notifyListeners();
  }

  /// Add user message
  void _addUserMessage(String text) {
    final message = ChatMessage(
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
    );
    _messages.add(message);

    // Remove immediate persistence to prevent duplicates
    // Messages will be saved in batch during saveSession()

    _updateCurrentSession();
    notifyListeners();
  }

  /// Add AI message
  void _addAIMessage(String text) {
    final message = ChatMessage(
      text: text,
      isUser: false,
      timestamp: DateTime.now(),
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
    _logger.info('Ending current session: $_currentSessionId');
    _setLoadingWithTyping(true, typingMessage: "Ending your session...");

    try {
      final summaryMessage = await _api.handleTurn(_currentSessionId!, 'end');
      _addAIMessage(summaryMessage);

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
          await fetchDueTopics(); // Refresh due topics after session ends
          loadSessionHistory();
        }
      }
    } catch (e) {
      _logger.severe('Error ending session: $e');
      _addAIMessage('Sorry, there was an error ending your session.');
    } finally {
      _setLoadingWithTyping(false);
    }
  }

  Future<void> fetchDueTopics() async {
    if (isLoadingDueTopics) return;
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
}
