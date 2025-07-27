import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:go_router/go_router.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_web_plugins/url_strategy.dart';

import 'themes/theme_data.dart';
import 'providers/auth_provider.dart';
import 'providers/chat_provider.dart';
import 'providers/settings_provider.dart';
import 'routing/app_router.dart';
import 'services/logger_service.dart';
import 'firebase_options.dart';

// Global key for showing snackbars from anywhere in the app
final GlobalKey<ScaffoldMessengerState> rootScaffoldMessengerKey =
    GlobalKey<ScaffoldMessengerState>();

// Main logger
final _logger = getLogger('Main');

// Constants for SharedPreferences
const String THEME_PREF_KEY = 'selected_theme';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  _logger.info('🚀 Starting app initialization');

  // Configure URL strategy for web (path-based routing, no hash)
  if (kIsWeb) {
    usePathUrlStrategy();
  }

  // Initialize Firebase
  _logger.info('🔥 Initializing Firebase');
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  // Initialize services
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);

  // Load shared preferences
  _logger.info('📦 Loading SharedPreferences');
  final prefs = await SharedPreferences.getInstance();

  _logger.info('✅ Initialization complete, starting app');

  runApp(MyAppProvider(prefs: prefs));
}

/// Root provider widget that sets up all global providers
class MyAppProvider extends StatelessWidget {
  final SharedPreferences prefs;

  const MyAppProvider({super.key, required this.prefs});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Provide SharedPreferences instance
        Provider<SharedPreferences>.value(value: prefs),

        // Theme provider
        ChangeNotifierProvider(create: (_) => ThemeNotifier(prefs)),

        // Authentication provider
        ChangeNotifierProvider(create: (_) => AuthProvider()),

        // Chat provider for persistent chat state - depends on auth
        ChangeNotifierProxyProvider<AuthProvider, ChatProvider>(
          create: (_) => ChatProvider(),
          update: (_, authProvider, chatProvider) {
            // Update chat provider when auth state changes
            chatProvider?.setUserId(authProvider.user?.uid);
            return chatProvider!;
          },
        ),

        // Settings provider
        ChangeNotifierProvider(create: (_) => SettingsProvider()),
      ],
      child: const MyApp(),
    );
  }
}

class MyApp extends StatelessWidget {
  static final _logger = getLogger('MyApp');
  static GoRouter? _router; // Store router as static

  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeNotifier = Provider.of<ThemeNotifier>(context);
    final authProvider = Provider.of<AuthProvider>(context);
    final chatProvider = Provider.of<ChatProvider>(context, listen: false);

    _logger.info('Building app with theme: ${themeNotifier.currentThemeKey}');

    // Show loading screen while auth is initializing to prevent white screens
    if (!authProvider.isInitialized) {
      return MaterialApp(
        title: 'Spaced',
        theme: themeNotifier.currentTheme,
        home: Scaffold(
          backgroundColor: themeNotifier.currentTheme.scaffoldBackgroundColor,
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.psychology,
                  size: 64,
                  color: themeNotifier.currentTheme.colorScheme.primary,
                ),
                const SizedBox(height: 24),
                Text(
                  'Spaced',
                  style: themeNotifier.currentTheme.textTheme.headlineMedium
                      ?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: themeNotifier.currentTheme.colorScheme.primary,
                      ),
                ),
                const SizedBox(height: 16),
                CircularProgressIndicator(
                  color: themeNotifier.currentTheme.colorScheme.primary,
                ),
              ],
            ),
          ),
        ),
      );
    }

    // Create router only once
    if (_router == null) {
      _logger.info('🚀 Creating new router instance');
      _router = createAppRouter(authProvider);
    } else {
      _logger.info('♻️ Reusing existing router instance');
    }

    // Provide router to chat provider for navigation
    chatProvider.setRouter(_router!);

    return MaterialApp.router(
      title: 'Spaced',
      theme: themeNotifier.currentTheme.copyWith(
        pageTransitionsTheme: const PageTransitionsTheme(
          builders: {
            // Remove transitions for all platforms
            TargetPlatform.android: NoTransitionPageTransitionsBuilder(),
            TargetPlatform.iOS: NoTransitionPageTransitionsBuilder(),
            TargetPlatform.macOS: NoTransitionPageTransitionsBuilder(),
            TargetPlatform.windows: NoTransitionPageTransitionsBuilder(),
            TargetPlatform.linux: NoTransitionPageTransitionsBuilder(),
            TargetPlatform.fuchsia: NoTransitionPageTransitionsBuilder(),
          },
        ),
      ),
      scaffoldMessengerKey: rootScaffoldMessengerKey,
      routerConfig: _router!,
    );
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

/// Custom PageTransitionsBuilder that removes all transitions
class NoTransitionPageTransitionsBuilder extends PageTransitionsBuilder {
  const NoTransitionPageTransitionsBuilder();

  @override
  Widget buildTransitions<T extends Object?>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    return child; // Return child directly without any transitions
  }
}
