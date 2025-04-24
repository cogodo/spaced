import 'package:flutter/material.dart';
import '../themes/theme_data.dart'; // To access ThemeMetadata and ThemeNotifier

class ThemePreviewCard extends StatelessWidget {
  final ThemeMetadata themeMeta;
  final bool isSelected;

  const ThemePreviewCard({
    super.key,
    required this.themeMeta,
    required this.isSelected,
  });

  @override
  Widget build(BuildContext context) {
    final theme = themeMeta.data; // Get the ThemeData

    // Use a Theme widget to apply the specific theme locally for the preview
    return Theme(
      data: theme,
      child: Card(
        // Use card's background color from the theme
        color: theme.cardColor,
        elevation: isSelected ? 8 : 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side:
              isSelected
                  ? BorderSide(color: theme.colorScheme.primary, width: 3)
                  : BorderSide.none,
        ),
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              // Fake Text Input preview
              Container(
                height: 25,
                decoration: BoxDecoration(
                  color:
                      theme.inputDecorationTheme.fillColor ?? theme.canvasColor,
                  border: Border.all(color: theme.dividerColor),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8.0),
                  child: Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Text Input',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.hintColor,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
              ),
              // Button Preview
              ElevatedButton(
                onPressed: () {},
                style: theme.elevatedButtonTheme.style, // Dummy button
                // Button style comes from the theme
                child: Text('Button'),
              ),
              // Theme Name
              Text(
                themeMeta.name,
                style: theme.textTheme.titleSmall, // Use theme's text style
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
