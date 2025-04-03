import 'package:flutter/material.dart';

class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool isDarkMode = false;
  double reviewInterval = 24.0; // in hours

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Settings"),
      ),
      body: ListView(
        children: [
          SwitchListTile(
            title: Text("Dark Mode"),
            value: isDarkMode,
            onChanged: (bool newValue) {
              setState(() {
                isDarkMode = newValue;
              });
            },
          ),
          ListTile(
            title: Text("Review Interval (Hours)"),
            subtitle: Text("${reviewInterval.toStringAsFixed(1)} hours"),
            trailing: Icon(Icons.timer),
            onTap: () {
              _selectReviewInterval(context);
            },
          ),
        ],
      ),
    );
  }

  Future<void> _selectReviewInterval(BuildContext context) async {
    // Open a dialog with a slider to select the review interval.
    double? newInterval = await showDialog<double>(
      context: context,
      builder: (context) {
        double tempInterval = reviewInterval;
        return AlertDialog(
          title: Text("Set Review Interval (Hours)"),
          content: StatefulBuilder(
            builder: (BuildContext context, StateSetter setState) {
              return Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text("Interval: ${tempInterval.toStringAsFixed(1)} hours"),
                  Slider(
                    min: 1,
                    max: 48,
                    divisions: 47,
                    value: tempInterval,
                    label: tempInterval.toStringAsFixed(1),
                    onChanged: (double value) {
                      setState(() {
                        tempInterval = value;
                      });
                    },
                  ),
                ],
              );
            },
          ),
          actions: [
            TextButton(
              child: Text("Cancel"),
              onPressed: () => Navigator.of(context).pop(null),
            ),
            TextButton(
              child: Text("Set"),
              onPressed: () => Navigator.of(context).pop(tempInterval),
            ),
          ],
        );
      },
    );

    if (newInterval != null) {
      setState(() {
        reviewInterval = newInterval;
      });
    }
  }
}
