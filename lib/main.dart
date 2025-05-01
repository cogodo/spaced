import 'package:flutter/material.dart';
import 'package:spaced/models/schedule_manager.dart';
import 'package:spaced/screens/tab_navigation_screen.dart';
import 'themes/theme_data.dart';
import 'package:provider/provider.dart';
import 'services/local_storage_service.dart';
import 'services/logger_service.dart';
import 'package:shared_preferences/shared_preferences.dart'; // Import SharedPreferences

// Define a global key for the root ScaffoldMessenger
final GlobalKey<ScaffoldMessengerState> rootScaffoldMessengerKey =
    GlobalKey<ScaffoldMessengerState>();

// Use a fixed user ID for local storage - no auth needed
const String LOCAL_USER_ID = "local_user";

// Logger for main.dart
final _logger = getLogger('Main');

// Key for storing theme preference
const String THEME_PREF_KEY = 'selectedThemeKey';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize logging service based on environment
  const bool isProduction = bool.fromEnvironment('dart.vm.product');
  if (isProduction) {
    loggerService.enableProductionLogs();
    _logger.info('Running in production mode');
  } else {
    loggerService.enableDebugLogs();
    _logger.info('Running in development mode with debug logs enabled');
  }

  // Initialize local storage service
  final localStorageService = LocalStorageService();
  _logger.info('LocalStorageService initialized');

  // Initialize SharedPreferences
  final prefs = await SharedPreferences.getInstance();
  _logger.info('SharedPreferences initialized');

  // Create a schedule manager directly with the fixed user ID
  final scheduleManager = ScheduleManager(
    userId: LOCAL_USER_ID,
    storage: localStorageService,
  );
  _logger.info('ScheduleManager initialized with user ID: $LOCAL_USER_ID');

  runApp(
    MultiProvider(
      providers: [
        // Provide LocalStorageService
        Provider<LocalStorageService>.value(value: localStorageService),

        // Provide SharedPreferences instance
        Provider<SharedPreferences>.value(value: prefs),

        // Directly provide fully initialized ScheduleManager
        ChangeNotifierProvider<ScheduleManager>.value(value: scheduleManager),

        // Theme Notifier now depends on SharedPreferences
        ChangeNotifierProvider(create: (_) => ThemeNotifier(prefs)),
      ],
      child: const MyApp(),
    ),
  );

  _logger.info('App started successfully');
}

class ThemeNotifier with ChangeNotifier {
  // Logger for ThemeNotifier
  final _logger = getLogger('ThemeNotifier');
  final SharedPreferences _prefs;

  // Store the whole ThemeMetadata object
  late ThemeMetadata _currentThemeMeta;

  ThemeNotifier(this._prefs) {
    _loadTheme(); // Load theme on initialization
  }

  // Getter returns the actual ThemeData from the metadata
  ThemeData get currentTheme => _currentThemeMeta.data;
  // Optional: Getter for the current theme name (key)
  String get currentThemeKey => _currentThemeMeta.name;

  void _loadTheme() {
    final String? storedThemeKey = _prefs.getString(THEME_PREF_KEY);
    _logger.info('Loading theme preference: $storedThemeKey');

    // Default to 'Light' if no preference is stored or the key is invalid
    final String initialThemeKey =
        storedThemeKey != null && appThemes.containsKey(storedThemeKey)
            ? storedThemeKey
            : 'Light';

    _currentThemeMeta = appThemes[initialThemeKey]!;
    _logger.info('Initial theme set to: ${currentThemeKey}');
    // No need to notifyListeners here as it's the initial state
  }

  Future<void> _saveTheme(String themeKey) async {
    await _prefs.setString(THEME_PREF_KEY, themeKey);
    _logger.info('Saved theme preference: $themeKey');
  }

  void setTheme(String themeKey) {
    if (appThemes.containsKey(themeKey)) {
      final newMeta = appThemes[themeKey]!;
      if (newMeta != _currentThemeMeta) {
        // Only update if it changed
        _currentThemeMeta = newMeta;
        _logger.info('Theme changed to: $themeKey');
        notifyListeners();
        _saveTheme(themeKey); // Save the new theme preference
      }
    } else {
      _logger.warning('Attempted to set unknown theme: $themeKey');
    }
  }
}

class MyApp extends StatelessWidget {
  static final _logger = getLogger('MyApp');

  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeNotifier = Provider.of<ThemeNotifier>(context);
    _logger.fine('Building app with theme: ${themeNotifier.currentThemeKey}');

    return MaterialApp(
      title: 'Spaced',
      theme: themeNotifier.currentTheme,
      scaffoldMessengerKey: rootScaffoldMessengerKey,
      home: const TabNavigationScreen(),
    );
  }
}
