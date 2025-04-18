import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'dart:io';

class AuthService with ChangeNotifier {
  final FirebaseAuth _firebaseAuth;
  final GoogleSignIn _googleSignIn = GoogleSignIn();

  // Constructor - Expects FirebaseAuth instance
  AuthService(this._firebaseAuth);

  // Stream to listen for authentication state changes
  Stream<User?> get authStateChanges => _firebaseAuth.authStateChanges();

  // Get current user (can be null)
  User? get currentUser => _firebaseAuth.currentUser;

  // --- Sign-in Methods ---

  /// Signs in the user anonymously.
  Future<UserCredential?> signInAnonymously() async {
    try {
      final userCredential = await _firebaseAuth.signInAnonymously();
      print("Signed in anonymously: ${userCredential.user?.uid}");
      // Note: ChangeNotifier is not strictly needed if only exposing stream,
      // but can be useful if adding other state later.
      // notifyListeners();
      return userCredential;
    } on FirebaseAuthException catch (e) {
      print("Firebase Anonymous Auth Error: ${e.code} - ${e.message}");
      // Handle specific errors if needed
      return null;
    } catch (e) {
      print("Anonymous Auth Error: $e");
      return null;
    }
  }

  /// Signs in a user with email and password.
  /// Returns UserCredential on success, null on failure.
  Future<UserCredential?> signInWithEmailAndPassword(
    String email,
    String password,
  ) async {
    try {
      final userCredential = await _firebaseAuth.signInWithEmailAndPassword(
        email: email.trim(), // Trim whitespace
        password: password,
      );
      print("Signed in with email: ${userCredential.user?.uid}");
      return userCredential;
    } on FirebaseAuthException catch (e) {
      print("Firebase Email/Pass Auth Error: ${e.code} - ${e.message}");
      // You can return the error code or a custom message based on it
      // throw e; // Re-throwing might be useful for LoginScreen to handle specific codes
      return null;
    } catch (e) {
      print("Email/Pass Auth Error: $e");
      return null;
    }
  }

  /// Creates a new user with email and password.
  /// Returns UserCredential on success, null on failure.
  Future<UserCredential?> signUpWithEmailAndPassword(
    String email,
    String password,
  ) async {
    try {
      final userCredential = await _firebaseAuth.createUserWithEmailAndPassword(
        email: email.trim(),
        password: password,
      );
      print("Signed up and signed in with email: ${userCredential.user?.uid}");
      // NOTE: User is automatically signed in after creation
      return userCredential;
    } on FirebaseAuthException catch (e) {
      print("Firebase Email/Pass SignUp Error: ${e.code} - ${e.message}");
      // Re-throw the exception so the UI can handle specific codes
      throw e;
    } catch (e) {
      print("Email/Pass SignUp Error: $e");
      return null; // Or re-throw a generic exception
    }
  }

  /// Signs in a user with Google.
  Future<UserCredential?> signInWithGoogle() async {
    print("Attempting Google Sign-In...");
    try {
      // Trigger the authentication flow
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();

      // Obtain the auth details from the request
      if (googleUser == null) {
        print("Google Sign-In cancelled by user.");
        return null; // User cancelled
      }
      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      // Create a new credential
      final AuthCredential credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // Once signed in, return the UserCredential
      final userCredential = await _firebaseAuth.signInWithCredential(
        credential,
      );
      print("Signed in with Google: ${userCredential.user?.uid}");
      return userCredential;
    } on FirebaseAuthException catch (e) {
      print("Firebase Google Auth Error: ${e.code} - ${e.message}");
      // Handle specific errors if needed (e.g., 'account-exists-with-different-credential')
      return null;
    } catch (e) {
      print("Google Sign-In Error: $e");
      return null;
    }
  }

  /// Signs in a user with Apple.
  Future<UserCredential?> signInWithApple() async {
    // Check if Apple Sign-In is available on the current platform
    if (!kIsWeb && !Platform.isIOS && !Platform.isMacOS) {
      print("Apple Sign-In is not available on this platform.");
      // Optionally throw an error or return a specific status
      return null;
    }
    print("Attempting Apple Sign-In...");

    try {
      final AuthorizationCredentialAppleID
      appleCredential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName, // Request name
        ],
        // Optional: Add webAuthenticationOptions for web/Android if needed later
      );

      // Create an OAuthProvider credential
      final OAuthProvider oAuthProvider = OAuthProvider("apple.com");
      final AuthCredential credential = oAuthProvider.credential(
        idToken: appleCredential.identityToken,
        accessToken:
            appleCredential
                .authorizationCode, // Use authorizationCode as accessToken
      );

      // Sign in to Firebase with the credential
      final userCredential = await _firebaseAuth.signInWithCredential(
        credential,
      );
      print("Signed in with Apple: ${userCredential.user?.uid}");

      // TODO: Optionally update user profile with name if available (first time only)
      // if (appleCredential.givenName != null && userCredential.user?.displayName == null) {
      //   await userCredential.user?.updateDisplayName("${appleCredential.givenName} ${appleCredential.familyName ?? ''}");
      // }

      return userCredential;
    } on SignInWithAppleAuthorizationException catch (e) {
      print("Apple Sign-In Authorization Error: ${e.code} - ${e.message}");
      // Handle specific errors (e.g., cancelled, failed, invalid response)
      return null;
    } on FirebaseAuthException catch (e) {
      print("Firebase Apple Auth Error: ${e.code} - ${e.message}");
      // Handle specific errors if needed (e.g., 'account-exists-with-different-credential')
      return null;
    } catch (e) {
      print("Apple Sign-In Error: $e");
      return null;
    }
  }

  // --- Sign-out Method ---

  Future<void> signOut() async {
    try {
      await _firebaseAuth.signOut();
      print("User signed out");
      // notifyListeners();
    } on FirebaseAuthException catch (e) {
      print("Firebase Sign Out Error: ${e.code} - ${e.message}");
      // Handle errors if needed
    } catch (e) {
      print("Sign Out Error: $e");
    }
  }
}
