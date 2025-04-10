import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // For FilteringTextInputFormatter
import 'package:provider/provider.dart';
import '../themes/theme_data.dart';
import '../main.dart';
import '../models/schedule_manager.dart'; // Import ScheduleManager
import '../widgets/theme_preview_card.dart'; // Import the new widget

class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _maxRepsController;

  @override
  void initState() {
    super.initState();
    final scheduleManager = Provider.of<ScheduleManager>(
      context,
      listen: false,
    );
    _maxRepsController = TextEditingController(
      text: scheduleManager.maxRepetitions.toString(),
    );
  }

  @override
  void dispose() {
    _maxRepsController.dispose();
    super.dispose();
  }

  // Placeholder for upgrade dialog
  void _showUpgradeDialog() {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: Text('Upgrade Required'),
            content: Text('This theme requires the Pro version.'),
            actions: [
              TextButton(
                child: Text('OK'),
                onPressed: () => Navigator.of(context).pop(),
              ),
            ],
          ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final themeNotifier = Provider.of<ThemeNotifier>(context);
    final scheduleManager = Provider.of<ScheduleManager>(context);

    if (_maxRepsController.text != scheduleManager.maxRepetitions.toString()) {
      _maxRepsController.text = scheduleManager.maxRepetitions.toString();
      _maxRepsController.selection = TextSelection.fromPosition(
        TextPosition(offset: _maxRepsController.text.length),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text('Settings')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
            ListTile(
              title: Text('Max Repetitions Before Completion'),
              subtitle: Text(
                'Task is considered learned after this many successful reviews.',
              ),
              trailing: SizedBox(
                width: 80, // Constrain width
                child: TextField(
                  controller: _maxRepsController,
                  keyboardType: TextInputType.number,
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly, // Allow only digits
                  ],
                  textAlign: TextAlign.center,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(),
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                  ),
                  onSubmitted: (String value) {
                    final int? newValue = int.tryParse(value);
                    if (newValue != null) {
                      print("Submitting max reps: $newValue");
                      scheduleManager.setMaxRepetitions(newValue);
                      // Optional: Show confirmation
                      rootScaffoldMessengerKey.currentState?.showSnackBar(
                        SnackBar(
                          content: Text('Max Repetitions updated to $newValue'),
                          behavior: SnackBarBehavior.floating,
                          duration: Duration(seconds: 2),
                        ),
                      );
                    } else {
                      print("Invalid input for max reps: $value");
                      _maxRepsController.text =
                          scheduleManager.maxRepetitions.toString();
                    }
                    FocusScope.of(context).unfocus();
                  },
                ),
              ),
            ),
            Text('App Theme', style: Theme.of(context).textTheme.titleLarge),
            SizedBox(height: 8),
            // GridView for Themes
            GridView.count(
              crossAxisCount: 2, // Adjust columns as needed
              shrinkWrap: true, // Important inside ListView
              physics:
                  NeverScrollableScrollPhysics(), // Disable GridView's scrolling
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
              children:
                  appThemes.values.map((themeMeta) {
                    // Determine if the current theme in the loop is the selected one
                    final bool isSelected =
                        themeNotifier.currentTheme == themeMeta.data;
                    return GestureDetector(
                      onTap: () {
                        if (themeMeta.isPremium && !scheduleManager.userIsPro) {
                          _showUpgradeDialog();
                        } else {
                          // Use the theme NAME (key) to set the theme
                          themeNotifier.setTheme(themeMeta.name);
                        }
                      },
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          ThemePreviewCard(
                            themeMeta: themeMeta,
                            isSelected: isSelected,
                          ),
                          if (themeMeta.isPremium && !scheduleManager.userIsPro)
                            Positioned(
                              top: 8,
                              right: 8,
                              child: Icon(
                                Icons.lock,
                                color:
                                    themeMeta.data.brightness == Brightness.dark
                                        ? Colors.white70
                                        : Colors.black54,
                                size: 18,
                              ),
                            ),
                        ],
                      ),
                    );
                  }).toList(),
            ),
            Divider(height: 32),

            // Max Repetitions Input
          ],
        ),
      ),
    );
  }
}
