import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../utils/time_provider.dart';
import '../widgets/question_management_dialog.dart';
import '../widgets/animated_topic_card.dart';
import '../services/session_api.dart';

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
      return const Color.fromARGB(
        255,
        241,
        237,
        16,
      ); // Due today or overdue by 1-2 days
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
                return AnimatedTopicCard(
                  topic: topic,
                  borderColor: borderColor,
                  onTap: () => _showQuestionManagementDialog(context, topic),
                  onDelete: () async {
                    await Provider.of<ChatProvider>(
                      context,
                      listen: false,
                    ).deleteTopic(topic.id);
                  },
                );
              },
            ),
          );
        },
      ),
    );
  }

  void _showQuestionManagementDialog(BuildContext context, Topic topic) {
    showDialog(
      context: context,
      builder:
          (context) => QuestionManagementDialog(
            topicId: topic.id,
            topicName: topic.name,
            topicDescription: topic.description,
          ),
    );
  }
}
