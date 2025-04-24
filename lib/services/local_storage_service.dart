import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

// A simple in-memory database to replace Firestore
class LocalStorageService {
  // In-memory database structure
  final Map<String, Map<String, dynamic>> _database = {};

  // Constructor
  LocalStorageService() {
    print("LocalStorageService initializing");
    // Load data asynchronously but don't block initialization
    _loadFromDisk();
  }

  // Load data from SharedPreferences on startup
  Future<void> _loadFromDisk() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final databaseJson = prefs.getString('localDatabase');
      if (databaseJson != null) {
        final Map<String, dynamic> loadedData = jsonDecode(databaseJson);
        for (var entry in loadedData.entries) {
          _database[entry.key] = Map<String, dynamic>.from(entry.value);
        }
      }
      print("Local database loaded from disk");
    } catch (e) {
      print("Error loading local database: $e");
    }
  }

  // Save data to SharedPreferences
  Future<void> _saveToDisk() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final databaseJson = jsonEncode(_database);
      await prefs.setString('localDatabase', databaseJson);
      print("Local database saved to disk");
    } catch (e) {
      print("Error saving local database: $e");
    }
  }

  // Get document reference - simulates Firestore DocumentReference
  LocalDocumentReference collection(String collectionPath) {
    return LocalDocumentReference(this, collectionPath);
  }

  // Get user document reference
  LocalDocumentReference getUserDocument(String userId) {
    return collection('users').doc(userId);
  }

  // Get tasks collection reference for a user
  LocalCollectionReference getUserTasksCollection(String userId) {
    return collection('users').doc(userId).collection('tasks');
  }

  // Internal methods to access database
  Map<String, dynamic>? _getDocument(String path) {
    return _database[path];
  }

  void _setDocument(
    String path,
    Map<String, dynamic> data, {
    bool merge = false,
  }) {
    if (merge && _database.containsKey(path)) {
      _database[path]!.addAll(data);
    } else {
      _database[path] = data;
    }
    _saveToDisk();
  }

  void _deleteDocument(String path) {
    _database.remove(path);
    _saveToDisk();
  }

  List<Map<String, dynamic>> _getCollection(String collectionPath) {
    final prefix = '$collectionPath/';
    final result = <Map<String, dynamic>>[];

    for (var entry in _database.entries) {
      final key = entry.key;
      if (key.startsWith(prefix) &&
          !key.substring(prefix.length).contains('/')) {
        result.add({...entry.value, 'id': key.substring(prefix.length)});
      }
    }

    return result;
  }

  // Clear all data (for testing)
  Future<void> clearAllData() async {
    _database.clear();
    await _saveToDisk();
  }
}

// Local document reference - simulates Firestore DocumentReference
class LocalDocumentReference {
  final LocalStorageService _service;
  final String _path;

  LocalDocumentReference(this._service, this._path);

  // Get a document by ID
  LocalDocumentReference doc(String docId) {
    return LocalDocumentReference(_service, '$_path/$docId');
  }

  // Get a subcollection
  LocalCollectionReference collection(String collectionPath) {
    return LocalCollectionReference(_service, '$_path/$collectionPath');
  }

  // Get document data
  Future<LocalDocumentSnapshot> get() async {
    final data = _service._getDocument(_path);
    return LocalDocumentSnapshot(_path, data);
  }

  // Set document data
  Future<void> set(
    Map<String, dynamic> data, {
    LocalSetOptions? options,
  }) async {
    _service._setDocument(_path, data, merge: options?.merge ?? false);
  }

  // Update document data
  Future<void> update(Map<String, dynamic> data) async {
    _service._setDocument(_path, data, merge: true);
  }

  // Delete document
  Future<void> delete() async {
    _service._deleteDocument(_path);
  }
}

// Local collection reference - simulates Firestore CollectionReference
class LocalCollectionReference {
  final LocalStorageService _service;
  final String _path;

  LocalCollectionReference(this._service, this._path);

  // Get a document by ID
  LocalDocumentReference doc(String docId) {
    return LocalDocumentReference(_service, '$_path/$docId');
  }

  // Get all documents in collection
  Future<LocalQuerySnapshot> get() async {
    final docs = _service._getCollection(_path);
    return LocalQuerySnapshot(docs);
  }

  // Add a document with auto-generated ID
  Future<LocalDocumentReference> add(Map<String, dynamic> data) async {
    final docId = DateTime.now().millisecondsSinceEpoch.toString();
    final docRef = doc(docId);
    await docRef.set(data);
    return docRef;
  }
}

// Local document snapshot - simulates Firestore DocumentSnapshot
class LocalDocumentSnapshot {
  final String _path;
  final Map<String, dynamic>? _data;

  LocalDocumentSnapshot(this._path, this._data);

  // Get document ID
  String get id => _path.split('/').last;

  // Check if document exists
  bool get exists => _data != null;

  // Get document data
  Map<String, dynamic>? data() =>
      _data != null ? Map<String, dynamic>.from(_data!) : null;
}

// Local query snapshot - simulates Firestore QuerySnapshot
class LocalQuerySnapshot {
  final List<Map<String, dynamic>> _docs;

  LocalQuerySnapshot(this._docs);

  // Get all document snapshots
  List<LocalDocumentSnapshot> get docs =>
      _docs.map((data) {
        final id = data['id'];
        data.remove('id');
        return LocalDocumentSnapshot(id, data);
      }).toList();
}

// Local set options - simulates Firestore SetOptions
class LocalSetOptions {
  final bool merge;

  LocalSetOptions({required this.merge});

  static LocalSetOptions get mergeOption => LocalSetOptions(merge: true);
}
