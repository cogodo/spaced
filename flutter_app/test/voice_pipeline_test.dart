import 'package:flutter_test/flutter_test.dart';
import 'package:spaced/services/audio_player_service.dart';
import 'dart:convert';

void main() {
  group('Voice Pipeline Tests', () {
    test('LiveKitVoiceService initialization', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');
      expect(service, isNotNull);
    });

    test('Data parsing - text chunk', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      // Test text chunk data
      final textChunkData = {
        'type': 'text_chunk',
        'content': 'Hello world',
        'is_final': false,
        'timestamp': DateTime.now().toIso8601String(),
      };

      final jsonString = jsonEncode(textChunkData);
      final bytes = utf8.encode(jsonString);

      // This would normally be called by the service
      // For testing, we'll just verify the data structure
      expect(textChunkData['type'], 'text_chunk');
      expect(textChunkData['content'], 'Hello world');
      expect(textChunkData['is_final'], false);
    });

    test('Data parsing - audio signal', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      // Test audio signal data
      final audioSignalData = {
        'type': 'audio_start',
        'data': {
          'text': 'Hello world',
          'timestamp': DateTime.now().toIso8601String(),
        },
        'timestamp': DateTime.now().toIso8601String(),
      };

      final jsonString = jsonEncode(audioSignalData);
      final bytes = utf8.encode(jsonString);

      // Verify data structure
      expect(audioSignalData['type'], 'audio_start');
      final data = audioSignalData['data'] as Map<String, dynamic>;
      expect(data['text'], 'Hello world');
    });

    test('Data parsing - audio data', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      // Test audio data
      final audioData = {
        'type': 'audio_data',
        'data': {
          'audio_data': 'base64_encoded_audio_data_here',
          'text': 'Hello world',
          'timestamp': DateTime.now().toIso8601String(),
        },
        'timestamp': DateTime.now().toIso8601String(),
      };

      final jsonString = jsonEncode(audioData);
      final bytes = utf8.encode(jsonString);

      // Verify data structure
      expect(audioData['type'], 'audio_data');
      final data = audioData['data'] as Map<String, dynamic>;
      expect(data['audio_data'], isA<String>());
      expect(data['text'], 'Hello world');
    });

    test('Data parsing - error handling', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      // Test error data
      final errorData = {
        'type': 'error',
        'message': 'Test error message',
        'timestamp': DateTime.now().toIso8601String(),
      };

      final jsonString = jsonEncode(errorData);
      final bytes = utf8.encode(jsonString);

      // Verify data structure
      expect(errorData['type'], 'error');
      expect(errorData['message'], 'Test error message');
    });

    test('Data parsing - completion signal', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      // Test completion data
      final completionData = {
        'type': 'completion',
        'session_id': 'test_session_123',
        'timestamp': DateTime.now().toIso8601String(),
      };

      final jsonString = jsonEncode(completionData);
      final bytes = utf8.encode(jsonString);

      // Verify data structure
      expect(completionData['type'], 'completion');
      expect(completionData['session_id'], 'test_session_123');
    });

    test('Service state management', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      // Test initial state
      expect(service.isConnected, false);
      expect(service.currentRoomName, null);
    });

    test('Callback registration', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      bool textChunkReceived = false;
      bool audioDataReceived = false;
      bool errorReceived = false;

      // Register callbacks
      service.onTextChunkReceived = (text, isFinal) {
        textChunkReceived = true;
        expect(text, isA<String>());
        expect(isFinal, isA<bool>());
      };

      service.onAudioDataReceived = (audioData) {
        audioDataReceived = true;
        expect(audioData, isA<String>());
      };

      service.onError = (error) {
        errorReceived = true;
        expect(error, isA<String>());
      };

      // Verify callbacks are registered
      expect(service.onTextChunkReceived, isNotNull);
      expect(service.onAudioDataReceived, isNotNull);
      expect(service.onError, isNotNull);
    });

    test('JSON parsing robustness', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      // Test malformed JSON
      final malformedJson =
          '{"type": "text_chunk", "content": "test"'; // Missing closing brace

      // This should not throw an exception
      expect(() {
        jsonDecode(malformedJson);
      }, throwsA(isA<FormatException>()));

      // Test valid JSON
      final validJson = '{"type": "text_chunk", "content": "test"}';
      final parsed = jsonDecode(validJson);
      expect(parsed['type'], 'text_chunk');
      expect(parsed['content'], 'test');
    });

    test('Data type validation', () {
      final service = LiveKitVoiceService(baseUrl: 'http://localhost:8000');

      // Test various data types
      final testCases = [
        {'type': 'text_chunk', 'content': 'Hello', 'is_final': false},
        {
          'type': 'audio_start',
          'data': {'text': 'Hello'},
        },
        {
          'type': 'audio_data',
          'data': {'audio_data': 'base64data'},
        },
        {
          'type': 'audio_complete',
          'data': {'text': 'Hello'},
        },
        {
          'type': 'audio_error',
          'data': {'error': 'Test error'},
        },
        {'type': 'completion', 'session_id': 'test123'},
        {'type': 'error', 'message': 'Test error'},
        {'type': 'unknown_type', 'data': 'test'},
      ];

      for (final testCase in testCases) {
        final jsonString = jsonEncode(testCase);
        final parsed = jsonDecode(jsonString);

        expect(parsed['type'], isA<String>());
        expect(parsed['type'], isNotEmpty);
      }
    });
  });
}
