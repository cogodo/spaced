import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../screens/login_screen.dart';
import '../screens/swipe_navigation_screen.dart';
import '../models/schedule_manager.dart';

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context, listen: false);

    return StreamBuilder<User?>(
      stream: authService.authStateChanges,
      builder: (context, authSnapshot) {
        if (authSnapshot.connectionState == ConnectionState.waiting) {
          return Scaffold(body: Center(child: CircularProgressIndicator()));
        }

        final User? user = authSnapshot.data;

        if (user != null) {
          print(
            "User is signed in (UID: ${user.uid}, Anonymous: ${user.isAnonymous})",
          );
          final scheduleManager = Provider.of<ScheduleManager?>(context);

          if (scheduleManager == null) {
            print(
              "[AuthWrapper] User logged in, waiting for ScheduleManager...",
            );
            return Scaffold(body: Center(child: CircularProgressIndicator()));
          } else {
            print("[AuthWrapper] User logged in and ScheduleManager ready.");
            return SwipeNavigationScreen();
          }
        } else {
          print("User is signed out.");
          return LoginScreen();
        }
      },
    );
  }
}
