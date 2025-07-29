import 'package:flutter/material.dart';
import '../services/session_api.dart';

class AnimatedTopicCard extends StatefulWidget {
  final Topic topic;
  final Color borderColor;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const AnimatedTopicCard({
    super.key,
    required this.topic,
    required this.borderColor,
    required this.onTap,
    required this.onDelete,
  });

  @override
  State<AnimatedTopicCard> createState() => _AnimatedTopicCardState();
}

class _AnimatedTopicCardState extends State<AnimatedTopicCard> {
  bool _isHovered = false;

  String _formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return '${date.month}/${date.day}/${date.year}';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color:
                _isHovered
                    ? theme.colorScheme.surfaceContainerHighest.withValues(
                      alpha: 0.3,
                    )
                    : theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color:
                  _isHovered
                      ? theme.colorScheme.primary.withValues(alpha: 0.7)
                      : widget.borderColor,
              width: _isHovered ? 2.0 : 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color:
                    _isHovered
                        ? theme.colorScheme.primary.withValues(alpha: 0.2)
                        : Colors.black.withValues(alpha: 0.1),
                blurRadius: _isHovered ? 8.0 : 4.0,
                offset: Offset(0, _isHovered ? 4.0 : 2.0),
              ),
            ],
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
                        widget.topic.name,
                        style: theme.textTheme.titleLarge,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete, color: Colors.red),
                      onPressed: widget.onDelete,
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildInfoColumn(
                      'Last Reviewed',
                      _formatDate(widget.topic.lastReviewedAt),
                    ),
                    _buildInfoColumn(
                      'Next Review',
                      _formatDate(widget.topic.nextReviewAt),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(
                      Icons.quiz_outlined,
                      size: 16,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Tap to manage questions',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withValues(
                          alpha: 0.6,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
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
