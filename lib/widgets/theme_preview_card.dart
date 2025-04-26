import 'package:flutter/material.dart';
import '../themes/theme_data.dart'; // To access ThemeMetadata

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
        elevation: isSelected ? 4 : 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side:
              isSelected
                  ? BorderSide(color: theme.colorScheme.primary, width: 2)
                  : BorderSide.none,
        ),
        child: Padding(
          padding: const EdgeInsets.all(10.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Color Sample Row
              Container(
                height: 20,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary,
                  borderRadius: BorderRadius.circular(10),
                ),
              ),

              SizedBox(height: 8),

              // Button Preview
              Container(
                height: 24,
                decoration: BoxDecoration(
                  color:
                      theme.elevatedButtonTheme.style?.backgroundColor?.resolve(
                        {},
                      ) ??
                      theme.colorScheme.primary,
                  borderRadius: BorderRadius.circular(8),
                ),
                alignment: Alignment.center,
                child: Text(
                  'Button',
                  style: TextStyle(fontSize: 10, color: Colors.white),
                ),
              ),

              SizedBox(height: 8),

              // Input Field Preview
              Container(
                height: 24,
                decoration: BoxDecoration(
                  color: theme.inputDecorationTheme.fillColor,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: theme.colorScheme.outline,
                    width: 0.5,
                  ),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 6),
                alignment: Alignment.centerLeft,
                child: Text(
                  'input',
                  style: TextStyle(fontSize: 10, color: theme.hintColor),
                ),
              ),

              SizedBox(height: 10),

              // Theme Name
              Text(
                themeMeta.name,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: _getContrastingTextColor(
                    themeMeta.data.colorScheme.primary,
                  ),
                ),
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getContrastingTextColor(Color backgroundColor) {
    // Calculate relative luminance using the formula recommended by WCAG
    // This is more accurate than just checking RGB values
    final double luminance = backgroundColor.computeLuminance();

    // If luminance is greater than 0.5, the color is considered light
    // This threshold provides good contrast for readability
    return luminance > 0.5 ? Colors.black : Colors.white;
  }
}
