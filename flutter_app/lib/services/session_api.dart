import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'circuit_breaker.dart';
import 'dart:async';

/// Exception thrown when the Session API returns an error
class SessionApiException implements Exception {
  final String message;
  final int? statusCode;

  SessionApiException(this.message, [this.statusCode]);

  @override
  String toString() {
    return statusCode != null
        ? 'SessionApiException($statusCode): $message'
        : 'SessionApiException: $message';
  }
}

/// Response model for starting a new session
class StartSessionResponse {
  final String sessionId;
  final String nextQuestion;
  final String message;
  final List<String> topics;
  final String topicId;

  StartSessionResponse({
    required this.sessionId,
    required this.nextQuestion,
    required this.message,
    required this.topics,
    required this.topicId,
  });

  factory StartSessionResponse.fromJson(Map<String, dynamic> json) {
    return StartSessionResponse(
      sessionId: json['session_id'] as String,
      nextQuestion:
          json['next_question'] as String? ?? json['message'] as String? ?? '',
      message: json['message'] as String? ?? '',
      topics: List<String>.from(json['topics'] as List? ?? []),
      topicId: json['topic_id'] as String,
    );
  }
}

/// Response model for a conversation turn
class ConversationTurnResponse {
  final String botResponse;

  ConversationTurnResponse({required this.botResponse});

  factory ConversationTurnResponse.fromJson(Map<String, dynamic> json) {
    return ConversationTurnResponse(
      botResponse: json['bot_response'] as String,
    );
  }
}

/// Response model for answering a question
class AnswerResponse {
  final String? nextQuestion;
  final String? message;
  final String? feedback;
  final Map<String, int>? scores;
  final bool isDone;
  final int? score;
  final int? questionIndex;
  final int? totalQuestions;
  final double? finalScore;

  AnswerResponse({
    this.nextQuestion,
    this.message,
    this.feedback,
    this.scores,
    required this.isDone,
    this.score,
    this.questionIndex,
    this.totalQuestions,
    this.finalScore,
  });

  factory AnswerResponse.fromJson(Map<String, dynamic> json) {
    return AnswerResponse(
      nextQuestion: json['next_question'] as String?,
      message: json['message'] as String?,
      feedback: json['feedback'] as String?,
      scores:
          json['scores'] != null
              ? Map<String, int>.from(json['scores'] as Map<String, dynamic>)
              : null,
      isDone: json['isDone'] as bool? ?? false,
      score: json['score'] as int?,
      questionIndex: json['question_index'] as int?,
      totalQuestions: json['total_questions'] as int?,
      finalScore: (json['final_score'] as num?)?.toDouble(),
    );
  }
}

/// Model for popular topics
class PopularTopic {
  final String name;
  final String description;

  PopularTopic({required this.name, required this.description});

  factory PopularTopic.fromJson(Map<String, dynamic> json) {
    return PopularTopic(
      name: json['name'] as String,
      description: json['description'] as String,
    );
  }
}

/// Model for topic validation response
class TopicValidationResponse {
  final List<String> validTopics;
  final List<TopicSuggestion> suggestions;
  final bool hasErrors;

  TopicValidationResponse({
    required this.validTopics,
    required this.suggestions,
    required this.hasErrors,
  });

  factory TopicValidationResponse.fromJson(Map<String, dynamic> json) {
    return TopicValidationResponse(
      validTopics: List<String>.from(json['valid_topics'] as List),
      suggestions:
          (json['suggestions'] as List)
              .map((s) => TopicSuggestion.fromJson(s as Map<String, dynamic>))
              .toList(),
      hasErrors: json['has_errors'] as bool,
    );
  }
}

/// Model for topic suggestions
class TopicSuggestion {
  final String input;
  final String suggestion;
  final String type;

  TopicSuggestion({
    required this.input,
    required this.suggestion,
    required this.type,
  });

  factory TopicSuggestion.fromJson(Map<String, dynamic> json) {
    return TopicSuggestion(
      input: json['input'] as String,
      suggestion: json['suggestion'] as String,
      type: json['type'] as String,
    );
  }
}

/// Model for user's existing topics
class UserTopic {
  final String id;
  final String name;
  final String description;
  final int questionCount;
  final DateTime? createdAt;
  final DateTime? lastReviewedAt;
  final DateTime? nextReviewAt;
  final bool isDue;
  final bool isOverdue;
  final String reviewUrgency;
  final Map<String, dynamic> fsrsParams;

  UserTopic({
    required this.id,
    required this.name,
    required this.description,
    required this.questionCount,
    this.createdAt,
    this.lastReviewedAt,
    this.nextReviewAt,
    required this.isDue,
    required this.isOverdue,
    required this.reviewUrgency,
    required this.fsrsParams,
  });

  factory UserTopic.fromJson(Map<String, dynamic> json) {
    return UserTopic(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      questionCount: json['questionCount'] as int,
      createdAt:
          json['createdAt'] != null
              ? DateTime.parse(json['createdAt'] as String)
              : null,
      lastReviewedAt:
          json['lastReviewedAt'] != null
              ? DateTime.parse(json['lastReviewedAt'] as String)
              : null,
      nextReviewAt:
          json['nextReviewAt'] != null
              ? DateTime.parse(json['nextReviewAt'] as String)
              : null,
      isDue: json['isDue'] as bool,
      isOverdue: json['isOverdue'] as bool,
      reviewUrgency: json['reviewUrgency'] as String,
      fsrsParams: json['fsrsParams'] as Map<String, dynamic>,
    );
  }
}

/// Session status model
class SessionStatus {
  final String sessionId;
  final bool isComplete;
  final int questionIndex;
  final int totalQuestions;
  final int responsesCount;
  final String? currentQuestion;
  final DateTime startedAt;

  SessionStatus({
    required this.sessionId,
    required this.isComplete,
    required this.questionIndex,
    required this.totalQuestions,
    required this.responsesCount,
    this.currentQuestion,
    required this.startedAt,
  });

  factory SessionStatus.fromJson(Map<String, dynamic> json) {
    return SessionStatus(
      sessionId: json['session_id'] as String,
      isComplete: json['is_complete'] as bool,
      questionIndex: json['question_index'] as int,
      totalQuestions: json['total_questions'] as int,
      responsesCount: json['responses_count'] as int,
      currentQuestion: json['current_question'] as String?,
      startedAt: DateTime.parse(json['started_at'] as String),
    );
  }
}

class SessionApi {
  /// Base URL for the backend API
  final String baseUrl;

  /// HTTP client timeout duration
  final Duration timeout;

  /// Circuit breakers for different services
  late final CircuitBreaker _sessionBreaker;
  late final CircuitBreaker _topicBreaker;
  late final CircuitBreaker _searchBreaker;

  SessionApi({
    required this.baseUrl,
    this.timeout = const Duration(seconds: 60),
  }) {
    // Ensure baseUrl doesn't end with a slash
    if (baseUrl.endsWith('/')) {
      throw ArgumentError('baseUrl should not end with a slash');
    }

    // Initialize circuit breakers
    _sessionBreaker = ServiceCircuitBreakers.getBreaker('session_api');
    _topicBreaker = ServiceCircuitBreakers.getBreaker('popular_topics');
    _searchBreaker = ServiceCircuitBreakers.getBreaker('topic_search');
  }

  /// Get authorization headers with Firebase ID token
  Future<Map<String, String>> _getHeaders() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw SessionApiException('User not authenticated');
    }

    final idToken = await user.getIdToken();

    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Bearer $idToken',
    };
  }

  /// Get headers with automatic token refresh
  Future<Map<String, String>> _getHeadersWithRefresh({
    bool forceRefresh = false,
  }) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw SessionApiException('User not authenticated');
    }

    final idToken = await user.getIdToken(forceRefresh);

    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Bearer $idToken',
    };
  }

  /// Make HTTP request with automatic token refresh retry
  Future<http.Response> _makeRequestWithRetry(
    Future<http.Response> Function(Map<String, String> headers) requestFunction,
  ) async {
    try {
      // First attempt with current token
      final headers = await _getHeaders();
      final response = await requestFunction(headers);

      // If unauthorized, try once more with refreshed token
      if (response.statusCode == 401) {
        final refreshedHeaders = await _getHeadersWithRefresh(
          forceRefresh: true,
        );
        return await requestFunction(refreshedHeaders);
      }

      return response;
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Get popular topics for quick-pick menu
  Future<List<PopularTopic>> getPopularTopics({int limit = 6}) async {
    // NOTE: This endpoint doesn't exist in deployed backend - using fallback topics
    try {
      // Use fallback popular topics since the API endpoint is not available
      return [
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
    } catch (e) {
      throw SessionApiException('Network error: $e');
    }
  }

  /// Validate topics and get suggestions
  Future<TopicValidationResponse> validateTopics(List<String> topics) async {
    // NOTE: This endpoint doesn't exist in deployed backend - return simple validation
    try {
      return TopicValidationResponse(
        validTopics: topics,
        suggestions: [],
        hasErrors: false,
      );
    } catch (e) {
      throw SessionApiException('Network error: $e');
    }
  }

  /// Search user's existing topics
  Future<List<UserTopic>> searchTopics(String query) async {
    // NOTE: This endpoint doesn't exist in deployed backend - return empty list
    return [];
  }

  /// Starts a new study session with the specified topics.
  ///
  /// Parameters:
  /// - [topics]: List of study topics (must not be empty)
  /// - [maxTopics]: Maximum number of topics to cover (default: 3, min: 1)
  /// - [maxQuestions]: Maximum questions per topic (default: 5, min: 1)
  /// - [sessionType]: Type of session - 'custom_topics' or 'due_items' (default: 'custom_topics')
  /// - [sessionId]: Optional session ID from frontend
  ///
  /// Returns [StartSessionResponse] containing:
  /// - sessionId: Unique identifier for this study session
  /// - nextQuestion: The first question to ask the user
  /// - message: Formatted message for chat display
  /// - topics: List of topics for the session
  ///
  /// Throws [SessionApiException] on API errors or [ArgumentError] on invalid input
  Future<StartSessionResponse> startSession({
    required List<String> topics,
    required int maxTopics,
    required int maxQuestions,
    required String sessionType,
    String? sessionId, // Optional session ID from frontend
  }) async {
    // Input validation
    if (topics.isEmpty) {
      throw ArgumentError('topics cannot be empty');
    }
    if (maxTopics < 1) {
      throw ArgumentError('maxTopics must be at least 1');
    }
    if (maxQuestions < 1) {
      throw ArgumentError('maxQuestions must be at least 1');
    }
    if (sessionType != 'custom_topics' && sessionType != 'due_items') {
      throw ArgumentError(
        'sessionType must be either "custom_topics" or "due_items"',
      );
    }

    final url = Uri.parse('$baseUrl/chat/start_session');

    // Get current user UID for the request
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw SessionApiException('User not authenticated');
    }

    // Generate session ID if not provided
    final effectiveSessionId =
        sessionId ?? DateTime.now().millisecondsSinceEpoch.toString();

    final requestBody = {
      'id': effectiveSessionId, // Session ID (required by backend)
      'topics': topics, // Send all topics as list
      'session_type': sessionType,
      'max_topics': maxTopics,
      'max_questions': maxQuestions,
      'session_id': effectiveSessionId, // Include session ID
    };

    // Request body prepared for backend session creation

    try {
      final response = await _sessionBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http
              .post(url, headers: headers, body: jsonEncode(requestBody))
              .timeout(timeout);
        });
      });

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          return StartSessionResponse.fromJson(data);
        } catch (e) {
          throw SessionApiException('Invalid response format: $e');
        }
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to start session: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } on TimeoutException {
      throw SessionApiException(
        'Session start timed out. This may happen with complex topics. Please try again or select fewer topics.',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Sends the user's answer to continue the study session.
  Future<ConversationTurnResponse> handleConversationTurn({
    required String sessionId,
    required String topicId,
    required String userInput,
  }) async {
    // Input validation
    if (sessionId.trim().isEmpty) {
      throw ArgumentError('sessionId cannot be empty');
    }
    if (topicId.trim().isEmpty) {
      throw ArgumentError('topicId cannot be empty');
    }
    if (userInput.trim().isEmpty) {
      throw ArgumentError('userInput cannot be empty');
    }

    final url = Uri.parse('$baseUrl/chat/conversation/turn');
    final payload = {
      'session_id': sessionId.trim(),
      'topic_id': topicId.trim(),
      'user_input': userInput.trim(),
    };

    try {
      final response = await _sessionBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http
              .post(url, headers: headers, body: jsonEncode(payload))
              .timeout(timeout);
        });
      });

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          return ConversationTurnResponse.fromJson(data);
        } catch (e) {
          throw SessionApiException('Invalid response format: $e');
        }
      } else if (response.statusCode == 404) {
        throw SessionApiException(
          'Session not found. The session may have expired or is invalid.',
          response.statusCode,
        );
      } else if (response.statusCode == 401) {
        throw SessionApiException(
          'Authentication failed. Please sign out and sign back in.',
          response.statusCode,
        );
      } else if (response.statusCode == 403) {
        throw SessionApiException(
          'Access denied. You can only access your own sessions.',
          response.statusCode,
        );
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to send answer: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// End the current conversation and get analytics
  Future<Map<String, dynamic>> endConversation({
    required String sessionId,
  }) async {
    if (sessionId.trim().isEmpty) {
      throw ArgumentError('sessionId cannot be empty');
    }

    final url = Uri.parse('$baseUrl/chat/conversation/end');
    final payload = {'session_id': sessionId.trim()};

    try {
      final response = await _sessionBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http
              .post(url, headers: headers, body: jsonEncode(payload))
              .timeout(timeout);
        });
      });

      if (response.statusCode == 200) {
        try {
          return jsonDecode(response.body) as Map<String, dynamic>;
        } catch (e) {
          throw SessionApiException('Invalid response format: $e');
        }
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to end session: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// End the current session early
  Future<Map<String, dynamic>> endSession({required String sessionId}) async {
    // Input validation
    if (sessionId.trim().isEmpty) {
      throw ArgumentError('sessionId cannot be empty');
    }

    final url = Uri.parse('$baseUrl/sessions/${sessionId.trim()}/end');

    try {
      final response = await _sessionBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http.post(url, headers: headers).timeout(timeout);
        });
      });

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          return data;
        } catch (e) {
          throw SessionApiException('Invalid response format: $e');
        }
      } else if (response.statusCode == 404) {
        throw SessionApiException(
          'Session not found. The session may have expired or is invalid.',
          response.statusCode,
        );
      } else if (response.statusCode == 403) {
        throw SessionApiException(
          'Access denied. You can only access your own sessions.',
          response.statusCode,
        );
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to end session: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Get session status
  Future<SessionStatus> getSessionStatus(String sessionId) async {
    // NOTE: This endpoint doesn't exist in deployed backend
    throw SessionApiException('Session status endpoint not available');
  }

  /// Test if the API is reachable
  Future<bool> isHealthy() async {
    try {
      final url = Uri.parse('$baseUrl/health');
      final response = await http.get(url).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Get circuit breaker status for monitoring
  Map<String, dynamic> getCircuitBreakerStatus() {
    return {
      'session_api': _sessionBreaker.getStatus(),
      'popular_topics': _topicBreaker.getStatus(),
      'topic_search': _searchBreaker.getStatus(),
    };
  }

  /// Reset circuit breakers (for manual recovery)
  void resetCircuitBreakers() {
    _sessionBreaker.reset();
    _topicBreaker.reset();
    _searchBreaker.reset();
  }

  /// Check if any circuit breaker is open
  bool get hasOpenCircuitBreakers {
    return _sessionBreaker.state == CircuitBreakerState.open ||
        _topicBreaker.state == CircuitBreakerState.open ||
        _searchBreaker.state == CircuitBreakerState.open;
  }

  /// Get today's reviews for a user
  ///
  /// Parameters:
  /// - [userId]: User ID to get reviews for (must not be empty)
  ///
  /// Returns Map containing today's review data with overdue, dueToday, and upcoming lists
  ///
  /// Throws [SessionApiException] on API errors or [ArgumentError] on invalid input
  Future<Map<String, dynamic>> getTodaysReviews(String userId) async {
    // Input validation
    if (userId.trim().isEmpty) {
      throw ArgumentError('userId cannot be empty');
    }

    final url = Uri.parse('$baseUrl/topics/${userId.trim()}/due-today');

    try {
      final response = await _sessionBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http.get(url, headers: headers).timeout(timeout);
        });
      });

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          return data;
        } catch (e) {
          throw SessionApiException('Invalid response format: $e');
        }
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to get today\'s reviews: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Skips the current question in a conversational session
  Future<SkipQuestionResponse> skipConversationQuestion({
    required String sessionId,
  }) async {
    if (sessionId.trim().isEmpty) {
      throw ArgumentError('sessionId cannot be empty');
    }
    final url = Uri.parse('$baseUrl/chat/conversation/skip');
    try {
      final response = await _sessionBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http
              .post(
                url,
                headers: headers,
                body: jsonEncode({'session_id': sessionId}),
              )
              .timeout(timeout);
        });
      });

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          return SkipQuestionResponse.fromJson(data);
        } catch (e) {
          throw SessionApiException('Invalid response format: $e');
        }
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to skip question: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Get all topics for a user
  Future<List<UserTopic>> getAllTopics() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw SessionApiException('User not authenticated');
    }

    final url = Uri.parse('$baseUrl/topics/${user.uid}/with-review-status');
    try {
      final response = await _topicBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http.get(url, headers: headers).timeout(timeout);
        });
      });

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as List;
          return data
              .map(
                (topicData) =>
                    UserTopic.fromJson(topicData as Map<String, dynamic>),
              )
              .toList();
        } catch (e) {
          throw SessionApiException('Invalid response format: $e');
        }
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to get topics: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  Future<void> deleteTopic(String topicId) async {
    final url = Uri.parse('$baseUrl/topics/$topicId');
    try {
      final response = await _topicBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http.delete(url, headers: headers).timeout(timeout);
        });
      });

      if (response.statusCode != 200) {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to delete topic: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  Future<SelfEvaluationResponse> submitSelfEvaluation({
    required String sessionId,
    required int score,
  }) async {
    final url = Uri.parse('$baseUrl/sessions/$sessionId/self-evaluate');
    try {
      final response = await _sessionBreaker.execute(() async {
        return await _makeRequestWithRetry((headers) async {
          return await http
              .post(url, headers: headers, body: jsonEncode({'score': score}))
              .timeout(timeout);
        });
      });

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          return SelfEvaluationResponse.fromJson(data);
        } catch (e) {
          throw SessionApiException('Invalid response format: $e');
        }
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to submit self-evaluation: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Service temporarily unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }
}

class SkipQuestionResponse {
  final bool isDone;
  final String nextQuestion;

  SkipQuestionResponse({required this.isDone, required this.nextQuestion});

  factory SkipQuestionResponse.fromJson(Map<String, dynamic> json) {
    return SkipQuestionResponse(
      isDone: json['is_done'],
      nextQuestion: json['next_question'],
    );
  }
}

class SelfEvaluationResponse {
  final bool isComplete;
  final String? nextQuestion;

  SelfEvaluationResponse({required this.isComplete, this.nextQuestion});

  factory SelfEvaluationResponse.fromJson(Map<String, dynamic> json) {
    return SelfEvaluationResponse(
      isComplete: json['isComplete'] as bool,
      nextQuestion: json['nextQuestion'] as String?,
    );
  }
}
