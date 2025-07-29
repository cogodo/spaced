import 'package:flutter/material.dart';
import '../models/question.dart';

class QuestionListWidget extends StatelessWidget {
  final List<Question> questions;
  final Function(String) onDeleteQuestion;
  final bool isLoading;
  final bool showDeleteButtons;

  const QuestionListWidget({
    super.key,
    required this.questions,
    required this.onDeleteQuestion,
    this.isLoading = false,
    this.showDeleteButtons = true,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (isLoading) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24.0),
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (questions.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.quiz_outlined,
                size: 64,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
              ),
              const SizedBox(height: 16),
              Text(
                'No questions yet',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Add some questions to get started!',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return ListView.builder(
      shrinkWrap: true,
      physics: const AlwaysScrollableScrollPhysics(),
      itemCount: questions.length,
      itemBuilder: (context, index) {
        final question = questions[index];
        return _QuestionCard(
          question: question,
          onDelete:
              showDeleteButtons ? () => onDeleteQuestion(question.id) : null,
        );
      },
    );
  }
}

class _QuestionCard extends StatelessWidget {
  final Question question;
  final VoidCallback? onDelete;

  const _QuestionCard({required this.question, this.onDelete});

  String _getTypeDisplayName(String type) {
    switch (type) {
      case 'multiple_choice':
        return 'Multiple Choice';
      case 'short_answer':
        return 'Short Answer';
      case 'explanation':
        return 'Explanation';
      default:
        return type.replaceAll('_', ' ').toUpperCase();
    }
  }

  Color _getTypeColor(String type, ThemeData theme) {
    switch (type) {
      case 'multiple_choice':
        return Colors.blue;
      case 'short_answer':
        return Colors.green;
      case 'explanation':
        return Colors.orange;
      default:
        return theme.colorScheme.primary;
    }
  }

  Color _getDifficultyColor(int difficulty, ThemeData theme) {
    switch (difficulty) {
      case 1:
        return Colors.green;
      case 2:
        return Colors.orange;
      case 3:
        return Colors.red;
      default:
        return theme.colorScheme.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 0),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(question.text, style: theme.textTheme.bodyLarge),
                ),
                if (onDelete != null) ...[
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: onDelete,
                    icon: const Icon(Icons.delete_outline, color: Colors.red),
                    tooltip: 'Delete question',
                    iconSize: 20,
                  ),
                ],
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                // Question type chip
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: _getTypeColor(
                      question.type,
                      theme,
                    ).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _getTypeColor(
                        question.type,
                        theme,
                      ).withValues(alpha: 0.3),
                    ),
                  ),
                  child: Text(
                    _getTypeDisplayName(question.type),
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: _getTypeColor(question.type, theme),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // Difficulty chip
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: _getDifficultyColor(
                      question.difficulty,
                      theme,
                    ).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: _getDifficultyColor(
                        question.difficulty,
                        theme,
                      ).withValues(alpha: 0.3),
                    ),
                  ),
                  child: Text(
                    'Level ${question.difficulty}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: _getDifficultyColor(question.difficulty, theme),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const Spacer(),
                // Generated by indicator
                if (question.metadata['generated_by'] != null)
                  Icon(
                    question.metadata['generated_by'] == 'user'
                        ? Icons.person_outline
                        : Icons.auto_awesome_outlined,
                    size: 16,
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
