import 'package:flutter/material.dart';
import 'package:spaced/models/task_holder.dart';
import 'package:intl/intl.dart'; // For date formatting

class AllReviewItemsScreen extends StatefulWidget {
  final List<Task> allTasks;
  final Function(Task) onDeleteTask;

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
    final allItems = List<Task>.from(widget.allTasks);
    final isDesktop = MediaQuery.of(context).size.width > 600;

    // Sort by next review date, null dates at the bottom
    allItems.sort((a, b) {
      if (a.nextReviewDate == null && b.nextReviewDate == null) {
        return a.task.compareTo(b.task); // If both null, sort by name
      } else if (a.nextReviewDate == null) {
        return 1; // a goes after b
      } else if (b.nextReviewDate == null) {
        return -1; // a goes before b
      } else {
        return a.nextReviewDate!.compareTo(b.nextReviewDate!);
      }
    });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Title section with stats
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 16.0),
          child: Row(
            children: [
              Text(
                'All Review Items',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
              ),
              SizedBox(width: 16),
              Chip(
                label: Text(
                  '${allItems.length} items',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                backgroundColor: Theme.of(context).colorScheme.primary,
                padding: EdgeInsets.symmetric(horizontal: 8),
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
                    color: Colors.grey.shade400,
                  ),
                  SizedBox(height: 24),
                  Text(
                    'No items added yet',
                    style: TextStyle(fontSize: 24, color: Colors.grey.shade700),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Add new items from the "Add" tab',
                    style: TextStyle(fontSize: 16, color: Colors.grey.shade600),
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

                return Card(
                  margin: EdgeInsets.symmetric(vertical: 8),
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
                                task.task,
                                style: TextStyle(
                                  fontSize: isDesktop ? 20 : 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            IconButton(
                              icon: Icon(
                                Icons.delete_outline,
                                color: Colors.red,
                                size: isDesktop ? 28 : 24,
                              ),
                              splashRadius: 28,
                              onPressed: () {
                                _showDeleteConfirmation(context, task);
                              },
                            ),
                          ],
                        ),

                        SizedBox(height: 12),

                        // Task details in a more readable format
                        // Add a label to indicate this is using FSRS algorithm
                        Align(
                          alignment: Alignment.centerRight,
                          child: Chip(
                            label: Text(
                              'FSRS',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.white,
                              ),
                            ),
                            backgroundColor:
                                Theme.of(context).colorScheme.secondary,
                            visualDensity: VisualDensity.compact,
                          ),
                        ),

                        SizedBox(height: 8),

                        // Group stats into two rows for better organization
                        // Row 1: Next review date and repetition count
                        Row(
                          children: [
                            // Next review date chip
                            Expanded(
                              child: Chip(
                                label: Text(
                                  'Next: ${_formatDate(task.nextReviewDate)}',
                                  style: TextStyle(
                                    fontSize: isDesktop ? 14 : 12,
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                ),
                                backgroundColor:
                                    Theme.of(
                                      context,
                                    ).colorScheme.surfaceContainerHighest,
                                visualDensity: VisualDensity.compact,
                              ),
                            ),
                            SizedBox(width: 8),

                            // Repetition count chip
                            Expanded(
                              child: Chip(
                                label: Text(
                                  'Reps: ${task.repetition}',
                                  style: TextStyle(
                                    fontSize: isDesktop ? 14 : 12,
                                  ),
                                ),
                                backgroundColor:
                                    Theme.of(
                                      context,
                                    ).colorScheme.surfaceContainerHighest,
                                visualDensity: VisualDensity.compact,
                              ),
                            ),
                          ],
                        ),

                        SizedBox(height: 8),

                        // Row 2: FSRS specific stats - stability and difficulty
                        Row(
                          children: [
                            // Stability chip (FSRS metric)
                            Expanded(
                              child: Chip(
                                label: Text(
                                  'Stability: ${task.stability.toStringAsFixed(1)}',
                                  style: TextStyle(
                                    fontSize: isDesktop ? 14 : 12,
                                  ),
                                ),
                                backgroundColor:
                                    Theme.of(
                                      context,
                                    ).colorScheme.surfaceContainerHighest,
                                visualDensity: VisualDensity.compact,
                              ),
                            ),
                            SizedBox(width: 8),

                            // Difficulty chip (FSRS metric)
                            Expanded(
                              child: Chip(
                                label: Text(
                                  'Difficulty: ${(task.difficulty * 100).round()}%',
                                  style: TextStyle(
                                    fontSize: isDesktop ? 14 : 12,
                                  ),
                                ),
                                backgroundColor:
                                    Theme.of(
                                      context,
                                    ).colorScheme.surfaceContainerHighest,
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
    );
  }

  Future<void> _showDeleteConfirmation(BuildContext context, Task task) async {
    final bool? confirmDelete = await showDialog<bool>(
      context: context,
      builder:
          (context) => AlertDialog(
            title: Text('Delete Item'),
            content: Text('Are you sure you want to delete "${task.task}"?'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () => Navigator.of(context).pop(true),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                child: Text('Delete'),
              ),
            ],
          ),
    );

    if (confirmDelete == true) {
      widget.onDeleteTask(task);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Item deleted'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    }
  }
}
