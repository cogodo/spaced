import 'dart:async';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

import 'logger_service.dart';

/// Authentication service that handles Firebase Auth operations
/// Supports email/password and Google OAuth authentication
class AuthService {
  final FirebaseAuth _firebaseAuth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();
  final _logger = getLogger('AuthService');

  /// Stream of authentication state changes
  Stream<User?> get authStateChanges => _firebaseAuth.authStateChanges();

  /// Current authenticated user
  User? get currentUser => _firebaseAuth.currentUser;

  /// Whether a user is currently signed in
  bool get isSignedIn => currentUser != null;

  /// Sign up with email and password
  Future<UserCredential> signUpWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      _logger.info('Signing up user with email: $email');

      final userCredential = await _firebaseAuth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );

      // Send email verification
      await userCredential.user?.sendEmailVerification();
      _logger.info('Email verification sent to: $email');

      return userCredential;
    } on FirebaseAuthException catch (e) {
      _logger.warning('Sign up failed: ${e.code} - ${e.message}');
      throw _handleAuthException(e);
    } catch (e) {
      _logger.severe('Unexpected error during sign up: $e');
      throw AuthException('An unexpected error occurred. Please try again.');
    }
  }

  /// Sign in with email and password
  Future<UserCredential> signInWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      _logger.info('Signing in user with email: $email');

      final userCredential = await _firebaseAuth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );

      _logger.info('User signed in successfully: ${userCredential.user?.uid}');
      return userCredential;
    } on FirebaseAuthException catch (e) {
      _logger.warning('Sign in failed: ${e.code} - ${e.message}');
      throw _handleAuthException(e);
    } catch (e) {
      _logger.severe('Unexpected error during sign in: $e');
      throw AuthException('An unexpected error occurred. Please try again.');
    }
  }

  /// Sign in with Google OAuth
  Future<UserCredential> signInWithGoogle() async {
    try {
      _logger.info('Starting Google sign in');

      // Trigger the authentication flow
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();

      if (googleUser == null) {
        _logger.info('Google sign in was cancelled by user');
        throw AuthException('Sign in was cancelled');
      }

      // Obtain the auth details from the request
      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      // Create a new credential
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // Sign in to Firebase with the Google credentials
      final userCredential = await _firebaseAuth.signInWithCredential(
        credential,
      );

      _logger.info('Google sign in successful: ${userCredential.user?.uid}');
      return userCredential;
    } on FirebaseAuthException catch (e) {
      _logger.warning('Google sign in failed: ${e.code} - ${e.message}');
      throw _handleAuthException(e);
    } catch (e) {
      _logger.severe('Unexpected error during Google sign in: $e');
      throw AuthException('Google sign in failed. Please try again.');
    }
  }

  /// Send password reset email
  Future<void> sendPasswordResetEmail(String email) async {
    try {
      _logger.info('Sending password reset email to: $email');

      await _firebaseAuth.sendPasswordResetEmail(email: email);

      _logger.info('Password reset email sent successfully');
    } on FirebaseAuthException catch (e) {
      _logger.warning('Password reset failed: ${e.code} - ${e.message}');
      throw _handleAuthException(e);
    } catch (e) {
      _logger.severe('Unexpected error during password reset: $e');
      throw AuthException(
        'Failed to send password reset email. Please try again.',
      );
    }
  }

  /// Sign out current user
  Future<void> signOut() async {
    try {
      _logger.info('Signing out user: ${currentUser?.uid}');

      // Sign out from both Firebase and Google
      await Future.wait([_firebaseAuth.signOut(), _googleSignIn.signOut()]);

      _logger.info('User signed out successfully');
    } catch (e) {
      _logger.severe('Error during sign out: $e');
      throw AuthException('Failed to sign out. Please try again.');
    }
  }

  /// Delete current user account
  Future<void> deleteAccount() async {
    try {
      final user = currentUser;
      if (user == null) {
        throw AuthException('No user is currently signed in');
      }

      _logger.info('Deleting user account: ${user.uid}');

      await user.delete();

      _logger.info('User account deleted successfully');
    } on FirebaseAuthException catch (e) {
      _logger.warning('Account deletion failed: ${e.code} - ${e.message}');
      throw _handleAuthException(e);
    } catch (e) {
      _logger.severe('Unexpected error during account deletion: $e');
      throw AuthException('Failed to delete account. Please try again.');
    }
  }

  /// Send email verification to current user
  Future<void> sendEmailVerification() async {
    try {
      final user = currentUser;
      if (user == null) {
        throw AuthException('No user is currently signed in');
      }

      if (user.emailVerified) {
        throw AuthException('Email is already verified');
      }

      _logger.info('Sending email verification to: ${user.email}');

      await user.sendEmailVerification();

      _logger.info('Email verification sent successfully');
    } on FirebaseAuthException catch (e) {
      _logger.warning('Email verification failed: ${e.code} - ${e.message}');
      throw _handleAuthException(e);
    } catch (e) {
      _logger.severe('Unexpected error during email verification: $e');
      throw AuthException(
        'Failed to send email verification. Please try again.',
      );
    }
  }

  /// Handle Firebase Auth exceptions and convert to user-friendly messages
  AuthException _handleAuthException(FirebaseAuthException e) {
    switch (e.code) {
      case 'weak-password':
        return AuthException(
          'The password provided is too weak. Please choose a stronger password.',
        );
      case 'email-already-in-use':
        return AuthException(
          'An account already exists for this email address.',
        );
      case 'user-not-found':
        return AuthException('No account found for this email address.');
      case 'wrong-password':
        return AuthException('Incorrect password. Please try again.');
      case 'invalid-email':
        return AuthException('The email address is not valid.');
      case 'user-disabled':
        return AuthException(
          'This account has been disabled. Please contact support.',
        );
      case 'too-many-requests':
        return AuthException(
          'Too many failed attempts. Please try again later.',
        );
      case 'operation-not-allowed':
        return AuthException(
          'This sign-in method is not enabled. Please contact support.',
        );
      case 'invalid-credential':
        return AuthException('The provided credentials are invalid.');
      case 'account-exists-with-different-credential':
        return AuthException(
          'An account already exists with a different sign-in method.',
        );
      case 'requires-recent-login':
        return AuthException(
          'This operation requires recent authentication. Please sign in again.',
        );
      case 'network-request-failed':
        return AuthException(
          'Network error. Please check your connection and try again.',
        );
      default:
        return AuthException(
          'Authentication failed: ${e.message ?? 'Unknown error'}',
        );
    }
  }
}

/// Custom exception class for authentication errors
class AuthException implements Exception {
  final String message;

  const AuthException(this.message);

  @override
  String toString() => 'AuthException: $message';
}
