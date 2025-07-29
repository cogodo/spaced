

/// Model for a question
class Question {
  final String id;
  final String topicId;
  final String text;
  final String type;
  final int difficulty;
  final Map<String, dynamic> metadata;

  Question({
    required this.id,
    required this.topicId,
    required this.text,
    required this.type,
    required this.difficulty,
    required this.metadata,
  });

  factory Question.fromJson(Map<String, dynamic> json) {
    return Question(
      id: json['id'] as String,
      topicId: json['topicId'] as String,
      text: json['text'] as String,
      type: json['type'] as String,
      difficulty: json['difficulty'] as int,
      metadata: json['metadata'] as Map<String, dynamic>? ?? {},
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'topicId': topicId,
      'text': text,
      'type': type,
      'difficulty': difficulty,
      'metadata': metadata,
    };
  }

  @override
  String toString() {
    return 'Question(id: $id, topicId: $topicId, text: $text, type: $type, difficulty: $difficulty)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Question &&
        other.id == id &&
        other.topicId == topicId &&
        other.text == text &&
        other.type == type &&
        other.difficulty == difficulty;
  }

  @override
  int get hashCode {
    return Object.hash(id, topicId, text, type, difficulty);
  }
}

/// Model for creating a single question
class CreateQuestionRequest {
  final String text;
  final String type;
  final int difficulty;

  CreateQuestionRequest({
    required this.text,
    required this.type,
    required this.difficulty,
  });

  Map<String, dynamic> toJson() {
    return {'text': text, 'type': type, 'difficulty': difficulty};
  }

  @override
  String toString() {
    return 'CreateQuestionRequest(text: $text, type: $type, difficulty: $difficulty)';
  }
}

/// Model for updating a question
class UpdateQuestionRequest {
  final String text;
  final String type;
  final int difficulty;

  UpdateQuestionRequest({
    required this.text,
    required this.type,
    required this.difficulty,
  });

  Map<String, dynamic> toJson() {
    return {'text': text, 'type': type, 'difficulty': difficulty};
  }

  @override
  String toString() {
    return 'UpdateQuestionRequest(text: $text, type: $type, difficulty: $difficulty)';
  }
}

/// Model for creating multiple questions
class CreateQuestionsRequest {
  final List<CreateQuestionRequest> questions;

  CreateQuestionsRequest({required this.questions});

  Map<String, dynamic> toJson() {
    return {'questions': questions.map((q) => q.toJson()).toList()};
  }

  @override
  String toString() {
    return 'CreateQuestionsRequest(questions: $questions)';
  }
}
