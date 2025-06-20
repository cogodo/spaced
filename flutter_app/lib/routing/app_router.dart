// ignore_for_file: no_leading_underscores_for_local_identifiers

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../screens/landing_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/signup_screen.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/privacy_policy_screen.dart';
import '../screens/tab_navigation_screen.dart';
import '../screens/all_review_items_screen.dart';
import '../screens/chat_screen.dart';
import '../screens/todays_reviews_screen.dart';
import '../screens/user_profile_screen.dart';
import '../providers/auth_provider.dart';
import '../services/logger_service.dart';
import '../main.dart';
import 'route_constants.dart';

/// Create router with auth provider context
GoRouter createAppRouter(AuthProvider authProvider) {
  final _logger = getLogger('AppRouter');

  _logger.info('🏗️ Creating new GoRouter instance');

  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    refreshListenable: authProvider,
    redirect: (context, state) {
      // Access current auth provider from context instead of using closure-captured parameter
      final currentAuthProvider = Provider.of<AuthProvider>(
        context,
        listen: false,
      );
      final currentPath = state.matchedLocation;
      final isSignedIn = currentAuthProvider.isSignedIn;
      final isInitialized = currentAuthProvider.isInitialized;

      _logger.info(
        '🧭 Router redirect: path=$currentPath, signed_in=$isSignedIn, initialized=$isInitialized',
      );

      // Wait for auth initialization
      if (!isInitialized) {
        _logger.info('⏳ Auth not initialized yet, waiting...');
        return null;
      }

      // Redirect signed-in users away from auth pages
      if (isSignedIn &&
          [
            Routes.login,
            Routes.signup,
            Routes.forgotPassword,
          ].contains(currentPath)) {
        _logger.info(
          '🔄 REDIRECTING signed-in user from $currentPath to ${Routes.appChat}',
        );
        return Routes.appChat;
      }

      // PROTECT /app routes - redirect unsigned users to landing
      if (currentPath.startsWith('/app') && !isSignedIn) {
        _logger.info(
          '🔒 REDIRECTING unsigned user from $currentPath to landing page',
        );
        return Routes.landing;
      }

      _logger.info('✅ No redirect needed');
      return null;
    },
    routes: [
      // ===== LANDING & AUTH ROUTES (No protection) =====
      GoRoute(
        path: Routes.landing,
        name: 'landing',
        builder: (context, state) => LandingScreen(),
      ),

      GoRoute(
        path: Routes.login,
        name: 'login',
        builder: (context, state) => LoginScreen(),
      ),

      GoRoute(
        path: Routes.signup,
        name: 'signup',
        builder: (context, state) => SignUpScreen(),
      ),

      GoRoute(
        path: Routes.forgotPassword,
        name: 'forgot-password',
        builder: (context, state) => ForgotPasswordScreen(),
      ),

      GoRoute(
        path: Routes.privacyPolicy,
        name: 'privacy-policy',
        builder: (context, state) => const PrivacyPolicyScreen(),
      ),

      // ===== APP ROUTES (Protected by redirect above) =====

      // Today's Reviews screen
      GoRoute(
        path: Routes.appHome,
        name: 'app-home',
        builder: (context, state) {
          _logger.info('🏠 Building app home route');
          return TabNavigationScreen(child: TodaysReviewsScreen());
        },
      ),

      // All Items screen
      GoRoute(
        path: Routes.appAll,
        name: 'app-all',
        builder: (context, state) {
          _logger.info('📋 Building app all items route');
          return TabNavigationScreen(
            child: AllReviewItemsScreen(
              allTasks: const [],
              onDeleteTask: (task) async {
                // No-op - no more task management
              },
            ),
          );
        },
      ),

      GoRoute(
        path: Routes.appChat,
        name: 'app-chat',
        builder: (context, state) {
          _logger.info('💬 Building app chat route');
          return TabNavigationScreen(child: ChatScreen());
        },
      ),

      // Chat with specific session token
      GoRoute(
        path: '/app/chat/:sessionToken',
        name: 'app-chat-session',
        builder: (context, state) {
          final sessionToken = state.pathParameters['sessionToken']!;
          _logger.info(
            '💬 Building app chat route with session token: $sessionToken',
          );
          return TabNavigationScreen(
            child: ChatScreen(sessionToken: sessionToken),
          );
        },
      ),

      GoRoute(
        path: Routes.appProfile,
        name: 'app-profile',
        builder: (context, state) {
          _logger.info('👤 Building app profile route');
          return TabNavigationScreen(child: UserProfileScreen());
        },
      ),

      // Add missing routes that might still be referenced
      GoRoute(
        path: Routes.appAdd,
        name: 'app-add-redirect',
        redirect: (context, state) => Routes.appChat,
      ),
    ],

    // ===== ERROR HANDLING =====
    errorBuilder: (context, state) {
      return Scaffold(
        appBar: AppBar(title: Text('Page Not Found')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 64),
              SizedBox(height: 16),
              Text('404 - Page Not Found'),
              SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => context.go('/'),
                child: Text('Go Home'),
              ),
            ],
          ),
        ),
      );
    },
  );
}
