/// Route constants for dual-domain routing structure
///
/// getspaced.app: Landing and authentication routes
/// app.getspaced.app: Main application routes (no /app prefix)
class Routes {
  // Landing domain routes (getspaced.app)
  static const String landing = '/';
  static const String login = '/login';
  static const String signup = '/signup';
  static const String forgotPassword = '/forgot-password';

  // App domain routes (app.getspaced.app) - NO /app prefix!
  static const String appHome = '/'; // app.getspaced.app/
  static const String appAdd = '/add'; // app.getspaced.app/add
  static const String appAll = '/all'; // app.getspaced.app/all
  static const String appChat = '/chat'; // app.getspaced.app/chat
  static const String appProfile = '/profile'; // app.getspaced.app/profile
}

class Domains {
  static const String landing = 'getspaced.app';
  static const String app = 'app.getspaced.app';

  // Helper methods
  static bool isAppDomain(String host) => host.startsWith('app.');
  static bool isLandingDomain(String host) =>
      host == landing || host == 'www.$landing';
}
