import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../services/session_api.dart';

class TopicSelectionWidget extends StatefulWidget {
  final Function(List<String> topics) onTopicsSelected;
  final Function(PopularTopic topic)? onPopularTopicSelected;

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
  late Future<List<UserTopic>> _userTopicsFuture;

  @override
  void initState() {
    super.initState();
    _userTopicsFuture =
        SessionApi(baseUrl: 'http://localhost:8000').getAllTopics();
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
    final chatProvider = Provider.of<ChatProvider>(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 24),
        Text(
          'Or select an existing topic:',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Expanded(
          child: FutureBuilder<List<UserTopic>>(
            future: _userTopicsFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              } else if (snapshot.hasError) {
                return Center(child: Text('Error: ${snapshot.error}'));
              } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                return const Center(child: Text('No topics found.'));
              }

              final topics = snapshot.data!;
              return ListView.builder(
                itemCount: topics.length,
                itemBuilder: (context, index) {
                  final topic = topics[index];
                  return Card(
                    child: ListTile(
                      title: Text(topic.name),
                      onTap: () {
                        widget.onTopicsSelected([topic.name]);
                      },
                    ),
                  );
                },
              );
            },
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _topicController,
          decoration: InputDecoration(
            hintText: 'Or enter new topics...',
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
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
  }
}
