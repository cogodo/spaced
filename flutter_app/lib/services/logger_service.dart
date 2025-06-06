import 'package:flutter/foundation.dart';

/// Simple logger service for debugging and monitoring
class Logger {
  final String name;

  const Logger(this.name);

  /// Log an info message
  void info(String message) {
    if (kDebugMode) {
      print('INFO [$name]: $message');
    }
  }

  /// Log a warning message
  void warning(String message) {
    if (kDebugMode) {
      print('WARNING [$name]: $message');
    }
  }

  /// Log a severe error message with optional error and stack trace
  void severe(String message, [Object? error, StackTrace? stackTrace]) {
    if (kDebugMode) {
      print('SEVERE [$name]: $message');
      if (error != null) {
        print('ERROR [$name]: $error');
      }
      if (stackTrace != null) {
        print('STACK TRACE [$name]: $stackTrace');
      }
    }
  }

  /// Log a debug message
  void debug(String message) {
    if (kDebugMode) {
      print('DEBUG [$name]: $message');
    }
  }
}

/// Get a logger instance for the given name
Logger getLogger(String name) => Logger(name);
