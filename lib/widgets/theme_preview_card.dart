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
        // Use scaffold background color from the theme to match the app background
        color: theme.scaffoldBackgroundColor,
        elevation: isSelected ? 4 : 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side:
              isSelected
                  ? BorderSide(color: theme.colorScheme.primary, width: 2)
                  : BorderSide(
                    color: theme.colorScheme.outline.withAlpha(40),
                    width: 0.5,
                  ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(10.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // App Bar Preview
              Container(
                height: 24,
                decoration: BoxDecoration(
                  color:
                      theme.colorScheme.primary,
                  borderRadius: BorderRadius.circular(10),
                ),
                alignment: Alignment.center,
                
              ),

            
              SizedBox(height: 8),

              // Button Preview
              Container(
                height: 20,
                decoration: BoxDecoration(
                  color:
                      theme.elevatedButtonTheme.style?.backgroundColor?.resolve(
                        {},
                      ) ??
                      theme.colorScheme.primary,
                  borderRadius: BorderRadius.circular(6),
                ),
                alignment: Alignment.center,
                
              ),

              SizedBox(height: 8),

              // Input Field Preview
              Container(
                height: 20,
                decoration: BoxDecoration(
                  color: theme.inputDecorationTheme.fillColor,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: theme.colorScheme.outline,
                    width: 0.5,
                  ),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 4),
                alignment: Alignment.centerLeft,
                
              ),

              SizedBox(height: 8),

              // Theme Name - Use the theme's default text style for consistency
              Text(
                themeMeta.name,
                style: theme.textTheme.labelMedium?.copyWith(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
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
}
