import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/session_api.dart';

class AllReviewItemsScreen extends StatefulWidget {
  const AllReviewItemsScreen({super.key});

  @override
  State<AllReviewItemsScreen> createState() => _AllReviewItemsScreenState();
}

class _AllReviewItemsScreenState extends State<AllReviewItemsScreen> {
  late Future<List<UserTopic>> _topicsFuture;

  @override
  void initState() {
    super.initState();
    _topicsFuture = SessionApi(baseUrl: 'http://localhost:8000').getAllTopics();
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return DateFormat.yMMMd().format(date);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('All Review Items')),
      body: FutureBuilder<List<UserTopic>>(
        future: _topicsFuture,
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
              final isDue = topic.isDue || topic.isOverdue;
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                shape: RoundedRectangleBorder(
                  side: BorderSide(
                    color: isDue ? Colors.orange : Colors.green,
                    width: 1.5,
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              topic.name,
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () async {
                              await SessionApi(
                                baseUrl: 'http://localhost:8000',
                              ).deleteTopic(topic.id);
                              setState(() {
                                _topicsFuture =
                                    SessionApi(
                                      baseUrl: 'http://localhost:8000',
                                    ).getAllTopics();
                              });
                            },
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _buildInfoColumn(
                            'Last Reviewed',
                            _formatDate(topic.lastReviewedAt),
                          ),
                          _buildInfoColumn(
                            'Next Review',
                            _formatDate(topic.nextReviewAt),
                          ),
                        ],
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
