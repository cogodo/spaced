import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../main.dart';

class ThemeToggle extends StatelessWidget {
  const ThemeToggle({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<ThemeNotifier>(
      builder: (context, themeNotifier, child) {
        final isDark = themeNotifier.currentThemeKey == 'Dark';

        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.light_mode,
              size: 18,
              color:
                  !isDark
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(
                        context,
                      ).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
            const SizedBox(width: 8),
            Switch(
              value: isDark,
              onChanged: (bool value) {
                themeNotifier.setTheme(value ? 'Dark' : 'Light');
              },
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            const SizedBox(width: 8),
            Icon(
              Icons.dark_mode,
              size: 18,
              color:
                  isDark
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(
                        context,
                      ).colorScheme.onSurface.withValues(alpha: 0.5),
            ),
          ],
        );
      },
    );
  }
}
