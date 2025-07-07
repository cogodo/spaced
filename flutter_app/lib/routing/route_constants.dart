/// Route constants for clean URL structure
///
/// getspaced.app: Landing and authentication routes
/// getspaced.app/app/*: Main application routes
class Routes {
  // Landing domain routes (getspaced.app)
  static const String landing = '/';
  static const String login = '/login';
  static const String signup = '/signup';
  static const String forgotPassword = '/forgot-password';
  static const String privacyPolicy = '/privacy-policy';

  // App routes (getspaced.app/app/*)
  static const String appHome = '/app'; // getspaced.app/app
  static const String appAdd = '/app/add'; // getspaced.app/app/add
  static const String appAll = '/app/all'; // getspaced.app/app/all
  static const String appTodays = '/app/today'; // getspaced.app/app/today
  static const String appChat = '/app/chat'; // getspaced.app/app/chat
  static const String appProfile = '/app/profile'; // getspaced.app/app/profile
}

class Domains {
  static const String landing = 'getspaced.app';
  static const String app = 'getspaced.app'; // Same domain now

  // Helper methods
  static bool isAppDomain(String host) => host.contains('getspaced.app');
  static bool isLandingDomain(String host) => host.contains('getspaced.app');
}
