import 'package:flutter_test/flutter_test.dart';
import 'package:spaced/providers/settings_provider.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('SettingsProvider', () {
    late SettingsProvider settingsProvider;

    setUp(() {
      settingsProvider = SettingsProvider();
    });

    test('should initialize with default voice disabled', () {
      expect(settingsProvider.voiceEnabled, false);
    });

    test('should toggle voice enabled', () async {
      expect(settingsProvider.voiceEnabled, false);

      await settingsProvider.toggleVoiceEnabled();
      expect(settingsProvider.voiceEnabled, true);

      await settingsProvider.toggleVoiceEnabled();
      expect(settingsProvider.voiceEnabled, false);
    });

    test('should set voice enabled', () async {
      expect(settingsProvider.voiceEnabled, false);

      await settingsProvider.setVoiceEnabled(true);
      expect(settingsProvider.voiceEnabled, true);

      await settingsProvider.setVoiceEnabled(false);
      expect(settingsProvider.voiceEnabled, false);
    });

    test('should not notify when setting same value', () async {
      expect(settingsProvider.voiceEnabled, false);

      // Setting to the same value should not trigger notification
      await settingsProvider.setVoiceEnabled(false);
      expect(settingsProvider.voiceEnabled, false);
    });

    test('should initialize with default STT enabled', () {
      expect(settingsProvider.sttEnabled, true);
    });

    test('should toggle STT enabled', () async {
      expect(settingsProvider.sttEnabled, true);

      await settingsProvider.toggleSttEnabled();
      expect(settingsProvider.sttEnabled, false);

      await settingsProvider.toggleSttEnabled();
      expect(settingsProvider.sttEnabled, true);
    });

    test('should set STT enabled', () async {
      expect(settingsProvider.sttEnabled, true);

      await settingsProvider.setSttEnabled(false);
      expect(settingsProvider.sttEnabled, false);

      await settingsProvider.setSttEnabled(true);
      expect(settingsProvider.sttEnabled, true);
    });
  });
}
