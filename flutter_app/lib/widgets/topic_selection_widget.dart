import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../services/session_api.dart'; // Keep for Topic model

class TopicSelectionWidget extends StatefulWidget {
  final Function(List<String>) onTopicsSelected;
  final Function(Topic)? onPopularTopicSelected;

  const TopicSelectionWidget({
    super.key,
    required this.onTopicsSelected,
    this.onPopularTopicSelected,
  });

  @override
  State<TopicSelectionWidget> createState() => _TopicSelectionWidgetState();
}

class _TopicSelectionWidgetState extends State<TopicSelectionWidget> {
  final TextEditingController _topicController = TextEditingController();

  @override
  void initState() {
    super.initState();
  }

  Future<void> _submitTopics() async {
    final text = _topicController.text.trim();
    if (text.isEmpty) return;

    final chatProvider = context.read<ChatProvider>();
    try {
      // Step 1: Generate questions first
      await chatProvider.apiService.generateQuestionsForName(text);

      if (!mounted) return;

      // Step 2: Prompt to start session
      final shouldStart = await showDialog<bool>(
        context: context,
        builder:
            (ctx) => AlertDialog(
              title: const Text('Questions generated!'),
              content: const Text('Start learning session now?'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(ctx).pop(false),
                  child: const Text('Not now'),
                ),
                ElevatedButton(
                  onPressed: () => Navigator.of(ctx).pop(true),
                  child: const Text('Start session'),
                ),
              ],
            ),
      );

      if (shouldStart == true) {
        // Start session using the original name (server will resolve to topic)
        widget.onTopicsSelected([text]);
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to generate questions: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<ChatProvider>(
      builder: (context, chatProvider, child) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 24),
            Text(
              'Enter a new topic to learn:',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _topicController,
              decoration: InputDecoration(
                hintText:
                    'e.g., Machine Learning, Spanish Grammar, World History...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onSubmitted: (value) => _submitTopics(),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _submitTopics,
                child: const Text('Generate Questions'),
              ),
            ),
          ],
        );
      },
    );
  }
}
