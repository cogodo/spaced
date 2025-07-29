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

  void _submitTopics() {
    final text = _topicController.text.trim();
    if (text.isEmpty) return;

    // Only allow single topic
    widget.onTopicsSelected([text]);
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
                hintText: 'e.g., Machine Learning, Spanish Grammar, World History...',
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
                child: const Text('Start Learning Session'),
              ),
            ),
          ],
        );
      },
    );
  }


}
