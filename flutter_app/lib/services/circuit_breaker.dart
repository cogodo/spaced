import 'dart:async';

enum CircuitBreakerState { closed, open, halfOpen }

class CircuitBreakerException implements Exception {
  final String message;
  CircuitBreakerException(this.message);

  @override
  String toString() => 'CircuitBreakerException: $message';
}

class CircuitBreaker {
  final int failureThreshold;
  final Duration timeout;
  final Duration resetTimeout;

  CircuitBreakerState _state = CircuitBreakerState.closed;
  int _failureCount = 0;
  DateTime? _lastFailureTime;
  DateTime? _nextAttemptTime;

  CircuitBreaker({
    this.failureThreshold = 5,
    this.timeout = const Duration(seconds: 30),
    this.resetTimeout = const Duration(minutes: 1),
  });

  CircuitBreakerState get state => _state;
  int get failureCount => _failureCount;

  Future<T> execute<T>(Future<T> Function() operation) async {
    if (_state == CircuitBreakerState.open) {
      if (_nextAttemptTime != null &&
          DateTime.now().isBefore(_nextAttemptTime!)) {
        throw CircuitBreakerException(
          'Circuit breaker is OPEN. Next attempt allowed at ${_nextAttemptTime!.toLocal()}',
        );
      } else {
        // Move to half-open state for testing
        _state = CircuitBreakerState.halfOpen;
      }
    }

    try {
      final result = await operation().timeout(timeout);
      _onSuccess();
      return result;
    } catch (e) {
      _onFailure();
      rethrow;
    }
  }

  void _onSuccess() {
    _failureCount = 0;
    _state = CircuitBreakerState.closed;
    _lastFailureTime = null;
    _nextAttemptTime = null;
  }

  void _onFailure() {
    _failureCount++;
    _lastFailureTime = DateTime.now();

    if (_failureCount >= failureThreshold) {
      _state = CircuitBreakerState.open;
      _nextAttemptTime = DateTime.now().add(resetTimeout);
    }
  }

  void reset() {
    _failureCount = 0;
    _state = CircuitBreakerState.closed;
    _lastFailureTime = null;
    _nextAttemptTime = null;
  }

  Map<String, dynamic> getStatus() {
    return {
      'state': _state.toString(),
      'failureCount': _failureCount,
      'lastFailureTime': _lastFailureTime?.toIso8601String(),
      'nextAttemptTime': _nextAttemptTime?.toIso8601String(),
    };
  }
}

/// Enhanced circuit breaker with adaptive timeout and exponential backoff
class AdaptiveCircuitBreaker extends CircuitBreaker {
  final Duration baseTimeout;
  final Duration maxTimeout;
  final double backoffMultiplier;

  AdaptiveCircuitBreaker({
    super.failureThreshold = 3,
    this.baseTimeout = const Duration(seconds: 15),
    this.maxTimeout = const Duration(minutes: 5),
    this.backoffMultiplier = 2.0,
    super.resetTimeout = const Duration(minutes: 1),
  }) : super(timeout: baseTimeout);

  @override
  Future<T> execute<T>(Future<T> Function() operation) async {
    // Calculate adaptive timeout based on failure count
    final adaptiveTimeout = Duration(
      milliseconds: (baseTimeout.inMilliseconds *
              (1 + (_failureCount * backoffMultiplier)))
          .round()
          .clamp(baseTimeout.inMilliseconds, maxTimeout.inMilliseconds),
    );

    if (_state == CircuitBreakerState.open) {
      if (_nextAttemptTime != null &&
          DateTime.now().isBefore(_nextAttemptTime!)) {
        throw CircuitBreakerException(
          'Circuit breaker is OPEN. Service may be down. Next retry in ${_nextAttemptTime!.difference(DateTime.now()).inSeconds} seconds.',
        );
      } else {
        _state = CircuitBreakerState.halfOpen;
      }
    }

    try {
      final result = await operation().timeout(adaptiveTimeout);
      _onSuccess();
      return result;
    } catch (e) {
      _onFailure();
      rethrow;
    }
  }

  @override
  void _onFailure() {
    super._onFailure();

    // Exponential backoff for reset timeout
    if (_state == CircuitBreakerState.open) {
      final backoffSeconds =
          (resetTimeout.inSeconds *
                  (1 + (_failureCount - failureThreshold) * 0.5))
              .round();
      _nextAttemptTime = DateTime.now().add(
        Duration(
          seconds: backoffSeconds.clamp(
            resetTimeout.inSeconds,
            resetTimeout.inSeconds * 4, // Max 4x the base reset timeout
          ),
        ),
      );
    }
  }
}

/// Service-specific circuit breakers for different API endpoints
class ServiceCircuitBreakers {
  static final Map<String, CircuitBreaker> _breakers = {};

  static CircuitBreaker getBreaker(String serviceName) {
    return _breakers.putIfAbsent(
      serviceName,
      () => AdaptiveCircuitBreaker(
        failureThreshold: _getFailureThreshold(serviceName),
        baseTimeout: _getBaseTimeout(serviceName),
        resetTimeout: _getResetTimeout(serviceName),
      ),
    );
  }

  static int _getFailureThreshold(String serviceName) {
    switch (serviceName) {
      case 'session_api':
        return 3; // More sensitive for session operations
      case 'topic_search':
        return 5; // Less sensitive for search
      case 'popular_topics':
        return 5; // Less sensitive for static data
      default:
        return 3;
    }
  }

  static Duration _getBaseTimeout(String serviceName) {
    switch (serviceName) {
      case 'session_api':
        return const Duration(seconds: 60); // Increased from 30 to 60 seconds
      case 'topic_search':
        return const Duration(seconds: 10); // Faster for search
      case 'popular_topics':
        return const Duration(seconds: 15); // Medium for static data
      default:
        return const Duration(seconds: 20);
    }
  }

  static Duration _getResetTimeout(String serviceName) {
    switch (serviceName) {
      case 'session_api':
        return const Duration(minutes: 2); // Longer recovery for critical ops
      case 'topic_search':
        return const Duration(seconds: 30); // Faster recovery for non-critical
      case 'popular_topics':
        return const Duration(minutes: 1); // Medium recovery
      default:
        return const Duration(minutes: 1);
    }
  }

  static Map<String, dynamic> getAllStatus() {
    return _breakers.map(
      (name, breaker) => MapEntry(name, breaker.getStatus()),
    );
  }

  static void resetAll() {
    for (final breaker in _breakers.values) {
      breaker.reset();
    }
  }

  static void reset(String serviceName) {
    _breakers[serviceName]?.reset();
  }
}
