import 'dart:typed_data';

/// Stub implementation for non-web platforms
class WebAudioRecorder {
  /// Start recording audio (stub - not supported on this platform)
  Future<bool> startRecording() async {
    return false;
  }

  /// Stop recording and get audio data (stub - not supported on this platform)
  Future<Uint8List?> stopRecording() async {
    return null;
  }

  /// Stop recording and transcribe (stub - not supported on this platform)
  Future<String?> stopRecordingAndTranscribe() async {
    return null;
  }

  /// Check if currently recording (stub - not supported on this platform)
  bool get isRecording => false;

  /// Dispose resources (stub - not supported on this platform)
  void dispose() {}
}
