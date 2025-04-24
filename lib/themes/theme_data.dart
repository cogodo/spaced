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
          ? textColor.withAlpha(208)
          : textColor.withAlpha(230);

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
      // Use ColorScheme.fromSeed for modern color generation
      colorScheme: ColorScheme.fromSeed(
        seedColor: Colors.blueGrey, // Seed color - influences overall palette
        brightness: Brightness.light,
      ),
      // Use generated scheme colors where appropriate
      scaffoldBackgroundColor: Colors.grey[50], // Very light grey background
      cardColor: Colors.white,

      appBarTheme: AppBarTheme(
        backgroundColor: Colors.white, // Clean white app bar
        foregroundColor: Colors.grey[800], // Dark grey text/icons on app bar
        elevation: 0.5, // Subtle elevation
        systemOverlayStyle: SystemUiOverlayStyle.dark, // Dark status bar icons
        iconTheme: IconThemeData(
          color: Colors.grey[700],
        ), // Specific icon color
        titleTextStyle: GoogleFonts.firaCode(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: Colors.grey[800],
        ),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          // Use primary color from the generated scheme
          backgroundColor:
              Colors.blueGrey[700], // Use a darker shade for contrast
          foregroundColor: Colors.white, // White text on button
          elevation: 0,
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10), // Rounded corners
          ),
          padding: EdgeInsets.symmetric(
            horizontal: 20,
            vertical: 12,
          ), // Standard padding
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.blueGrey[700],
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

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.grey[300], // Slightly darker fill for inputs
        hintStyle: GoogleFonts.firaCode(
          color: Colors.grey[600],
          fontStyle: FontStyle.italic,
        ), // Lighter hint text
        // Use a subtle underline border for minimalist look
        border: OutlineInputBorder(
          borderSide: BorderSide(color: Colors.blueGrey[500]!),
          borderRadius: BorderRadius.circular(8), // Keep slight rounding
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(color: Colors.blueGrey[500]!),
          borderRadius: BorderRadius.circular(8),
        ),
        focusedBorder: OutlineInputBorder(
          // Use primary color variant when focused
          borderSide: BorderSide(color: Colors.blueGrey[600]!, width: 1.5),
          borderRadius: BorderRadius.circular(8),
        ),
        contentPadding: EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ), // Comfortable padding
      ),

      cardTheme: CardTheme(
        elevation: 0, // Minimal elevation
        color: Colors.white, // Explicitly white card background
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12.0), // Consistent rounding
        ),
      ),

      // Apply our custom Fira Code text theme
      textTheme: _createFiraCodeTextTheme(Colors.black, Brightness.light),
      primaryTextTheme: _createFiraCodeTextTheme(
        Colors.black,
        Brightness.light,
      ),

      dividerColor: Colors.grey[200], // Light divider color

      iconTheme: IconThemeData(
        color: Colors.grey[700], // Default icon color
      ),

      // Ensure useMaterial3 is enabled for fromSeed to work best
      useMaterial3: true,
      fontFamily: GoogleFonts.firaCode().fontFamily,
    ),
  ),
  'Dark': ThemeMetadata(
    name: 'Dark',
    data: ThemeData(
      brightness: Brightness.dark,
      primarySwatch: Colors.pink, // Example primary color
      // Apply our custom text theme for dark mode
      textTheme: _createFiraCodeTextTheme(Colors.white, Brightness.dark),
      primaryTextTheme: _createFiraCodeTextTheme(Colors.white, Brightness.dark),

      appBarTheme: AppBarTheme(
        backgroundColor: const Color(0xFF1E1E1E),
        titleTextStyle: GoogleFonts.firaCode(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color.fromARGB(255, 234, 21, 181),
          foregroundColor: Colors.black,
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.pink[300],
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      cardColor: Colors.grey[850],
      scaffoldBackgroundColor: Colors.grey[900],

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.grey[700],
        border: OutlineInputBorder(
          borderSide: BorderSide.none,
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: GoogleFonts.firaCode(
          color: Colors.grey[400],
          fontStyle: FontStyle.italic,
        ),
      ),

      useMaterial3: true,
      fontFamily: GoogleFonts.firaCode().fontFamily,
    ),
  ),
  'Ocean Blue': ThemeMetadata(
    name: 'Ocean Blue',
    isPremium: true,
    data: ThemeData(
      brightness: Brightness.light,
      primarySwatch: Colors.lightBlue,
      // Apply our custom text theme
      textTheme: _createFiraCodeTextTheme(Colors.white, Brightness.light),
      primaryTextTheme: _createFiraCodeTextTheme(
        Colors.white,
        Brightness.light,
      ),

      appBarTheme: AppBarTheme(
        backgroundColor: Colors.lightBlue.shade700,
        foregroundColor: Colors.white,
        titleTextStyle: GoogleFonts.firaCode(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),

      cardColor: const Color.fromARGB(255, 171, 207, 224),
      scaffoldBackgroundColor: Colors.lightBlue,

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.lightBlue[100],
          foregroundColor: Colors.lightBlue[900],
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

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.white,
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.lightBlue[100],
        border: OutlineInputBorder(
          borderSide: BorderSide.none,
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: GoogleFonts.firaCode(
          color: Colors.lightBlue[700],
          fontStyle: FontStyle.italic,
        ),
      ),

      useMaterial3: true,
      fontFamily: GoogleFonts.firaCode().fontFamily,
    ),
  ),
  'Forest Green': ThemeMetadata(
    name: 'Forest Green',
    isPremium: true,
    data: ThemeData(
      brightness: Brightness.dark,
      primarySwatch: Colors.green,
      // Apply our custom text theme for dark mode
      textTheme: _createFiraCodeTextTheme(Colors.white, Brightness.dark),
      primaryTextTheme: _createFiraCodeTextTheme(Colors.white, Brightness.dark),

      appBarTheme: AppBarTheme(
        backgroundColor: const Color.fromARGB(255, 3, 63, 24),
        titleTextStyle: GoogleFonts.firaCode(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      ),

      cardColor: Colors.green[900]?.withAlpha(204),
      scaffoldBackgroundColor: const Color.fromARGB(255, 3, 63, 24),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.greenAccent,
          foregroundColor: Colors.black,
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.greenAccent,
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.green[800]?.withAlpha(128),
        border: OutlineInputBorder(
          borderSide: BorderSide.none,
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: GoogleFonts.firaCode(
          color: Colors.greenAccent[100],
          fontStyle: FontStyle.italic,
        ),
      ),

      useMaterial3: true,
      fontFamily: GoogleFonts.firaCode().fontFamily,
    ),
  ),
  // Add more themes here following the ThemeMetadata structure
};
