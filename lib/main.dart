import 'package:flutter/material.dart';
import 'package:spaced/models/schedule_manager.dart';
import 'package:spaced/screens/tab_navigation_screen.dart';
import 'themes/theme_data.dart';
import 'package:provider/provider.dart';
import 'services/local_storage_service.dart';

// Define a global key for the root ScaffoldMessenger
final GlobalKey<ScaffoldMessengerState> rootScaffoldMessengerKey =
    GlobalKey<ScaffoldMessengerState>();

// Use a fixed user ID for local storage - no auth needed
const String LOCAL_USER_ID = "local_user";

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize local storage service
  final localStorageService = LocalStorageService();

  // Create a schedule manager directly with the fixed user ID
  final scheduleManager = ScheduleManager(
    userId: LOCAL_USER_ID,
    storage: localStorageService,
  );

  runApp(
    MultiProvider(
      providers: [
        // Provide LocalStorageService
        Provider<LocalStorageService>.value(value: localStorageService),

        // Directly provide fully initialized ScheduleManager
        ChangeNotifierProvider<ScheduleManager>.value(value: scheduleManager),

        // Theme Notifier is independent
        ChangeNotifierProvider(create: (_) => ThemeNotifier()),
      ],
      child: MyApp(),
    ),
  );
}

class ThemeNotifier with ChangeNotifier {
  // Store the whole ThemeMetadata object
  ThemeMetadata _currentThemeMeta = appThemes['Light']!;

  // Getter returns the actual ThemeData from the metadata
  ThemeData get currentTheme => _currentThemeMeta.data;
  // Optional: Getter for the current theme name (key)
  String get currentThemeKey => _currentThemeMeta.name;

  void setTheme(String themeKey) {
    if (appThemes.containsKey(themeKey)) {
      final newMeta = appThemes[themeKey]!;
      if (newMeta != _currentThemeMeta) {
        // Only update if it changed
        _currentThemeMeta = newMeta;
        notifyListeners();
      }
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
      scaffoldMessengerKey: rootScaffoldMessengerKey,
      home: TabNavigationScreen(),
    );
  }
}
