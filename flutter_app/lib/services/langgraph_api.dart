// lib/services/langgraph_api.dart

import 'dart:convert';
import 'package:http/http.dart' as http;

/// Exception thrown when the LangGraph API returns an error
class LangGraphApiException implements Exception {
  final String message;
  final int? statusCode;

  LangGraphApiException(this.message, [this.statusCode]);

  @override
  String toString() {
    return statusCode != null
        ? 'LangGraphApiException($statusCode): $message'
        : 'LangGraphApiException: $message';
  }
}

/// Response model for starting a new session
class StartSessionResponse {
  final String sessionId;
  final String nextQuestion;

  StartSessionResponse({required this.sessionId, required this.nextQuestion});

  factory StartSessionResponse.fromJson(Map<String, dynamic> json) {
    return StartSessionResponse(
      sessionId: json['session_id'] as String,
      nextQuestion:
          json['message'] as String? ?? json['next_question'] as String? ?? '',
    );
  }
}

/// Response model for answering a question
class AnswerResponse {
  final String? nextQuestion;
  final Map<String, int>? scores;
  final bool isDone;

  AnswerResponse({this.nextQuestion, this.scores, required this.isDone});

  factory AnswerResponse.fromJson(Map<String, dynamic> json) {
    final hasScores = json.containsKey('scores');
    return AnswerResponse(
      nextQuestion: json['next_question'] as String?,
      scores:
          hasScores
              ? Map<String, int>.from(json['scores'] as Map<String, dynamic>)
              : null,
      isDone: hasScores,
    );
  }
}

class LangGraphApi {
  /// Base URL for the LangGraph backend API
  ///
  /// Development URLs:
  /// - Local development: 'http://localhost:8000'
  /// - Android emulator: 'http://10.0.2.2:8000' (maps to host machine's localhost)
  /// - iOS Simulator: 'http://localhost:8000' or 'http://127.0.0.1:8000'
  /// - Physical device on same network: 'http://YOUR_MACHINE_IP:8000'
  ///
  /// Production: Use your deployed backend URL
  final String baseUrl;

  /// HTTP client timeout duration
  final Duration timeout;

  LangGraphApi({
    required this.baseUrl,
    this.timeout = const Duration(seconds: 30),
  }) {
    // Ensure baseUrl doesn't end with a slash
    if (baseUrl.endsWith('/')) {
      throw ArgumentError('baseUrl should not end with a slash');
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
  ///
  /// Throws [LangGraphApiException] on API errors or [ArgumentError] on invalid input
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

    final url = Uri.parse('$baseUrl/start_session');

    final payload = {
      'session_type': sessionType,
      'topics': topics,
      'max_topics': maxTopics,
      'max_questions': maxQuestions,
    };

    try {
      final response = await http
          .post(
            url,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(payload),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          return StartSessionResponse.fromJson(data);
        } catch (e) {
          throw LangGraphApiException('Invalid response format: $e');
        }
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw LangGraphApiException(
          'Failed to start session: $errorBody',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is LangGraphApiException) rethrow;
      throw LangGraphApiException('Network error: $e');
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
  ///
  /// Throws [LangGraphApiException] on API errors or [ArgumentError] on invalid input
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

    final url = Uri.parse('$baseUrl/answer');

    final payload = {
      'session_id': sessionId.trim(),
      'user_input': userInput.trim(),
    };

    try {
      final response = await http
          .post(
            url,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(payload),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        try {
          final data = jsonDecode(response.body) as Map<String, dynamic>;
          return AnswerResponse.fromJson(data);
        } catch (e) {
          throw LangGraphApiException('Invalid response format: $e');
        }
      } else if (response.statusCode == 404) {
        throw LangGraphApiException(
          'Session not found. The session may have expired or is invalid.',
          response.statusCode,
        );
      } else {
        final errorBody =
            response.body.isNotEmpty ? response.body : 'No error details';
        throw LangGraphApiException(
          'Failed to send answer: $errorBody',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is LangGraphApiException) rethrow;
      throw LangGraphApiException('Network error: $e');
    }
  }

  /// Test if the API is reachable
  Future<bool> isHealthy() async {
    try {
      final url = Uri.parse('$baseUrl/docs');
      final response = await http.get(url).timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
