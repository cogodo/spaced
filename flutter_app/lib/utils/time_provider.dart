/// Provides the current time, allowing for easy mocking and testing.
abstract class TimeProvider {
  DateTime now();
  DateTime nowUtc();
}

/// A concrete implementation of [TimeProvider] that returns the system's time.
class SystemTimeProvider implements TimeProvider {
  @override
  DateTime now() => DateTime.now();

  @override
  DateTime nowUtc() => DateTime.now().toUtc();
}
