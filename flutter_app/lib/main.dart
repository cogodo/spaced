import 'package:flutter/material.dart';
import 'package:spaced/models/schedule_manager.dart';
import 'package:spaced/screens/tab_navigation_screen.dart';
import 'package:spaced/screens/auth/login_screen.dart';
import 'package:spaced/screens/landing_screen.dart';
import 'package:spaced/screens/auth/signup_screen.dart';
import 'package:spaced/providers/auth_provider.dart';
import 'themes/theme_data.dart';
import 'package:provider/provider.dart';
import 'services/local_storage_service.dart';
import 'services/firestore_service.dart';
import 'services/logger_service.dart';
import 'package:shared_preferences/shared_preferences.dart'; // Import SharedPreferences
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'dart:async';
import 'routing/app_router.dart';

// Define a global key for the root ScaffoldMessenger
final GlobalKey<ScaffoldMessengerState> rootScaffoldMessengerKey =
    GlobalKey<ScaffoldMessengerState>();

// Logger for main.dart
final _logger = getLogger('Main');

// Key for storing theme preference
const String THEME_PREF_KEY = 'selectedThemeKey';

// Fix for web: declare as const at compile time
const bool kIsProduction = bool.fromEnvironment('dart.vm.product');

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  _logger.info('🚀 Starting Spaced app...');

  // Initialize SharedPreferences
  final prefs = await SharedPreferences.getInstance();

  runApp(
    MultiProvider(
      providers: [
        // Provide SharedPreferences instance
        Provider<SharedPreferences>.value(value: prefs),

        // Theme provider
        ChangeNotifierProvider(create: (_) => ThemeNotifier(prefs)),
        // Authentication provider
        ChangeNotifierProvider(create: (_) => AuthProvider()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  static final _logger = getLogger('MyApp');

  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeNotifier = Provider.of<ThemeNotifier>(context);
    final authProvider = Provider.of<AuthProvider>(context);

    _logger.info('Building app with theme: ${themeNotifier.currentThemeKey}');

    return MaterialApp.router(
      title: 'Spaced',
      theme: themeNotifier.currentTheme,
      scaffoldMessengerKey: rootScaffoldMessengerKey,
      routerConfig: createAppRouter(
        authProvider,
      ), // Pass auth provider to router
    );
  }
}

/// Creates a ScheduleManager for the authenticated user
Future<ScheduleManager> _createScheduleManager(
  BuildContext context,
  String userId,
) async {
  _logger.info('Creating ScheduleManager for user: $userId');

  try {
    // Create storage service based on authentication status
    final storageService = FirestoreService();

    // Create the ScheduleManager
    final scheduleManager = ScheduleManager(
      userId: userId,
      storage: storageService,
    );

    _logger.info('✅ ScheduleManager created successfully');
    return scheduleManager;
  } catch (e, stackTrace) {
    _logger.severe('❌ Error creating ScheduleManager: $e', e, stackTrace);
    rethrow;
  }
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

    // Default to 'Dark' if no preference is stored or the key is invalid
    final String initialThemeKey =
        storedThemeKey != null && appThemes.containsKey(storedThemeKey)
            ? storedThemeKey
            : 'Dark';

    _currentThemeMeta = appThemes[initialThemeKey]!;
    _logger.info('Initial theme set to: $currentThemeKey');
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
