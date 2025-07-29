import 'package:flutter/material.dart';

class QuestionGenerationLoadingScreen extends StatefulWidget {
  final String topicName;

  const QuestionGenerationLoadingScreen({super.key, required this.topicName});

  @override
  State<QuestionGenerationLoadingScreen> createState() =>
      _QuestionGenerationLoadingScreenState();
}

class _QuestionGenerationLoadingScreenState
    extends State<QuestionGenerationLoadingScreen>
    with TickerProviderStateMixin {
  late AnimationController _dotController;
  late Animation<double> _dotAnimation;

  @override
  void initState() {
    super.initState();

    // Dot animation for the loading indicator
    _dotController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _dotAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _dotController, curve: Curves.easeInOut));
    _dotController.repeat();
  }

  @override
  void dispose() {
    _dotController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.colorScheme.surface,
      body: SafeArea(
        child: Center(
          child: Container(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Icon
                Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Icon(
                    Icons.quiz,
                    size: 40,
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                ),

                const SizedBox(height: 32),

                // Title
                Text(
                  'Generating Questions',
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onSurface,
                  ),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 16),

                // Topic name
                Text(
                  'for "${widget.topicName}"',
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                  ),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 32),

                // Loading indicator
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(3, (index) {
                    return AnimatedBuilder(
                      animation: _dotAnimation,
                      builder: (context, child) {
                        final delay = index * 0.2;
                        final animationValue =
                            (_dotAnimation.value + delay) % 1.0;
                        final opacity = (animationValue * 2).clamp(0.0, 1.0);

                        return Container(
                          margin: EdgeInsets.only(right: index < 2 ? 8 : 0),
                          child: Opacity(
                            opacity: opacity,
                            child: Container(
                              width: 12,
                              height: 12,
                              decoration: BoxDecoration(
                                color: theme.colorScheme.primary,
                                shape: BoxShape.circle,
                              ),
                            ),
                          ),
                        );
                      },
                    );
                  }),
                ),

                const SizedBox(height: 32),

                // Description
                Text(
                  'Creating personalized questions to help you learn effectively...',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                  ),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 16),

                // Additional info
                Text(
                  'This may take a few moments',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
