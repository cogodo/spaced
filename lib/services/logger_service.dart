import 'package:logging/logging.dart';

/// LoggerService provides a centralized logging system for the application.
///
/// It uses the 'logging' package to provide different log levels and consistent
/// formatting across the application.
class LoggerService {
  static final LoggerService _instance = LoggerService._internal();

  // Factory constructor to return the singleton instance
  factory LoggerService() => _instance;

  // Private constructor
  LoggerService._internal() {
    _initializeLogging();
  }

  // Initialize the logging configuration
  void _initializeLogging() {
    // Set the default log level
    Logger.root.level = Level.INFO;

    // Set up logging output format
    Logger.root.onRecord.listen((record) {
      // ignore: avoid_print
      print(
        '${record.time} [${record.level.name}] ${record.loggerName}: ${record.message}',
      );

      // If there's an error and stack trace, print them
      if (record.error != null) {
        // ignore: avoid_print
        print('ERROR: ${record.error}');
      }

      if (record.stackTrace != null) {
        // ignore: avoid_print
        print('STACKTRACE: ${record.stackTrace}');
      }
    });
  }

  // Get a logger for a specific component
  Logger getLogger(String name) {
    return Logger(name);
  }

  // Set the global log level (useful for switching between dev/prod)
  void setLogLevel(Level level) {
    Logger.root.level = level;
  }

  // Helper method to enable debug logs (for development)
  void enableDebugLogs() {
    Logger.root.level = Level.ALL;
  }

  // Helper method to disable all but warning and error logs (for production)
  void enableProductionLogs() {
    Logger.root.level = Level.WARNING;
  }
}

// Create a global instance for easy access
final loggerService = LoggerService();

// Helper function to quickly get a logger for a class
Logger getLogger(String name) => loggerService.getLogger(name);
