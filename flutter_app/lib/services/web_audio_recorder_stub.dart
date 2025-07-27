import 'dart:typed_data';

/// Stub implementation for non-web platforms
class WebAudioRecorder {
  Future<bool> startRecording() async {
    throw UnsupportedError('WebAudioRecorder is only available on web');
  }

  Future<Uint8List?> stopRecording() async {
    throw UnsupportedError('WebAudioRecorder is only available on web');
  }

  bool get isRecording => false;

  void dispose() {
    // No-op on non-web platforms
  }
}
