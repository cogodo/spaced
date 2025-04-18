import 'package:flutter/material.dart';
import 'package:lr_scheduler/models/schedule_manager.dart';
import 'package:lr_scheduler/screens/swipe_navigation_screen.dart';
import 'themes/theme_data.dart';
import 'package:provider/provider.dart';
import 'screens/login_screen.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'services/auth_service.dart';
import 'widgets/auth_wrapper.dart';

// Define a global key for the root ScaffoldMessenger
final GlobalKey<ScaffoldMessengerState> rootScaffoldMessengerKey =
    GlobalKey<ScaffoldMessengerState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
    print("Firebase initialized successfully.");
  } catch (e) {
    print("Firebase initialization failed: $e");
    // Handle critical error if Firebase is essential
    runApp(
      MaterialApp(
        home: Scaffold(
          body: Center(child: Text("Error initializing Firebase: $e")),
        ),
      ),
    );
    return;
  }

  // No longer create ScheduleManager here
  // ScheduleManager? scheduleManager;
  // try { ... } catch { ... }

  runApp(
    MultiProvider(
      providers: [
        // Provide Firebase instances
        Provider<FirebaseAuth>.value(value: FirebaseAuth.instance),
        Provider<FirebaseFirestore>.value(value: FirebaseFirestore.instance),
        // Auth Service depends on FirebaseAuth
        ChangeNotifierProvider<AuthService>(
          create: (context) => AuthService(context.read<FirebaseAuth>()),
        ),
        // Theme Notifier is independent
        ChangeNotifierProvider(create: (_) => ThemeNotifier()),

        // ScheduleManager depends on AuthService (for User) and Firestore
        ChangeNotifierProxyProvider<AuthService, ScheduleManager?>(
          create: (context) => null, // Initial value is null
          update: (context, authService, previousScheduleManager) {
            final user = authService.currentUser;
            if (user != null) {
              // If user exists, create/update ScheduleManager
              // Check if manager already exists for this user to avoid unnecessary reloads
              if (previousScheduleManager == null ||
                  previousScheduleManager.userId != user.uid) {
                print(
                  "[ProxyProvider] Creating new ScheduleManager for user ${user.uid}",
                );
                return ScheduleManager(
                  userId: user.uid,
                  firestore: context.read<FirebaseFirestore>(),
                );
              }
              // Otherwise, return the existing manager instance
              return previousScheduleManager;
            } else {
              // If user is null, dispose of previous manager (if any) and return null
              print(
                "[ProxyProvider] User is null, returning null ScheduleManager",
              );
              // Note: Provider automatically handles disposal of ChangeNotifier if needed
              return null;
            }
          },
        ),
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
      home: AuthWrapper(),
    );
  }
}
