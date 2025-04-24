import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // For FilteringTextInputFormatter
import 'package:provider/provider.dart';
import '../services/logger_service.dart';
import '../themes/theme_data.dart';
import '../main.dart';
import '../models/schedule_manager.dart'; // Import ScheduleManager
import '../widgets/theme_preview_card.dart'; // Import the new widget

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _logger = getLogger('SettingsScreen');
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

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: ListView(
        // Keep outer ListView for overall scrolling if needed
        children: [
          // --- Max Repetitions Section (Moved Up) ---
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
                    _logger.info("Submitting max reps: $newValue");
                    scheduleManager.setMaxRepetitions(newValue);
                    rootScaffoldMessengerKey.currentState?.showSnackBar(
                      SnackBar(
                        content: Text('Max Repetitions updated to $newValue'),
                        behavior: SnackBarBehavior.floating,
                        duration: Duration(seconds: 2),
                      ),
                    );
                  } else {
                    _logger.warning("Invalid input for max reps: $value");
                    _maxRepsController.text =
                        scheduleManager.maxRepetitions.toString();
                  }
                  FocusScope.of(context).unfocus();
                },
              ),
            ),
          ),
          Divider(height: 32), // Divider moved up
          // --- App Theme Section ---
          Text('App Theme', style: Theme.of(context).textTheme.titleLarge),
          SizedBox(height: 12),
          // Horizontal ListView for Themes
          SizedBox(
            height: 150, // Define a height for the horizontal list
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: appThemes.length,
              itemBuilder: (context, index) {
                final themeKey = appThemes.keys.elementAt(index);
                final themeMeta = appThemes[themeKey]!;
                final bool isSelected =
                    themeNotifier.currentTheme == themeMeta.data;

                return Container(
                  width: 130, // Define a width for each theme card
                  margin: EdgeInsets.only(right: 10), // Spacing between cards
                  child: GestureDetector(
                    onTap: () {
                      themeNotifier.setTheme(themeMeta.name);
                    },
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        ThemePreviewCard(
                          themeMeta: themeMeta,
                          isSelected: isSelected,
                        ),

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
                  ),
                );
              },
            ),
          ),
          // Divider removed from here
        ],
      ),
    );
  }
}
