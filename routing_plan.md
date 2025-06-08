import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

// 1) Your “RequireAuth” redirect logic
bool isLoggedIn() {
  // TODO: hook into your auth state
  return false;
}

final _router = GoRouter(
  initialLocation: '/',
  debugLogDiagnostics: true,  
  // 2) Global redirect: protect /app/* and prevent logged‐in users hitting login/signup
  redirect: (GoRouterState state) {
    final loggedIn = isLoggedIn();
    final loggingIn  = state.subloc == '/login';
    final signingUp  = state.subloc == '/signup';

    if (!loggedIn && state.subloc.startsWith('/app')) {
      return '/login';
    }
    if (loggedIn && (loggingIn || signingUp)) {
      return '/app/profile';
    }
    return null;
  },
  routes: [
    // Public
    GoRoute(
      path: '/',
      builder: (context, state) => LandingPage(),
    ),
    GoRoute(
      path: '/login',
      builder: (context, state) => LoginPage(),
    ),
    GoRoute(
      path: '/signup',
      builder: (context, state) => SignUpPage(),
    ),

    // Protected “app” section
    ShellRoute(
      builder: (context, state, child) => AppScaffold(child: child),
      routes: [
        GoRoute(
          path: '/app/profile',
          builder: (context, state) => ProfilePage(),
        ),
        GoRoute(
          path: '/app/reviews',
          builder: (context, state) => AllReviewsPage(),
          routes: [
            GoRoute(
              path: 'today',
              builder: (context, state) => TodaysReviewsPage(),
            ),
            GoRoute(
              path: 'all',
              builder: (context, state) => AllReviewsPage(),
            ),
            GoRoute(
              path: 'add',
              builder: (context, state) => AddReviewPage(),
            ),
          ],
        ),
        GoRoute(
          path: '/app/chat',
          builder: (context, state) => ChatPage(),
        ),
      ],
    ),
  ],
);

void main() {
  runApp(MaterialApp.router(
    title: 'GetSpaced',
    routerConfig: _router,
    theme: ThemeData.light(),
    darkTheme: ThemeData.dark(),
    // if you prefer no trailing slash, you can add a redirect rule above
  ));
}
 this will be used to route to proper url slugs at a later date.