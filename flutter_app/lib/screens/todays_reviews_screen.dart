import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../routing/route_constants.dart';

import '../utils/time_provider.dart';

class TodaysReviewsScreen extends StatefulWidget {
  const TodaysReviewsScreen({super.key});

  @override
  State<TodaysReviewsScreen> createState() => _TodaysReviewsScreenState();
}

class _TodaysReviewsScreenState extends State<TodaysReviewsScreen> {
  @override
  void initState() {
    super.initState();
    // Fetch initial data when the screen loads
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
      return Colors.yellow.shade800; // Due today or overdue by 1-2 days
    } else {
      return Colors.green.shade700; // Upcoming
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Consumer<ChatProvider>(
          builder: (context, chatProvider, child) {
            final lastReviewed = chatProvider.dueTopics?.lastReviewedAt;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("Today's Reviews"),
                if (lastReviewed != null)
                  Text(
                    'Last reviewed: ${_formatDate(lastReviewed)}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
              ],
            );
          },
        ),
      ),
      body: Consumer<ChatProvider>(
        builder: (context, chatProvider, child) {
          if (chatProvider.isLoadingDueTopics &&
              chatProvider.dueTopics == null) {
            return const Center(child: CircularProgressIndicator());
          } else if (chatProvider.dueTopics == null) {
            return const Center(child: Text('Could not load review topics.'));
          }

          final dueTopics = chatProvider.dueTopics!;
          final recentlyReviewed = chatProvider.recentlyReviewedTopicIds;

          // Perform client-side categorization based on local time
          final now = SystemTimeProvider().nowUtc().toLocal();
          final today = DateTime(now.year, now.month, now.day);

          final allTopics =
              dueTopics.topics.where((topic) {
                if (recentlyReviewed.contains(topic.id)) {
                  return false; // Filter out recently reviewed
                }
                if (topic.nextReviewAt == null) {
                  return false; // Filter out topics with no review date
                }
                // Compare using the local timezone
                final reviewDateLocal = topic.nextReviewAt!.toLocal();
                final reviewDay = DateTime(
                  reviewDateLocal.year,
                  reviewDateLocal.month,
                  reviewDateLocal.day,
                );
                return reviewDay.isBefore(today) ||
                    reviewDay.isAtSameMomentAs(today);
              }).toList();

          if (allTopics.isEmpty) {
            return RefreshIndicator(
              onRefresh: () => chatProvider.fetchDueTopics(),
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                child: Container(
                  height: MediaQuery.of(context).size.height * 0.8,
                  alignment: Alignment.center,
                  child: const Text('No reviews due today!'),
                ),
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => chatProvider.fetchDueTopics(),
            child: ListView.builder(
              itemCount: allTopics.length,
              itemBuilder: (context, index) {
                final topic = allTopics[index];
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
                        Text(
                          topic.name,
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          topic.isOverdue
                              ? 'Overdue for review'
                              : 'Due for review today',
                          style: TextStyle(
                            color: borderColor,
                            fontWeight: FontWeight.bold,
                          ),
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
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () {
                            Provider.of<ChatProvider>(
                              context,
                              listen: false,
                            ).startNewSession([topic.name]);
                            context.go(Routes.appChat);
                          },
                          child: const Text('Start Review'),
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
