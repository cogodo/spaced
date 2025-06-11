import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/chat_session.dart';
import '../screens/chat_screen.dart'; // For ChatMessage
import '../services/logger_service.dart';

class ChatSessionService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final _logger = getLogger('ChatSessionService');

  // Collection references
  CollectionReference<Map<String, dynamic>> _getUserSessionsCollection(
    String userId,
  ) {
    return _firestore
        .collection('users')
        .doc(userId)
        .collection('chatSessions');
  }

  CollectionReference<Map<String, dynamic>> _getSessionMessagesCollection(
    String userId,
    String sessionId,
  ) {
    return _getUserSessionsCollection(
      userId,
    ).doc(sessionId).collection('messages');
  }

  /// Save a complete chat session to Firestore
  Future<void> saveSession(String userId, ChatSession session) async {
    _logger.info('Saving session ${session.id} for user $userId');

    try {
      final batch = _firestore.batch();
      final sessionRef = _getUserSessionsCollection(userId).doc(session.id);

      // Save session metadata
      batch.set(sessionRef, session.toFirestore());

      // Save all messages in batch
      final messagesRef = _getSessionMessagesCollection(userId, session.id);

      // Clear existing messages first (in case we're updating)
      final existingMessages = await messagesRef.get();
      for (final doc in existingMessages.docs) {
        batch.delete(doc.reference);
      }

      // Add current messages
      for (int i = 0; i < session.messages.length; i++) {
        final message = session.messages[i];
        final messageRef = messagesRef.doc();
        batch.set(messageRef, {
          'text': message.text,
          'isUser': message.isUser,
          'isSystem': message.isSystem,
          'timestamp': Timestamp.fromDate(message.timestamp),
          'messageIndex': i,
        });
      }

      await batch.commit();
      _logger.info('Successfully saved session ${session.id}');
    } catch (e, stackTrace) {
      _logger.severe('Error saving session ${session.id}: $e', e, stackTrace);
      throw ChatSessionException('Failed to save session: $e');
    }
  }

  /// Load a specific chat session from Firestore
  Future<ChatSession?> loadSession(String userId, String sessionId) async {
    _logger.info('Loading session $sessionId for user $userId');

    try {
      // Get session metadata
      final sessionDoc =
          await _getUserSessionsCollection(userId).doc(sessionId).get();

      if (!sessionDoc.exists) {
        _logger.warning('Session $sessionId not found');
        return null;
      }

      // Get session messages
      final messagesSnapshot =
          await _getSessionMessagesCollection(
            userId,
            sessionId,
          ).orderBy('messageIndex').get();

      final messages =
          messagesSnapshot.docs.map((doc) {
            final data = doc.data();
            return ChatMessage(
              text: data['text'],
              isUser: data['isUser'],
              isSystem: data['isSystem'] ?? false,
              timestamp: (data['timestamp'] as Timestamp).toDate(),
            );
          }).toList();

      final session = ChatSession.fromFirestore(sessionDoc, messages);
      _logger.info(
        'Successfully loaded session $sessionId with ${messages.length} messages',
      );
      return session;
    } catch (e, stackTrace) {
      _logger.severe('Error loading session $sessionId: $e', e, stackTrace);
      throw ChatSessionException('Failed to load session: $e');
    }
  }

  /// Get session history summaries for a user
  Future<List<ChatSessionSummary>> getSessionHistory(
    String userId, {
    int limit = 50,
    DocumentSnapshot? startAfter,
  }) async {
    _logger.info('Loading session history for user $userId (limit: $limit)');

    try {
      Query<Map<String, dynamic>> query = _getUserSessionsCollection(
        userId,
      ).orderBy('updatedAt', descending: true).limit(limit);

      if (startAfter != null) {
        query = query.startAfterDocument(startAfter);
      }

      final snapshot = await query.get();

      final sessions =
          snapshot.docs
              .map((doc) {
                try {
                  return ChatSessionSummary.fromFirestore(doc);
                } catch (e) {
                  _logger.warning('Error parsing session ${doc.id}: $e');
                  return null;
                }
              })
              .where((session) => session != null)
              .cast<ChatSessionSummary>()
              .toList();

      _logger.info('Loaded ${sessions.length} session summaries');
      return sessions;
    } catch (e, stackTrace) {
      _logger.severe('Error loading session history: $e', e, stackTrace);
      throw ChatSessionException('Failed to load session history: $e');
    }
  }

  /// Delete a chat session and all its messages
  Future<void> deleteSession(String userId, String sessionId) async {
    _logger.info('Deleting session $sessionId for user $userId');

    try {
      final batch = _firestore.batch();

      // Delete all messages
      final messagesSnapshot =
          await _getSessionMessagesCollection(userId, sessionId).get();
      for (final doc in messagesSnapshot.docs) {
        batch.delete(doc.reference);
      }

      // Delete session document
      final sessionRef = _getUserSessionsCollection(userId).doc(sessionId);
      batch.delete(sessionRef);

      await batch.commit();
      _logger.info('Successfully deleted session $sessionId');
    } catch (e, stackTrace) {
      _logger.severe('Error deleting session $sessionId: $e', e, stackTrace);
      throw ChatSessionException('Failed to delete session: $e');
    }
  }

  /// Save a single message to an existing session
  Future<void> saveMessage(
    String userId,
    String sessionId,
    ChatMessage message,
    int messageIndex,
  ) async {
    try {
      final messageRef = _getSessionMessagesCollection(userId, sessionId).doc();

      await messageRef.set({
        'text': message.text,
        'isUser': message.isUser,
        'isSystem': message.isSystem,
        'timestamp': Timestamp.fromDate(message.timestamp),
        'messageIndex': messageIndex,
      });

      // Update session metadata
      await _getUserSessionsCollection(userId).doc(sessionId).update({
        'updatedAt': Timestamp.fromDate(DateTime.now()),
        'lastMessageAt': Timestamp.fromDate(message.timestamp),
        'messageCount': FieldValue.increment(1),
      });

      _logger.info('Saved message to session $sessionId');
    } catch (e, stackTrace) {
      _logger.severe(
        'Error saving message to session $sessionId: $e',
        e,
        stackTrace,
      );
      throw ChatSessionException('Failed to save message: $e');
    }
  }

  /// Load messages for a specific session
  Future<List<ChatMessage>> loadMessages(
    String userId,
    String sessionId,
  ) async {
    try {
      final snapshot =
          await _getSessionMessagesCollection(
            userId,
            sessionId,
          ).orderBy('messageIndex').get();

      final messages =
          snapshot.docs.map((doc) {
            final data = doc.data();
            return ChatMessage(
              text: data['text'],
              isUser: data['isUser'],
              isSystem: data['isSystem'] ?? false,
              timestamp: (data['timestamp'] as Timestamp).toDate(),
            );
          }).toList();

      _logger.info('Loaded ${messages.length} messages for session $sessionId');
      return messages;
    } catch (e, stackTrace) {
      _logger.severe(
        'Error loading messages for session $sessionId: $e',
        e,
        stackTrace,
      );
      throw ChatSessionException('Failed to load messages: $e');
    }
  }

  /// Update session name
  Future<void> updateSessionName(
    String userId,
    String sessionId,
    String newName, {
    bool isAutoGenerated = false,
  }) async {
    _logger.info('Updating session $sessionId name to: $newName');

    try {
      final updateData = <String, dynamic>{
        'updatedAt': Timestamp.fromDate(DateTime.now()),
      };

      if (isAutoGenerated) {
        updateData['autoGeneratedName'] = newName;
      } else {
        updateData['name'] = newName;
      }

      await _getUserSessionsCollection(
        userId,
      ).doc(sessionId).update(updateData);
      _logger.info('Successfully updated session $sessionId name');
    } catch (e, stackTrace) {
      _logger.severe(
        'Error updating session $sessionId name: $e',
        e,
        stackTrace,
      );
      throw ChatSessionException('Failed to update session name: $e');
    }
  }

  /// Update session state
  Future<void> updateSessionState(
    String userId,
    String sessionId,
    SessionState state, {
    Map<String, int>? finalScores,
  }) async {
    try {
      final updateData = {
        'state': state.name,
        'updatedAt': Timestamp.fromDate(DateTime.now()),
        'isCompleted': state == SessionState.completed,
      };

      if (finalScores != null) {
        updateData['finalScores'] = finalScores;
      }

      await _getUserSessionsCollection(
        userId,
      ).doc(sessionId).update(updateData);
      _logger.info('Updated session $sessionId state to ${state.name}');
    } catch (e, stackTrace) {
      _logger.severe(
        'Error updating session $sessionId state: $e',
        e,
        stackTrace,
      );
      throw ChatSessionException('Failed to update session state: $e');
    }
  }

  /// Search sessions by name or topics
  Future<List<ChatSessionSummary>> searchSessions(
    String userId,
    String query, {
    int limit = 20,
  }) async {
    _logger.info('Searching sessions for user $userId with query: $query');

    try {
      // Note: Firestore doesn't support full-text search, so we'll implement
      // a simple name-based search. For production, consider using Algolia or similar.
      final snapshot =
          await _getUserSessionsCollection(userId)
              .where('name', isGreaterThanOrEqualTo: query)
              .where('name', isLessThan: query + '\uf8ff')
              .limit(limit)
              .get();

      final sessions =
          snapshot.docs
              .map((doc) {
                try {
                  return ChatSessionSummary.fromFirestore(doc);
                } catch (e) {
                  _logger.warning('Error parsing session ${doc.id}: $e');
                  return null;
                }
              })
              .where((session) => session != null)
              .cast<ChatSessionSummary>()
              .toList();

      _logger.info('Found ${sessions.length} sessions matching query');
      return sessions;
    } catch (e, stackTrace) {
      _logger.severe('Error searching sessions: $e', e, stackTrace);
      throw ChatSessionException('Failed to search sessions: $e');
    }
  }

  /// Get sessions by state (active, completed, etc.)
  Future<List<ChatSessionSummary>> getSessionsByState(
    String userId,
    SessionState state, {
    int limit = 20,
  }) async {
    try {
      final snapshot =
          await _getUserSessionsCollection(userId)
              .where('state', isEqualTo: state.name)
              .orderBy('updatedAt', descending: true)
              .limit(limit)
              .get();

      final sessions =
          snapshot.docs
              .map((doc) {
                try {
                  return ChatSessionSummary.fromFirestore(doc);
                } catch (e) {
                  _logger.warning('Error parsing session ${doc.id}: $e');
                  return null;
                }
              })
              .where((session) => session != null)
              .cast<ChatSessionSummary>()
              .toList();

      _logger.info('Found ${sessions.length} sessions in state ${state.name}');
      return sessions;
    } catch (e, stackTrace) {
      _logger.severe('Error getting sessions by state: $e', e, stackTrace);
      throw ChatSessionException('Failed to get sessions by state: $e');
    }
  }

  /// Check if user has any incomplete sessions
  Future<List<ChatSessionSummary>> getIncompleteSessions(String userId) async {
    _logger.info('Checking for incomplete sessions for user $userId');

    try {
      final activeSessionsQuery = _getUserSessionsCollection(userId)
          .where('isCompleted', isEqualTo: false)
          .orderBy('updatedAt', descending: true);

      final snapshot = await activeSessionsQuery.get();

      final sessions =
          snapshot.docs
              .map((doc) {
                try {
                  return ChatSessionSummary.fromFirestore(doc);
                } catch (e) {
                  _logger.warning('Error parsing session ${doc.id}: $e');
                  return null;
                }
              })
              .where((session) => session != null)
              .cast<ChatSessionSummary>()
              .toList();

      _logger.info('Found ${sessions.length} incomplete sessions');
      return sessions;
    } catch (e, stackTrace) {
      _logger.severe('Error getting incomplete sessions: $e', e, stackTrace);
      throw ChatSessionException('Failed to get incomplete sessions: $e');
    }
  }

  /// Stream session updates for real-time sync
  Stream<List<ChatSessionSummary>> watchSessionHistory(
    String userId, {
    int limit = 50,
  }) {
    return _getUserSessionsCollection(userId)
        .orderBy('updatedAt', descending: true)
        .limit(limit)
        .snapshots()
        .map((snapshot) {
          return snapshot.docs
              .map((doc) {
                try {
                  return ChatSessionSummary.fromFirestore(doc);
                } catch (e) {
                  _logger.warning('Error parsing session ${doc.id}: $e');
                  return null;
                }
              })
              .where((session) => session != null)
              .cast<ChatSessionSummary>()
              .toList();
        });
  }

  /// Load a specific chat session from Firestore by token
  Future<ChatSession?> loadSessionByToken(String userId, String token) async {
    _logger.info('Loading session by token: $token for user $userId');

    try {
      // Query by token field first
      var query = _getUserSessionsCollection(
        userId,
      ).where('token', isEqualTo: token).limit(1);

      var snapshot = await query.get();

      // If not found, try the old slug field for backward compatibility
      if (snapshot.docs.isEmpty) {
        query = _getUserSessionsCollection(
          userId,
        ).where('slug', isEqualTo: token).limit(1);

        snapshot = await query.get();
      }

      if (snapshot.docs.isEmpty) {
        _logger.warning('Session with token $token not found');
        return null;
      }

      final sessionDoc = snapshot.docs.first;

      // Get session messages
      final messagesSnapshot =
          await _getSessionMessagesCollection(
            userId,
            sessionDoc.id,
          ).orderBy('messageIndex').get();

      final messages =
          messagesSnapshot.docs.map((doc) {
            final data = doc.data();
            return ChatMessage(
              text: data['text'],
              isUser: data['isUser'],
              isSystem: data['isSystem'] ?? false,
              timestamp: (data['timestamp'] as Timestamp).toDate(),
            );
          }).toList();

      final session = ChatSession.fromFirestore(sessionDoc, messages);
      _logger.info(
        'Successfully loaded session by token $token with ${messages.length} messages',
      );
      return session;
    } catch (e, stackTrace) {
      _logger.severe(
        'Error loading session by token $token: $e',
        e,
        stackTrace,
      );
      throw ChatSessionException('Failed to load session by token: $e');
    }
  }

  /// Check if a token is available for a user
  Future<bool> isTokenAvailable(String userId, String token) async {
    try {
      // Check both token and slug fields for collision
      final tokenSnapshot =
          await _getUserSessionsCollection(
            userId,
          ).where('token', isEqualTo: token).limit(1).get();

      final slugSnapshot =
          await _getUserSessionsCollection(
            userId,
          ).where('slug', isEqualTo: token).limit(1).get();

      return tokenSnapshot.docs.isEmpty && slugSnapshot.docs.isEmpty;
    } catch (e) {
      _logger.warning('Error checking token availability: $e');
      return false;
    }
  }

  /// Get all existing tokens for a user (for uniqueness checking)
  Future<List<String>> getExistingTokens(String userId) async {
    try {
      final snapshot = await _getUserSessionsCollection(userId).get();

      final tokens = <String>[];

      for (final doc in snapshot.docs) {
        final data = doc.data();
        // Collect both tokens and slugs to ensure uniqueness
        if (data['token'] != null) {
          tokens.add(data['token'] as String);
        }
        if (data['slug'] != null) {
          tokens.add(data['slug'] as String);
        }
      }

      return tokens;
    } catch (e) {
      _logger.warning('Error getting existing tokens: $e');
      return [];
    }
  }

  /// Generate a unique token for a new session
  Future<String> generateUniqueToken(String userId) async {
    final existingTokens = await getExistingTokens(userId);
    return ChatSession.generateUniqueToken(existingTokens);
  }

  /// Migrate sessions with slugs to use tokens (optional migration utility)
  Future<void> migrateSessionsToTokens(String userId) async {
    _logger.info('Migrating sessions to use tokens for user $userId');

    try {
      final snapshot = await _getUserSessionsCollection(userId).get();
      final batch = _firestore.batch();
      int migratedCount = 0;

      for (final doc in snapshot.docs) {
        final data = doc.data();

        // Skip if already has a token
        if (data['token'] != null) continue;

        // Generate a new token
        final existingTokens = await getExistingTokens(userId);
        final newToken = ChatSession.generateUniqueToken(existingTokens);

        // Update the document
        batch.update(doc.reference, {'token': newToken});
        migratedCount++;
      }

      if (migratedCount > 0) {
        await batch.commit();
        _logger.info(
          'Successfully migrated $migratedCount sessions to use tokens',
        );
      } else {
        _logger.info('No sessions needed migration');
      }
    } catch (e, stackTrace) {
      _logger.severe('Error migrating sessions to tokens: $e', e, stackTrace);
      throw ChatSessionException('Failed to migrate sessions to tokens: $e');
    }
  }
}

/// Custom exception for chat session operations
class ChatSessionException implements Exception {
  final String message;
  final dynamic originalError;

  ChatSessionException(this.message, [this.originalError]);

  @override
  String toString() {
    return 'ChatSessionException: $message${originalError != null ? ' (caused by $originalError)' : ''}';
  }
}
