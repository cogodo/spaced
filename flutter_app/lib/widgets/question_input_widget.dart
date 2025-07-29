import 'package:flutter/material.dart';
import '../models/question.dart';

class QuestionInputWidget extends StatefulWidget {
  final Function(List<CreateQuestionRequest>) onQuestionsSubmitted;
  final bool isLoading;

  const QuestionInputWidget({
    super.key,
    required this.onQuestionsSubmitted,
    this.isLoading = false,
  });

  @override
  State<QuestionInputWidget> createState() => _QuestionInputWidgetState();
}

class _QuestionInputWidgetState extends State<QuestionInputWidget> {
  final TextEditingController _singleQuestionController =
      TextEditingController();
  final TextEditingController _bulkQuestionsController =
      TextEditingController();
  String _selectedType = 'short_answer';
  int _selectedDifficulty = 1;
  bool _isBulkMode = false;

  final List<String> _questionTypes = [
    'multiple_choice',
    'short_answer',
    'explanation',
  ];

  final List<int> _difficulties = [1, 2, 3];

  @override
  void dispose() {
    _singleQuestionController.dispose();
    _bulkQuestionsController.dispose();
    super.dispose();
  }

  void _submitSingleQuestion() {
    final text = _singleQuestionController.text.trim();
    if (text.isEmpty) return;

    final question = CreateQuestionRequest(
      text: text,
      type: _selectedType,
      difficulty: _selectedDifficulty,
    );

    widget.onQuestionsSubmitted([question]);
    _singleQuestionController.clear();
  }

  void _submitBulkQuestions() {
    final text = _bulkQuestionsController.text.trim();
    if (text.isEmpty) return;

    final lines =
        text.split('\n').where((line) => line.trim().isNotEmpty).toList();
    final questions =
        lines
            .map(
              (line) => CreateQuestionRequest(
                text: line.trim(),
                type: _selectedType,
                difficulty: _selectedDifficulty,
              ),
            )
            .toList();

    widget.onQuestionsSubmitted(questions);
    _bulkQuestionsController.clear();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Mode toggle
        Row(
          children: [
            Expanded(
              child: ChoiceChip(
                label: const Text('Single Question'),
                selected: !_isBulkMode,
                onSelected: (selected) {
                  setState(() {
                    _isBulkMode = !selected;
                  });
                },
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: ChoiceChip(
                label: const Text('Multiple Questions'),
                selected: _isBulkMode,
                onSelected: (selected) {
                  setState(() {
                    _isBulkMode = selected;
                  });
                },
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Question type and difficulty selection
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                initialValue: _selectedType,
                decoration: const InputDecoration(
                  labelText: 'Question Type',
                  border: OutlineInputBorder(),
                ),
                items:
                    _questionTypes.map((type) {
                      return DropdownMenuItem(
                        value: type,
                        child: Text(type.replaceAll('_', ' ').toUpperCase()),
                      );
                    }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      _selectedType = value;
                    });
                  }
                },
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: DropdownButtonFormField<int>(
                initialValue: _selectedDifficulty,
                decoration: const InputDecoration(
                  labelText: 'Difficulty',
                  border: OutlineInputBorder(),
                ),
                items:
                    _difficulties.map((difficulty) {
                      return DropdownMenuItem(
                        value: difficulty,
                        child: Text('Level $difficulty'),
                      );
                    }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      _selectedDifficulty = value;
                    });
                  }
                },
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Question input
        if (!_isBulkMode) ...[
          TextField(
            controller: _singleQuestionController,
            decoration: InputDecoration(
              labelText: 'Question Text',
              hintText: 'Enter your question here...',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            maxLines: 3,
            onSubmitted: (value) => _submitSingleQuestion(),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: widget.isLoading ? null : _submitSingleQuestion,
              child:
                  widget.isLoading
                      ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                      : const Text('Add Question'),
            ),
          ),
        ] else ...[
          TextField(
            controller: _bulkQuestionsController,
            decoration: InputDecoration(
              labelText: 'Questions (one per line)',
              hintText:
                  'Enter multiple questions, one per line...\n\nExample:\nWhat is the capital of France?\nWhat is 2 + 2?\nExplain photosynthesis.',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            maxLines: 6,
          ),
          const SizedBox(height: 8),
          Text(
            'Each line will be treated as a separate question with the selected type and difficulty.',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: widget.isLoading ? null : _submitBulkQuestions,
              child:
                  widget.isLoading
                      ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                      : const Text('Add Questions'),
            ),
          ),
        ],
      ],
    );
  }
}
