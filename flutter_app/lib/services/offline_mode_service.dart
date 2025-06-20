import 'dart:async';
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'session_api.dart';

class OfflineModeService {
  static const String _popularTopicsCacheKey = 'cached_popular_topics';
  static const String _lastSyncKey = 'last_sync_timestamp';
  static const String _userTopicsCacheKey = 'cached_user_topics';

  final SessionApi _sessionApi;
  Timer? _syncTimer;

  OfflineModeService(this._sessionApi);

  /// Check if we're in offline mode (circuit breakers open or no connectivity)
  bool get isOfflineMode => _sessionApi.hasOpenCircuitBreakers;

  /// Start periodic sync when online
  void startPeriodicSync() {
    _syncTimer?.cancel();
    _syncTimer = Timer.periodic(const Duration(minutes: 5), (_) {
      if (!isOfflineMode) {
        _syncCachedData();
      }
    });
  }

  /// Stop periodic sync
  void stopPeriodicSync() {
    _syncTimer?.cancel();
  }

  /// Get popular topics with offline fallback
  Future<List<PopularTopic>> getPopularTopics() async {
    try {
      // Try to get from API first
      if (!isOfflineMode) {
        final topics = await _sessionApi.getPopularTopics();
        await _cachePopularTopics(topics);
        return topics;
      }
    } catch (e) {
      // Fall back to cached data
    }

    // Return cached data or fallback
    return await _getCachedPopularTopics();
  }

  /// Search topics with offline fallback
  Future<List<UserTopic>> searchTopics(String query) async {
    try {
      // Try to get from API first
      if (!isOfflineMode) {
        final topics = await _sessionApi.searchTopics(query);
        await _cacheUserTopics(topics, query);
        return topics;
      }
    } catch (e) {
      // Fall back to cached data
    }

    // Return cached data
    return await _getCachedUserTopics(query);
  }

  /// Validate topics with offline fallback
  Future<TopicValidationResponse?> validateTopics(List<String> topics) async {
    try {
      if (!isOfflineMode) {
        return await _sessionApi.validateTopics(topics);
      }
    } catch (e) {
      // Fall back to simple validation
    }

    // Offline validation - just return valid topics
    return TopicValidationResponse(
      validTopics: topics,
      suggestions: [],
      hasErrors: false,
    );
  }

  /// Get offline session suggestions
  List<String> getOfflineSessionSuggestions() {
    return [
      "I'm currently in offline mode. Here's what you can do:",
      "",
      "✅ **Browse cached topics** - I have some popular topics saved locally",
      "✅ **Review past sessions** - Access your session history",
      "✅ **Practice mode** - Work with pre-loaded questions",
      "",
      "❌ **New AI sessions** - Requires internet connection",
      "❌ **Real-time scoring** - Backend processing needed",
      "",
      "💡 **Tip**: I'll automatically reconnect when your internet is back!",
    ];
  }

  /// Cache popular topics
  Future<void> _cachePopularTopics(List<PopularTopic> topics) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonData =
          topics
              .map((t) => {'name': t.name, 'description': t.description})
              .toList();

      await prefs.setString(_popularTopicsCacheKey, jsonEncode(jsonData));
      await prefs.setInt(_lastSyncKey, DateTime.now().millisecondsSinceEpoch);
    } catch (e) {
      // Ignore cache errors
    }
  }

  /// Get cached popular topics
  Future<List<PopularTopic>> _getCachedPopularTopics() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cachedData = prefs.getString(_popularTopicsCacheKey);

      if (cachedData != null) {
        final jsonList = jsonDecode(cachedData) as List;
        return jsonList
            .map(
              (item) => PopularTopic(
                name: item['name'] as String,
                description: item['description'] as String,
              ),
            )
            .toList();
      }
    } catch (e) {
      // Ignore cache errors
    }

    // Fallback popular topics
    return [
      PopularTopic(
        name: 'Python Programming',
        description: 'Learn Python fundamentals',
      ),
      PopularTopic(
        name: 'Machine Learning',
        description: 'ML algorithms and models',
      ),
      PopularTopic(
        name: 'Web Development',
        description: 'Frontend and backend technologies',
      ),
      PopularTopic(
        name: 'Data Science',
        description: 'Data analysis and visualization',
      ),
      PopularTopic(
        name: 'Mobile Development',
        description: 'iOS, Android development',
      ),
      PopularTopic(name: 'Cloud Computing', description: 'AWS, Azure, GCP'),
    ];
  }

  /// Cache user topics for a query
  Future<void> _cacheUserTopics(List<UserTopic> topics, String query) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cacheKey = '${_userTopicsCacheKey}_${query.toLowerCase()}';

      final jsonData =
          topics
              .map(
                (t) => {
                  'id': t.id,
                  'name': t.name,
                  'description': t.description,
                },
              )
              .toList();

      await prefs.setString(cacheKey, jsonEncode(jsonData));
    } catch (e) {
      // Ignore cache errors
    }
  }

  /// Get cached user topics for a query
  Future<List<UserTopic>> _getCachedUserTopics(String query) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cacheKey = '${_userTopicsCacheKey}_${query.toLowerCase()}';
      final cachedData = prefs.getString(cacheKey);

      if (cachedData != null) {
        final jsonList = jsonDecode(cachedData) as List;
        return jsonList
            .map(
              (item) => UserTopic(
                id: item['id'] as String,
                name: item['name'] as String,
                description: item['description'] as String,
              ),
            )
            .toList();
      }
    } catch (e) {
      // Ignore cache errors
    }

    return [];
  }

  /// Sync cached data when coming back online
  Future<void> _syncCachedData() async {
    try {
      // Refresh popular topics cache
      final topics = await _sessionApi.getPopularTopics();
      await _cachePopularTopics(topics);
    } catch (e) {
      // Sync will retry on next timer
    }
  }

  /// Clear all cached data
  Future<void> clearCache() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_popularTopicsCacheKey);
      await prefs.remove(_lastSyncKey);

      // Remove all user topic caches
      final keys = prefs.getKeys();
      for (final key in keys) {
        if (key.startsWith(_userTopicsCacheKey)) {
          await prefs.remove(key);
        }
      }
    } catch (e) {
      // Ignore cache errors
    }
  }

  /// Get cache status for debugging
  Future<Map<String, dynamic>> getCacheStatus() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final lastSync = prefs.getInt(_lastSyncKey);
      final hasPopularTopics = prefs.containsKey(_popularTopicsCacheKey);

      final userTopicCaches =
          prefs
              .getKeys()
              .where((key) => key.startsWith(_userTopicsCacheKey))
              .length;

      return {
        'hasPopularTopicsCache': hasPopularTopics,
        'userTopicCaches': userTopicCaches,
        'lastSyncTime':
            lastSync != null
                ? DateTime.fromMillisecondsSinceEpoch(
                  lastSync,
                ).toIso8601String()
                : null,
        'isOfflineMode': isOfflineMode,
      };
    } catch (e) {
      return {'error': e.toString()};
    }
  }

  void dispose() {
    stopPeriodicSync();
  }
}
