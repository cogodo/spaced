import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // Import for SystemUiOverlayStyle

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

// Map holding the ThemeMetadata objects, keyed by name
final Map<String, ThemeMetadata> appThemes = {
  'Light': ThemeMetadata(
    name: 'Light',
    data: ThemeData(
      // Use ColorScheme.fromSeed for modern color generation
      colorScheme: ColorScheme.fromSeed(
        seedColor: Colors.blueGrey, // Seed color - influences overall palette
        brightness: Brightness.light,
        // Optional: Override specific scheme colors if needed
        // primary: Colors.blueGrey[700],
        // secondary: Colors.tealAccent,
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
      ),

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          // Use primary color from the generated scheme
          backgroundColor:
              Colors.blueGrey[700], // Use a darker shade for contrast
          foregroundColor: Colors.white, // White text on button
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10), // Rounded corners
          ),
          padding: EdgeInsets.symmetric(
            horizontal: 20,
            vertical: 12,
          ), // Standard padding
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        
        fillColor: Colors.grey[300], // Slightly darker fill for inputs
        hintStyle: TextStyle(color: Colors.grey[600]), // Lighter hint text
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
          // side: BorderSide(color: Colors.grey[200]!) // Optional: Subtle border
        ),
      ),

      textTheme: TextTheme(
        // Define specific text styles if needed, otherwise defaults work with scheme
        titleLarge: TextStyle(color: Colors.black),
        bodyMedium: TextStyle(color: Colors.blueGrey[700]),
        // ... other styles
      ),
      

      dividerColor: Colors.grey[200], // Light divider color

      iconTheme: IconThemeData(
        color: Colors.grey[700], // Default icon color
      ),

      // Ensure useMaterial3 is enabled for fromSeed to work best
      useMaterial3: true,
    ),
  ),
  'Dark': ThemeMetadata(
    name: 'Dark',
    data: ThemeData(
      brightness: Brightness.dark,
      primarySwatch: Colors.pink, // Example primary color
      // Define other dark theme properties...
      cardColor: Colors.grey[850],
      scaffoldBackgroundColor: Colors.grey[900],
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color.fromARGB(255, 234, 21, 181),
          foregroundColor: Colors.black,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.grey[700],
        border: OutlineInputBorder(
          borderSide: BorderSide.none,
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: TextStyle(color: Colors.grey[400]),
      ),
      // ... etc
    ),
  ),
  'Ocean Blue (Pro)': ThemeMetadata(
    name:
        'Ocean Blue (Pro)', // Keep name consistent with key if using name for lookup
    isPremium: true,
    data: ThemeData(
      brightness: Brightness.light,
      primarySwatch: Colors.lightBlue,
      // Define other Ocean Blue theme properties...
      cardColor: const Color.fromARGB(255, 171, 207, 224),
      scaffoldBackgroundColor: Colors.lightBlue,
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.lightBlue[100],
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
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
        hintStyle: TextStyle(color: Colors.lightBlue[700]),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.lightBlue.shade700, // Or Colors.lightBlue, etc.
        // You can also set foregroundColor (for title/icons), elevation, etc. here
        foregroundColor: Colors.white, // Example: Set text/icon color to white
      ),
      // ... etc
    ),
  ),
  'Forest Green (Pro)': ThemeMetadata(
    name: 'Forest Green (Pro)',
    isPremium: true,
    data: ThemeData(
      brightness: Brightness.dark,
      primarySwatch: Colors.green,
      // Define other Forest Green theme properties...
      cardColor: Colors.green[900]?.withAlpha(204),
      scaffoldBackgroundColor: const Color.fromARGB(255, 3, 63, 24),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.greenAccent,
          foregroundColor: Colors.black,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.green[800]?.withAlpha(128),
        border: OutlineInputBorder(
          borderSide: BorderSide.none,
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: TextStyle(color: Colors.greenAccent[100]),
      ),
      // ... etc
    ),
  ),
  // Add more themes here following the ThemeMetadata structure
};
