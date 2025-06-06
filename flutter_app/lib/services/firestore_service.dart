import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../services/logger_service.dart';
import 'storage_interface.dart';

/// Firestore service that provides the same interface as LocalStorageService
/// but uses Firebase Firestore for persistent, user-specific data storage
class FirestoreService implements StorageInterface {
  final _firestore = FirebaseFirestore.instance;
  final _logger = getLogger('FirestoreService');

  // Add timeout for all operations
  static const Duration _timeout = Duration(seconds: 10);

  @override
  bool get supportsSync => true; // Firestore is the cloud storage

  @override
  StorageDocumentReference getUserDocument(String userId) {
    _logger.info('Getting user document for: $userId');
    return FirestoreDocumentReference(
      _firestore.collection('users').doc(userId),
    );
  }

  @override
  StorageCollectionReference getUserTasksCollection(String userId) {
    _logger.info('Getting tasks collection for: $userId');
    return FirestoreCollectionReference(
      _firestore.collection('users').doc(userId).collection('tasks'),
    );
  }

  @override
  Future<List<SyncOperation>> getPendingSyncOperations(String userId) async {
    // Firestore doesn't need pending operations - it's the target
    return [];
  }

  @override
  Future<void> markAsSynced(String userId, String operationId) async {
    // Firestore doesn't track pending operations
  }

  @override
  Future<void> addPendingSyncOperation(
    String userId,
    SyncOperation operation,
  ) async {
    // Firestore doesn't add pending operations
  }
}

/// Wrapper for Firestore DocumentReference to match StorageInterface
class FirestoreDocumentReference implements StorageDocumentReference {
  final DocumentReference _ref;
  final _logger = getLogger('FirestoreDocumentReference');

  FirestoreDocumentReference(this._ref);

  @override
  Future<StorageDocumentSnapshot> get() async {
    try {
      _logger.info('Getting document: ${_ref.path}');
      final snapshot = await _ref.get().timeout(FirestoreService._timeout);
      _logger.info('Retrieved document: ${_ref.path}');
      return FirestoreDocumentSnapshot(snapshot);
    } catch (e) {
      _logger.severe('Error getting document ${_ref.path}: $e');
      rethrow;
    }
  }

  @override
  Future<void> set(
    Map<String, dynamic> data, {
    StorageSetOptions? options,
  }) async {
    try {
      _logger.info('Setting document: ${_ref.path}');
      if (options?.merge == true) {
        await _ref
            .set(data, SetOptions(merge: true))
            .timeout(FirestoreService._timeout);
      } else {
        await _ref.set(data).timeout(FirestoreService._timeout);
      }
      _logger.info('Set document: ${_ref.path}');
    } catch (e) {
      _logger.severe('Error setting document ${_ref.path}: $e');
      rethrow;
    }
  }

  @override
  Future<void> update(Map<String, dynamic> data) async {
    try {
      _logger.info('Updating document: ${_ref.path}');
      await _ref.update(data).timeout(FirestoreService._timeout);
      _logger.info('Updated document: ${_ref.path}');
    } catch (e) {
      _logger.severe('Error updating document ${_ref.path}: $e');
      rethrow;
    }
  }

  @override
  Future<void> delete() async {
    try {
      _logger.info('Deleting document: ${_ref.path}');
      await _ref.delete().timeout(FirestoreService._timeout);
      _logger.info('Deleted document: ${_ref.path}');
    } catch (e) {
      _logger.severe('Error deleting document ${_ref.path}: $e');
      rethrow;
    }
  }
}

/// Wrapper for Firestore CollectionReference to match StorageInterface
class FirestoreCollectionReference implements StorageCollectionReference {
  final CollectionReference _ref;
  final _logger = getLogger('FirestoreCollectionReference');

  FirestoreCollectionReference(this._ref);

  @override
  Future<StorageQuerySnapshot> get() async {
    try {
      _logger.info('Getting collection: ${_ref.path}');
      final snapshot = await _ref.get().timeout(FirestoreService._timeout);
      _logger.info(
        'Retrieved collection: ${_ref.path} (${snapshot.docs.length} docs)',
      );
      return FirestoreQuerySnapshot(snapshot);
    } catch (e) {
      _logger.severe('Error getting collection ${_ref.path}: $e');
      rethrow;
    }
  }

  @override
  StorageDocumentReference doc(String docId) {
    return FirestoreDocumentReference(_ref.doc(docId));
  }
}

/// Wrapper for Firestore DocumentSnapshot to match StorageInterface
class FirestoreDocumentSnapshot implements StorageDocumentSnapshot {
  final DocumentSnapshot _snapshot;

  FirestoreDocumentSnapshot(this._snapshot);

  @override
  String get id => _snapshot.id;

  @override
  bool get exists => _snapshot.exists;

  @override
  Map<String, dynamic>? data() {
    return _snapshot.data() as Map<String, dynamic>?;
  }
}

/// Wrapper for Firestore QuerySnapshot to match StorageInterface
class FirestoreQuerySnapshot implements StorageQuerySnapshot {
  final QuerySnapshot _snapshot;

  FirestoreQuerySnapshot(this._snapshot);

  @override
  List<StorageDocumentSnapshot> get docs {
    return _snapshot.docs.map((doc) => FirestoreDocumentSnapshot(doc)).toList();
  }
}

/// Set options for Firestore operations
class FirestoreSetOptions implements StorageSetOptions {
  @override
  final bool merge;

  const FirestoreSetOptions({this.merge = false});
}
