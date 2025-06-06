/// Abstract storage interface that defines the contract for data storage
/// This allows ScheduleManager to work with both local storage and Firestore
abstract class StorageInterface {
  /// Get user document reference
  StorageDocumentReference getUserDocument(String userId);

  /// Get user tasks collection reference
  StorageCollectionReference getUserTasksCollection(String userId);

  /// Check if this storage supports syncing (true for Firestore, false for local)
  bool get supportsSync;

  /// Get pending sync operations (only for local storage)
  Future<List<SyncOperation>> getPendingSyncOperations(String userId);

  /// Mark operation as synced (only for local storage)
  Future<void> markAsSynced(String userId, String operationId);

  /// Add pending sync operation (only for local storage)
  Future<void> addPendingSyncOperation(String userId, SyncOperation operation);
}

/// Represents a data operation that needs to be synced
class SyncOperation {
  final String id;
  final SyncOperationType type;
  final String collection;
  final String documentId;
  final Map<String, dynamic>? data;
  final DateTime timestamp;

  SyncOperation({
    required this.id,
    required this.type,
    required this.collection,
    required this.documentId,
    this.data,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type.toString(),
      'collection': collection,
      'documentId': documentId,
      'data': data,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory SyncOperation.fromJson(Map<String, dynamic> json) {
    return SyncOperation(
      id: json['id'] as String,
      type: SyncOperationType.values.firstWhere(
        (e) => e.toString() == json['type'],
      ),
      collection: json['collection'] as String,
      documentId: json['documentId'] as String,
      data: json['data'] as Map<String, dynamic>?,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}

enum SyncOperationType { create, update, delete }

/// Abstract document reference interface
abstract class StorageDocumentReference {
  /// Get document data
  Future<StorageDocumentSnapshot> get();

  /// Set document data
  Future<void> set(Map<String, dynamic> data, {StorageSetOptions? options});

  /// Update document data
  Future<void> update(Map<String, dynamic> data);

  /// Delete document
  Future<void> delete();
}

/// Abstract collection reference interface
abstract class StorageCollectionReference {
  /// Get collection documents
  Future<StorageQuerySnapshot> get();

  /// Get document reference in this collection
  StorageDocumentReference doc(String docId);
}

/// Abstract document snapshot interface
abstract class StorageDocumentSnapshot {
  /// Document ID
  String get id;

  /// Whether the document exists
  bool get exists;

  /// Get document data
  Map<String, dynamic>? data();
}

/// Abstract query snapshot interface
abstract class StorageQuerySnapshot {
  /// Get document snapshots
  List<StorageDocumentSnapshot> get docs;
}

/// Abstract set options interface
abstract class StorageSetOptions {
  bool get merge;
}

/// Universal set options implementation
class UniversalSetOptions implements StorageSetOptions {
  @override
  final bool merge;

  const UniversalSetOptions({this.merge = false});

  static const UniversalSetOptions mergeOption = UniversalSetOptions(
    merge: true,
  );
}
