import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/logger_service.dart';

/// Settings provider that manages user preferences
class SettingsProvider with ChangeNotifier {
  final _logger = getLogger('SettingsProvider');

  // Settings keys
  static const String _voiceEnabledKey = 'voice_enabled';
  static const String _sttEnabledKey = 'stt_enabled';

  // Default values
  bool _voiceEnabled = false; // Default to disabled
  bool _sttEnabled = true; // Default to enabled

  // Getters
  bool get voiceEnabled => _voiceEnabled;
  bool get sttEnabled => _sttEnabled;

  SettingsProvider() {
    _loadSettings();
  }

  /// Load settings from SharedPreferences
  Future<void> _loadSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _voiceEnabled = prefs.getBool(_voiceEnabledKey) ?? true;
      _sttEnabled = prefs.getBool(_sttEnabledKey) ?? false;
      _logger.info(
        'Settings loaded - voice enabled: $_voiceEnabled, stt enabled: $_sttEnabled',
      );
      notifyListeners();
    } catch (e) {
      _logger.severe('Error loading settings: $e');
    }
  }

  /// Save settings to SharedPreferences
  Future<void> _saveSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_voiceEnabledKey, _voiceEnabled);
      await prefs.setBool(_sttEnabledKey, _sttEnabled);
      _logger.info(
        'Settings saved - voice enabled: $_voiceEnabled, stt enabled: $_sttEnabled',
      );
    } catch (e) {
      _logger.severe('Error saving settings: $e');
    }
  }

  /// Toggle voice feature
  Future<void> toggleVoiceEnabled() async {
    _voiceEnabled = !_voiceEnabled;
    await _saveSettings();
    notifyListeners();
    _logger.info('Voice feature toggled to: $_voiceEnabled');
  }

  /// Set voice feature enabled/disabled
  Future<void> setVoiceEnabled(bool enabled) async {
    if (_voiceEnabled != enabled) {
      _voiceEnabled = enabled;
      await _saveSettings();
      notifyListeners();
      _logger.info('Voice feature set to: $_voiceEnabled');
    }
  }

  /// Toggle STT feature
  Future<void> toggleSttEnabled() async {
    _sttEnabled = !_sttEnabled;
    await _saveSettings();
    notifyListeners();
    _logger.info('STT feature toggled to: $_sttEnabled');
  }

  /// Set STT feature enabled/disabled
  Future<void> setSttEnabled(bool enabled) async {
    if (_sttEnabled != enabled) {
      _sttEnabled = enabled;
      await _saveSettings();
      notifyListeners();
      _logger.info('STT feature set to: $_sttEnabled');
    }
  }
}
