import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; // For date formatting

class AllReviewItemsScreen extends StatefulWidget {
  final List<dynamic> allTasks; // Changed from List<Task> to List<dynamic>
  final Function(dynamic)
  onDeleteTask; // Changed from Function(Task) to Function(dynamic)

  const AllReviewItemsScreen({
    super.key,
    required this.allTasks,
    required this.onDeleteTask,
  });

  @override
  State<AllReviewItemsScreen> createState() => _AllReviewItemsScreenState();
}

class _AllReviewItemsScreenState extends State<AllReviewItemsScreen> {
  String _formatDate(DateTime? date) {
    if (date == null) {
      return 'Not reviewed yet';
    }
    return DateFormat.yMMMd().format(date); // Example format: Jul 10, 2024
  }

  @override
  Widget build(BuildContext context) {
    final allItems = List<dynamic>.from(widget.allTasks);
    final isDesktop = MediaQuery.of(context).size.width > 600;
    final theme = Theme.of(context);

    // Since we no longer have Task objects, we can't sort by nextReviewDate
    // Just sort by name if items are strings, or keep original order
    if (allItems.isNotEmpty && allItems.first is String) {
      allItems.sort();
    }

    return Container(
      decoration: BoxDecoration(color: theme.scaffoldBackgroundColor),
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Title section with stats
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16.0),
            child: Row(
              children: [
                Text(
                  'All Review Items',
                  style: theme.textTheme.headlineLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 16),
                Chip(
                  label: Text(
                    '${allItems.length} items',
                    style: TextStyle(
                      color: theme.colorScheme.onPrimary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  backgroundColor: theme.colorScheme.primary,
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                ),
              ],
            ),
          ),

          // Empty state
          if (allItems.isEmpty)
            Expanded(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.assignment_outlined,
                      size: 86,
                      color: theme.colorScheme.outline,
                    ),
                    const SizedBox(height: 24),
                    Text(
                      'No items added yet',
                      style: theme.textTheme.headlineMedium?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.7),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Use the chat interface to create learning sessions',
                      style: theme.textTheme.bodyLarge?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ),
            ),

          // List of tasks
          if (allItems.isNotEmpty)
            Expanded(
              child: ListView.builder(
                itemCount: allItems.length,
                itemBuilder: (context, index) {
                  final task = allItems[index];
                  final taskName =
                      task is String ? task : (task['name'] ?? 'Unknown Item');

                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 8),
                    elevation: 1,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Padding(
                      padding: EdgeInsets.all(isDesktop ? 20.0 : 16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Task title
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  taskName,
                                  style: TextStyle(
                                    fontSize: isDesktop ? 20 : 18,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                              IconButton(
                                icon: Icon(
                                  Icons.delete_outline,
                                  color: theme.colorScheme.error,
                                  size: isDesktop ? 28 : 24,
                                ),
                                onPressed: () {
                                  _showDeleteConfirmation(context, task);
                                },
                              ),
                            ],
                          ),

                          const SizedBox(height: 12),

                          // Since we no longer have the old task data structure, show placeholder info
                          Row(
                            children: [
                              Expanded(
                                child: Chip(
                                  label: Text(
                                    'Legacy item (no scheduling data)',
                                    style: TextStyle(
                                      fontSize: isDesktop ? 14 : 12,
                                    ),
                                  ),
                                  backgroundColor:
                                      theme.colorScheme.surfaceContainerHighest,
                                  visualDensity: VisualDensity.compact,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _showDeleteConfirmation(
    BuildContext context,
    dynamic task,
  ) async {
    final bool? confirmDelete = await showDialog<bool>(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Delete Item'),
            content: Text(
              'Are you sure you want to delete "${task is String ? task : (task['name'] ?? 'Unknown Item')}"?',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.of(context).pop(true),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.error,
                ),
                child: const Text('Delete'),
              ),
            ],
          ),
    );

    if (confirmDelete == true) {
      widget.onDeleteTask(task);
    }
  }
}
