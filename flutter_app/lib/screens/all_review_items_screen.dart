import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../services/session_api.dart';
import '../utils/time_provider.dart';

class AllReviewItemsScreen extends StatefulWidget {
  const AllReviewItemsScreen({super.key});

  @override
  State<AllReviewItemsScreen> createState() => _AllReviewItemsScreenState();
}

class _AllReviewItemsScreenState extends State<AllReviewItemsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<ChatProvider>(context, listen: false).fetchDueTopics();
    });
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return DateFormat.yMMMd().format(date);
  }

  Color _getBorderColor(DateTime? nextReviewAt) {
    if (nextReviewAt == null) {
      return Colors.grey; // Default color for topics without a review date
    }

    final now = SystemTimeProvider().nowUtc();
    final today = DateTime.utc(now.year, now.month, now.day);
    final reviewDay = DateTime.utc(
      nextReviewAt.year,
      nextReviewAt.month,
      nextReviewAt.day,
    );
    final difference = today.difference(reviewDay).inDays;

    if (difference > 2) {
      return Colors.red.shade700; // Overdue by more than 2 days
    } else if (difference >= 0) {
      return const Color.fromARGB(255, 241, 237, 16); // Due today or overdue by 1-2 days
    } else {
      return Colors.green.shade700; // Upcoming
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('All Review Items')),
      body: Consumer<ChatProvider>(
        builder: (context, chatProvider, child) {
          if (chatProvider.isLoadingDueTopics &&
              chatProvider.dueTopics == null) {
            return const Center(child: CircularProgressIndicator());
          } else if (chatProvider.dueTopics == null ||
              chatProvider.dueTopics!.topics.isEmpty) {
            return const Center(child: Text('No topics found.'));
          }

          final topics = chatProvider.dueTopics!.topics;
          return RefreshIndicator(
            onRefresh: () => chatProvider.fetchDueTopics(),
            child: ListView.builder(
              itemCount: topics.length,
              itemBuilder: (context, index) {
                final topic = topics[index];
                final borderColor = _getBorderColor(topic.nextReviewAt);
                return Card(
                  margin: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  shape: RoundedRectangleBorder(
                    side: BorderSide(color: borderColor, width: 1.5),
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
                                await Provider.of<ChatProvider>(
                                  context,
                                  listen: false,
                                ).deleteTopic(topic.id);
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
            ),
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
