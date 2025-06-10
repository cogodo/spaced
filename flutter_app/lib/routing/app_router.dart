import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'dart:html' as html;

import '../screens/landing_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/signup_screen.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/tab_navigation_screen.dart';
import '../screens/home_screen.dart';
import '../screens/add_screen.dart';
import '../screens/all_review_items_screen.dart';
import '../screens/chat_screen.dart';
import '../screens/user_profile_screen.dart';
import '../models/schedule_manager.dart';
import '../providers/auth_provider.dart';
import 'route_constants.dart';
import 'domain_guard.dart';

/// Create router with auth provider context
GoRouter createAppRouter(AuthProvider authProvider) {
  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    refreshListenable: authProvider, // Listen to auth state changes
    redirect:
        (context, state) => DomainGuard.handleDomainRouting(context, state),
    routes: [
      // ===== LANDING DOMAIN ROUTES (getspaced.app) =====
      GoRoute(
        path: Routes.landing,
        name: 'landing',
        builder: (context, state) {
          return LandingScreen(
            onNavigateToLogin: () => context.go(Routes.login),
          );
        },
      ),

      GoRoute(
        path: Routes.login,
        name: 'login',
        builder:
            (context, state) => LoginScreen(
              onNavigateToSignUp: () => context.go(Routes.signup),
              onBackToLanding: () => context.go(Routes.landing),
            ),
      ),

      GoRoute(
        path: Routes.signup,
        name: 'signup',
        builder:
            (context, state) => SignUpScreen(
              onNavigateToLogin: () => context.go(Routes.login),
              onBackToLanding: () => context.go(Routes.landing),
            ),
      ),

      GoRoute(
        path: Routes.forgotPassword,
        name: 'forgot-password',
        builder: (context, state) => ForgotPasswordScreen(),
      ),

      // ===== APP ROUTES (getspaced.app/app/*) =====
      ShellRoute(
        builder: (context, state, child) {
          return Consumer<ScheduleManager>(
            builder: (context, scheduleManager, _) {
              return TabNavigationScreen(
                child: child,
                onNavigateToLanding: () => context.go(Routes.landing),
              );
            },
          );
        },
        routes: [
          // App home (Today's reviews)
          GoRoute(
            path: Routes.appHome,
            name: 'app-home',
            builder: (context, state) => HomeScreen(),
          ),

          // Add new items
          GoRoute(
            path: Routes.appAdd,
            name: 'app-add',
            builder:
                (context, state) => Consumer<ScheduleManager>(
                  builder:
                      (context, scheduleManager, _) =>
                          AdderScreen(onAddTask: scheduleManager.addTask),
                ),
          ),

          // All items
          GoRoute(
            path: Routes.appAll,
            name: 'app-all',
            builder:
                (context, state) => Consumer<ScheduleManager>(
                  builder:
                      (context, scheduleManager, _) => AllReviewItemsScreen(
                        allTasks: scheduleManager.allTasks,
                        onDeleteTask: scheduleManager.removeTask,
                      ),
                ),
          ),

          // Chat interface
          GoRoute(
            path: Routes.appChat,
            name: 'app-chat',
            builder: (context, state) => ChatScreen(),
          ),

          // User profile
          GoRoute(
            path: Routes.appProfile,
            name: 'app-profile',
            builder:
                (context, state) => UserProfileScreen(
                  onNavigateToLanding: () => context.go(Routes.landing),
                ),
          ),
        ],
      ),
    ],

    // ===== ERROR HANDLING =====
    errorBuilder: (context, state) {
      final currentPath = state.matchedLocation;
      final isAppRoute = currentPath.startsWith('/app');

      return Scaffold(
        appBar: AppBar(
          title: Text('Page Not Found'),
          backgroundColor: Theme.of(context).scaffoldBackgroundColor,
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                size: 64,
                color: Theme.of(context).colorScheme.error,
              ),
              SizedBox(height: 16),
              Text(
                '404 - Page Not Found',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              SizedBox(height: 8),
              Text(
                'The page you\'re looking for doesn\'t exist.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(
                    context,
                  ).textTheme.bodyMedium?.color?.withOpacity(0.7),
                ),
              ),
              SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () {
                  if (isAppRoute) {
                    context.go(Routes.appHome);
                  } else {
                    context.go(Routes.landing);
                  }
                },
                icon: Icon(Icons.home),
                label: Text(isAppRoute ? 'Go to App Home' : 'Go to Landing'),
              ),
            ],
          ),
        ),
      );
    },
  );
}

/// Helper widget for domain errors
Widget _buildDomainError(BuildContext context, String expectedDomain) {
  return Scaffold(
    body: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.warning, size: 64, color: Colors.orange),
          SizedBox(height: 16),
          Text('Wrong Domain'),
          SizedBox(height: 8),
          Text('This content should be accessed from $expectedDomain'),
        ],
      ),
    ),
  );
}
