import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'circuit_breaker.dart';
import 'dart:async';
import '../models/question.dart';

/// Enums

enum MessageAction { answer, skip, end, other }

enum TopicAction { generate_questions, delete }

/// Exception thrown when the Session API returns an error
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, [this.statusCode]);

  @override
  String toString() {
    return statusCode != null
        ? 'ApiException($statusCode): $message'
        : 'ApiException: $message';
  }
}

/// Response model for starting a new session
class StartChatResponse {
  final String chatId;
  final String message;
  final String nextQuestion;
  final List<String> topics;
  final String topicId;

  StartChatResponse({
    required this.chatId,
    required this.message,
    required this.nextQuestion,
    required this.topics,
    required this.topicId,
  });

  factory StartChatResponse.fromJson(Map<String, dynamic> json) {
    return StartChatResponse(
      chatId: json['chat_id'] as String,
      message: json['message'] as String,
      nextQuestion: json['next_question'] as String,
      topics: List<String>.from(json['topics'] as List),
      topicId: json['topic_id'] as String,
    );
  }
}

/// Response model for a conversation turn
class MessageResponse {
  final String botResponse;
  final bool sessionEnded;
  final Map<String, dynamic>? analytics;

  MessageResponse({
    required this.botResponse,
    required this.sessionEnded,
    this.analytics,
  });

  factory MessageResponse.fromJson(Map<String, dynamic> json) {
    return MessageResponse(
      botResponse: json['bot_response'] as String,
      sessionEnded: json['session_ended'] as bool,
      analytics: json['analytics'] as Map<String, dynamic>?,
    );
  }
}

/// Model for user's existing topics
class Topic {
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

  Topic({
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
  });

  factory Topic.fromJson(Map<String, dynamic> json) {
    return Topic(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      questionCount: json['questionCount'] as int? ?? 0,
      createdAt:
          json['createdAt'] != null ? DateTime.parse(json['createdAt']) : null,
      lastReviewedAt:
          json['lastReviewedAt'] != null
              ? DateTime.parse(json['lastReviewedAt'])
              : null,
      nextReviewAt:
          json['nextReviewAt'] != null
              ? DateTime.parse(json['nextReviewAt'])
              : null,
      isDue: json['isDue'] as bool? ?? false,
      isOverdue: json['isOverdue'] as bool? ?? false,
      reviewUrgency: json['reviewUrgency'] as String? ?? 'not_scheduled',
    );
  }
}

/// A special model for the "Today's Reviews" screen.
class DueTopics {
  final List<Topic> topics;
  final DateTime? lastReviewedAt;

  DueTopics({required this.topics, this.lastReviewedAt});

  factory DueTopics.fromJson(Map<String, dynamic> json) {
    final topics =
        (json['topics'] as List)
            .map((item) => Topic.fromJson(item as Map<String, dynamic>))
            .toList();
    return DueTopics(
      topics: topics,
      lastReviewedAt:
          json['lastReviewedAt'] != null
              ? DateTime.parse(json['lastReviewedAt'])
              : null,
    );
  }
}

class ApiService {
  final String _baseUrl;
  final String _apiPrefix = '/api/v1';
  final Duration timeout;
  late final CircuitBreaker _breaker;

  // Expose baseUrl as a getter
  String get baseUrl => _baseUrl;

  ApiService({
    required String baseUrl,
    this.timeout = const Duration(seconds: 60),
  }) : _baseUrl = baseUrl {
    _breaker = ServiceCircuitBreakers.getBreaker('api_service');
  }

  Future<Map<String, String>> _getHeaders() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw ApiException('User not authenticated');
    }
    final idToken = await user.getIdToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $idToken',
    };
  }

  Future<http.Response> _makeRequestWithRetry(
    Future<http.Response> Function(Map<String, String> headers) requestFunction,
  ) async {
    try {
      final headers = await _getHeaders();
      final response = await requestFunction(headers);

      if (response.statusCode == 401) {
        final refreshedHeaders = await _getHeaders();
        return await requestFunction(refreshedHeaders);
      }
      return response;
    } catch (e) {
      throw ApiException('Network error: $e');
    }
  }

  // --- Chat Endpoints ---

  Future<StartChatResponse> startChat(
    List<String> topics, [
    String? chatId,
  ]) async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/chat/start');
    final body = jsonEncode({'topics': topics, 'chat_id': chatId});

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) =>
            http.post(url, headers: headers, body: body).timeout(timeout),
      ),
    );

    if (response.statusCode == 200) {
      return StartChatResponse.fromJson(jsonDecode(response.body));
    } else {
      throw ApiException('Failed to start chat', response.statusCode);
    }
  }

  Future<String> handleTurn(String chatId, String userInput) async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/chat/$chatId/messages');
    final body = jsonEncode({'user_input': userInput});

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) =>
            http.post(url, headers: headers, body: body).timeout(timeout),
      ),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['bot_response'] as String;
    } else {
      try {
        final errorBody = jsonDecode(response.body);
        throw ApiException(
          errorBody['detail'] ?? 'Failed to handle turn',
          response.statusCode,
        );
      } catch (_) {
        throw ApiException(
          response.reasonPhrase ?? 'An unknown error occurred',
          response.statusCode,
        );
      }
    }
  }

  // --- Topic Endpoints ---

  Future<List<Topic>> getTopics({String? view}) async {
    final queryParams = view != null ? '?view=$view' : '';
    final url = Uri.parse('$_baseUrl$_apiPrefix/topics$queryParams');

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.get(url, headers: headers).timeout(timeout),
      ),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as List;
      return data
          .map((item) => Topic.fromJson(item as Map<String, dynamic>))
          .toList();
    } else {
      throw ApiException('Failed to get topics', response.statusCode);
    }
  }

  Future<Topic> getTopic(String topicId, {String? view}) async {
    final queryParams = {'topic_id': topicId, 'view': view}
      ..removeWhere((_, v) => v == null);
    final url = Uri.parse(
      '$_baseUrl$_apiPrefix/topics',
    ).replace(queryParameters: queryParams);

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.get(url, headers: headers).timeout(timeout),
      ),
    );

    if (response.statusCode == 200) {
      return Topic.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    } else {
      throw ApiException('Failed to get topic', response.statusCode);
    }
  }

  Future<void> manageTopic(
    String topicId,
    TopicAction action, {
    String? idempotencyKey,
  }) async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/topics/$topicId');
    final headers = await _getHeaders();
    if (idempotencyKey != null) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    final body = jsonEncode({'action': action.name});

    final response = await _breaker.execute(
      () => http.post(url, headers: headers, body: body).timeout(timeout),
    );

    if (response.statusCode != 200) {
      throw ApiException('Failed to manage topic', response.statusCode);
    }
  }

  Future<void> deleteTopic(String topicId) async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/topics/$topicId');

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.delete(url, headers: headers).timeout(timeout),
      ),
    );

    if (response.statusCode != 204) {
      throw ApiException('Failed to delete topic', response.statusCode);
    }
  }

  Future<DueTopics> getDueTopics() async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/topics/?view=due');

    final response = await _breaker.execute(
      () async => http.get(url, headers: await _getHeaders()).timeout(timeout),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return DueTopics.fromJson(data as Map<String, dynamic>);
    } else {
      throw ApiException('Failed to get due topics', response.statusCode);
    }
  }

  Future<List<Topic>> getPopularTopics({int limit = 10}) async {
    final queryParams = {'limit': limit.toString()};
    final url = Uri.parse(
      '$_baseUrl$_apiPrefix/topics/popular',
    ).replace(queryParameters: queryParams);

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.get(url, headers: headers).timeout(timeout),
      ),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as List;
      return data
          .map((item) => Topic.fromJson(item as Map<String, dynamic>))
          .toList();
    } else {
      throw ApiException('Failed to get popular topics', response.statusCode);
    }
  }

  Future<void> generateQuestions(String topicId) async {
    final url = Uri.parse(
      '$_baseUrl$_apiPrefix/topics/$topicId/generate-questions',
    );
    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.post(url, headers: headers).timeout(timeout),
      ),
    );
    if (response.statusCode != 200) {
      throw ApiException('Failed to generate questions', response.statusCode);
    }
  }

  // --- Question Management Endpoints ---

  Future<List<Question>> getTopicQuestions(String topicId) async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/topics/$topicId/questions');

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.get(url, headers: headers).timeout(timeout),
      ),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as List;
      return data
          .map((item) => Question.fromJson(item as Map<String, dynamic>))
          .toList();
    } else {
      throw ApiException('Failed to get topic questions', response.statusCode);
    }
  }

  Future<List<Question>> createQuestions(String topicId, List<CreateQuestionRequest> questions) async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/topics/$topicId/questions');
    final body = jsonEncode(CreateQuestionsRequest(questions: questions).toJson());

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.post(url, headers: headers, body: body).timeout(timeout),
      ),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as List;
      return data
          .map((item) => Question.fromJson(item as Map<String, dynamic>))
          .toList();
    } else {
      throw ApiException('Failed to create questions', response.statusCode);
    }
  }

  Future<void> deleteQuestion(String topicId, String questionId) async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/topics/$topicId/questions/$questionId');

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.delete(url, headers: headers).timeout(timeout),
      ),
    );

    if (response.statusCode != 204) {
      throw ApiException('Failed to delete question', response.statusCode);
    }
  }

  Future<Question> updateQuestion(String topicId, String questionId, UpdateQuestionRequest question) async {
    final url = Uri.parse('$_baseUrl$_apiPrefix/topics/$topicId/questions/$questionId');
    final body = jsonEncode(question.toJson());

    final response = await _breaker.execute(
      () => _makeRequestWithRetry(
        (headers) => http.put(url, headers: headers, body: body).timeout(timeout),
      ),
    );

    if (response.statusCode == 200) {
      return Question.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    } else {
      throw ApiException('Failed to update question', response.statusCode);
    }
  }
}
