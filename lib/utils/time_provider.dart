abstract class TimeProvider {
  DateTime now();
}

class SystemTimeProvider implements TimeProvider {
  @override
  DateTime now() => DateTime.now();
}
