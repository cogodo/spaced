import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/session_api.dart';

class TodaysReviewsScreen extends StatefulWidget {
  const TodaysReviewsScreen({super.key});

  @override
  State<TodaysReviewsScreen> createState() => _TodaysReviewsScreenState();
}

class _TodaysReviewsScreenState extends State<TodaysReviewsScreen> {
  bool _isLoading = true;
  Map<String, dynamic>? _reviewData;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTodaysReviews();
  }

  Future<void> _loadTodaysReviews() async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final userId = authProvider.user?.uid;

    if (userId == null) {
      setState(() {
        _error = 'User not authenticated';
        _isLoading = false;
      });
      return;
    }

    try {
      // Use SessionApi to get today's reviews
      const backendUrl = String.fromEnvironment(
        'BACKEND_URL',
        defaultValue: 'http://localhost:8000',
      );
      print('TodaysReviewsScreen: Using backend URL: $backendUrl'); // Debug log
      final api = SessionApi(baseUrl: backendUrl);

      print(
        'TodaysReviewsScreen: Calling API with userId: $userId',
      ); // Debug log
      final response = await api.getTodaysReviews(userId);
      print('TodaysReviewsScreen: API response: $response'); // Debug log

      setState(() {
        _reviewData = response;
        _isLoading = false;
      });
    } catch (e, stackTrace) {
      print('TodaysReviewsScreen: Error loading reviews: $e'); // Debug log
      print('TodaysReviewsScreen: Stack trace: $stackTrace'); // Debug log
      setState(() {
        _error = 'Failed to load reviews: ${e.toString()}';
        _isLoading = false;
      });
    }
  }

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

            // Content based on loading state
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else if (_error != null)
              _buildErrorState(theme)
            else
              _buildReviewContent(theme, isDesktop),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(ThemeData theme) {
    return Center(
      child: Column(
        children: [
          Icon(Icons.error_outline, size: 64, color: theme.colorScheme.error),
          const SizedBox(height: 16),
          Text(
            'Error Loading Reviews',
            style: theme.textTheme.headlineMedium?.copyWith(
              color: theme.colorScheme.error,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _error!,
            style: theme.textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: () {
              setState(() {
                _isLoading = true;
                _error = null;
              });
              _loadTodaysReviews();
            },
            icon: const Icon(Icons.refresh),
            label: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildReviewContent(ThemeData theme, bool isDesktop) {
    if (_reviewData == null) return const SizedBox();

    final overdue = _reviewData!['overdue'] as List? ?? [];
    final dueToday = _reviewData!['dueToday'] as List? ?? [];
    final upcoming = _reviewData!['upcoming'] as List? ?? [];
    final totalDue = overdue.length + dueToday.length;

    return Column(
      children: [
        // Stats cards section
        _buildStatsSection(
          theme,
          isDesktop,
          overdue.length,
          dueToday.length,
          upcoming.length,
        ),
        const SizedBox(height: 32),

        // Review sections
        if (overdue.isNotEmpty) ...[
          _buildReviewSection(theme, 'Overdue Items', overdue, Colors.red),
          const SizedBox(height: 24),
        ],
        if (dueToday.isNotEmpty) ...[
          _buildReviewSection(
            theme,
            'Due Today',
            dueToday,
            theme.colorScheme.primary,
          ),
          const SizedBox(height: 24),
        ],
        if (upcoming.isNotEmpty) ...[
          _buildReviewSection(theme, 'Coming Soon', upcoming, Colors.orange),
          const SizedBox(height: 24),
        ],

        // Empty state or action buttons
        if (totalDue == 0)
          _buildNoReviewsState(theme)
        else
          _buildActionButtons(theme),
      ],
    );
  }

  Widget _buildStatsSection(
    ThemeData theme,
    bool isDesktop,
    int overdue,
    int dueToday,
    int upcoming,
  ) {
    return isDesktop
        ? Row(
          children: [
            Expanded(
              child: _buildStatCard(
                theme,
                'Overdue',
                overdue.toString(),
                Icons.warning,
                Colors.red,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildStatCard(
                theme,
                'Due Today',
                dueToday.toString(),
                Icons.assignment_turned_in,
                theme.colorScheme.primary,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildStatCard(
                theme,
                'Coming Soon',
                upcoming.toString(),
                Icons.schedule,
                Colors.orange,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildStatCard(
                theme,
                'Total Due',
                (overdue + dueToday).toString(),
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
                    'Overdue',
                    overdue.toString(),
                    Icons.warning,
                    Colors.red,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildStatCard(
                    theme,
                    'Due Today',
                    dueToday.toString(),
                    Icons.assignment_turned_in,
                    theme.colorScheme.primary,
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
                    'Coming Soon',
                    upcoming.toString(),
                    Icons.schedule,
                    Colors.orange,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildStatCard(
                    theme,
                    'Total Due',
                    (overdue + dueToday).toString(),
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

  Widget _buildReviewSection(
    ThemeData theme,
    String title,
    List items,
    Color color,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.bookmark, color: color, size: 20),
            const SizedBox(width: 8),
            Text(
              title,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(width: 8),
            Chip(
              label: Text(items.length.toString()),
              backgroundColor: color.withValues(alpha: 0.1),
              labelStyle: TextStyle(color: color, fontWeight: FontWeight.bold),
              visualDensity: VisualDensity.compact,
            ),
          ],
        ),
        const SizedBox(height: 12),
        ...items.take(5).map((item) => _buildTopicCard(theme, item)),
        if (items.length > 5)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Text(
              '... and ${items.length - 5} more',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                fontStyle: FontStyle.italic,
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildTopicCard(ThemeData theme, Map<String, dynamic> topic) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.1),
          child: Icon(Icons.psychology, color: theme.colorScheme.primary),
        ),
        title: Text(
          topic['name'] ?? 'Unknown Topic',
          style: const TextStyle(fontWeight: FontWeight.w500),
        ),
        subtitle: Text(
          topic['description'] ?? 'No description',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '${topic['questionCount'] ?? 0} questions',
              style: theme.textTheme.bodySmall,
            ),
            if (topic['daysOverdue'] != null)
              Text(
                '${topic['daysOverdue']} days overdue',
                style: theme.textTheme.bodySmall?.copyWith(color: Colors.red),
              )
            else if (topic['daysUntil'] != null)
              Text(
                'Due in ${topic['daysUntil']} days',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: Colors.orange,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildNoReviewsState(ThemeData theme) {
    return Center(
      child: Column(
        children: [
          Icon(Icons.check_circle, size: 64, color: Colors.green),
          const SizedBox(height: 16),
          Text(
            'All Caught Up!',
            style: theme.textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.green,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'No reviews due today. Great job staying on top of your learning!',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          _buildActionButtons(theme),
        ],
      ),
    );
  }

  Widget _buildActionButtons(ThemeData theme) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        OutlinedButton.icon(
          onPressed: () => context.go('/app/chat'),
          icon: const Icon(Icons.chat, size: 20),
          label: const Text('Start Learning Session'),
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
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
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          ),
        ),
      ],
    );
  }
}
