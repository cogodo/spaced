import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../screens/chat_screen.dart';

class ChatProgressWidget extends StatelessWidget {
  const ChatProgressWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<ChatProvider>(
      builder: (context, chatProvider, child) {
        // Only show progress during active sessions
        if (chatProvider.sessionState != SessionState.active ||
            chatProvider.currentSession == null) {
          return const SizedBox.shrink();
        }

        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: Theme.of(context).colorScheme.outline.withOpacity(0.2),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Session header with topic info
              Row(
                children: [
                  Icon(
                    Icons.psychology,
                    color: Theme.of(context).colorScheme.primary,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Learning: ${chatProvider.currentSession!.topics.join(", ")}',
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Progress information
              _buildProgressInfo(context, chatProvider),

              const SizedBox(height: 12),

              // Progress bar
              _buildProgressBar(context, chatProvider),
            ],
          ),
        );
      },
    );
  }

  Widget _buildProgressInfo(BuildContext context, ChatProvider chatProvider) {
    // Calculate progress from messages
    final userMessages = chatProvider.messages.where((m) => m.isUser).length;
    final estimatedTotalQuestions =
        chatProvider.currentSession!.topics.length *
        7; // Max questions per topic
    final currentQuestion = userMessages + 1;

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        // Question progress
        RichText(
          text: TextSpan(
            style: Theme.of(context).textTheme.bodyMedium,
            children: [
              const TextSpan(text: 'Question '),
              TextSpan(
                text: '$currentQuestion',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
              TextSpan(text: ' of ~$estimatedTotalQuestions'),
            ],
          ),
        ),

        // Percentage
        Text(
          '${((currentQuestion / estimatedTotalQuestions) * 100).round()}%',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.secondary,
          ),
        ),
      ],
    );
  }

  Widget _buildProgressBar(BuildContext context, ChatProvider chatProvider) {
    final userMessages = chatProvider.messages.where((m) => m.isUser).length;
    final estimatedTotalQuestions =
        chatProvider.currentSession!.topics.length * 7;
    final progress = (userMessages / estimatedTotalQuestions).clamp(0.0, 1.0);

    return Column(
      children: [
        LinearProgressIndicator(
          value: progress,
          backgroundColor: Theme.of(
            context,
          ).colorScheme.outline.withOpacity(0.2),
          valueColor: AlwaysStoppedAnimation<Color>(
            Theme.of(context).colorScheme.primary,
          ),
          minHeight: 6,
        ),
        const SizedBox(height: 8),

        // Motivational text based on progress
        Text(
          _getMotivationalText(progress),
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
            fontStyle: FontStyle.italic,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  String _getMotivationalText(double progress) {
    if (progress < 0.25) {
      return "Just getting started! 🚀";
    } else if (progress < 0.5) {
      return "Making great progress! 💪";
    } else if (progress < 0.75) {
      return "You're doing amazing! 🌟";
    } else if (progress < 0.9) {
      return "Almost there! 🏃‍♂️";
    } else {
      return "Final stretch! 🎯";
    }
  }
}

/// Compact progress indicator for the app bar
class CompactProgressWidget extends StatelessWidget {
  const CompactProgressWidget({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<ChatProvider>(
      builder: (context, chatProvider, child) {
        if (chatProvider.sessionState != SessionState.active) {
          return const SizedBox.shrink();
        }

        final userMessages =
            chatProvider.messages.where((m) => m.isUser).length;
        final estimatedTotalQuestions =
            chatProvider.currentSession?.topics.length ?? 1 * 7;
        final progress = (userMessages / estimatedTotalQuestions).clamp(
          0.0,
          1.0,
        );

        return SizedBox(
          width: 60,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              LinearProgressIndicator(
                value: progress,
                backgroundColor: Colors.white.withOpacity(0.3),
                valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
                minHeight: 3,
              ),
              const SizedBox(height: 2),
              Text(
                '${(progress * 100).round()}%',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
