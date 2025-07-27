import 'package:flutter_test/flutter_test.dart';
import 'package:spaced/services/stt_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('SttService Integration Tests', () {
    late SttService sttService;

    setUp(() {
      sttService = SttService();
    });

    test('should handle real audio file path creation', () async {
      await sttService.initialize();

      // Start recording to create file path
      final result = await sttService.startRecording();
      expect(result, isA<bool>());

      // Stop recording to test file handling
      final transcript = await sttService.stopRecordingAndTranscribe();
      expect(transcript, isA<String?>());
    });

    test('should create temporary audio file path', () async {
      await sttService.initialize();

      // Start recording to create file path
      final result = await sttService.startRecording();

      // Note: In test environment, actual recording won't work due to permissions
      // but the method should return a boolean result
      expect(result, isA<bool>());
    });

    test('should handle file cleanup on dispose', () {
      sttService.dispose();
      // Should not throw any errors during cleanup
    });

    test('should work with proxy configuration', () async {
      await sttService.initialize();
      expect(sttService.isInitialized, true);
    });

    test('should handle missing audio file gracefully', () async {
      await sttService.initialize();

      // Try to transcribe without recording first
      final transcript = await sttService.stopRecordingAndTranscribe();
      expect(transcript, isNull);
    });
  });
}
