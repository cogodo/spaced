import 'package:flutter/material.dart';

final Map<String, ThemeData> appThemes = {
  'Light': ThemeData(
    primaryColor: Colors.blue,
    colorScheme: ColorScheme.light(secondary: Colors.orange),
    brightness: Brightness.light,
  ),
  'Dark': ThemeData(
    primaryColor: Colors.grey[900],
    colorScheme: ColorScheme.dark(secondary: Colors.teal),
    brightness: Brightness.dark,
  ),
  'Custom': ThemeData(
    primaryColor: Colors.purple,
    colorScheme: ColorScheme.light(secondary: Colors.amber),
    brightness: Brightness.light,
  ),
};
