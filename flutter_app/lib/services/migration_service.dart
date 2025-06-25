import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:logging/logging.dart';

/// Service for handling data migrations between schema versions
///
/// Note: Updated to use 'sessions' collection (unified with backend)
/// instead of legacy 'chatSessions' collection
class MigrationService {
  static final Logger _logger = Logger('MigrationService');
  final FirebaseFirestore _firestore;

  MigrationService({FirebaseFirestore? firestore})
    : _firestore = firestore ?? FirebaseFirestore.instance;

  /// Migrate all sessions for a user from slugs to tokens
  Future<MigrationResult> migrateUserSessionsToTokens(String userId) async {
    _logger.info('Starting migration to tokens for user: $userId');

    try {
      // Get all user sessions from unified 'sessions' collection
      final sessionsCollection = _firestore
          .collection('users')
          .doc(userId)
          .collection('sessions'); // Changed from 'chatSessions' to 'sessions'

      final snapshot = await sessionsCollection.get();

      if (snapshot.docs.isEmpty) {
        _logger.info('No sessions found for user $userId');
        return MigrationResult(
          success: true,
          totalSessions: 0,
          migratedSessions: 0,
          skippedSessions: 0,
          message: 'No sessions to migrate',
        );
      }

      final batch = _firestore.batch();
      final existingTokens = <String>[];
      int migratedCount = 0;
      int skippedCount = 0;

      // First pass: collect existing tokens
      for (final doc in snapshot.docs) {
        final data = doc.data();
        if (data['token'] != null) {
          existingTokens.add(data['token'] as String);
        }
        if (data['slug'] != null) {
          existingTokens.add(data['slug'] as String);
        }
      }

      // Second pass: migrate sessions that need tokens
      for (final doc in snapshot.docs) {
        final data = doc.data();

        // Skip if already has a token
        if (data['token'] != null) {
          skippedCount++;
          continue;
        }

        // Generate a unique token
        final newToken = doc.id; // Use session ID as token
        existingTokens.add(newToken); // Add to list to avoid collisions

        // Update the document
        batch.update(doc.reference, {'token': newToken});
        migratedCount++;

        _logger.fine('Migrating session ${doc.id}: adding token $newToken');
      }

      // Commit all changes
      if (migratedCount > 0) {
        await batch.commit();
        _logger.info(
          'Successfully migrated $migratedCount sessions for user $userId',
        );
      }

      return MigrationResult(
        success: true,
        totalSessions: snapshot.docs.length,
        migratedSessions: migratedCount,
        skippedSessions: skippedCount,
        message:
            migratedCount > 0
                ? 'Successfully migrated $migratedCount sessions'
                : 'All sessions already have tokens',
      );
    } catch (e, stackTrace) {
      _logger.severe(
        'Error migrating sessions for user $userId: $e',
        e,
        stackTrace,
      );
      return MigrationResult(
        success: false,
        totalSessions: 0,
        migratedSessions: 0,
        skippedSessions: 0,
        message: 'Migration failed: $e',
      );
    }
  }

  /// Migrate all users' sessions (admin utility)
  Future<GlobalMigrationResult> migrateAllUsersToTokens() async {
    _logger.info('Starting global migration to tokens for all users');

    try {
      final usersSnapshot = await _firestore.collection('users').get();

      final results = <String, MigrationResult>{};
      int totalUsers = usersSnapshot.docs.length;
      int successfulUsers = 0;
      int totalSessionsMigrated = 0;

      for (final userDoc in usersSnapshot.docs) {
        final userId = userDoc.id;
        _logger.info('Migrating user: $userId');

        final result = await migrateUserSessionsToTokens(userId);
        results[userId] = result;

        if (result.success) {
          successfulUsers++;
          totalSessionsMigrated += result.migratedSessions;
        }
      }

      _logger.info(
        'Global migration completed: $successfulUsers/$totalUsers users, '
        '$totalSessionsMigrated total sessions migrated',
      );

      return GlobalMigrationResult(
        success: true,
        totalUsers: totalUsers,
        successfulUsers: successfulUsers,
        totalSessionsMigrated: totalSessionsMigrated,
        userResults: results,
        message: 'Global migration completed successfully',
      );
    } catch (e, stackTrace) {
      _logger.severe('Error in global migration: $e', e, stackTrace);
      return GlobalMigrationResult(
        success: false,
        totalUsers: 0,
        successfulUsers: 0,
        totalSessionsMigrated: 0,
        userResults: {},
        message: 'Global migration failed: $e',
      );
    }
  }
}

/// Result of a single user's session migration
class MigrationResult {
  final bool success;
  final int totalSessions;
  final int migratedSessions;
  final int skippedSessions;
  final String message;

  MigrationResult({
    required this.success,
    required this.totalSessions,
    required this.migratedSessions,
    required this.skippedSessions,
    required this.message,
  });

  @override
  String toString() {
    return 'MigrationResult(success: $success, total: $totalSessions, '
        'migrated: $migratedSessions, skipped: $skippedSessions, '
        'message: "$message")';
  }
}

/// Result of global migration across all users
class GlobalMigrationResult {
  final bool success;
  final int totalUsers;
  final int successfulUsers;
  final int totalSessionsMigrated;
  final Map<String, MigrationResult> userResults;
  final String message;

  GlobalMigrationResult({
    required this.success,
    required this.totalUsers,
    required this.successfulUsers,
    required this.totalSessionsMigrated,
    required this.userResults,
    required this.message,
  });

  @override
  String toString() {
    return 'GlobalMigrationResult(success: $success, '
        'users: $successfulUsers/$totalUsers, '
        'sessions: $totalSessionsMigrated, message: "$message")';
  }
}
