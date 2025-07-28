import 'package:flutter/material.dart';

class ThemeLogo extends StatelessWidget {
  final double size;
  final Color? overrideColor;

  const ThemeLogo({super.key, this.size = 32, this.overrideColor});

  @override
  Widget build(BuildContext context) {
    // Determine the color based on theme
    Color logoColor;
    if (overrideColor != null) {
      logoColor = overrideColor!;
    } else {
      // Use theme-appropriate colors
      final isDark = Theme.of(context).brightness == Brightness.dark;
      if (isDark) {
        // Lighter color for dark theme (as requested)
        logoColor = Theme.of(
          context,
        ).colorScheme.primary.withValues(alpha: 0.9);
      } else {
        // Keep current light mode color (perfect as is)
        logoColor = Theme.of(context).colorScheme.primary;
      }
    }

    return SizedBox(
      width: size,
      height: size,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(size * 0.2),
        child: ColorFiltered(
          colorFilter: ColorFilter.mode(logoColor, BlendMode.srcIn),
          child: Image.asset(
            'assets/images/logo_purple.png',
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) {
              // Fallback to icon if image fails to load
              return Icon(Icons.psychology, size: size, color: logoColor);
            },
          ),
        ),
      ),
    );
  }
}
