import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class TodaysReviewsScreen extends StatefulWidget {
  const TodaysReviewsScreen({super.key});

  @override
  State<TodaysReviewsScreen> createState() => _TodaysReviewsScreenState();
}

class _TodaysReviewsScreenState extends State<TodaysReviewsScreen> {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDesktop = MediaQuery.of(context).size.width > 800;

    return Scaffold(
      body: SingleChildScrollView(
        padding: EdgeInsets.all(isDesktop ? 40 : 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header section
            Row(
              children: [
                Icon(Icons.today, size: 32, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Text(
                  'Today\'s Reviews',
                  style: theme.textTheme.headlineLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Spaced repetition reviews due today',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
              ),
            ),
            const SizedBox(height: 32),

            // Stats cards section
            _buildStatsSection(theme, isDesktop),
            const SizedBox(height: 32),

            // Main content area - placeholder
            _buildMainContent(theme, isDesktop),
          ],
        ),
      ),
    );
  }

  Widget _buildStatsSection(ThemeData theme, bool isDesktop) {
    return isDesktop
        ? Row(
          children: [
            Expanded(
              child: _buildStatCard(
                theme,
                'Due Today',
                '0',
                Icons.assignment_turned_in,
                theme.colorScheme.primary,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildStatCard(
                theme,
                'Completed',
                '0',
                Icons.check_circle,
                Colors.green,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildStatCard(
                theme,
                'Study Streak',
                '0 days',
                Icons.local_fire_department,
                Colors.orange,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildStatCard(
                theme,
                'Total Items',
                '0',
                Icons.library_books,
                theme.colorScheme.secondary,
              ),
            ),
          ],
        )
        : Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    theme,
                    'Due Today',
                    '0',
                    Icons.assignment_turned_in,
                    theme.colorScheme.primary,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildStatCard(
                    theme,
                    'Completed',
                    '0',
                    Icons.check_circle,
                    Colors.green,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildStatCard(
                    theme,
                    'Study Streak',
                    '0 days',
                    Icons.local_fire_department,
                    Colors.orange,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildStatCard(
                    theme,
                    'Total Items',
                    '0',
                    Icons.library_books,
                    theme.colorScheme.secondary,
                  ),
                ),
              ],
            ),
          ],
        );
  }

  Widget _buildStatCard(
    ThemeData theme,
    String title,
    String value,
    IconData icon,
    Color color,
  ) {
    return Card(
      elevation: 0,
      color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: theme.colorScheme.outline.withValues(alpha: 0.1),
          width: 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMainContent(ThemeData theme, bool isDesktop) {
    return Card(
      elevation: 0,
      color: theme.colorScheme.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: theme.colorScheme.outline.withValues(alpha: 0.1),
          width: 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Icon
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(40),
                ),
                child: Icon(
                  Icons.construction,
                  size: 40,
                  color: theme.colorScheme.onPrimaryContainer,
                ),
              ),
              const SizedBox(height: 24),

              // Title
              Text(
                'Coming Soon',
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: theme.colorScheme.onSurface,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),

              // Description
              Text(
                'Today\'s reviews feature is under development.\n\n'
                'This will show your spaced repetition items that are due for review today, '
                'organized by priority and difficulty. You\'ll be able to complete reviews '
                'directly from this screen with optimal scheduling.',
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),

              // Action buttons
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  OutlinedButton.icon(
                    onPressed: () => context.go('/app/chat'),
                    icon: const Icon(Icons.chat, size: 20),
                    label: const Text('Start Learning Session'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                      side: BorderSide(color: theme.colorScheme.primary),
                      foregroundColor: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(width: 16),
                  ElevatedButton.icon(
                    onPressed: () => context.go('/app/all'),
                    icon: const Icon(Icons.list, size: 20),
                    label: const Text('View All Items'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: theme.colorScheme.primary,
                      foregroundColor: theme.colorScheme.onPrimary,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
