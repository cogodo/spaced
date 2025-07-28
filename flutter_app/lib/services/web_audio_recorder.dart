// Conditional import for web platform
export 'web_audio_recorder_web.dart'
    if (dart.library.io) 'web_audio_recorder_stub.dart';
