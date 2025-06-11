import 'package:flutter/material.dart';
import 'package:spaced/models/schedule_manager.dart';
import 'package:spaced/providers/auth_provider.dart';
import 'package:spaced/providers/chat_provider.dart';
import 'themes/theme_data.dart';
import 'package:provider/provider.dart';
import 'services/firestore_service.dart';
import 'services/logger_service.dart';
import 'package:shared_preferences/shared_preferences.dart'; // Import SharedPreferences
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'dart:async';
import 'routing/app_router.dart';
import 'package:flutter/foundation.dart';
import 'package:go_router/go_router.dart';

// Import URL strategy for web
import 'package:flutter_web_plugins/url_strategy.dart';

// Custom page transition builder with no animations
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
    return child; // No transition, just return the child directly
  }
}

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

  // Configure URL strategy for web (path-based routing, no hash)
  if (kIsWeb) {
    usePathUrlStrategy();
  }

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

        // Chat provider for persistent chat state - depends on auth
        ChangeNotifierProxyProvider<AuthProvider, ChatProvider>(
          create: (_) => ChatProvider(),
          update: (_, authProvider, chatProvider) {
            // Update chat provider when auth state changes
            chatProvider?.setUserId(authProvider.user?.uid);
            return chatProvider!;
          },
        ),
      ],
      child: const MyApp(),
    ),
  );
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

/// Wrapper that provides ScheduleManager for authenticated users
class ScheduleManagerProvider extends StatelessWidget {
  final Widget child;

  const ScheduleManagerProvider({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    if (!authProvider.isSignedIn || authProvider.user == null) {
      // Show loading screen during sign-out transition instead of returning child
      // This prevents ProviderNotFoundException while router redirect is processing
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Signing out...'),
            ],
          ),
        ),
      );
    }

    return FutureBuilder<ScheduleManager>(
      future: _createScheduleManager(context, authProvider.user!.uid),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Scaffold(body: Center(child: CircularProgressIndicator()));
        }

        if (snapshot.hasError) {
          return Scaffold(
            body: Center(
              child: Text('Error loading user data: ${snapshot.error}'),
            ),
          );
        }

        return ChangeNotifierProvider<ScheduleManager>.value(
          value: snapshot.data!,
          child: child,
        );
      },
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
