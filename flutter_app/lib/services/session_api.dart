import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'circuit_breaker.dart';

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

  StartSessionResponse({
    required this.sessionId,
    required this.nextQuestion,
    required this.message,
    required this.topics,
  });

  factory StartSessionResponse.fromJson(Map<String, dynamic> json) {
    return StartSessionResponse(
      sessionId: json['session_id'] as String,
      nextQuestion: json['next_question'] as String? ?? '',
      message: json['message'] as String? ?? '',
      topics: List<String>.from(json['topics'] as List? ?? []),
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

  UserTopic({required this.id, required this.name, required this.description});

  factory UserTopic.fromJson(Map<String, dynamic> json) {
    return UserTopic(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
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
    this.timeout = const Duration(seconds: 30),
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
    final url = Uri.parse('$baseUrl/api/v1/chat/popular-topics?limit=$limit');

    try {
      final response = await _topicBreaker.execute(() async {
        final headers = await _getHeaders();
        return await http.get(url, headers: headers).timeout(timeout);
      });

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final topics = data['topics'] as List;
        return topics
            .map((t) => PopularTopic.fromJson(t as Map<String, dynamic>))
            .toList();
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to get popular topics: $errorBody',
          response.statusCode,
        );
      }
    } on CircuitBreakerException catch (e) {
      throw SessionApiException(
        'Popular topics service unavailable: ${e.message}',
      );
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Validate topics and get suggestions
  Future<TopicValidationResponse> validateTopics(List<String> topics) async {
    final url = Uri.parse('$baseUrl/api/v1/chat/validate-topics');

    try {
      final headers = await _getHeaders();
      final payload = {'topics': topics};

      final response = await http
          .post(url, headers: headers, body: jsonEncode(payload))
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return TopicValidationResponse.fromJson(data);
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to validate topics: $errorBody',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Search user's existing topics
  Future<List<UserTopic>> searchTopics(String query) async {
    final url = Uri.parse(
      '$baseUrl/api/v1/chat/search-topics?q=${Uri.encodeComponent(query)}',
    );

    try {
      final headers = await _getHeaders();
      final response = await http.get(url, headers: headers).timeout(timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final topics = data['topics'] as List;
        return topics
            .map((t) => UserTopic.fromJson(t as Map<String, dynamic>))
            .toList();
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to search topics: $errorBody',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Starts a new study session with the specified topics.
  ///
  /// Parameters:
  /// - [topics]: List of study topics (must not be empty)
  /// - [maxTopics]: Maximum number of topics to cover (default: 3, min: 1)
  /// - [maxQuestions]: Maximum questions per topic (default: 7, min: 1)
  /// - [sessionType]: Type of session - 'custom_topics' or 'due_items' (default: 'custom_topics')
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
    int maxTopics = 3,
    int maxQuestions = 7,
    String sessionType = 'custom_topics',
  }) async {
    // Input validation
    if (topics.isEmpty) {
      throw ArgumentError('Topics list cannot be empty');
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

    final url = Uri.parse('$baseUrl/api/v1/chat/start_session');
    final payload = {
      'topics': topics,
      'session_type': sessionType,
      'max_topics': maxTopics,
      'max_questions': maxQuestions,
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
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
  }

  /// Sends the user's answer to continue the study session.
  ///
  /// Parameters:
  /// - [sessionId]: Session ID from [startSession] (must not be empty)
  /// - [userInput]: User's answer to the current question (must not be empty)
  ///
  /// Returns [AnswerResponse] containing either:
  /// - nextQuestion: Next question if session continues
  /// - scores: Final topic scores if session is complete
  /// - message: Formatted message for chat display
  /// - feedback: Feedback on the answer
  ///
  /// Throws [SessionApiException] on API errors or [ArgumentError] on invalid input
  Future<AnswerResponse> answer({
    required String sessionId,
    required String userInput,
  }) async {
    // Input validation
    if (sessionId.trim().isEmpty) {
      throw ArgumentError('sessionId cannot be empty');
    }
    if (userInput.trim().isEmpty) {
      throw ArgumentError('userInput cannot be empty');
    }

    final url = Uri.parse('$baseUrl/api/v1/chat/answer');
    final payload = {
      'session_id': sessionId.trim(),
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
          return AnswerResponse.fromJson(data);
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

  /// Get current session status
  Future<SessionStatus> getSessionStatus(String sessionId) async {
    final url = Uri.parse('$baseUrl/api/v1/chat/session/$sessionId/status');

    try {
      final headers = await _getHeaders();
      final response = await http.get(url, headers: headers).timeout(timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return SessionStatus.fromJson(data);
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw SessionApiException(
          'Failed to get session status: $errorBody',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is SessionApiException) rethrow;
      throw SessionApiException('Network error: $e');
    }
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
}
