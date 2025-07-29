import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../screens/chat_screen.dart';

class DueTopicsSelectionWidget extends StatefulWidget {
  final List<dynamic> dueTasks;
  final String? selectedTopicId;
  final bool isLoadingDueTasks;
  final List<dynamic> existingTopics;
  final bool isLoadingExistingTopics;
  final VoidCallback onBackPressed;
  final VoidCallback onStartSession;
  final Function(String) onTopicSelected;
  final Function(String) onExistingTopicSelected;

  const DueTopicsSelectionWidget({
    super.key,
    required this.dueTasks,
    required this.selectedTopicId,
    required this.isLoadingDueTasks,
    required this.existingTopics,
    required this.isLoadingExistingTopics,
    required this.onBackPressed,
    required this.onStartSession,
    required this.onTopicSelected,
    required this.onExistingTopicSelected,
  });

  @override
  State<DueTopicsSelectionWidget> createState() =>
      _DueTopicsSelectionWidgetState();
}

class _DueTopicsSelectionWidgetState extends State<DueTopicsSelectionWidget> {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      children: [
        // Header
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            border: Border(
              bottom: BorderSide(
                color: theme.colorScheme.outline.withValues(alpha: 0.2),
              ),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  IconButton(
                    onPressed: widget.onBackPressed,
                    icon: const Icon(Icons.arrow_back),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Select Topic to Review',
                          style: theme.textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Choose a topic you\'d like to review today',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: theme.colorScheme.onSurface.withValues(
                              alpha: 0.7,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Content with tabs
        Expanded(
          child: DefaultTabController(
            length: 2,
            child: Column(
              children: [
                TabBar(
                  tabs: const [
                    Tab(text: 'Due Reviews'),
                    Tab(text: 'Existing Topics'),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    children: [
                      // Due Reviews Tab
                      widget.isLoadingDueTasks
                          ? const Center(child: CircularProgressIndicator())
                          : widget.dueTasks.isEmpty
                          ? _buildNoDueTasksMessage()
                          : _buildDueTasksList(),
                      // Existing Topics Tab
                      widget.isLoadingExistingTopics
                          ? const Center(child: CircularProgressIndicator())
                          : _buildExistingTopicsList(),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),

        // Bottom action bar
        if (widget.dueTasks.isNotEmpty)
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              border: Border(
                top: BorderSide(
                  color: theme.colorScheme.outline.withValues(alpha: 0.2),
                ),
              ),
            ),
            child: Row(
              children: [
                Text(
                  widget.selectedTopicId != null
                      ? '1 topic selected'
                      : 'No topic selected',
                  style: theme.textTheme.bodyMedium,
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed:
                      widget.selectedTopicId == null
                          ? null
                          : widget.onStartSession,
                  child: const Text('Start Review Session'),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildNoDueTasksMessage() {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 64,
            color: theme.colorScheme.primary,
          ),
          const SizedBox(height: 16),
          Text(
            'All Caught Up!',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'You have no topics due for review today.\nGreat job staying on top of your learning!',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () {
              final chatProvider = Provider.of<ChatProvider>(
                context,
                listen: false,
              );
              chatProvider.setSessionState(SessionState.initial);
            },
            icon: const Icon(Icons.add),
            label: const Text('Start New Items Session'),
          ),
        ],
      ),
    );
  }

  Widget _buildDueTasksList() {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: widget.dueTasks.length,
      itemBuilder: (context, index) {
        final task = widget.dueTasks[index];
        final topicId = task['topic_id'] as String? ?? '';
        final topicName = task['topic_name'] as String? ?? 'Unknown Topic';
        final topic = task['topic'] as dynamic;
        final isSelected = widget.selectedTopicId == topicId;

        // Get border color based on review date (same logic as today's reviews)
        final borderColor = _getBorderColor(topic?.nextReviewAt);

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          shape: RoundedRectangleBorder(
            side: BorderSide(
              color:
                  isSelected
                      ? Theme.of(context).colorScheme.primary
                      : borderColor,
              width: isSelected ? 2.0 : 1.5,
            ),
            borderRadius: BorderRadius.circular(12),
          ),
          child: InkWell(
            onTap: () {
              widget.onTopicSelected(topicId);
            },
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          topicName,
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                      ),
                      if (isSelected)
                        Icon(
                          Icons.check_circle,
                          color: Theme.of(context).colorScheme.primary,
                          size: 24,
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (topic != null) ...[
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
                  ] else ...[
                    Text(
                      'Due for review',
                      style: TextStyle(
                        color: borderColor,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        );
      },
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

  String _formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return '${date.month}/${date.day}/${date.year}';
  }

  Color _getBorderColor(DateTime? nextReviewAt) {
    if (nextReviewAt == null) {
      return Colors.grey; // Default color for topics without a review date
    }

    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final reviewDay = DateTime(
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

  Widget _buildExistingTopicsList() {
    if (widget.existingTopics.isEmpty) {
      return const Center(child: Text('No existing topics found.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: widget.existingTopics.length,
      itemBuilder: (context, index) {
        final topic = widget.existingTopics[index];
        final topicName = topic['name'] as String? ?? 'Unknown Topic';
        final topicDescription = topic['description'] as String? ?? '';

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            title: Text(topicName),
            subtitle: Text(topicDescription),
            trailing: const Icon(Icons.arrow_forward_ios),
            onTap: () {
              widget.onExistingTopicSelected(topicName);
            },
          ),
        );
      },
    );
  }
}
