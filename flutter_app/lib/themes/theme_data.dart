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
      // Use ColorScheme.fromSeed for better cohesive colors
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF0078D7), // Windows blue as seed
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
        systemOverlayStyle: SystemUiOverlayStyle.light,
        backgroundColor: const Color(0xFF0078D7),
      ),

      // More harmonious card and background colors
      cardColor: Colors.white,
      scaffoldBackgroundColor: const Color(
        0xFFE4F0F6,
      ), // Light blue-gray background
      // Cohesive buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF0078D7), // Primary blue
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
          foregroundColor: const Color(0xFF0078D7),
          side: const BorderSide(color: Color(0xFF0078D7), width: 1.5),
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

      // Input decoration
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderSide: BorderSide(
            color: const Color(0xFF0078D7).withValues(alpha: 0.5),
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(
            color: const Color(0xFF0078D7).withValues(alpha: 0.5),
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(color: Color(0xFF0078D7), width: 1.5),
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: GoogleFonts.firaCode(
          color: const Color(0xFF0078D7).withValues(alpha: 0.6),
          fontStyle: FontStyle.italic,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
      ),

      // Add divider color
      dividerColor: const Color(0xFFBEE6FD),

      // Add icon theme
      iconTheme: const IconThemeData(color: Color(0xFF0078D7)),

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
  'Red': ThemeMetadata(
    name: 'Red',
    data: ThemeData(
      // Use a scarlet/red color scheme
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFFD32F2F), // Deep scarlet/red as primary
        brightness: Brightness.light,
        secondary: const Color(0xFF795548), // Brown as secondary
        tertiary: const Color(0xFF009688), // Teal as tertiary
      ),

      // Light neutral background with red undertones
      scaffoldBackgroundColor: const Color(0xFFFFF5F5), // Very light red tint
      cardColor: Colors.white,

      // Apply system overlay style for status bar icons
      appBarTheme: AppBarTheme(
        systemOverlayStyle:
            SystemUiOverlayStyle.light, // Light status bar icons
        backgroundColor: const Color(0xFFD32F2F), // Scarlet app bar
        elevation: 0,
        centerTitle: true, // Center titles for a different look
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(16)),
        ),
      ),

      // Rounded, outlined, scarlet buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.white, // White background
          foregroundColor: const Color(0xFFD32F2F), // Scarlet text
          elevation: 0, // No shadow
          side: const BorderSide(
            color: Color(0xFFD32F2F),
            width: 2,
          ), // Thick border
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: 24,
            vertical: 14,
          ), // More padding
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24), // Very rounded corners
          ),
        ),
      ),

      // Text buttons
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: const Color(0xFF795548), // Brown text
          textStyle: GoogleFonts.firaCode(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        ),
      ),

      // Filled, rounded inputs with light red
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFFFEBEE), // Very light red fill
        border: OutlineInputBorder(
          borderSide: BorderSide.none, // No border
          borderRadius: BorderRadius.circular(16), // Rounded
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide.none,
          borderRadius: BorderRadius.circular(16),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(color: Color(0xFFD32F2F), width: 2),
          borderRadius: BorderRadius.circular(16),
        ),
        hintStyle: GoogleFonts.firaCode(
          color: const Color(0xFFBDBDBD),
          fontStyle: FontStyle.italic,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 20,
          vertical: 16,
        ), // More padding
      ),

      // Styled cards with red shadows
      cardTheme: CardThemeData(
        elevation: 4, // More elevation
        shadowColor: const Color(
          0xFFEF5350,
        ).withValues(alpha: 0.3), // Red tinted shadow
        color: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16.0), // More rounded
          side: BorderSide(
            color: const Color(0xFFFFCDD2).withValues(alpha: 0.5),
            width: 1,
          ), // Subtle border
        ),
      ),

      // Checkboxes and selectable items
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const Color(0xFFD32F2F); // Scarlet when selected
          }
          return Colors.white; // White when not selected
        }),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
      ),

      // Switch theme
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const Color(0xFFD32F2F); // Scarlet when selected
          }
          return Colors.grey[400]; // Grey when not selected
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const Color(
              0xFFEF5350,
            ).withValues(alpha: 0.5); // Light red track
          }
          return Colors.grey[300]; // Grey track when not selected
        }),
      ),

      // Custom text theme with slightly larger sizes
      textTheme: _createFiraCodeTextTheme(
        const Color(0xFF212121),
        Brightness.light,
      ) // Dark text
      .copyWith(
        titleLarge: GoogleFonts.firaCode(
          fontSize: 22,
          fontWeight: FontWeight.w600,
          color: const Color(0xFF212121),
          letterSpacing: 0.15,
        ),
        titleMedium: GoogleFonts.firaCode(
          fontSize: 18, // Larger than default
          fontWeight: FontWeight.w500,
          color: const Color(0xFF212121),
          letterSpacing: 0.15,
        ),
      ),

      primaryTextTheme: _createFiraCodeTextTheme(
        Colors.white, // White text for primary surfaces
        Brightness.light,
      ),

      // Red-toned dividers
      dividerColor: const Color(0xFFFFCDD2), // Light red divider
      dividerTheme: const DividerThemeData(
        color: Color(0xFFFFCDD2),
        thickness: 2, // Thicker dividers
        indent: 12,
        endIndent: 12,
      ),

      // Icon themes
      iconTheme: const IconThemeData(
        color: Color(0xFF795548), // Brown icons
        size: 24, // Slightly larger
      ),
      primaryIconTheme: const IconThemeData(
        color: Colors.white, // White icons on primary surfaces
      ),

      // Floating action button
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: const Color(0xFFD32F2F),
        foregroundColor: Colors.white,
        elevation: 4,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),

      // Ensure useMaterial3 is enabled
      useMaterial3: true,
      fontFamily: GoogleFonts.firaCode().fontFamily,
    ),
  ),
  'Green': ThemeMetadata(
    name: 'Green',
    isPremium: true,
    data: ThemeData(
      brightness: Brightness.dark,
      // Use ColorScheme.fromSeed for more cohesive colors
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF2E7D32), // Deep green seed color
        brightness: Brightness.dark,
      ),
      // Apply our custom text theme for dark mode
      textTheme: _createFiraCodeTextTheme(Colors.white, Brightness.dark),
      primaryTextTheme: _createFiraCodeTextTheme(Colors.white, Brightness.dark),

      // Apply system overlay style for status bar icons
      appBarTheme: AppBarTheme(
        systemOverlayStyle: SystemUiOverlayStyle.light,
        backgroundColor: const Color(0xFF0F2C19), // Dark green surface
      ),

      // Rich green buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF81C784), // Medium green
          foregroundColor: Colors.black, // Black text for better contrast
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
          foregroundColor: const Color(0xFFA5D6A7), // Light green
          side: const BorderSide(color: Color(0xFF4CAF50), width: 1.5),
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
      cardColor: const Color(0xFF1B3726),
      scaffoldBackgroundColor: const Color(0xFF0F2C19),

      // Input decoration matching the theme
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF1B3726),
        border: OutlineInputBorder(
          borderSide: BorderSide(
            color: const Color(0xFF4CAF50).withValues(alpha: 0.5),
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(
            color: const Color(0xFF4CAF50).withValues(alpha: 0.5),
          ),
          borderRadius: BorderRadius.circular(8),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(color: Color(0xFF81C784), width: 1.5),
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: GoogleFonts.firaCode(
          color: const Color(0xFFA5D6A7).withValues(alpha: 0.7),
          fontStyle: FontStyle.italic,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
      ),

      // Add a divider color
      dividerColor: const Color(0xFF2C4C39),

      // Add icon theme
      iconTheme: const IconThemeData(color: Color(0xFF81C784)),

      useMaterial3: true,
      fontFamily: GoogleFonts.firaCode().fontFamily,
    ),
  ),
  // Add more themes here following the ThemeMetadata structure
};
