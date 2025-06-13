import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import 'package:go_router/go_router.dart';
import '../models/chat_session.dart';
import '../screens/chat_screen.dart'; // For SessionState and ChatMessage
import '../services/langgraph_api.dart';
import '../services/chat_session_service.dart';
import '../services/logger_service.dart';

class ChatProvider extends ChangeNotifier {
  final _logger = getLogger('ChatProvider');
  final _uuid = const Uuid();

  // Current session state
  ChatSession? _currentSession;
  SessionState _sessionState = SessionState.initial;
  List<ChatMessage> _messages = [];
  String? _currentSessionId;
  bool _isLoading = false;
  Map<String, int>? _finalScores;

  // Session history
  List<ChatSessionSummary> _sessionHistory = [];
  bool _isLoadingHistory = false;

  // Services
  late final LangGraphApi _api;
  late final ChatSessionService _sessionService;

  // Session configuration
  final int _maxTopics = 3;
  final int _maxQuestions = 7;

  // User ID for Firebase operations
  String? _userId;

  // Navigation context for URL updates
  GoRouter? _router;

  ChatProvider() {
    // Use environment-based backend URL
    const String? backendUrl = String.fromEnvironment(
      'BACKEND_URL',
      defaultValue: 'https://spaced-staging.onrender.com',
    );

    _api = LangGraphApi(baseUrl: backendUrl);
    _sessionService = ChatSessionService();
  }

  // Getters
  ChatSession? get currentSession => _currentSession;
  SessionState get sessionState => _sessionState;
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  String? get currentSessionId => _currentSessionId;
  bool get isLoading => _isLoading;
  Map<String, int>? get finalScores => _finalScores;
  List<ChatSessionSummary> get sessionHistory =>
      List.unmodifiable(_sessionHistory);
  bool get hasActiveSession => _currentSession != null;
  bool get isLoadingHistory => _isLoadingHistory;
  String? get userId => _userId;

  /// Set the router for navigation
  void setRouter(GoRouter router) {
    _router = router;
  }

  /// Set the current user ID for Firebase operations
  void setUserId(String? userId) {
    if (_userId != userId) {
      _userId = userId;
      if (userId != null) {
        // Load session history when user is set
        loadSessionHistory();
      } else {
        // Clear data when user is signed out
        clear();
      }
    }
  }

  /// Set the session state manually (for UI state management)
  void setSessionState(SessionState newState) {
    if (_sessionState != newState) {
      _sessionState = newState;
      notifyListeners();
    }
  }

  /// Initialize a new chat session
  Future<void> startNewSession({
    List<String>? initialTopics,
    String? sessionType,
    List<String>? selectedTopics,
  }) async {
    _logger.info('Starting new chat session with type: $sessionType');

    final sessionId = _uuid.v4();
    final now = DateTime.now();

    // Generate unique token if user is authenticated
    String? token;
    if (_userId != null) {
      try {
        token = await _sessionService.generateUniqueToken(_userId!);
      } catch (e) {
        _logger.warning('Failed to generate unique token: $e');
        // Fall back to default token generation
        token = ChatSession.generateSessionToken();
      }
    } else {
      // Generate default token when no user
      token = ChatSession.generateSessionToken();
    }

    // Determine topics based on session type
    List<String> topics = [];
    if (sessionType == 'due_items' && selectedTopics != null) {
      topics = selectedTopics;
    } else if (initialTopics != null) {
      topics = initialTopics;
    }

    // Create new session
    _currentSession = ChatSession.create(
      id: sessionId,
      topics: topics,
      name: 'New Session - ${_formatTimestamp(now)}',
      token: token,
    );

    _currentSessionId = sessionId;
    _sessionState = SessionState.initial;
    _messages = [];
    _isLoading = false;
    _finalScores = null;

    // Add appropriate welcome message based on session type
    if (sessionType == 'due_items') {
      _addSystemMessage(
        "Great! Let's review your selected topics using spaced repetition. 🧠✨\n\n"
        "I'll ask you questions about: ${topics.join(', ')}\n\n"
        "This will help reinforce your memory and identify areas that need more attention.",
      );
      _sessionState = SessionState.active;

      // Start the backend session immediately for due items
      await _startBackendSession(sessionType, topics);
    } else if (sessionType == 'custom_topics') {
      _addSystemMessage(
        "Welcome to your personalized spaced repetition learning session! 🧠✨\n\n"
        "I'll help you learn and retain information using scientifically-proven spaced repetition techniques.\n\n"
        "To get started, please tell me what topics you'd like to study today. "
        "You can list multiple topics separated by commas.\n\n"
        "For example: 'Flutter widgets, Dart programming, Mobile development'",
      );
      _sessionState = SessionState.collectingTopics;
    } else {
      // Default behavior
      _addSystemMessage(
        "Welcome to your personalized spaced repetition learning session! 🧠✨\n\n"
        "I'll help you learn and retain information using scientifically-proven spaced repetition techniques.\n\n"
        "To get started, please tell me what topics you'd like to study today. "
        "You can list multiple topics separated by commas.\n\n"
        "For example: 'Flutter widgets, Dart programming, Mobile development'",
      );
      _sessionState = SessionState.collectingTopics;
    }

    _updateCurrentSession();
    notifyListeners();

    // Save session to Firebase if user is authenticated
    if (_userId != null) {
      try {
        await _sessionService.saveSession(_userId!, _currentSession!);
        _logger.info('New session saved to Firebase');

        // Refresh session history to show the new session immediately
        await loadSessionHistory();

        // Navigate to token URL for due items sessions
        if (sessionType == 'due_items' && _router != null) {
          _router!.go('/app/chat/${token}');
        }
      } catch (e) {
        _logger.warning('Failed to save new session to Firebase: $e');
        // Continue without Firebase - session will be saved later
      }
    }

    _logger.info('New chat session started with ID: $sessionId, token: $token');
  }

  /// Start the backend session
  Future<void> _startBackendSession(
    String? sessionType,
    List<String> topics,
  ) async {
    try {
      final response = await _api.startSession(
        topics: topics,
        maxTopics: _maxTopics,
        maxQuestions: _maxQuestions,
        sessionType: sessionType ?? 'custom_topics',
      );

      _logger.info('Backend session started successfully');

      // Add the initial AI message
      final initialMessage = response.nextQuestion;
      if (initialMessage.isNotEmpty) {
        _addSystemMessage(initialMessage);
      }
    } catch (e) {
      _logger.severe('Error starting backend session: $e');
      _addSystemMessage(
        'Sorry, there was an error starting your session. Please try again.',
      );
      _sessionState = SessionState.error;
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
      _sessionState = session.state;
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

    _logger.info('Loading session by token: $token');
    _setLoading(true);

    try {
      final session = await _sessionService.loadSessionByToken(_userId!, token);

      if (session == null) {
        _logger.warning('Session with token $token not found');
        throw Exception('Session not found');
      }

      // Set loaded session as current
      _currentSession = session;
      _currentSessionId = session.id;
      _sessionState = session.state;
      _messages = List.from(session.messages);
      _finalScores = session.finalScores;

      notifyListeners();
      _logger.info('Successfully loaded session by token $token');
    } catch (e) {
      _logger.severe('Error loading session by token $token: $e');
      rethrow; // Re-throw to let the UI handle the error
    } finally {
      _setLoading(false);
    }
  }

  /// Send a message in the current session
  Future<void> sendMessage(String message) async {
    if (_currentSession == null) {
      _logger.warning('Cannot send message: No active session');
      return;
    }

    _addUserMessage(message);
    await _handleUserInput(message);
  }

  /// Handle user input based on current session state
  Future<void> _handleUserInput(String userInput) async {
    _setLoading(true);

    try {
      switch (_sessionState) {
        case SessionState.initial:
        case SessionState.selectingSessionType:
        case SessionState.selectingDueTopics:
          // These states are handled by UI, not user input
          break;
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
      _setLoading(false);
    }
  }

  /// Handle topics input during session setup
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

      // Update session with actual topics
      _currentSession = _currentSession!.copyWith(
        topics: topics,
        state: SessionState.active,
        updatedAt: DateTime.now(),
      );

      await Future.delayed(
        const Duration(milliseconds: 500),
      ); // Brief pause for UX

      _addAIMessage(
        "📚 **Session Started!**\n\n"
        "I'll ask you up to $_maxQuestions questions per topic to assess your knowledge. "
        "Answer as best as you can - this helps me understand what you know and what needs more practice.\n\n"
        "**Question 1:**\n${response.nextQuestion}",
      );

      // Now navigate to the token URL after session is active
      if (_router != null && _currentSession != null) {
        _router!.go('/app/chat/${_currentSession!.token}');
      }
    } on LangGraphApiException catch (e) {
      _sessionState = SessionState.error;
      _addAIMessage(
        "Sorry, I encountered an error starting your session: ${e.message}\n\n"
        "Would you like to try again with different topics?",
      );
    }

    _updateCurrentSession();
    await _autoSaveSession();
  }

  /// Handle answer input during active session
  Future<void> _handleAnswerInput(String answer) async {
    if (_currentSessionId == null) {
      _addAIMessage("Session error: No active session ID. Let's start over.");
      _resetSession();
      return;
    }

    // Handle "continue" command for expired sessions
    final lowerAnswer = answer.toLowerCase().trim();
    if (lowerAnswer == 'continue' || lowerAnswer == 'new question') {
      await _handleExpiredSession(answer);
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

        _currentSession = _currentSession!.copyWith(
          state: SessionState.completed,
          isCompleted: true,
          finalScores: response.scores,
          updatedAt: DateTime.now(),
        );

        _addAIMessage(_buildCompletionMessage(response.scores!));
      } else {
        // Continue with next question
        _addAIMessage("**Next Question:**\n${response.nextQuestion!}");
      }
    } on LangGraphApiException catch (e) {
      if (e.statusCode == 404) {
        // Backend session expired - handle gracefully
        await _handleExpiredSession(answer);
      } else {
        _sessionState = SessionState.error;
        _addAIMessage(
          "I encountered an error: ${e.message}\n\n"
          "Would you like to try answering again, or start a new session?",
        );
      }
    }

    _updateCurrentSession();
    await _autoSaveSession();
  }

  /// Handle expired backend sessions gracefully
  Future<void> _handleExpiredSession(String answer) async {
    _logger.info('Backend session expired, attempting to continue gracefully');

    try {
      // If we have topics from the current session, restart the backend session
      if (_currentSession != null && _currentSession!.topics.isNotEmpty) {
        // Restart the backend session with existing topics
        final response = await _api.startSession(
          topics: _currentSession!.topics,
          maxTopics: _maxTopics,
          maxQuestions: _maxQuestions,
        );

        _currentSessionId = response.sessionId;

        // Try to process the user's answer directly instead of starting from the beginning
        try {
          final continueResponse = await _api.answer(
            sessionId: _currentSessionId!,
            userInput: answer,
          );

          if (continueResponse.isDone) {
            // Session completed
            _sessionState = SessionState.completed;
            _finalScores = continueResponse.scores;

            _currentSession = _currentSession!.copyWith(
              state: SessionState.completed,
              isCompleted: true,
              finalScores: continueResponse.scores,
              updatedAt: DateTime.now(),
            );

            _addAIMessage(_buildCompletionMessage(continueResponse.scores!));
          } else {
            // Continue with next question
            _addAIMessage(
              "**Next Question:**\n${continueResponse.nextQuestion!}",
            );
          }
        } catch (e) {
          // If answer processing fails, show the first question from the restarted session
          _logger.warning(
            'Failed to process answer after restart, showing first question: $e',
          );
          _addAIMessage("**Question:**\n${response.nextQuestion}");
        }
      } else {
        // No topics available, ask user to restart
        _addAIMessage("Please tell me what topics you'd like to study.");
        _sessionState = SessionState.collectingTopics;
        _currentSessionId = null;
      }
    } catch (e) {
      // If restart fails, gracefully degrade
      _logger.warning('Failed to restart expired session: $e');
      _addAIMessage("Please tell me what topics you'd like to study today.");
      _sessionState = SessionState.collectingTopics;
      _currentSessionId = null;
    }
  }

  /// Handle input when session is completed
  Future<void> _handleCompletedState(String input) async {
    final lowerInput = input.toLowerCase();

    if (lowerInput.contains('new') ||
        lowerInput.contains('again') ||
        lowerInput.contains('restart')) {
      _addAIMessage(
        "Starting a new session! What topics would you like to study this time?",
      );
      await startNewSession();
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

  /// Handle input when session is in error state
  Future<void> _handleErrorState(String input) async {
    final lowerInput = input.toLowerCase();

    if (lowerInput.contains('try') ||
        lowerInput.contains('again') ||
        lowerInput.contains('restart')) {
      _addAIMessage("Let's start fresh! What topics would you like to study?");
      await startNewSession();
    } else {
      _addAIMessage(
        "I'm still having issues. Would you like to **try again** or **restart** with new topics?",
      );
    }
  }

  /// Handle errors
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

    _updateCurrentSession();
    await _autoSaveSession();
  }

  /// Reset the current session
  void _resetSession() {
    _sessionState = SessionState.initial;
    _currentSessionId = null;
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
    _updateCurrentSession();
    notifyListeners();
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

  /// Build completion message
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
    _isLoading = false;
    _finalScores = null;
    _sessionHistory = [];
    _isLoadingHistory = false;
    _userId = null;
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

    try {
      await _sessionService.deleteSession(_userId!, sessionId);

      // Remove from local history immediately
      _sessionHistory.removeWhere((session) => session.id == sessionId);

      // If this is the current session, clear it
      if (_currentSession?.id == sessionId) {
        _currentSession = null;
        _currentSessionId = null;
        _sessionState = SessionState.initial;
        _messages = [];
        _finalScores = null;
      }

      // Notify listeners immediately for UI update
      notifyListeners();

      // Also refresh from Firebase to ensure consistency
      await loadSessionHistory();

      _logger.info('Session $sessionId deleted');
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
      return await _sessionService.getIncompleteSessions(_userId!);
    } catch (e) {
      _logger.severe('Error getting incomplete sessions: $e');
      return [];
    }
  }

  /// Auto-naming placeholder (will be implemented in Phase 5)
  Future<void> autoNameSession() async {
    // TODO: Implement in Phase 5 with AI naming
    _logger.info('Auto-naming will be implemented in Phase 5');
  }

  /// Get the current session token for routing
  String? get currentSessionToken => _currentSession?.token;
}
