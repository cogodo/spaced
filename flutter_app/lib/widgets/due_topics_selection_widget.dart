import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../screens/chat_screen.dart';

class DueTopicsSelectionWidget extends StatefulWidget {
  final List<dynamic> dueTasks;
  final Set<String> selectedTopics;
  final bool isLoadingDueTasks;
  final VoidCallback onBackPressed;
  final VoidCallback onStartSession;
  final Function(String) onTopicToggled;

  const DueTopicsSelectionWidget({
    super.key,
    required this.dueTasks,
    required this.selectedTopics,
    required this.isLoadingDueTasks,
    required this.onBackPressed,
    required this.onStartSession,
    required this.onTopicToggled,
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
                          'Select Topics to Review',
                          style: theme.textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Choose which topics you\'d like to review today',
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

        // Content
        Expanded(
          child:
              widget.isLoadingDueTasks
                  ? const Center(child: CircularProgressIndicator())
                  : widget.dueTasks.isEmpty
                  ? _buildNoDueTasksMessage()
                  : _buildDueTasksList(),
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
                  '${widget.selectedTopics.length} topic${widget.selectedTopics.length == 1 ? '' : 's'} selected',
                  style: theme.textTheme.bodyMedium,
                ),
                const Spacer(),
                ElevatedButton(
                  onPressed:
                      widget.selectedTopics.isEmpty
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
        final isSelected = widget.selectedTopics.contains(topicId);

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: CheckboxListTile(
            title: Text(topicName),
            subtitle: Text('Due for review'),
            value: isSelected,
            onChanged: (value) {
              widget.onTopicToggled(topicId);
            },
            controlAffinity: ListTileControlAffinity.leading,
          ),
        );
      },
    );
  }
}
