import 'package:flutter/material.dart';

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
      brightness: Brightness.light,
      primarySwatch: Colors.grey, // Example primary color
      // Define other light theme properties...
      cardColor: Colors.white,
      scaffoldBackgroundColor: Colors.grey[100],
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color.fromARGB(255, 54, 56, 58),
          foregroundColor: Colors.white,
        ),
        
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.grey[200],
        border: OutlineInputBorder(
          borderSide: BorderSide.none,
          borderRadius: BorderRadius.circular(8),
        ),
        hintStyle: TextStyle(color: Colors.grey[600]),
      ),
      // ... etc
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
      cardColor: Colors.lightBlue[50],
      scaffoldBackgroundColor: Colors.white,
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.lightBlue,
          foregroundColor: Colors.white,
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
      cardColor: Colors.green[900]?.withOpacity(0.8),
      scaffoldBackgroundColor: const Color.fromARGB(255, 3, 63, 24),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.greenAccent,
          foregroundColor: Colors.black,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.green[800]?.withOpacity(0.5),
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
