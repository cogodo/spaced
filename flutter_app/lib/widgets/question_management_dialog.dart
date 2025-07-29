import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/question.dart';
import '../services/logger_service.dart';
import '../providers/chat_provider.dart';
import 'question_list_widget.dart';
import 'question_input_widget.dart';

class QuestionManagementDialog extends StatefulWidget {
  final String topicId;
  final String topicName;
  final String topicDescription;

  const QuestionManagementDialog({
    super.key,
    required this.topicId,
    required this.topicName,
    required this.topicDescription,
  });

  @override
  State<QuestionManagementDialog> createState() =>
      _QuestionManagementDialogState();
}

class _QuestionManagementDialogState extends State<QuestionManagementDialog>
    with SingleTickerProviderStateMixin {
  final _logger = getLogger('QuestionManagementDialog');

  List<Question> _questions = [];
  bool _isLoadingQuestions = true;
  bool _isLoadingOperations = false;
  String? _errorMessage;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadQuestions();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadQuestions() async {
    setState(() {
      _isLoadingQuestions = true;
      _errorMessage = null;
    });

    try {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      final questions = await chatProvider.apiService.getTopicQuestions(
        widget.topicId,
      );
      setState(() {
        _questions = questions;
        _isLoadingQuestions = false;
      });
    } catch (e) {
      _logger.severe('Error loading questions: $e');
      setState(() {
        _errorMessage = 'Failed to load questions: ${e.toString()}';
        _isLoadingQuestions = false;
      });
    }
  }

  Future<void> _addQuestions(List<CreateQuestionRequest> questions) async {
    // Show confirmation for bulk operations
    if (questions.length > 5) {
      final confirmed = await showDialog<bool>(
        context: context,
        builder:
            (context) => AlertDialog(
              title: const Text('Add Multiple Questions'),
              content: Text(
                'You are about to add ${questions.length} questions. Do you want to continue?',
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(false),
                  child: const Text('Cancel'),
                ),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(true),
                  child: const Text('Add Questions'),
                ),
              ],
            ),
      );

      if (confirmed != true || !mounted) return;
    }

    setState(() {
      _isLoadingOperations = true;
      _errorMessage = null;
    });

    try {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      final createdQuestions = await chatProvider.apiService.createQuestions(
        widget.topicId,
        questions,
      );
      setState(() {
        _questions.addAll(createdQuestions);
        _isLoadingOperations = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Successfully added ${questions.length} question${questions.length == 1 ? '' : 's'}',
            ),
            backgroundColor: Colors.green,
            action: SnackBarAction(label: 'Refresh', onPressed: _loadQuestions),
          ),
        );
      }
    } catch (e) {
      _logger.severe('Error adding questions: $e');
      setState(() {
        _errorMessage = 'Failed to add questions: ${e.toString()}';
        _isLoadingOperations = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to add questions: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _deleteQuestion(String questionId) async {
    // Show confirmation dialog
    final confirmed = await showDialog<bool>(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Delete Question'),
            content: const Text(
              'Are you sure you want to delete this question? This action cannot be undone.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Cancel'),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).pop(true),
                style: TextButton.styleFrom(foregroundColor: Colors.red),
                child: const Text('Delete'),
              ),
            ],
          ),
    );

    if (confirmed != true || !mounted) return;

    setState(() {
      _isLoadingOperations = true;
      _errorMessage = null;
    });

    try {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      await chatProvider.apiService.deleteQuestion(widget.topicId, questionId);
      setState(() {
        _questions.removeWhere((q) => q.id == questionId);
        _isLoadingOperations = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Question deleted successfully'),
            backgroundColor: Colors.green,
            action: SnackBarAction(
              label: 'Undo',
              onPressed: () {
                // Note: In a real implementation, you might want to implement undo functionality
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Undo functionality not implemented yet'),
                    duration: Duration(seconds: 2),
                  ),
                );
              },
            ),
          ),
        );
      }
    } catch (e) {
      _logger.severe('Error deleting question: $e');
      setState(() {
        _errorMessage = 'Failed to delete question: ${e.toString()}';
        _isLoadingOperations = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to delete question: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDesktop = MediaQuery.of(context).size.width > 800;

    return Dialog(
      child: Container(
        width: isDesktop ? 1000 : double.infinity,
        height: isDesktop ? 700 : MediaQuery.of(context).size.height * 0.9,
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Manage Questions',
                        style: theme.textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        widget.topicName,
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: theme.colorScheme.primary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      if (widget.topicDescription.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          widget.topicDescription,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(
                              alpha: 0.7,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Error message
            if (_errorMessage != null) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.red.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.error_outline,
                      color: Colors.red,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: Colors.red,
                        ),
                      ),
                    ),
                    IconButton(
                      onPressed: () => setState(() => _errorMessage = null),
                      icon: const Icon(
                        Icons.close,
                        color: Colors.red,
                        size: 20,
                      ),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Tabs
            Container(
              decoration: BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: theme.colorScheme.outline.withValues(alpha: 0.2),
                  ),
                ),
              ),
              child: TabBar(
                controller: _tabController,
                tabs: [
                  Tab(
                    icon: const Icon(Icons.quiz_outlined),
                    text: 'Questions (${_questions.length})',
                  ),
                  Tab(
                    icon: const Icon(Icons.add_circle_outline),
                    text: 'Add Questions',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Tab content
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // Questions tab
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            'Manage Questions',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const Spacer(),
                          IconButton(
                            onPressed: _loadQuestions,
                            icon: const Icon(Icons.refresh),
                            tooltip: 'Refresh questions',
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Expanded(
                        child: Stack(
                          children: [
                            QuestionListWidget(
                              questions: _questions,
                              onDeleteQuestion: _deleteQuestion,
                              isLoading: _isLoadingQuestions,
                              showDeleteButtons: !_isLoadingOperations,
                            ),
                            if (_isLoadingOperations)
                              Container(
                                color: Colors.black.withValues(alpha: 0.3),
                                child: const Center(
                                  child: Card(
                                    child: Padding(
                                      padding: EdgeInsets.all(16.0),
                                      child: Column(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          CircularProgressIndicator(),
                                          SizedBox(height: 8),
                                          Text('Processing...'),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  // Add questions tab
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Add New Questions',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Expanded(
                        child: QuestionInputWidget(
                          onQuestionsSubmitted: _addQuestions,
                          isLoading: _isLoadingOperations,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
