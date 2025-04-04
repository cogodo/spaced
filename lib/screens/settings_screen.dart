import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../themes/theme_data.dart';
import '../main.dart';

class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String? _selectedTheme;

  @override
  Widget build(BuildContext context) {
    final themeNotifier = Provider.of<ThemeNotifier>(context);

    _selectedTheme ??=
        appThemes.entries
            .firstWhere(
              (entry) => entry.value == themeNotifier.currentTheme,
              orElse: () => appThemes.entries.first,
            )
            .key;

    return Scaffold(
      appBar: AppBar(title: Text('Settings')),
      body: Center(
        child: DropdownButton<String>(
          value: _selectedTheme,
          items:
              appThemes.keys.map((String key) {
                return DropdownMenuItem<String>(value: key, child: Text(key));
              }).toList(),
          onChanged: (String? newValue) {
            if (newValue != null) {
              setState(() {
                _selectedTheme = newValue;
                themeNotifier.setTheme(newValue);
              });
            }
          },
        ),
      ),
    );
  }
}
