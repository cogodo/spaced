import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // Import for SystemUiOverlayStyle
import 'package:google_fonts/google_fonts.dart'; // Import Google Fonts

// Class to hold theme data along with metadata
class ThemeMetadata {
  final String name;
  final ThemeData data;
  final bool isPremium;

  ThemeMetadata({
    required this.name,
    required this.data,
    this.isPremium = false,
  });
}

// Create text theme with Fira Code for all text styles
TextTheme _createFiraCodeTextTheme(Color textColor, Brightness brightness) {
  final Color secondaryTextColor =
      brightness == Brightness.light
          ? textColor.withValues(alpha: 208 / 255.0)
          : textColor.withValues(alpha: 230 / 255.0);

  return TextTheme(
    // Headings
    displayLarge: GoogleFonts.firaCode(
      fontSize: 57,
      fontWeight: FontWeight.bold,
      color: textColor,
      letterSpacing: -0.25,
    ),
    displayMedium: GoogleFonts.firaCode(
      fontSize: 45,
      fontWeight: FontWeight.w600,
      color: textColor,
    ),
    displaySmall: GoogleFonts.firaCode(
      fontSize: 36,
      fontWeight: FontWeight.w600,
      color: textColor,
    ),
    headlineLarge: GoogleFonts.firaCode(
      fontSize: 32,
      fontWeight: FontWeight.w600,
      color: textColor,
    ),
    headlineMedium: GoogleFonts.firaCode(
      fontSize: 28,
      fontWeight: FontWeight.w600,
      color: textColor,
    ),
    headlineSmall: GoogleFonts.firaCode(
      fontSize: 24,
      fontWeight: FontWeight.w600,
      color: textColor,
    ),
    titleLarge: GoogleFonts.firaCode(
      fontSize: 22,
      fontWeight: FontWeight.w500,
      color: textColor,
    ),

    // Body text
    titleMedium: GoogleFonts.firaCode(
      fontSize: 16,
      fontWeight: FontWeight.w500,
      color: textColor,
      letterSpacing: 0.15,
    ),
    titleSmall: GoogleFonts.firaCode(
      fontSize: 14,
      fontWeight: FontWeight.w500,
      color: textColor,
      letterSpacing: 0.1,
    ),
    bodyLarge: GoogleFonts.firaCode(
      fontSize: 16,
      fontWeight: FontWeight.normal,
      color: textColor,
    ),
    bodyMedium: GoogleFonts.firaCode(
      fontSize: 14,
      fontWeight: FontWeight.normal,
      color: textColor,
    ),
    bodySmall: GoogleFonts.firaCode(
      fontSize: 12,
      fontWeight: FontWeight.normal,
      color: secondaryTextColor,
      letterSpacing: 0.4,
    ),

    // Labels
    labelLarge: GoogleFonts.firaCode(
      fontSize: 18,
      fontWeight: FontWeight.w500,
      color: textColor,
    ),
    labelMedium: GoogleFonts.firaCode(
      fontSize: 16,
      fontWeight: FontWeight.w500,
      color: textColor,
    ),
    labelSmall: GoogleFonts.firaCode(
      fontSize: 14,
      fontWeight: FontWeight.w500,
      color: textColor,
    ),
  );
}

// Map holding the ThemeMetadata objects, keyed by name
final Map<String, ThemeMetadata> appThemes = {
  'Light': ThemeMetadata(
    name: 'Light',
    data: ThemeData(
      brightness: Brightness.light,
      // Use ColorScheme.fromSeed with the same purple seed as dark theme
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF6750A4), // Same deep purple as dark theme
        brightness: Brightness.light,
      ),
      // Apply our custom text theme with dark text for readability
      textTheme: _createFiraCodeTextTheme(Colors.black87, Brightness.light),
      primaryTextTheme: _createFiraCodeTextTheme(
        Colors.white,
        Brightness.light,
      ),

      // System UI overlay
      appBarTheme: AppBarTheme(
        systemOverlayStyle:
            SystemUiOverlayStyle.dark, // Dark status bar for light theme
        backgroundColor: const Color(0xFF6750A4), // Purple app bar
      ),

      // White background with purple accents
      cardColor: Colors.white,
      scaffoldBackgroundColor: Colors.white, // Pure white background
      // Purple buttons matching dark theme
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF6750A4), // Same purple as dark theme
          foregroundColor: Colors.white, // White text for contrast
          elevation: 1, // Slight elevation
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF6750A4), // Purple text
          side: const BorderSide(
            color: Color(0xFF6750A4),
            width: 1.5,
          ), // Purple border
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),

      // Input decoration with purple accents
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderSide: BorderSide(
            color: const Color(
              0xFF6750A4,
            ).withValues(alpha: 0.5), // Light purple border
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(
            color: const Color(0xFF6750A4).withValues(alpha: 0.5),
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(
            color: Color(0xFF6750A4),
            width: 1.5,
          ), // Purple focus
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: GoogleFonts.firaCode(
          color: const Color(0xFF6750A4).withValues(alpha: 0.6),
          fontStyle: FontStyle.italic,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
      ),

      // Purple dividers and icons
      dividerColor: const Color(
        0xFF6750A4,
      ).withValues(alpha: 0.2), // Light purple divider
      iconTheme: const IconThemeData(color: Color(0xFF6750A4)), // Purple icons

      useMaterial3: true,
      fontFamily: GoogleFonts.firaCode().fontFamily,
    ),
  ),
  'Dark': ThemeMetadata(
    name: 'Dark',
    data: ThemeData(
      brightness: Brightness.dark,
      // Use ColorScheme.fromSeed for more cohesive colors
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF6750A4), // Deep purple seed color
        brightness: Brightness.dark,
      ),
      // Apply our custom text theme for dark mode
      textTheme: _createFiraCodeTextTheme(Colors.white, Brightness.dark),
      primaryTextTheme: _createFiraCodeTextTheme(Colors.white, Brightness.dark),

      // Apply system overlay style for status bar icons
      appBarTheme: AppBarTheme(
        systemOverlayStyle: SystemUiOverlayStyle.light,
        backgroundColor: const Color(0xFF1E1E2E), // Dark surface color
      ),

      // Rich deep purple buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF9A86FD), // Lighter purple
          foregroundColor: Colors.white, // White text for better contrast
          elevation: 0, // Flat design
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(
              10,
            ), // Consistent rounded corners
          ),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(
            0xFFB4A9FF,
          ), // Light purple for outlined buttons
          side: const BorderSide(color: Color(0xFF7B68EE), width: 1.5),
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),

      // Improved card & scaffold backgrounds
      cardColor: const Color(0xFF2D2D40),
      scaffoldBackgroundColor: const Color(0xFF1E1E2E),

      // Input decoration matching the theme
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF2D2D40),
        border: OutlineInputBorder(
          borderSide: BorderSide(
            color: const Color(0xFF7B68EE).withValues(alpha: 0.5),
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(
            color: const Color(0xFF7B68EE).withValues(alpha: 0.5),
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(color: Color(0xFF9A86FD), width: 1.5),
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: GoogleFonts.firaCode(
          color: Colors.grey[400],
          fontStyle: FontStyle.italic,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
      ),

      // Add a divider color
      dividerColor: const Color(0xFF3D3A50),

      // Add icon theme
      iconTheme: const IconThemeData(color: Color(0xFF9A86FD)),

      useMaterial3: true,
      fontFamily: GoogleFonts.firaCode().fontFamily,
    ),
  ),
  // Removed Red and Green themes to simplify to just Light/Dark toggle
};
