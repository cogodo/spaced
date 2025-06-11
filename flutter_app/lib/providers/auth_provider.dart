import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';

import '../services/auth_service.dart';
import '../services/logger_service.dart';

/// Authentication state provider that manages user authentication state
/// and provides authentication methods to the UI
class AuthProvider with ChangeNotifier {
  final AuthService _authService = AuthService();
  final _logger = getLogger('AuthProvider');

  StreamSubscription<User?>? _authStateSubscription;
  User? _user;
  bool _isLoading = false;
  String? _errorMessage;
  bool _isInitialized = false;

  /// Current authenticated user
  User? get user => _user;

  /// Whether a user is currently signed in
  bool get isSignedIn => _user != null;

  /// Whether an authentication operation is in progress
  bool get isLoading => _isLoading;

  /// Current error message, if any
  String? get errorMessage => _errorMessage;

  /// Whether the auth provider has been initialized
  bool get isInitialized => _isInitialized;

  /// User display name (fallback to email if no display name)
  String get displayName {
    if (_user?.displayName != null && _user!.displayName!.isNotEmpty) {
      return _user!.displayName!;
    }
    return _user?.email ?? 'User';
  }

  /// User's email address
  String? get email => _user?.email;

  /// Whether the user's email is verified
  bool get isEmailVerified => _user?.emailVerified ?? false;

  AuthProvider() {
    _initializeAuthState();
  }

  /// Initialize authentication state listener
  void _initializeAuthState() {
    _logger.info('🔥 Initializing auth state listener');

    // Get the current user immediately
    _user = _authService.currentUser;
    _logger.info('🔥 Initial user state: ${_user?.uid ?? 'null'}');

    // Mark as initialized immediately if we have a definitive state
    if (_user == null) {
      _isInitialized = true;
      _logger.info('🔥 Auth initialized immediately (no user)');
      notifyListeners();
    }

    // Set up the stream listener
    _authStateSubscription = _authService.authStateChanges.listen(
      (User? user) {
        _logger.info(
          '🔥 Auth state changed: ${user?.uid ?? 'null'} (email: ${user?.email ?? 'null'})',
        );

        final bool wasSignedIn = _user != null;
        final bool isNowSignedIn = user != null;

        _user = user;

        // Clear errors on auth state changes to prevent stale error messages
        _clearError();

        if (!_isInitialized) {
          _isInitialized = true;
          _logger.info('🔥 Auth provider initialized via stream');
        }

        // Log state transition for debugging
        if (wasSignedIn != isNowSignedIn) {
          _logger.info(
            '🔥 Auth state transition: wasSignedIn=$wasSignedIn -> isNowSignedIn=$isNowSignedIn',
          );
        }

        _logger.info(
          '🔥 About to call notifyListeners(), isSignedIn will be: $isNowSignedIn',
        );
        notifyListeners();
        _logger.info('🔥 notifyListeners() completed');
      },
      onError: (error) {
        _logger.severe('🔥 Auth state stream error: $error');
        _setError('Authentication state error');
        if (!_isInitialized) {
          _isInitialized = true;
          _logger.info('🔥 Auth initialized due to error');
        }
        notifyListeners();
      },
    );

    // If we already have a user, mark as initialized
    if (_user != null) {
      _isInitialized = true;
      _logger.info('🔥 Auth initialized immediately (user exists)');
      notifyListeners();
    }
  }

  /// Sign up with email and password
  Future<void> signUpWithEmail({
    required String email,
    required String password,
  }) async {
    await _performAuthOperation(() async {
      final userCredential = await _authService.signUpWithEmail(
        email: email,
        password: password,
      );
      _logger.info('User signed up successfully: ${userCredential.user?.uid}');

      // Force update the user state immediately after successful sign up
      _user = userCredential.user;
      _logger.info('Updated local user state after sign up');
      notifyListeners(); // Immediately notify listeners for faster UI response
    });
  }

  /// Sign in with email and password
  Future<void> signInWithEmail({
    required String email,
    required String password,
  }) async {
    await _performAuthOperation(() async {
      _logger.info('🔐 Starting email sign in process');
      final userCredential = await _authService.signInWithEmail(
        email: email,
        password: password,
      );
      _logger.info('User signed in successfully: ${userCredential.user?.uid}');

      // Force update the user state immediately after successful sign in
      _user = userCredential.user;
      _logger.info('Updated local user state after sign in');
      _logger.info(
        '🚀 Sign in complete, calling notifyListeners() - this should trigger router redirect',
      );
      notifyListeners(); // Immediately notify listeners for faster UI response
    });
  }

  /// Sign in with Google OAuth
  Future<void> signInWithGoogle() async {
    await _performAuthOperation(() async {
      final userCredential = await _authService.signInWithGoogle();
      _logger.info(
        'User signed in with Google successfully: ${userCredential.user?.uid}',
      );

      // Force update the user state immediately after successful Google sign in
      _user = userCredential.user;
      _logger.info('Updated local user state after Google sign in');
      notifyListeners(); // Immediately notify listeners for faster UI response
    });
  }

  /// Send password reset email
  Future<void> sendPasswordResetEmail(String email) async {
    await _performAuthOperation(() async {
      await _authService.sendPasswordResetEmail(email);
      _logger.info('Password reset email sent');
    });
  }

  /// Sign out current user
  Future<void> signOut() async {
    await _performAuthOperation(() async {
      await _authService.signOut();
      _logger.info('User signed out successfully');
      // Clear any existing errors after successful sign out
      _clearError();
    });
  }

  /// Delete current user account
  Future<void> deleteAccount() async {
    await _performAuthOperation(() async {
      await _authService.deleteAccount();
      _logger.info('User account deleted successfully');
    });
  }

  /// Send email verification to current user
  Future<void> sendEmailVerification() async {
    await _performAuthOperation(() async {
      await _authService.sendEmailVerification();
      _logger.info('Email verification sent successfully');
    });
  }

  /// Reload current user to get updated information
  Future<void> reloadUser() async {
    if (_user != null) {
      await _performAuthOperation(() async {
        await _user!.reload();
        _user = _authService.currentUser;
        _logger.info('User data reloaded');
      });
    }
  }

  /// Clear current error message
  void clearError() {
    _clearError();
    notifyListeners();
  }

  /// Perform an authentication operation with loading state and error handling
  Future<void> _performAuthOperation(Future<void> Function() operation) async {
    _setLoading(true);
    _clearError();

    try {
      await operation();
    } on AuthException catch (e) {
      _logger.warning('Auth operation failed: ${e.message}');
      _setError(e.message);
    } catch (e) {
      _logger.severe('Unexpected error during auth operation: $e');
      _setError('An unexpected error occurred. Please try again.');
    } finally {
      _setLoading(false);
    }
  }

  /// Set loading state
  void _setLoading(bool isLoading) {
    _isLoading = isLoading;
    notifyListeners();
  }

  /// Set error message
  void _setError(String message) {
    _errorMessage = message;
    notifyListeners();
  }

  /// Clear error message
  void _clearError() {
    _errorMessage = null;
  }

  @override
  void dispose() {
    _authStateSubscription?.cancel();
    super.dispose();
  }
}
