import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'dart:html' as html;

import '../providers/auth_provider.dart';
import 'route_constants.dart';

/// Domain-aware authentication guard
/// Handles authentication state and routing with return URL support
class DomainGuard {
  static String? handleDomainRouting(
    BuildContext context,
    GoRouterState state,
  ) {
    final currentHost = html.window.location.host;
    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    // Development mode - simple routing
    if (currentHost.contains('localhost') ||
        currentHost.contains('127.0.0.1')) {
      return _handleLocalDevelopment(context, state);
    }

    // Production mode - all routes on same domain
    // Use /app prefix for main app routes to maintain clean separation

    // User is not authenticated and trying to access app routes → redirect to login with return URL
    if (!authProvider.isSignedIn && _isAppRoute(state.matchedLocation)) {
      final returnUrl = Uri.encodeComponent(state.matchedLocation);
      return '${Routes.login}?returnTo=$returnUrl';
    }

    // User is authenticated and on landing/auth pages → redirect to app or return URL
    if (authProvider.isSignedIn && _isLandingRoute(state.matchedLocation)) {
      // Check if there's a return URL from login
      final returnTo = state.uri.queryParameters['returnTo'];
      if (returnTo != null && _isAppRoute(returnTo)) {
        return returnTo; // Redirect to intended destination
      }
      return Routes.appHome; // Default to app home
    }

    return null; // No redirect needed
  }

  /// Handle local development routing (simplified)
  static String? _handleLocalDevelopment(
    BuildContext context,
    GoRouterState state,
  ) {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    // Simple auth-based routing for development
    if (!authProvider.isSignedIn && _isAppRoute(state.matchedLocation)) {
      final returnUrl = Uri.encodeComponent(state.matchedLocation);
      return '${Routes.login}?returnTo=$returnUrl';
    }

    if (authProvider.isSignedIn &&
        [Routes.login, Routes.signup].contains(state.matchedLocation)) {
      // Check if there's a return URL from login
      final returnTo = state.uri.queryParameters['returnTo'];
      if (returnTo != null && _isAppRoute(returnTo)) {
        return returnTo; // Redirect to intended destination
      }
      return Routes.appHome; // Default to app home
    }

    return null;
  }

  static bool _isAppRoute(String path) {
    return [
          '/app',
          '/app/',
          '/app/add',
          '/app/all',
          '/app/chat',
          '/app/profile',
        ].contains(path) ||
        path.startsWith('/app/');
  }

  static bool _isLandingRoute(String path) {
    return ['/', '/login', '/signup', '/forgot-password'].contains(path);
  }
}
