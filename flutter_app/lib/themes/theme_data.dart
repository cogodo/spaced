import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // Import for SystemUiOverlayStyle
import 'package:google_fonts/google_fonts.dart';
import 'design_tokens.dart';

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

// Create text theme with Google Fonts (Inter)
TextTheme _createChironSungTextTheme(Color textColor, Brightness brightness) {
  final Color secondaryTextColor =
      brightness == Brightness.light
          ? textColor.withValues(alpha: 208 / 255.0)
          : textColor.withValues(alpha: 230 / 255.0);

  final String fontFamily = GoogleFonts.inter().fontFamily ?? 'Inter';

  return TextTheme(
    // Headings - using Chiron Sung HK for elegant look
    displayLarge: TextStyle(
      fontFamily: fontFamily,
      fontSize: 57,
      fontWeight: FontWeight.w700,
      color: textColor,
      letterSpacing: -0.25,
      height: 1.1,
    ),
    displayMedium: TextStyle(
      fontFamily: fontFamily,
      fontSize: 45,
      fontWeight: FontWeight.w600,
      color: textColor,
      height: 1.2,
    ),
    displaySmall: TextStyle(
      fontFamily: fontFamily,
      fontSize: 36,
      fontWeight: FontWeight.w600,
      color: textColor,
      height: 1.2,
    ),
    headlineLarge: TextStyle(
      fontFamily: fontFamily,
      fontSize: 32,
      fontWeight: FontWeight.w600,
      color: textColor,
      height: 1.25,
    ),
    headlineMedium: TextStyle(
      fontFamily: fontFamily,
      fontSize: 28,
      fontWeight: FontWeight.w600,
      color: textColor,
      height: 1.25,
    ),
    headlineSmall: TextStyle(
      fontFamily: fontFamily,
      fontSize: 24,
      fontWeight: FontWeight.w600,
      color: textColor,
      height: 1.3,
    ),
    titleLarge: TextStyle(
      fontFamily: fontFamily,
      fontSize: 22,
      fontWeight: FontWeight.w500,
      color: textColor,
      height: 1.3,
    ),

    // Body text - using Chiron Sung HK for excellent readability
    titleMedium: TextStyle(
      fontFamily: fontFamily,
      fontSize: 16,
      fontWeight: FontWeight.w500,
      color: textColor,
      letterSpacing: 0.1,
      height: 1.4,
    ),
    titleSmall: TextStyle(
      fontFamily: fontFamily,
      fontSize: 14,
      fontWeight: FontWeight.w500,
      color: textColor,
      letterSpacing: 0.1,
      height: 1.4,
    ),
    bodyLarge: TextStyle(
      fontFamily: fontFamily,
      fontSize: 16,
      fontWeight: FontWeight.w400,
      color: textColor,
      letterSpacing: 0.15,
      height: 1.5,
    ),
    bodyMedium: TextStyle(
      fontFamily: fontFamily,
      fontSize: 14,
      fontWeight: FontWeight.w400,
      color: textColor,
      letterSpacing: 0.2,
      height: 1.5,
    ),
    bodySmall: TextStyle(
      fontFamily: fontFamily,
      fontSize: 12,
      fontWeight: FontWeight.w400,
      color: secondaryTextColor,
      letterSpacing: 0.4,
      height: 1.4,
    ),

    // Labels - using Chiron Sung HK for consistency
    labelLarge: TextStyle(
      fontFamily: fontFamily,
      fontSize: 14,
      fontWeight: FontWeight.w500,
      color: textColor,
      letterSpacing: 0.1,
      height: 1.4,
    ),
    labelMedium: TextStyle(
      fontFamily: fontFamily,
      fontSize: 12,
      fontWeight: FontWeight.w500,
      color: textColor,
      letterSpacing: 0.5,
      height: 1.33,
    ),
    labelSmall: TextStyle(
      fontFamily: fontFamily,
      fontSize: 11,
      fontWeight: FontWeight.w500,
      color: textColor,
      letterSpacing: 0.5,
      height: 1.45,
    ),
  );
}

// Map holding the ThemeMetadata objects, keyed by name
final Map<String, ThemeMetadata> appThemes = {
  'Light': ThemeMetadata(
    name: 'Light',
    data: ThemeData(
      brightness: Brightness.light,
      // Use ColorScheme.fromSeed with even paler violet seed
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFFF4EEFF),
        brightness: Brightness.light,
      ),
      extensions: <ThemeExtension<dynamic>>[
        const SpacedTokens(
          brandPrimary: Color(0xFFFAF7FF),
          brandSecondary: Color(0xFFD7F1FF),
          brandAccent: Color(0xFFFFDEE5),
          brandOnPrimary: Colors.white,
          success: Color(0xFFD1FAE5),
          warning: Color(0xFFF9A825),
          error: Color(0xFFD32F2F),
          info: Color(0xFF0288D1),
          background: Colors.white,
          surface: Color(0xFFFFFFFF),
          surfaceAlt: Color(0xFFF7F7FB),
          surfaceElevated: Color(0xFFF0EFF7),
          onBackground: Color(0xFF0E0E13),
          onSurface: Color(0xFF0E0E13),
          outline: Color(0x1AF2ECFF),
        ),
      ],
      // TEMP: use white text to verify full-black background wiring
      textTheme: _createChironSungTextTheme(Colors.white, Brightness.light),
      primaryTextTheme: _createChironSungTextTheme(
        Colors.white,
        Brightness.light,
      ),

      // System UI overlay
      appBarTheme: const AppBarTheme(
        systemOverlayStyle: SystemUiOverlayStyle.dark,
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),

      // Backgrounds - unify surfaces for liminal look
      cardColor: const Color(0xFF0B0B11),
      scaffoldBackgroundColor: const Color(0xFF0B0B11),
      // Pale-accent buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFF2ECFF),
          foregroundColor: Colors.white,
          elevation: 2,
          shadowColor: const Color(0x80F2ECFF),
          textStyle: TextStyle(
            fontFamily: GoogleFonts.inter().fontFamily,
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
          foregroundColor: const Color(0xFFFAF7FF),
          side: const BorderSide(
            color: Color(0xFFFAF7FF),
            width: 1.5,
          ), // Purple border
          textStyle: TextStyle(
            fontFamily: GoogleFonts.inter().fontFamily,
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
        hintStyle: TextStyle(
          color: const Color(0xFF6750A4).withValues(alpha: 0.6),
          fontStyle: FontStyle.italic,
          fontFamily: GoogleFonts.inter().fontFamily,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
      ),

      // Dividers and icons
      dividerColor: const Color(0xFFF2ECFF).withValues(alpha: 0.2),
      iconTheme: const IconThemeData(color: Color(0xFFF2ECFF)),
      // Component themes (Light)
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        surfaceTintColor: const Color(0xFF6750A4).withValues(alpha: 0.06),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: BorderSide(
            color: const Color(0xFF6750A4).withValues(alpha: 0.1),
          ),
        ),
        margin: const EdgeInsets.all(8),
      ),
      chipTheme: const ChipThemeData(
        backgroundColor: Color(0xFFF0EFF7),
        selectedColor: Color(0xFF6750A4),
        secondarySelectedColor: Color(0xFF6750A4),
        checkmarkColor: Colors.white,
        labelStyle: TextStyle(color: Colors.black87),
        secondaryLabelStyle: TextStyle(color: Colors.white),
        brightness: Brightness.light,
        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        shape: StadiumBorder(),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: const Color(0xFF6750A4),
        contentTextStyle: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w600,
        ),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: Colors.white,
        surfaceTintColor: const Color(0xFF6750A4).withValues(alpha: 0.06),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      listTileTheme: const ListTileThemeData(
        iconColor: Color(0xFF6750A4),
        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),

      useMaterial3: true,
    ),
  ),
  'Dark': ThemeMetadata(
    name: 'Dark',
    data: ThemeData(
      brightness: Brightness.dark,
      // Use ColorScheme.fromSeed with even paler violet seed
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFFF4EEFF),
        brightness: Brightness.dark,
      ),
      extensions: <ThemeExtension<dynamic>>[
        const SpacedTokens(
          brandPrimary: Color(0xFFFAF7FF),
          brandSecondary: Color(0xFFD7F1FF),
          brandAccent: Color(0xFFFFDEE5),
          brandOnPrimary: Colors.white,
          success: Color(0xFFD1FAE5),
          warning: Color(0xFFFFB300),
          error: Color(0xFFEF5350),
          info: Color(0xFF4FC3F7),
          background: Color(0xFF0B0B11),
          surface: Color(0xFF11111A),
          surfaceAlt: Color(0xFF0D0D14),
          surfaceElevated: Color(0xFF1A1A28),
          onBackground: Color(0xFFF5F7FF),
          onSurface: Color(0xFFF2F3F7),
          outline: Color(0x333C3C50),
        ),
      ],
      // Apply our custom text theme for dark mode
      textTheme: _createChironSungTextTheme(Colors.white, Brightness.dark),
      primaryTextTheme: _createChironSungTextTheme(
        Colors.white,
        Brightness.dark,
      ),

      // Apply system overlay style for status bar icons
      appBarTheme: const AppBarTheme(
        systemOverlayStyle: SystemUiOverlayStyle.light,
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),

      // Pale-accent buttons
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFF2ECFF),
          foregroundColor: Colors.white,
          elevation: 3,
          shadowColor: const Color(0x80F2ECFF),
          textStyle: TextStyle(
            fontFamily: GoogleFonts.inter().fontFamily,
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
          foregroundColor: const Color(0xFFE9F6FF),
          side: const BorderSide(color: Color(0xFFE9F6FF), width: 1.5),
          textStyle: TextStyle(
            fontFamily: GoogleFonts.inter().fontFamily,
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.5,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),

      // Backgrounds - unify surfaces for liminal look
      cardColor: const Color(0xFF0B0B11),
      scaffoldBackgroundColor: const Color(0xFF0B0B11),

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
        hintStyle: TextStyle(
          color: Colors.grey[400],
          fontStyle: FontStyle.italic,
          fontFamily: GoogleFonts.inter().fontFamily,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 12,
        ),
      ),

      // Add a divider color
      dividerColor: const Color(0xFF3D3A50),

      // Add icon theme
      iconTheme: const IconThemeData(color: Color(0xFFCBB6FF)),

      // Component themes (Dark)
      cardTheme: CardThemeData(
        color: const Color(0xFF2D2D40),
        elevation: 0,
        surfaceTintColor: const Color(0xFF9A86FD).withValues(alpha: 0.05),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: Color(0xFF3D3A50), width: 1),
        ),
        margin: const EdgeInsets.all(8),
      ),
      chipTheme: const ChipThemeData(
        backgroundColor: Color(0xFF34344A),
        selectedColor: Color(0xFF9A86FD),
        secondarySelectedColor: Color(0xFF9A86FD),
        checkmarkColor: Colors.white,
        labelStyle: TextStyle(color: Colors.white),
        secondaryLabelStyle: TextStyle(color: Colors.white),
        brightness: Brightness.dark,
        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        shape: StadiumBorder(),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: const Color(0xFF9A86FD),
        contentTextStyle: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w600,
        ),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: const Color(0xFF2D2D40),
        surfaceTintColor: const Color(0xFF9A86FD).withValues(alpha: 0.05),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      listTileTheme: const ListTileThemeData(
        iconColor: Color(0xFF9A86FD),
        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),

      useMaterial3: true,
    ),
  ),
  // Removed Red and Green themes to simplify to just Light/Dark toggle
};
