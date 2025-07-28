import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert' as convert;

import 'dart:async';
import 'package:livekit_client/livekit_client.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:firebase_auth/firebase_auth.dart';

class LiveKitVoiceService {
  Room? _room;
  final String _baseUrl;
  String? _currentUserId;
  EventsListener<RoomEvent>? _roomListener;
  Timer? _reconnectTimer;
  bool _isConnecting = false;

  // Connection details
  String? _currentRoomName;
  String? _currentToken;
  String? _serverUrl;

  // Event callbacks
  void Function(String transcript)? onTranscriptReceived;
  void Function(String response)? onAgentResponse;
  void Function()? onConnected;
  void Function()? onDisconnected;
  void Function(String error)? onError;
  void Function(bool isSpeaking)? onLocalSpeakingChanged;
  void Function(String transcript)? onFinalTranscriptReceived;

  LiveKitVoiceService({required String baseUrl}) : _baseUrl = baseUrl;

  /// Get authenticated headers for API requests
  Future<Map<String, String>> _getHeaders() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      throw Exception('User not authenticated');
    }
    final idToken = await user.getIdToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $idToken',
    };
  }

  /// Make authenticated HTTP request with retry on 401
  Future<http.Response> _makeAuthenticatedRequest(
    Future<http.Response> Function(Map<String, String> headers) requestFunction,
  ) async {
    try {
      final headers = await _getHeaders();
      final response = await requestFunction(headers);

      if (response.statusCode == 401) {
        // Token might be expired, get a fresh one
        final refreshedHeaders = await _getHeaders();
        return await requestFunction(refreshedHeaders);
      }
      return response;
    } catch (e) {
      throw Exception('Authentication error: $e');
    }
  }

  /// Unlock audio playback. Must be called after a user gesture.
  Future<void> startAudioPlayback() async {
    if (_room == null) return;
    try {
      // On web, this must be called after a user gesture to start playback.
      await _room!.startAudio();
    } catch (e) {
      onError?.call('Failed to unlock audio playback: $e');
    }
  }

  /// Create a voice room and return connection details
  Future<Map<String, dynamic>> createVoiceRoom(String chatId) async {
    try {
      final url = '$_baseUrl/api/v1/voice/create-room';
      final requestBody = {'chat_id': chatId};

      final response = await _makeAuthenticatedRequest(
        (headers) => http
            .post(
              Uri.parse(url),
              headers: headers,
              body: convert.json.encode(requestBody),
            )
            .timeout(
              const Duration(seconds: 10),
              onTimeout: () {
                throw TimeoutException('Request timed out after 10 seconds');
              },
            ),
      );

      if (response.statusCode == 200) {
        final data = convert.json.decode(response.body);

        // Store connection details for potential reconnection
        _currentRoomName = data['room_name'];
        _currentToken = data['token'];
        _serverUrl = data['server_url'];

        return data;
      } else {
        final errorMsg =
            'Failed to create room: ${response.statusCode} - ${response.body}';
        throw Exception(errorMsg);
      }
    } catch (e) {
      onError?.call('Failed to create room: $e');
      rethrow;
    }
  }

  /// Check if microphone permission is granted
  Future<bool> hasMicrophonePermission() async {
    try {
      final status = await Permission.microphone.status;
      return status.isGranted;
    } catch (e) {
      return false;
    }
  }

  /// Request microphone permission
  Future<bool> requestMicrophonePermission() async {
    try {
      final status = await Permission.microphone.request();
      return status.isGranted;
    } catch (e) {
      return false;
    }
  }

  /// Connect to a LiveKit room for voice chat
  Future<void> connectToRoom({
    required String roomName,
    required String token,
    required String serverUrl,
    required String userId,
  }) async {
    if (_isConnecting) {
      return;
    }

    try {
      _isConnecting = true;
      _currentUserId = userId;

      // Revert to the simplest, most robust pattern from official docs
      _room = Room();
      _roomListener = _room!.createListener();
      _setupEventListeners();

      await _room!.connect(serverUrl, token);

      // Wait a moment for connection to stabilize
      await Future.delayed(const Duration(milliseconds: 500));

      // Explicitly enable the microphone after connecting.
      await _enableMicrophone();

      // Double-check microphone state after enabling
      await Future.delayed(const Duration(milliseconds: 200));
      final isEnabled = isMicrophoneEnabled;

      if (!isEnabled) {
        await _enableMicrophone();
      }

      onConnected?.call();
    } catch (e) {
      debugPrint('[LiveKitVoiceService] Connection error: $e');
      onError?.call('Connection failed: $e');
      _isConnecting = false;
      rethrow;
    } finally {
      _isConnecting = false;
    }
  }

  /// Set up comprehensive event listeners
  void _setupEventListeners() {
    if (_roomListener == null) return;

    _roomListener!
      // Track subscriptions (agent audio)
      ..on<TrackSubscribedEvent>((event) {
        debugPrint(
          '[LiveKitVoiceService] Track subscribed: ${event.track.kind} from ${event.participant.identity}',
        );

        if (event.track.kind == TrackType.AUDIO) {
          debugPrint('[LiveKitVoiceService] Agent audio track received');
          // The audio will automatically play through the system
        }
      })
      // Data messages (transcripts, responses)
      ..on<DataReceivedEvent>((event) {
        try {
          final dataString = String.fromCharCodes(event.data);
          final data = convert.json.decode(dataString);
          debugPrint('[LiveKitVoiceService] Data received: $data');

          final messageType = data['type'] as String?;
          final text = data['text'] as String?;

          if (messageType == 'transcript' && text != null) {
            onTranscriptReceived?.call(text);
          } else if (messageType == 'agent_response' && text != null) {
            onAgentResponse?.call(text);
          } else if (messageType == 'final_transcript' && text != null) {
            debugPrint(
              '[LiveKitVoiceService] Received final transcript: "$text"',
            );
            onFinalTranscriptReceived?.call(text);
          } else if (messageType == 'voice_error') {
            final errorMessage =
                data['message'] as String? ?? 'Unknown voice error';
            debugPrint(
              '[LiveKitVoiceService] Received voice error: $errorMessage',
            );
            onError?.call(errorMessage);
          } else {
            debugPrint(
              '[LiveKitVoiceService] Unknown data type: ${data['type']}',
            );
          }
        } catch (e) {
          debugPrint('[LiveKitVoiceService] Error parsing data: $e');
        }
      })
      // Speaking status changes
      ..on<SpeakingChangedEvent>((event) {
        final isLocal = event.participant == _room?.localParticipant;
        debugPrint(
          '[LiveKitVoiceService] SpeakingChangedEvent: participant=${event.participant.identity}, isSpeaking=${event.speaking}, isLocal=$isLocal',
        );
        if (isLocal) {
          onLocalSpeakingChanged?.call(event.speaking);
        }
      })
      // Local track published
      ..on<LocalTrackPublishedEvent>((e) {
        debugPrint(
          '[LiveKitVoiceService] LocalTrackPublishedEvent: track publication sid: ${e.publication.sid}',
        );
      })
      // Participant events
      ..on<ParticipantConnectedEvent>((event) {
        debugPrint(
          '[LiveKitVoiceService] Participant connected: ${event.participant.identity}',
        );
      })
      ..on<ParticipantDisconnectedEvent>((event) {
        debugPrint(
          '[LiveKitVoiceService] Participant disconnected: ${event.participant.identity}',
        );
      })
      // Room connection events
      ..on<RoomDisconnectedEvent>((event) {
        debugPrint('[LiveKitVoiceService] Room disconnected: ${event.reason}');
        onDisconnected?.call();
        _scheduleReconnect();
      })
      // Track events
      ..on<TrackMutedEvent>((event) {
        debugPrint(
          '[LiveKitVoiceService] Track muted: ${event.publication.kind}',
        );
      })
      ..on<TrackUnmutedEvent>((event) {
        debugPrint(
          '[LiveKitVoiceService] Track unmuted: ${event.publication.kind}',
        );
      });
  }

  /// Schedule reconnection attempt
  void _scheduleReconnect() {
    if (_reconnectTimer?.isActive == true) return;

    _reconnectTimer = Timer(const Duration(seconds: 3), () {
      if (_currentRoomName != null &&
          _currentToken != null &&
          _serverUrl != null &&
          _currentUserId != null) {
        debugPrint('[LiveKitVoiceService] Attempting to reconnect...');
        connectToRoom(
          roomName: _currentRoomName!,
          token: _currentToken!,
          serverUrl: _serverUrl!,
          userId: _currentUserId!,
        ).catchError((e) {
          debugPrint('[LiveKitVoiceService] Reconnection failed: $e');
          onError?.call('Reconnection failed: $e');
        });
      }
    });
  }

  /// Enable microphone for voice input
  Future<void> _enableMicrophone() async {
    try {
      debugPrint('[LiveKitVoiceService] Attempting to enable microphone...');

      // Check if room and local participant exist
      if (_room == null) {
        throw Exception('Room not connected');
      }

      final localParticipant = _room!.localParticipant;
      if (localParticipant == null) {
        throw Exception('Local participant not available');
      }

      // Check microphone permission first
      final hasPermission = await hasMicrophonePermission();
      if (!hasPermission) {
        final granted = await requestMicrophonePermission();
        if (!granted) {
          throw Exception('Microphone permission not granted');
        }
      }

      // Enable microphone
      await localParticipant.setMicrophoneEnabled(true);
      debugPrint('[LiveKitVoiceService] Microphone enabled successfully.');

      // Wait a moment for the track to be published
      await Future.delayed(const Duration(milliseconds: 300));

      // Log the state of all audio tracks for debugging
      final audioPublications = localParticipant.audioTrackPublications;
      debugPrint(
        '[LiveKitVoiceService] Found ${audioPublications.length} audio track publications',
      );

      for (final pub in audioPublications) {
        debugPrint(
          '[LiveKitVoiceService] Audio track: sid=${pub.sid}, muted=${pub.muted}, source=${pub.source}',
        );
      }

      // Check if we have a microphone track
      final micTrack =
          audioPublications
              .where((pub) => pub.source == TrackSource.microphone)
              .firstOrNull;
      if (micTrack != null) {
        debugPrint(
          '[LiveKitVoiceService] Microphone track found: sid=${micTrack.sid}, muted=${micTrack.muted}',
        );
      } else {
        debugPrint(
          '[LiveKitVoiceService] No microphone track found in publications',
        );
      }
    } catch (e) {
      debugPrint('[LiveKitVoiceService] Error enabling microphone: $e');
      onError?.call('Failed to enable microphone: $e');
      rethrow;
    }
  }

  /// Disable microphone
  Future<void> muteMicrophone() async {
    try {
      debugPrint('[LiveKitVoiceService] Muting microphone...');
      await _room?.localParticipant?.setMicrophoneEnabled(false);
      debugPrint('[LiveKitVoiceService] Microphone muted');
    } catch (e) {
      debugPrint('[LiveKitVoiceService] Error muting microphone: $e');
    }
  }

  /// Enable microphone
  Future<void> unmuteMicrophone() async {
    try {
      debugPrint('[LiveKitVoiceService] Unmuting microphone...');
      await _room?.localParticipant?.setMicrophoneEnabled(true);
      debugPrint('[LiveKitVoiceService] Microphone unmuted');
    } catch (e) {
      debugPrint('[LiveKitVoiceService] Error unmuting microphone: $e');
    }
  }

  /// Check if microphone is enabled
  bool get isMicrophoneEnabled {
    try {
      final audioPublications = _room?.localParticipant?.audioTrackPublications;
      if (audioPublications == null || audioPublications.isEmpty) return false;

      // Find microphone track
      for (final pub in audioPublications) {
        if (pub.source == TrackSource.microphone) {
          return !pub.muted;
        }
      }
      return false;
    } catch (e) {
      debugPrint('[LiveKitVoiceService] Error checking microphone state: $e');
      return false;
    }
  }

  /// Send a text message to the agent (alternative to voice)
  Future<void> sendTextMessage(String message) async {
    try {
      final data = convert.json.encode({
        'type': 'text_message',
        'message': message,
        'user_id': _currentUserId,
        'timestamp': DateTime.now().toIso8601String(),
      });

      await _room?.localParticipant?.publishData(
        convert.utf8.encode(data),
        reliable: true,
      );

      debugPrint('[LiveKitVoiceService] Text message sent: $message');
    } catch (e) {
      debugPrint('[LiveKitVoiceService] Error sending text message: $e');
      onError?.call('Failed to send message: $e');
    }
  }

  /// Disconnect from the room
  Future<void> disconnect() async {
    try {
      _reconnectTimer?.cancel();
      _reconnectTimer = null;

      // The room must be disconnected before the listener is disposed.
      // This ensures all disconnection events are received properly.
      await _room?.disconnect();
      _roomListener?.dispose();

      _room = null;
      _roomListener = null;

      // Clear connection details
      _currentRoomName = null;
      _currentToken = null;
      _serverUrl = null;
      _currentUserId = null;

      debugPrint('[LiveKitVoiceService] Disconnected from room');
    } catch (e) {
      debugPrint('[LiveKitVoiceService] Error disconnecting: $e');
    }
  }

  /// Check if connected to a room
  bool get isConnected => _room?.connectionState == ConnectionState.connected;

  /// Get current room name
  String? get currentRoomName => _room?.name;

  /// Get list of participants (excluding local user)
  List<RemoteParticipant> get remoteParticipants =>
      _room?.remoteParticipants.values.toList() ?? [];

  /// Get connection state
  ConnectionState get connectionState =>
      _room?.connectionState ?? ConnectionState.disconnected;

  /// Start a complete voice session (create room + connect)
  Future<void> startVoiceSession(String chatId, String userId) async {
    try {
      debugPrint(
        '[LiveKitVoiceService] Starting voice session for chat: $chatId',
      );

      // Step 1: Create room
      final roomData = await createVoiceRoom(chatId);

      // Step 2: Connect to room
      await connectToRoom(
        roomName: roomData['room_name'],
        token: roomData['token'],
        serverUrl: roomData['server_url'],
        userId: userId,
      );

      // Voice agent should automatically join and handle STT -> Backend -> TTS
      debugPrint('[LiveKitVoiceService] Voice session started successfully');
    } catch (e) {
      debugPrint('[LiveKitVoiceService] Failed to start voice session: $e');
      onError?.call('Failed to start voice session: $e');
      rethrow;
    }
  }

  /// Dispose of resources
  void dispose() {
    disconnect();
  }

  /// Check if voice service is healthy by calling the health endpoint
  Future<bool> checkVoiceServiceHealth() async {
    try {
      debugPrint('[LiveKitVoiceService] Checking voice service health...');

      final response = await _makeAuthenticatedRequest(
        (headers) => http
            .get(Uri.parse('$_baseUrl/api/v1/voice/health'), headers: headers)
            .timeout(
              const Duration(seconds: 10),
              onTimeout: () {
                throw TimeoutException(
                  'Health check timed out after 10 seconds',
                );
              },
            ),
      );

      if (response.statusCode == 200) {
        final data = convert.json.decode(response.body);
        final isHealthy = data['status'] == 'healthy';
        debugPrint('[LiveKitVoiceService] Voice service health: $isHealthy');
        return isHealthy;
      } else {
        debugPrint(
          '[LiveKitVoiceService] Voice service health check failed: ${response.statusCode}',
        );
        return false;
      }
    } catch (e) {
      debugPrint(
        '[LiveKitVoiceService] Error checking voice service health: $e',
      );
      return false;
    }
  }

  /// Get voice service status details
  Future<Map<String, dynamic>?> getVoiceServiceStatus() async {
    try {
      debugPrint('[LiveKitVoiceService] Getting voice service status...');

      final response = await _makeAuthenticatedRequest(
        (headers) => http
            .get(Uri.parse('$_baseUrl/api/v1/voice/health'), headers: headers)
            .timeout(
              const Duration(seconds: 10),
              onTimeout: () {
                throw TimeoutException(
                  'Status check timed out after 10 seconds',
                );
              },
            ),
      );

      if (response.statusCode == 200) {
        final data = convert.json.decode(response.body);
        debugPrint('[LiveKitVoiceService] Voice service status: $data');
        return data;
      } else {
        debugPrint(
          '[LiveKitVoiceService] Voice service status check failed: ${response.statusCode}',
        );
        return null;
      }
    } catch (e) {
      debugPrint(
        '[LiveKitVoiceService] Error getting voice service status: $e',
      );
      return null;
    }
  }
}
