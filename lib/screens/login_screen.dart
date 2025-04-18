import 'package:flutter/material.dart';
import 'package:provider/provider.dart'; // Import Provider
import '../services/auth_service.dart'; // Import AuthService
import 'package:firebase_auth/firebase_auth.dart'; // Import FirebaseAuthException

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;
  bool _isPasswordVisible = false; // State for visibility

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  // Helper to set loading state and clear errors
  void _setLoading(bool loading) {
    if (mounted) {
      setState(() {
        _isLoading = loading;
        if (loading) {
          _errorMessage = null; // Clear previous errors when starting
        }
      });
    }
  }

  // Helper to show errors
  void _showError(String message) {
    if (mounted) {
      setState(() {
        _errorMessage = message;
        // Optional: Show SnackBar as well
        // rootScaffoldMessengerKey.currentState?.showSnackBar(...);
      });
    }
  }

  // --- Authentication Handlers using AuthService ---

  Future<void> _loginWithEmailPassword() async {
    // Basic validation
    if (_emailController.text.isEmpty || _passwordController.text.isEmpty) {
      _showError("Please enter both email and password.");
      return;
    }

    _setLoading(true);
    final authService = Provider.of<AuthService>(context, listen: false);
    try {
      final userCredential = await authService.signInWithEmailAndPassword(
        _emailController.text,
        _passwordController.text,
      );

      // Error handled within the catch block now
      // if (userCredential == null) {
      //   _showError("Login failed. Please check credentials.");
      // }
      // Successful login is handled by AuthWrapper navigation
    } on FirebaseAuthException catch (e) {
      // Catch specific exceptions
      // Map common error codes to user-friendly messages
      String message = "An error occurred. Please try again.";
      if (e.code == 'user-not-found' ||
          e.code == 'wrong-password' ||
          e.code == 'invalid-credential') {
        message = "Incorrect email or password.";
      } else if (e.code == 'invalid-email') {
        message = "Please enter a valid email address.";
      } else if (e.code == 'user-disabled') {
        message = "This account has been disabled.";
      }
      _showError(message);
    } catch (e) {
      // Catch generic errors
      _showError("An unexpected error occurred. Please try again.");
    } finally {
      _setLoading(false); // Ensure loading state is reset
    }
  }

  Future<void> _signInWithGoogle() async {
    _setLoading(true);
    final authService = Provider.of<AuthService>(context, listen: false);
    await authService.signInWithGoogle(); // Call placeholder
    _setLoading(false);
    // TODO: Handle Google sign-in result/errors
  }

  Future<void> _signInWithApple() async {
    _setLoading(true);
    final authService = Provider.of<AuthService>(context, listen: false);
    await authService.signInWithApple(); // Call placeholder
    _setLoading(false);
    // TODO: Handle Apple sign-in result/errors
  }

  Future<void> _continueAsGuest() async {
    _setLoading(true);
    final authService = Provider.of<AuthService>(context, listen: false);
    final userCredential = await authService.signInAnonymously();
    _setLoading(false);

    if (userCredential == null) {
      // Handle error (AuthService already prints)
      _showError("Could not sign in as guest. Please try again.");
    }
    // No navigation here - AuthWrapper will handle it
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final textTheme = theme.textTheme;

    return Scaffold(
      // Use theme's background color
      backgroundColor: theme.scaffoldBackgroundColor,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // --- Logo Placeholder --- (Adjust height as needed)
              SizedBox(
                height: MediaQuery.of(context).size.height * 0.25,
                child: Center(
                  child: Icon(
                    Icons.memory, // Example icon, replace with your logo
                    size: 100,
                    color: colorScheme.primary, // Use theme color
                  ),
                ),
              ),
              const SizedBox(height: 32),

              // --- Email Field ---
              TextField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(
                  labelText: 'Email',
                  prefixIcon: Icon(Icons.email_outlined),
                  // Uses theme's inputDecorationTheme
                ),
                enabled: !_isLoading,
              ),
              const SizedBox(height: 16),

              // --- Password Field ---
              TextField(
                controller: _passwordController,
                obscureText: !_isPasswordVisible, // Use state variable
                decoration: InputDecoration(
                  labelText: 'Password',
                  prefixIcon: Icon(Icons.lock_outline),
                  // Add visibility toggle button
                  suffixIcon: IconButton(
                    icon: Icon(
                      _isPasswordVisible
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                    ),
                    onPressed: () {
                      setState(() {
                        _isPasswordVisible = !_isPasswordVisible;
                      });
                    },
                  ),
                ),
                enabled: !_isLoading,
              ),
              const SizedBox(height: 16), // Space for error message
              // Display Error Message if present
              if (_errorMessage != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Text(
                    _errorMessage!,
                    style: textTheme.bodySmall?.copyWith(
                      color: colorScheme.error,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              const SizedBox(height: 8),

              // --- Login Button ---
              _isLoading
                  ? Center(child: CircularProgressIndicator())
                  : ElevatedButton(
                    onPressed: _loginWithEmailPassword,
                    // Uses theme's elevatedButtonTheme
                    child: Text('Login'),
                    style: theme.elevatedButtonTheme.style?.copyWith(
                      padding: MaterialStateProperty.all(
                        EdgeInsets.symmetric(
                          vertical: 16,
                        ), // Make button taller
                      ),
                    ),
                  ),
              const SizedBox(height: 24),

              // --- Social & Guest Options ---
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(height: 1, width: 60, color: theme.dividerColor),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16.0),
                    child: Text(
                      'OR',
                      style: textTheme.bodySmall?.copyWith(
                        color: theme.hintColor,
                      ),
                    ),
                  ),
                  Container(height: 1, width: 60, color: theme.dividerColor),
                ],
              ),
              const SizedBox(height: 24),

              // --- Google Sign-In Button ---
              OutlinedButton.icon(
                icon: Image.asset(
                  'assets/google_logo.png',
                  height: 20,
                ), // ASSUMES you have a google logo asset
                label: Text('Sign in with Google'),
                onPressed: _isLoading ? null : _signInWithGoogle,
                style: OutlinedButton.styleFrom(
                  foregroundColor:
                      theme.textTheme.bodyLarge?.color, // Use theme text color
                  side: BorderSide(color: theme.dividerColor),
                  padding: EdgeInsets.symmetric(vertical: 14),
                ),
              ),
              const SizedBox(height: 12),

              // --- Apple Sign-In Button ---
              OutlinedButton.icon(
                icon: Icon(
                  Icons.apple,
                  color:
                      theme.brightness == Brightness.dark
                          ? Colors.white
                          : Colors.black,
                ),
                label: Text('Sign in with Apple'),
                onPressed: _isLoading ? null : _signInWithApple,
                style: OutlinedButton.styleFrom(
                  foregroundColor: theme.textTheme.bodyLarge?.color,
                  side: BorderSide(color: theme.dividerColor),
                  padding: EdgeInsets.symmetric(vertical: 14),
                ),
              ),
              const SizedBox(height: 24),

              // --- Guest Option ---
              TextButton(
                onPressed: _isLoading ? null : _continueAsGuest,
                child: Text(
                  'Continue as Guest',
                  style: textTheme.bodyMedium?.copyWith(color: theme.hintColor),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
