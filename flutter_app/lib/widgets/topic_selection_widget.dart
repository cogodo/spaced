import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../services/session_api.dart'; // Keep for Topic model

class TopicSelectionWidget extends StatefulWidget {
  final Function(List<String> topics) onTopicsSelected;

  const TopicSelectionWidget({super.key, required this.onTopicsSelected});

  @override
  State<TopicSelectionWidget> createState() => _TopicSelectionWidgetState();
}

class _TopicSelectionWidgetState extends State<TopicSelectionWidget> {
  final TextEditingController _topicController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Use addPostFrameCallback to avoid calling provider during build
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final chatProvider = Provider.of<ChatProvider>(context, listen: false);
      if (chatProvider.popularTopics.isEmpty) {
        chatProvider.loadPopularTopics();
      }
    });
  }

  void _submitTopics() {
    final text = _topicController.text.trim();
    if (text.isEmpty) return;

    final topics =
        text
            .split(',')
            .map((t) => t.trim())
            .where((t) => t.isNotEmpty)
            .toList();
    widget.onTopicsSelected(topics);
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
              'Select an existing topic:',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Expanded(child: _buildTopicList(chatProvider)),
            const SizedBox(height: 16),
            TextField(
              controller: _topicController,
              decoration: InputDecoration(
                hintText: 'Or enter new topics (comma-separated)...',
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

  Widget _buildTopicList(ChatProvider chatProvider) {
    if (chatProvider.isLoadingPopularTopics) {
      return const Center(child: CircularProgressIndicator());
    }

    if (chatProvider.popularTopics.isEmpty) {
      return const Center(child: Text('No topics found. Create a new one!'));
    }

    final topics = chatProvider.popularTopics;
    return ListView.builder(
      itemCount: topics.length,
      itemBuilder: (context, index) {
        final topic = topics[index];
        return Card(
          child: ListTile(
            title: Text(topic.name),
            subtitle: Text(topic.description),
            onTap: () {
              widget.onTopicsSelected([topic.name]);
            },
          ),
        );
      },
    );
  }
}
