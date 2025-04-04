import 'package:flutter/material.dart';
import 'package:lr_scheduler/models/schedule_manager.dart';
import 'package:lr_scheduler/screens/swipe_navigation_screen.dart';
import 'themes/theme_data.dart';
import 'package:provider/provider.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final scheduleManager = ScheduleManager();
  runApp(
    MultiProvider(
      providers: [
        Provider<ScheduleManager>.value(value: scheduleManager),
        ChangeNotifierProvider(create: (_) => ThemeNotifier()),
      ],
      child: MyApp(),
    ),
  );
}

class ThemeNotifier with ChangeNotifier {
  ThemeData _currentTheme = appThemes['Light']!;

  ThemeData get currentTheme => _currentTheme;

  void setTheme(String themeKey) {
    if (appThemes.containsKey(themeKey)) {
      _currentTheme = appThemes[themeKey]!;
      notifyListeners();
    }
  }
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final themeNotifier = Provider.of<ThemeNotifier>(context);

    return MaterialApp(
      title: 'LR Scheduler',
      theme: themeNotifier.currentTheme,
      home: SwipeNavigationScreen(),
    );
  }
}
