import 'package:flutter/material.dart';

class VoiceButton extends StatelessWidget {
  final bool isConnecting;
  final bool isVoiceConnected;
  final bool isSpeaking;
  final VoidCallback? onTap;
  final double size;

  const VoiceButton({
    super.key,
    required this.isConnecting,
    required this.isVoiceConnected,
    required this.isSpeaking,
    this.onTap,
    this.size = 56.0,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final Color iconColor;
    final Color backgroundColor;
    final IconData iconData;

    if (isConnecting) {
      iconColor = theme.colorScheme.onSurface.withValues(alpha: 0.5);
      backgroundColor = theme.colorScheme.surfaceContainerHighest;
      iconData = Icons.hourglass_empty;
    } else if (isVoiceConnected) {
      iconColor = theme.colorScheme.onPrimary;
      backgroundColor = theme.colorScheme.primary;
      iconData = Icons.headphones;
    } else {
      iconColor = theme.colorScheme.onSurface;
      backgroundColor = theme.colorScheme.surfaceContainerHighest;
      iconData = Icons.headphones_outlined;
    }

    return GestureDetector(
      onTap: isConnecting ? null : onTap,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: backgroundColor,
          boxShadow: [
            BoxShadow(
              color: theme.shadowColor.withValues(alpha: 0.1),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child:
            isConnecting
                ? SizedBox(
                  width: size * 0.5,
                  height: size * 0.5,
                  child: const CircularProgressIndicator(),
                )
                : Icon(iconData, color: iconColor, size: size * 0.5),
      ),
    );
  }
}
