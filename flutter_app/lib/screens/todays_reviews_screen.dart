import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../services/session_api.dart';

class TodaysReviewsScreen extends StatefulWidget {
  const TodaysReviewsScreen({super.key});

  @override
  State<TodaysReviewsScreen> createState() => _TodaysReviewsScreenState();
}

class _TodaysReviewsScreenState extends State<TodaysReviewsScreen> {
  late Future<List<UserTopic>> _dueTopicsFuture;

  @override
  void initState() {
    super.initState();
    _dueTopicsFuture = _fetchDueTopics();
  }

  Future<List<UserTopic>> _fetchDueTopics() async {
    final topics =
        await SessionApi(baseUrl: 'http://localhost:8000').getAllTopics();
    return topics.where((topic) => topic.isDue || topic.isOverdue).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Today's Reviews")),
      body: FutureBuilder<List<UserTopic>>(
        future: _dueTopicsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text('No reviews due today!'));
          }

          final dueTopics = snapshot.data!;
          return ListView.builder(
            itemCount: dueTopics.length,
            itemBuilder: (context, index) {
              final topic = dueTopics[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        topic.name,
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _buildInfoColumn(
                            'Ease',
                            topic.fsrsParams['ease'].toStringAsFixed(2),
                          ),
                          _buildInfoColumn(
                            'Interval',
                            '${topic.fsrsParams['interval']} days',
                          ),
                          _buildInfoColumn(
                            'Repetitions',
                            topic.fsrsParams['repetition'].toString(),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () async {
                          final chatProvider = Provider.of<ChatProvider>(
                            context,
                            listen: false,
                          );
                          await chatProvider.startNewSession(
                            sessionType: 'due_items',
                            selectedTopics: [topic.name],
                          );
                          if (mounted) context.go('/app/chat');
                        },
                        child: const Text('Start Review'),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildInfoColumn(String title, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: Theme.of(context).textTheme.bodySmall),
        Text(value, style: Theme.of(context).textTheme.titleMedium),
      ],
    );
  }
}
