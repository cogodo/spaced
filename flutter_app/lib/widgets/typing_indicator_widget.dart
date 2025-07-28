import 'package:flutter/material.dart';

class TypingIndicatorWidget extends StatefulWidget {
  final String? customMessage;
  final Color? dotColor;
  final double dotSize;
  final Duration animationDuration;

  const TypingIndicatorWidget({
    super.key,
    this.customMessage,
    this.dotColor,
    this.dotSize = 8.0,
    this.animationDuration = const Duration(milliseconds: 600),
  });

  @override
  State<TypingIndicatorWidget> createState() => _TypingIndicatorWidgetState();
}

class _TypingIndicatorWidgetState extends State<TypingIndicatorWidget>
    with TickerProviderStateMixin {
  late AnimationController _animationController;
  late List<Animation<double>> _dotAnimations;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: widget.animationDuration,
      vsync: this,
    );

    // Create staggered animations for three dots
    _dotAnimations = List.generate(3, (index) {
      final startTime = index * 0.2; // Stagger by 20% of duration
      return Tween<double>(begin: 0.4, end: 1.0).animate(
        CurvedAnimation(
          parent: _animationController,
          curve: Interval(
            startTime,
            startTime + 0.4, // Each dot animates for 40% of duration
            curve: Curves.easeInOut,
          ),
        ),
      );
    });

    _animationController.repeat();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          // AI avatar
          CircleAvatar(
            radius: 16,
            backgroundColor: Theme.of(
              context,
            ).colorScheme.primary.withValues(alpha: 0.1),
            child: Icon(
              Icons.psychology,
              size: 18,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
          const SizedBox(width: 12),

          // Typing bubble
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(20),
                  topRight: Radius.circular(20),
                  bottomRight: Radius.circular(20),
                  bottomLeft: Radius.circular(4),
                ),
                border: Border.all(
                  color: Theme.of(
                    context,
                  ).colorScheme.outline.withValues(alpha: 0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Custom message or default
                  if (widget.customMessage != null) ...[
                    Text(
                      widget.customMessage!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(
                          context,
                        ).colorScheme.onSurface.withValues(alpha: 0.7),
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],

                  // Animated dots
                  AnimatedBuilder(
                    animation: _animationController,
                    builder: (context, child) {
                      return Row(
                        mainAxisSize: MainAxisSize.min,
                        children: List.generate(3, (index) {
                          return Container(
                            margin: EdgeInsets.only(right: index < 2 ? 4 : 0),
                            child: Transform.scale(
                              scale: _dotAnimations[index].value,
                              child: Container(
                                width: widget.dotSize,
                                height: widget.dotSize,
                                decoration: BoxDecoration(
                                  color:
                                      widget.dotColor ??
                                      Theme.of(context).colorScheme.primary
                                          .withValues(alpha: 0.6),
                                  shape: BoxShape.circle,
                                ),
                              ),
                            ),
                          );
                        }),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Smart typing indicator that changes message based on context
class SmartTypingIndicator extends StatelessWidget {
  final String? sessionState;
  final bool isGeneratingQuestions;
  final bool isProcessingAnswer;

  const SmartTypingIndicator({
    super.key,
    this.sessionState,
    this.isGeneratingQuestions = false,
    this.isProcessingAnswer = false,
  });

  @override
  Widget build(BuildContext context) {
    String message = _getContextualMessage();

    return TypingIndicatorWidget(customMessage: message);
  }

  String _getContextualMessage() {
    if (isGeneratingQuestions) {
      return "Generating personalized questions...";
    } else if (isProcessingAnswer) {
      return "Analyzing your response...";
    } else if (sessionState == 'starting') {
      return "Starting your learning session...";
    } else if (sessionState == 'scoring') {
      return "Scoring your answer...";
    } else {
      return "AI is thinking...";
    }
  }
}

/// Compact typing indicator for smaller spaces
class CompactTypingIndicator extends StatefulWidget {
  const CompactTypingIndicator({super.key});

  @override
  State<CompactTypingIndicator> createState() => _CompactTypingIndicatorState();
}

class _CompactTypingIndicatorState extends State<CompactTypingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _animation = Tween<double>(
      begin: 0.3,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
    _controller.repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (index) {
            return Container(
              margin: EdgeInsets.only(right: index < 2 ? 2 : 0),
              child: Opacity(
                opacity: _animation.value,
                child: Container(
                  width: 4,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primary,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            );
          }),
        );
      },
    );
  }
}
