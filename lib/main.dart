import 'package:flutter/material.dart';
import 'package:lr_scheduler/models/schedule_manager.dart';
import 'package:lr_scheduler/screens/swipe_navigation_screen.dart';
import 'themes/theme_data.dart';
import 'package:provider/provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  ScheduleManager? scheduleManager;
  try {
    print("Creating ScheduleManager instance...");
    scheduleManager = ScheduleManager();
    print("ScheduleManager instance created. Initializing...");
    await scheduleManager.init();
    print("ScheduleManager initialized successfully.");
  } catch (e, s) {
    print("Error during ScheduleManager creation or initialization: $e\n$s");
    print("ScheduleManager failed to initialize. Showing error screen.");
    runApp(
      MaterialApp(
        home: Scaffold(body: Center(child: Text("Initialization Error: $e"))),
      ),
    );
    return;
  }

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider<ScheduleManager>.value(value: scheduleManager),
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
