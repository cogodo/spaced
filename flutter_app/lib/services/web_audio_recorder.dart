import 'dart:html' as html;
import 'dart:typed_data';
import 'dart:async';
import '../services/logger_service.dart';

/// Web-specific audio recorder using MediaRecorder API
class WebAudioRecorder {
  final _logger = getLogger('WebAudioRecorder');

  html.MediaRecorder? _mediaRecorder;
  html.MediaStream? _mediaStream;
  final List<html.Blob> _recordedChunks = [];
  bool _isRecording = false;

  /// Start recording audio
  Future<bool> startRecording() async {
    if (_isRecording) {
      _logger.warning('Already recording');
      return false;
    }

    try {
      // Request microphone access
      _mediaStream = await html.window.navigator.mediaDevices!.getUserMedia({
        'audio': true,
      });

      // Create MediaRecorder
      _mediaRecorder = html.MediaRecorder(_mediaStream!, {
        'mimeType': 'audio/webm;codecs=opus',
      });

      // Clear previous chunks
      _recordedChunks.clear();

      // Listen for data
      _mediaRecorder!.addEventListener('dataavailable', (event) {
        final blobEvent = event as html.BlobEvent;
        if (blobEvent.data!.size > 0) {
          _recordedChunks.add(blobEvent.data!);
        }
      });

      // Start recording
      _mediaRecorder!.start();
      _isRecording = true;

      _logger.info('Web audio recording started');
      return true;
    } catch (e) {
      _logger.severe('Error starting web recording: $e');
      return false;
    }
  }

  /// Stop recording and get audio data
  Future<Uint8List?> stopRecording() async {
    if (!_isRecording || _mediaRecorder == null) {
      _logger.warning('Not recording');
      return null;
    }

    try {
      final completer = Completer<Uint8List?>();

      // Listen for stop event
      _mediaRecorder!.addEventListener('stop', (event) async {
        try {
          if (_recordedChunks.isNotEmpty) {
            final blob = html.Blob(_recordedChunks, 'audio/webm');
            final reader = html.FileReader();

            reader.onLoad.listen((event) {
              final arrayBuffer = reader.result as List<int>;
              completer.complete(Uint8List.fromList(arrayBuffer));
            });

            reader.onError.listen((event) {
              _logger.severe('Error reading recorded blob');
              completer.complete(null);
            });

            reader.readAsArrayBuffer(blob);
          } else {
            completer.complete(null);
          }
        } catch (e) {
          _logger.severe('Error processing recorded audio: $e');
          completer.complete(null);
        }
      });

      // Stop recording
      _mediaRecorder!.stop();
      _isRecording = false;

      // Stop media stream
      _mediaStream?.getTracks().forEach((track) => track.stop());
      _mediaStream = null;
      _mediaRecorder = null;

      _logger.info('Web audio recording stopped');
      return await completer.future;
    } catch (e) {
      _logger.severe('Error stopping web recording: $e');
      return null;
    }
  }

  /// Check if currently recording
  bool get isRecording => _isRecording;

  /// Dispose resources
  void dispose() {
    if (_isRecording) {
      _mediaRecorder?.stop();
    }
    _mediaStream?.getTracks().forEach((track) => track.stop());
    _mediaStream = null;
    _mediaRecorder = null;
    _recordedChunks.clear();
    _isRecording = false;
    _logger.info('Web audio recorder disposed');
  }
}
