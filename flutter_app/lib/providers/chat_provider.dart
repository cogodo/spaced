import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import 'package:go_router/go_router.dart';
import '../models/chat_session.dart';
import '../screens/chat_screen.dart'; // For SessionState and ChatMessage
import '../services/session_api.dart';
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
  late final SessionApi _api;
  late final ChatSessionService _sessionService;

  // Session configuration
  final int _maxTopics = 3;
  final int _maxQuestions = 7;

  // User ID for Firebase operations
  String? _userId;

  // Navigation context for URL updates
  GoRouter? _router;

  // Popular topics support
  List<PopularTopic> _popularTopics = [];
  bool _isLoadingPopularTopics = false;

  // Enhanced loading and typing states
  bool _isTyping = false;
  String? _typingMessage;
  bool _isGeneratingQuestions = false;
  bool _isProcessingAnswer = false;
  bool _isStartingSession =
      false; // Add flag to prevent multiple simultaneous sessions

  ChatProvider() {
    // Use environment-based backend URL with local development support
    String backendUrl;

    // Force localhost for local development (more explicit)
    backendUrl = const String.fromEnvironment(
      'BACKEND_URL',
      defaultValue:
          'http://localhost:8000', // Default to localhost for development
    );

    // Log the backend URL for debugging
    _logger.info('ChatProvider initialized with backend URL: $backendUrl');

    _api = SessionApi(baseUrl: backendUrl);
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
  List<PopularTopic> get popularTopics => List.unmodifiable(_popularTopics);
  bool get isLoadingPopularTopics => _isLoadingPopularTopics;

  // Enhanced loading state getters
  bool get isTyping => _isTyping;
  String? get typingMessage => _typingMessage;
  bool get isGeneratingQuestions => _isGeneratingQuestions;
  bool get isProcessingAnswer => _isProcessingAnswer;
  bool get isStartingSession => _isStartingSession;

  /// Set the router for navigation
  void setRouter(GoRouter router) {
    _router = router;
  }

  /// Set the current user ID for Firebase operations
  void setUserId(String? userId) {
    if (_userId != userId) {
      _userId = userId;
      if (userId != null) {
        // Load session history and popular topics when user is set
        loadSessionHistory();
        loadPopularTopics();
      } else {
        // Clear data when user is signed out
        clear();
      }
    }
  }

  /// Load popular topics for quick-pick menu
  Future<void> loadPopularTopics() async {
    if (_isLoadingPopularTopics) return;

    _isLoadingPopularTopics = true;
    notifyListeners();

    try {
      _popularTopics = await _api.getPopularTopics();
      _logger.info('Loaded ${_popularTopics.length} popular topics');
    } catch (e) {
      _logger.warning('Failed to load popular topics: $e');
      // Use fallback popular topics
      _popularTopics = [
        PopularTopic(
          name: 'Python Programming',
          description: 'Learn Python fundamentals',
        ),
        PopularTopic(
          name: 'Machine Learning',
          description: 'ML algorithms and models',
        ),
        PopularTopic(
          name: 'Web Development',
          description: 'Frontend and backend technologies',
        ),
        PopularTopic(
          name: 'Data Science',
          description: 'Data analysis and visualization',
        ),
        PopularTopic(
          name: 'Mobile Development',
          description: 'iOS, Android development',
        ),
        PopularTopic(name: 'Cloud Computing', description: 'AWS, Azure, GCP'),
      ];
    } finally {
      _isLoadingPopularTopics = false;
      notifyListeners();
    }
  }

  /// Validate topics and get suggestions
  Future<TopicValidationResponse?> validateTopics(List<String> topics) async {
    try {
      return await _api.validateTopics(topics);
    } catch (e) {
      _logger.warning('Failed to validate topics: $e');
      return null;
    }
  }

  /// Search user's existing topics
  Future<List<UserTopic>> searchTopics(String query) async {
    if (query.trim().isEmpty) return [];

    try {
      return await _api.searchTopics(query);
    } catch (e) {
      _logger.warning('Failed to search topics: $e');
      return [];
    }
  }

  /// Set the session state manually (for UI state management)
  void setSessionState(SessionState newState) {
    if (_sessionState != newState) {
      _sessionState = newState;
      notifyListeners();
    }
  }

  /// Reset to initial state for new session selection
  void resetToInitialState() {
    _currentSession = null;
    _sessionState = SessionState.initial;
    _messages = [];
    _currentSessionId = null;
    _isLoading = false;
    _finalScores = null;
    notifyListeners();
    _logger.info(
      'Chat provider reset to initial state for new session selection',
    );
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
    } else {
      // Default behavior - show topic selection (no intro message)
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
          _router!.go('/app/chat/$token');
        }
      } catch (e) {
        _logger.warning('Failed to save new session to Firebase: $e');
        // Continue without Firebase - session will be saved later
      }
    }

    _logger.info('New chat session started with ID: $sessionId, token: $token');
  }

  /// Start a session with popular topic
  Future<void> startSessionWithPopularTopic(PopularTopic topic) async {
    // Prevent multiple simultaneous session starts
    if (_isStartingSession) {
      _logger.warning('Session start already in progress, ignoring request');
      return;
    }

    _isStartingSession = true;
    _logger.info('Starting session with popular topic: ${topic.name}');

    // Set loading state immediately for UI feedback
    _sessionState = SessionState.active;
    _messages = [];
    _isLoading = false;
    _finalScores = null;

    // Notify listeners for immediate loading state
    notifyListeners();

    // Start the backend session first to get the proper session ID
    _setLoadingWithTyping(
      true,
      typingMessage: "Starting your learning session...",
      generatingQuestions: true,
    );

    try {
      final response = await _api.startSession(
        topics: [topic.name],
        maxTopics: _maxTopics,
        maxQuestions: _maxQuestions,
        sessionType: 'custom_topics',
      );

      // Now create the session with the backend session ID
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

      // Create session with backend session ID and actual topics from response
      _currentSession = ChatSession.create(
        id: response.sessionId, // Use backend session ID
        topics: response.topics.isNotEmpty ? response.topics : [topic.name],
        name: 'New Session - ${_formatTimestamp(now)}',
        token: token,
      );

      _currentSessionId = response.sessionId; // Consistent with session
      _sessionState = SessionState.active;

      // Show the response message which includes the first question
      _addAIMessage(response.message);

      _logger.info('Backend session started successfully');

      _updateCurrentSession();

      // Save session to Firebase if user is authenticated
      if (_userId != null) {
        try {
          await _sessionService.saveSession(_userId!, _currentSession!);
          _logger.info('New session saved to Firebase');

          // Refresh session history to show the new session immediately
          await loadSessionHistory();
        } catch (e) {
          _logger.warning('Failed to save new session to Firebase: $e');
          // Continue without Firebase - session will be saved later
        }
      }

      // Navigate to token URL after session is properly set up
      if (_router != null && _currentSession != null) {
        _router!.go('/app/chat/${_currentSession!.token}');
      }
    } catch (e) {
      _logger.severe('Error starting session with popular topic: $e');
      _sessionState = SessionState.error;

      if (e is SessionApiException) {
        _addAIMessage('Error starting session: ${e.message}');
      } else {
        _addAIMessage('Error starting session: ${e.toString()}');
      }
    } finally {
      _setLoadingWithTyping(false);
      _isStartingSession = false; // Always reset the flag
    }

    _updateCurrentSession();
    await _autoSaveSession();
  }

  /// Start the backend session
  Future<void> _startBackendSession(
    String? sessionType,
    List<String> topics,
  ) async {
    _setLoadingWithTyping(
      true,
      typingMessage: "Starting your learning session...",
      generatingQuestions: true,
    );

    try {
      final response = await _api.startSession(
        topics: topics,
        maxTopics: _maxTopics,
        maxQuestions: _maxQuestions,
        sessionType: sessionType ?? 'custom_topics',
      );

      _currentSessionId = response.sessionId;
      _sessionState = SessionState.active;

      // Update session with actual topics
      _currentSession = _currentSession!.copyWith(
        topics: response.topics,
        state: SessionState.active,
        updatedAt: DateTime.now(),
      );

      // Show the response message which includes the first question
      _addAIMessage(response.message);

      _logger.info('Backend session started successfully');

      // Navigate to token URL after session is active
      if (_router != null && _currentSession != null) {
        _router!.go('/app/chat/${_currentSession!.token}');
      }
    } catch (e) {
      _logger.severe('Error starting backend session: $e');
      _sessionState = SessionState.error;

      if (e is SessionApiException) {
        _addAIMessage('Error starting session: ${e.message}');
      } else {
        _addAIMessage('Error starting session: ${e.toString()}');
      }
    } finally {
      _setLoadingWithTyping(false);
    }

    _updateCurrentSession();
    await _autoSaveSession();
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

        case SessionState.collectingTopics:
          await _handleTopicsInputFromString(input);
          break;

        case SessionState.active:
          await _handleAnswerInput(input);
          break;

        case SessionState.completed:
        case SessionState.error:
          // Session has ended - no user input allowed
          break;
      }
    } catch (e) {
      await _handleError(e);
    } finally {
      _setLoading(false);
    }
  }

  /// Handle topics input with a list of topics (public method for UI)
  Future<void> handleTopicsInput(List<String> topics) async {
    if (topics.isEmpty) {
      _addAIMessage(
        "I couldn't find any topics in your selection. Please select at least one topic to study.",
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

    // Validate topics first
    final validation = await validateTopics(topics);
    if (validation != null && validation.hasErrors) {
      _addTopicSuggestions(validation);
      return;
    }

    // Start the session
    await _startBackendSession('custom_topics', topics);
  }

  /// Add topic suggestions to chat
  void _addTopicSuggestions(TopicValidationResponse validation) {
    String message = "I found some topics that might need clarification:\n\n";

    for (final suggestion in validation.suggestions) {
      message += "• You typed: **${suggestion.input}**\n";
      message += "  Did you mean: **${suggestion.suggestion}**?\n\n";
    }

    message +=
        "Please clarify your topics, or I can proceed with the ones I understood: ";
    message += validation.validTopics.join(', ');

    _addAIMessage(message);
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

    await _submitAnswerWithRetry(answer);
  }

  /// Submit answer with automatic retry for format errors
  Future<void> _submitAnswerWithRetry(
    String answer, {
    int retryCount = 0,
  }) async {
    _setLoadingWithTyping(
      true,
      typingMessage: "Analyzing your response...",
      processingAnswer: true,
    );

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

        // Use the formatted message from the backend
        _addAIMessage(
          response.message ?? _buildCompletionMessage(response.scores!),
        );
      } else {
        // Check if we have a next question or message
        if (response.nextQuestion?.trim().isEmpty == true &&
            response.message?.trim().isEmpty == true) {
          // Empty response - show informative message
          _addAIMessage(
            "No more questions available for this topic. "
            "This might happen if:\n\n"
            "• The topic doesn't have enough questions generated yet\n"
            "• You've completed all available questions",
          );
        } else {
          // Continue with next question - use the formatted message from backend
          _addAIMessage(
            response.message ?? "**Next Question:**\n${response.nextQuestion!}",
          );
        }
      }
    } on SessionApiException catch (e) {
      if (e.statusCode == 404) {
        // Backend session expired - handle gracefully
        await _handleExpiredSession(answer);
      } else if (e.statusCode == 401) {
        // Authentication issue - user needs to re-authenticate
        _sessionState = SessionState.error;
        _addAIMessage(
          "Authentication expired. Please sign out and sign back in to continue.",
        );
      } else if ((e.message.contains('formatting error') ||
              e.message.contains('Invalid format specifier') ||
              e.message.contains('for object of type \'str\'')) &&
          retryCount < 2) {
        // Auto-retry with basic sanitization only
        _logger.warning(
          'Format error detected, retrying with sanitized input (attempt ${retryCount + 1})',
        );

        final sanitizedAnswer = _basicSanitizeInput(answer);
        await _submitAnswerWithRetry(
          sanitizedAnswer,
          retryCount: retryCount + 1,
        );
        return; // Don't execute the rest of the method
      } else if (e.message.contains('formatting error') ||
          e.message.contains('Invalid format specifier')) {
        // Handle backend formatting errors with user-friendly message after retries failed
        _addAIMessage(
          "I'm having trouble processing your answer due to a technical issue. "
          "Please try rephrasing your answer using simpler language.\n\n"
          "Tips:\n"
          "• Use basic words and sentences\n"
          "• Avoid mathematical symbols or special characters\n"
          "• Keep your response concise\n\n"
          "You can also type 'new question' to skip to the next question.",
        );
      } else {
        _sessionState = SessionState.error;
        _addAIMessage("Error: ${e.message}");
      }
    } finally {
      _setLoadingWithTyping(false);
    }

    _updateCurrentSession();
    await _autoSaveSession();
  }

  /// Basic sanitization for retry attempts - less aggressive than before
  String _basicSanitizeInput(String input) {
    return input
        .replaceAll(
          RegExp(r'[{}%]'),
          '',
        ) // Remove only problematic format characters
        .replaceAll(RegExp(r'\s+'), ' ') // Normalize whitespace
        .trim();
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

            _addAIMessage(
              continueResponse.message ??
                  _buildCompletionMessage(continueResponse.scores!),
            );
          } else {
            // Continue with next question
            _addAIMessage(
              continueResponse.message ??
                  "**Next Question:**\n${continueResponse.nextQuestion!}",
            );
          }
        } catch (e) {
          // If answer processing fails, show the first question from the restarted session
          _logger.warning(
            'Failed to process answer after restart, showing first question: $e',
          );
          _addAIMessage(response.message);
        }
      } else {
        // No topics available, session expired
        _addAIMessage("Session expired. No topic information available.");
        _sessionState = SessionState.error;
      }
    } catch (e) {
      _logger.severe('Failed to handle expired session: $e');
      _addAIMessage("Error reconnecting session: ${e.toString()}");
      _sessionState = SessionState.error;
    }

    _updateCurrentSession();
    await _autoSaveSession();
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

  /// Get the current session token for routing
  String? get currentSessionToken => _currentSession?.token;

  /// Handle errors
  Future<void> _handleError(dynamic error) async {
    _sessionState = SessionState.error;
    String errorMessage = "Unexpected error occurred";

    if (error is SessionApiException) {
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

  /// Handle topics input during topic collection (from string input)
  Future<void> _handleTopicsInputFromString(String input) async {
    // Parse topics from user input
    List<String> topics =
        input
            .split(',')
            .map((topic) => topic.trim())
            .where((topic) => topic.isNotEmpty)
            .toList();

    await handleTopicsInput(topics);
  }

  /// Request a new question when encountering errors
  Future<void> requestNewQuestion() async {
    if (_currentSessionId == null) {
      _addAIMessage("Session error: No active session ID. Let's start over.");
      _resetSession();
      return;
    }

    _setLoadingWithTyping(
      true,
      typingMessage: "Getting a new question...",
      generatingQuestions: true,
    );

    try {
      // Try to get a new question by sending a simple "new question" request
      final response = await _api.answer(
        sessionId: _currentSessionId!,
        userInput: "new question",
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

        _addAIMessage(
          response.message ?? _buildCompletionMessage(response.scores!),
        );
      } else {
        // Show the new question
        _addAIMessage(
          response.message ?? "**New Question:**\n${response.nextQuestion!}",
        );
      }
    } catch (e) {
      // If getting a new question fails, restart the session
      await _handleExpiredSession("continue");
    } finally {
      _setLoadingWithTyping(false);
    }

    _updateCurrentSession();
    await _autoSaveSession();
  }
}
