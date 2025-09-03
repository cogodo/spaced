import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';

class NewChatButton extends StatelessWidget {
  final VoidCallback? onPressed;

  const NewChatButton({super.key, this.onPressed});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      child: OutlinedButton.icon(
        onPressed:
            onPressed ??
            () {
              // This now calls the provider to handle resetting state and navigation.
              Provider.of<ChatProvider>(
                context,
                listen: false,
              ).startNewChatFlow();
            },
        icon: const Icon(Icons.add, size: 20),
        label: const Text(
          'New Chat',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
        ),
        style: OutlinedButton.styleFrom(
          foregroundColor: theme.colorScheme.primary,
          side: BorderSide(
            color: theme.colorScheme.primary.withValues(alpha: 0.35),
            width: 1,
          ),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          minimumSize: const Size(double.infinity, 44),
        ),
      ),
    );
  }
}
