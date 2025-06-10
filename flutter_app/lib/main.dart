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

  // Performance optimization: Set up error handling early
  FlutterError.onError = (FlutterErrorDetails details) {
    if (!kIsProduction) {
      FlutterError.dumpErrorToConsole(details);
    }
  };

  // Initialize logging service based on environment
  if (kIsProduction) {
    // loggerService.enableProductionLogs();
    _logger.info('Running in production mode');
  } else {
    // loggerService.enableDebugLogs();
    _logger.info('Running in development mode with debug logs enabled');
  }

  // Initialize local storage service for fallback
  final localStorageService = LocalStorageService();
  _logger.info('LocalStorageService initialized');

  // Initialize Firestore service for authenticated users
  final firestoreService = FirestoreService();
  _logger.info('FirestoreService initialized');

  // Initialize SharedPreferences
  final prefs = await SharedPreferences.getInstance();
  _logger.info('SharedPreferences initialized');

  runApp(
    MultiProvider(
      providers: [
        // Provide LocalStorageService
        Provider<LocalStorageService>.value(value: localStorageService),

        // Provide FirestoreService
        Provider<FirestoreService>.value(value: firestoreService),

        // Provide SharedPreferences instance
        Provider<SharedPreferences>.value(value: prefs),

        // Authentication Provider
        ChangeNotifierProvider(create: (_) => AuthProvider()),

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

class MyApp extends StatelessWidget {
  static final _logger = getLogger('MyApp');

  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeNotifier = Provider.of<ThemeNotifier>(context);
    _logger.info('Building app with theme: ${themeNotifier.currentThemeKey}');

    return MaterialApp(
      title: 'Spaced',
      theme: themeNotifier.currentTheme,
      scaffoldMessengerKey: rootScaffoldMessengerKey,
      home: const AuthWrapper(),
    );
  }
}

/// Wrapper widget that determines whether to show landing page or authenticated app
class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  static final _logger = getLogger('AuthWrapper');
  static int buildCount = 0;

  bool showLoginScreen = false;
  bool showSignUpScreen = false;
  bool showLandingWhileSignedIn =
      false; // New state for landing ↔ app navigation

  void _navigateToLogin() {
    setState(() {
      showLoginScreen = true;
      showSignUpScreen = false;
      showLandingWhileSignedIn = false;
    });
  }

  void _navigateToSignUp() {
    setState(() {
      showLoginScreen = false;
      showSignUpScreen = true;
      showLandingWhileSignedIn = false;
    });
  }

  void _navigateToLanding() {
    setState(() {
      showLoginScreen = false;
      showSignUpScreen = false;
      showLandingWhileSignedIn = false;
    });
  }

  void _navigateToLandingWhileSignedIn() {
    setState(() {
      showLoginScreen = false;
      showSignUpScreen = false;
      showLandingWhileSignedIn = true;
    });
  }

  void _navigateBackToApp() {
    setState(() {
      showLoginScreen = false;
      showSignUpScreen = false;
      showLandingWhileSignedIn = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        buildCount++;
        _logger.info(
          '🔍 AuthWrapper Consumer BUILD #$buildCount - isSignedIn: ${authProvider.isSignedIn}',
        );

        // Show loading screen while auth provider is initializing
        if (!authProvider.isInitialized) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        // Reset navigation state when user signs out
        if (!authProvider.isSignedIn &&
            (showLoginScreen || showSignUpScreen || showLandingWhileSignedIn)) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            setState(() {
              showLoginScreen = false;
              showSignUpScreen = false;
              showLandingWhileSignedIn = false;
            });
          });
        }

        // Show the main app if user is signed in
        if (authProvider.isSignedIn) {
          // Check if user wants to see landing page while signed in
          if (showLandingWhileSignedIn) {
            _logger.info('📱 Showing LandingScreen (while signed in)');
            return LandingScreen(
              onNavigateToLogin:
                  _navigateBackToApp, // "Back to App" functionality
            );
          }

          _logger.info('✅ User IS SIGNED IN - showing AuthenticatedApp');
          return AuthenticatedApp(
            onNavigateToLanding: _navigateToLandingWhileSignedIn,
          );
        }

        // State-based rendering - NO NAVIGATION!
        if (showSignUpScreen) {
          _logger.info('📱 Showing SignUpScreen');
          return SignUpScreen(
            onNavigateToLogin: _navigateToLogin,
            onBackToLanding: _navigateToLanding,
          );
        }

        if (showLoginScreen) {
          _logger.info('📱 Showing LoginScreen');
          return LoginScreen(
            onNavigateToSignUp: _navigateToSignUp,
            onBackToLanding: _navigateToLanding,
          );
        }

        // Show landing page by default
        _logger.info('📱 Showing LandingScreen');
        return LandingScreen(onNavigateToLogin: _navigateToLogin);
      },
    );
  }
}

/// Main app for authenticated users with Firebase integration
class AuthenticatedApp extends StatelessWidget {
  static final _logger = getLogger('AuthenticatedApp');
  final VoidCallback onNavigateToLanding;

  const AuthenticatedApp({super.key, required this.onNavigateToLanding});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        final user = authProvider.user;
        if (user == null) {
          _logger.warning('AuthenticatedApp rendered with null user');
          return const Scaffold(
            body: Center(child: Text('Authentication error')),
          );
        }

        return FutureBuilder<ScheduleManager>(
          future: _createScheduleManager(context, user.uid),
          builder: (context, snapshot) {
            _logger.info(
              'FutureBuilder state: ${snapshot.connectionState}, hasError: ${snapshot.hasError}, hasData: ${snapshot.hasData}',
            );

            if (snapshot.connectionState == ConnectionState.waiting) {
              _logger.info(
                'FutureBuilder: Still waiting for ScheduleManager...',
              );
              return const Scaffold(
                body: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('Setting up your workspace...'),
                    ],
                  ),
                ),
              );
            }

            if (snapshot.hasError) {
              _logger.severe(
                'Error creating ScheduleManager: ${snapshot.error}',
              );
              return Scaffold(
                body: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 64, color: Colors.red),
                      SizedBox(height: 16),
                      Text('Error setting up workspace'),
                      SizedBox(height: 8),
                      Text('${snapshot.error}', style: TextStyle(fontSize: 12)),
                    ],
                  ),
                ),
              );
            }

            final scheduleManager = snapshot.data!;
            _logger.info(
              'FutureBuilder: About to display TabNavigationScreen with ScheduleManager for user: ${user.uid}',
            );

            return ChangeNotifierProvider<ScheduleManager>.value(
              value: scheduleManager,
              child: Builder(
                builder: (context) {
                  _logger.info(
                    'Provider Builder: About to render TabNavigationScreen',
                  );

                  // Test if Provider is working
                  try {
                    final testManager = Provider.of<ScheduleManager>(
                      context,
                      listen: false,
                    );
                    _logger.info(
                      'Provider test successful: ${testManager.userId}',
                    );
                  } catch (e) {
                    _logger.severe('Provider test failed: $e');
                  }

                  return TabNavigationScreen(
                    onNavigateToLanding: onNavigateToLanding,
                  );
                },
              ),
            );
          },
        );
      },
    );
  }

  /// Creates a ScheduleManager with Firestore, falls back to LocalStorage if needed
  Future<ScheduleManager> _createScheduleManager(
    BuildContext context,
    String userId,
  ) async {
    _logger.info('Creating ScheduleManager for user: $userId');

    final firestoreService = Provider.of<FirestoreService>(
      context,
      listen: false,
    );
    final localStorageService = Provider.of<LocalStorageService>(
      context,
      listen: false,
    );

    try {
      // Try to use Firestore first
      _logger.info('Testing Firestore connectivity...');
      await firestoreService.getUserDocument(userId).get();

      _logger.info('Firestore available - using FirestoreService');
      return ScheduleManager(userId: userId, storage: firestoreService);
    } catch (e) {
      _logger.warning(
        'Firestore not available, falling back to LocalStorage: $e',
      );

      // Create ScheduleManager with local storage
      final scheduleManager = ScheduleManager(
        userId: userId,
        storage: localStorageService,
      );

      // Set up background sync when Firestore becomes available
      _setupBackgroundSync(scheduleManager, firestoreService, userId);

      return scheduleManager;
    }
  }

  /// Set up background sync to retry Firestore connection
  void _setupBackgroundSync(
    ScheduleManager scheduleManager,
    FirestoreService firestoreService,
    String userId,
  ) {
    _logger.info('Setting up background sync for user: $userId');

    // Retry Firestore connection every 30 seconds
    Timer.periodic(const Duration(seconds: 30), (timer) async {
      try {
        // Test if Firestore is now available
        await firestoreService.getUserDocument(userId).get();

        _logger.info('Firestore connection restored! Enabling sync...');

        // Enable cloud storage for syncing
        scheduleManager.setCloudStorage(firestoreService);

        // Cancel the timer since we're now connected
        timer.cancel();
      } catch (e) {
        _logger.info('Firestore still unavailable, will retry...');
      }
    });
  }
}
