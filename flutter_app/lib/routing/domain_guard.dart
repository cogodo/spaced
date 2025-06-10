import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'dart:html' as html;

import '../providers/auth_provider.dart';
import 'route_constants.dart';

/// Domain-aware authentication guard
/// Handles cross-domain redirects and authentication state
class DomainGuard {
  static String? handleDomainRouting(
    BuildContext context,
    GoRouterState state,
  ) {
    final currentHost = html.window.location.host;

    // Development mode - allow localhost routing without domain restrictions
    if (currentHost.contains('localhost') ||
        currentHost.contains('127.0.0.1')) {
      return _handleLocalDevelopment(context, state);
    }

    final isAppDomain = Domains.isAppDomain(currentHost);
    final isLandingDomain = Domains.isLandingDomain(currentHost);

    final authProvider = Provider.of<AuthProvider>(context, listen: false);

    // ===== AUTHENTICATION-BASED REDIRECTS =====

    // User is authenticated and on landing domain → redirect to app domain
    if (authProvider.isSignedIn &&
        isLandingDomain &&
        state.matchedLocation == Routes.landing) {
      return 'https://${Domains.app}/';
    }

    // User is authenticated and trying to access auth screens → redirect to app
    if (authProvider.isSignedIn &&
        isLandingDomain &&
        [
          Routes.login,
          Routes.signup,
          Routes.forgotPassword,
        ].contains(state.matchedLocation)) {
      return 'https://${Domains.app}/';
    }

    // User is not authenticated and on app domain → redirect to landing login
    if (!authProvider.isSignedIn && isAppDomain) {
      return 'https://${Domains.landing}/login';
    }

    // ===== DOMAIN ENFORCEMENT =====

    // If someone tries to access app routes on landing domain, redirect to app domain
    if (isLandingDomain && _isAppRoute(state.matchedLocation)) {
      return 'https://${Domains.app}${state.matchedLocation}';
    }

    // If someone tries to access landing routes on app domain, redirect to landing domain
    if (isAppDomain && _isLandingRoute(state.matchedLocation)) {
      return 'https://${Domains.landing}${state.matchedLocation}';
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
      return Routes.login;
    }

    if (authProvider.isSignedIn &&
        [Routes.login, Routes.signup].contains(state.matchedLocation)) {
      return Routes.appHome;
    }

    return null;
  }

  static bool _isAppRoute(String path) {
    return [
      Routes.appAdd,
      Routes.appAll,
      Routes.appChat,
      Routes.appProfile,
    ].contains(path);
  }

  static bool _isLandingRoute(String path) {
    return [Routes.login, Routes.signup, Routes.forgotPassword].contains(path);
  }
}
