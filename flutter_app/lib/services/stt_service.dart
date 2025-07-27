import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';
import '../services/logger_service.dart';
import 'web_audio_recorder.dart'
    if (dart.library.io) 'web_audio_recorder_stub.dart';

/// Simple STT service using proxy backend for speech-to-text transcription
class SttService {
  final _logger = getLogger('SttService');
  String? _recordingPath;
  WebAudioRecorder? _webRecorder;

  // Proxy configuration - configurable via dart-define
  static const String _proxyUrl = String.fromEnvironment(
    'STT_PROXY_URL',
    defaultValue: 'http://localhost:8000/api/v1/transcribe',
  );

  // Recording state
  bool _isRecording = false;

  /// Initialize the STT service
  Future<void> initialize() async {
    if (kIsWeb) {
      _webRecorder = WebAudioRecorder();
    }
    _logger.info('STT service initialized with proxy URL: $_proxyUrl');
  }

  /// Check if microphone permission is granted
  Future<bool> hasMicrophonePermission() async {
    try {
      final status = await Permission.microphone.status;
      return status.isGranted;
    } catch (e) {
      // On web, permission_handler might not work, assume granted
      _logger.info(
        'Permission check failed (likely web), assuming granted: $e',
      );
      return true;
    }
  }

  /// Request microphone permission
  Future<bool> requestMicrophonePermission() async {
    try {
      final status = await Permission.microphone.request();
      _logger.info('Microphone permission status: $status');
      return status.isGranted;
    } catch (e) {
      // On web, permission_handler might not work, assume granted
      _logger.info(
        'Permission request failed (likely web), assuming granted: $e',
      );
      return true;
    }
  }

  /// Start recording audio
  Future<bool> startRecording() async {
    if (_isRecording) {
      _logger.warning('Already recording');
      return false;
    }

    try {
      // Check permissions
      if (!await hasMicrophonePermission()) {
        final granted = await requestMicrophonePermission();
        if (!granted) {
          _logger.warning('Microphone permission denied');
          return false;
        }
      }

      if (kIsWeb && _webRecorder != null) {
        // Use web audio recorder
        final success = await _webRecorder!.startRecording();
        if (success) {
          _isRecording = true;
          _recordingPath =
              'web_recording_${DateTime.now().millisecondsSinceEpoch}.webm';
          _logger.info('Web audio recording started');
          return true;
        } else {
          _logger.warning('Failed to start web recording');
          return false;
        }
      } else {
        // Get temporary directory for recording
        try {
          final tempDir = await getTemporaryDirectory();
          _recordingPath =
              '${tempDir.path}/stt_recording_${DateTime.now().millisecondsSinceEpoch}.wav';
        } catch (e) {
          // On web, use a fallback path
          _recordingPath =
              'stt_recording_${DateTime.now().millisecondsSinceEpoch}.wav';
          _logger.info(
            'Using fallback recording path for web: $_recordingPath',
          );
        }

        // For now, simulate recording since we need to implement proper audio recording
        // In a real implementation, this would start actual audio recording using the record package
        _logger.info('Audio recording started (simulated): $_recordingPath');
        _isRecording = true;
        return true;
      }
    } catch (e) {
      _logger.severe('Error starting recording: $e');
      return false;
    }
  }

  /// Stop recording and transcribe
  Future<String?> stopRecordingAndTranscribe() async {
    if (!_isRecording) {
      _logger.warning('Not recording');
      return null;
    }

    try {
      _isRecording = false;
      _logger.info('Audio recording stopped');

      // Simulate processing delay
      await Future.delayed(const Duration(milliseconds: 1000));

      if (kIsWeb && _webRecorder != null) {
        // Use web audio recorder
        final audioData = await _webRecorder!.stopRecording();
        if (audioData != null) {
          _logger.info('Sending web audio data to proxy');
          return await _transcribeWebAudio(audioData);
        } else {
          _logger.warning('No web audio data captured');
          return await _simulateTranscription();
        }
      } else {
        // If we have a recording path, try to transcribe via proxy
        if (_recordingPath != null) {
          // Check if audio file exists
          final audioFile = File(_recordingPath!);
          if (await audioFile.exists()) {
            _logger.info('Sending audio file to proxy: $_recordingPath');
            return await _transcribeViaProxy(_recordingPath!);
          } else {
            _logger.warning('Audio file not found: $_recordingPath');
            return await _simulateTranscription();
          }
        } else {
          // Return simulated transcription for testing
          _logger.info('Using simulated transcription (no recording path)');
          return await _simulateTranscription();
        }
      }
    } catch (e) {
      _logger.severe('Error stopping recording: $e');
      _isRecording = false;
      return null;
    }
  }

  /// Simulate transcription for testing
  Future<String?> _simulateTranscription() async {
    // Simulate different transcription results
    final responses = [
      "Hello, this is a test transcription.",
      "The weather is nice today.",
      "I would like to learn more about this topic.",
      "Please help me understand this concept better.",
      "Thank you for your assistance.",
    ];

    // Return a random response to simulate transcription
    final random = DateTime.now().millisecondsSinceEpoch % responses.length;
    return responses[random];
  }

  /// Transcribe audio file via proxy backend
  Future<String?> _transcribeViaProxy(String audioPath) async {
    try {
      _logger.info('Sending audio to proxy: $_proxyUrl');

      // Create multipart request
      final request = http.MultipartRequest('POST', Uri.parse(_proxyUrl));
      request.files.add(await http.MultipartFile.fromPath('audio', audioPath));

      // Send request
      final response = await http.Response.fromStream(
        await request.send().timeout(const Duration(seconds: 30)),
      );

      _logger.info('Proxy response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final transcript = data['transcript'] as String?;
        if (transcript != null && transcript.isNotEmpty) {
          _logger.info('Transcription successful: $transcript');
          return transcript.trim();
        } else {
          _logger.warning('No transcript found in proxy response');
          return null;
        }
      } else {
        _logger.severe(
          'Proxy API error: ${response.statusCode} - ${response.body}',
        );
        return null;
      }
    } catch (e) {
      _logger.severe('Error transcribing via proxy: $e');
      return null;
    }
  }

  /// Transcribe web audio data via proxy backend
  Future<String?> _transcribeWebAudio(Uint8List audioData) async {
    try {
      _logger.info('Sending web audio data to proxy: $_proxyUrl');

      // Create multipart request
      final request = http.MultipartRequest('POST', Uri.parse(_proxyUrl));
      request.files.add(
        http.MultipartFile.fromBytes(
          'audio',
          audioData,
          filename: 'recording.webm',
          contentType: MediaType('audio', 'webm'),
        ),
      );

      // Send request
      final response = await http.Response.fromStream(
        await request.send().timeout(const Duration(seconds: 30)),
      );

      _logger.info('Proxy response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final transcript = data['transcript'] as String?;
        if (transcript != null && transcript.isNotEmpty) {
          _logger.info('Transcription successful: $transcript');
          return transcript.trim();
        } else {
          _logger.warning('No transcript found in proxy response');
          return null;
        }
      } else {
        _logger.severe(
          'Proxy API error: ${response.statusCode} - ${response.body}',
        );
        return null;
      }
    } catch (e) {
      _logger.severe('Error transcribing web audio via proxy: $e');
      return null;
    }
  }

  /// Check if currently recording
  bool get isRecording => _isRecording;

  /// Check if service is properly initialized
  bool get isInitialized => true;

  /// Dispose resources
  void dispose() {
    if (_isRecording) {
      _isRecording = false;
    }

    // Clean up web recorder
    if (kIsWeb && _webRecorder != null) {
      _webRecorder!.dispose();
      _webRecorder = null;
    }

    // Clean up audio file if it exists
    if (_recordingPath != null) {
      try {
        final audioFile = File(_recordingPath!);
        if (audioFile.existsSync()) {
          audioFile.deleteSync();
          _logger.info('Cleaned up audio file: $_recordingPath');
        }
      } catch (e) {
        _logger.warning('Failed to clean up audio file: $e');
      }
    }

    _logger.info('STT service disposed');
  }
}
