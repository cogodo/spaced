import 'package:flutter/material.dart';

class PulsingMicButton extends StatefulWidget {
  final bool isConnecting;
  final bool isVoiceConnected;
  final bool isSpeaking;
  final VoidCallback? onTap;
  final double size;

  const PulsingMicButton({
    Key? key,
    required this.isConnecting,
    required this.isVoiceConnected,
    required this.isSpeaking,
    this.onTap,
    this.size = 80.0,
  }) : super(key: key);

  @override
  State<PulsingMicButton> createState() => _PulsingMicButtonState();
}

class _PulsingMicButtonState extends State<PulsingMicButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animationController;
  late final Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );

    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.4).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );

    _updateAnimation();
  }

  @override
  void didUpdateWidget(PulsingMicButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isSpeaking != oldWidget.isSpeaking) {
      debugPrint(
        '[PulsingMicButton] Speaking status changed: ${widget.isSpeaking}',
      );
      _updateAnimation();
    }
  }

  void _updateAnimation() {
    if (widget.isSpeaking && widget.isVoiceConnected) {
      _animationController.repeat(reverse: true);
    } else {
      _animationController.stop();
      _animationController.reset();
    }
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    debugPrint(
      '[PulsingMicButton] Building with: isConnecting=${widget.isConnecting}, isConnected=${widget.isVoiceConnected}, isSpeaking=${widget.isSpeaking}',
    );
    final theme = Theme.of(context);
    final Color iconColor;
    final Color backgroundColor;
    final IconData iconData;

    if (widget.isConnecting) {
      iconColor = theme.colorScheme.onSurface.withOpacity(0.5);
      backgroundColor = theme.colorScheme.surfaceContainerHighest;
      iconData = Icons.hourglass_empty;
    } else if (widget.isVoiceConnected) {
      iconColor = theme.colorScheme.onPrimary;
      backgroundColor = theme.colorScheme.primary;
      iconData = Icons.headphones; // Use headphones icon for voice chat
    } else {
      iconColor = theme.colorScheme.onSurface;
      backgroundColor = theme.colorScheme.surfaceContainerHighest;
      iconData =
          Icons
              .headphones_outlined; // Use outlined headphones when not connected
    }

    return GestureDetector(
      onTap: widget.isConnecting ? null : widget.onTap,
      child: Stack(
        alignment: Alignment.center,
        children: [
          if (widget.isVoiceConnected)
            ScaleTransition(
              scale: _scaleAnimation,
              child: Container(
                width: widget.size,
                height: widget.size,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: theme.colorScheme.primary.withOpacity(0.2),
                ),
              ),
            ),
          Container(
            width: widget.size,
            height: widget.size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: backgroundColor,
              boxShadow: [
                BoxShadow(
                  color: theme.shadowColor.withOpacity(0.1),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child:
                widget.isConnecting
                    ? SizedBox(
                      width: widget.size * 0.5,
                      height: widget.size * 0.5,
                      child: const CircularProgressIndicator(),
                    )
                    : Icon(iconData, color: iconColor, size: widget.size * 0.5),
          ),
        ],
      ),
    );
  }
}
