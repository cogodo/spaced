import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';

import '../../providers/auth_provider.dart';
import '../../widgets/auth/email_form_field.dart';
import '../../widgets/auth/password_form_field.dart';
import '../../widgets/auth/google_sign_in_button.dart';
import '../../widgets/auth/auth_error_message.dart';
import '../../widgets/theme_logo.dart';
import '../../routing/route_constants.dart';
import 'signup_screen.dart';
import 'forgot_password_screen.dart';

/// Login screen with email/password and Google OAuth options
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();

  bool _obscurePassword = true;

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        Provider.of<AuthProvider>(context, listen: false).clearError();
      }
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    super.dispose();
  }

  /// Get return URL from current route query parameters
  String? get _returnUrl {
    final state = GoRouterState.of(context);
    return state.uri.queryParameters['returnTo'];
  }

  Future<void> _handleEmailSignIn() async {
    if (_formKey.currentState!.validate()) {
      final authProvider = context.read<AuthProvider>();

      try {
        await authProvider.signInWithEmail(
          email: _emailController.text.trim(),
          password: _passwordController.text,
        );

        // Complete autofill context after successful login
        TextInput.finishAutofillContext();

        // Router will automatically handle redirect to return URL via DomainGuard
        // No need to manually navigate here - the auth state change will trigger routing
      } catch (e) {
        // Error is handled by AuthProvider
      }
    }
  }

  Future<void> _handleGoogleSignIn() async {
    final authProvider = context.read<AuthProvider>();

    try {
      await authProvider.signInWithGoogle();

      // Complete autofill context after successful login
      TextInput.finishAutofillContext();

      // Router will automatically handle redirect to return URL via DomainGuard
      // No need to manually navigate here - the auth state change will trigger routing
    } catch (e) {
      // Error is handled by AuthProvider
    }
  }

  void _navigateToSignUp() {
    // Preserve return URL when navigating to signup
    final returnUrl = _returnUrl;
    if (returnUrl != null) {
      final encodedReturnUrl = Uri.encodeComponent(returnUrl);
      context.go('${Routes.signup}?returnTo=$encodedReturnUrl');
    } else {
      context.go(Routes.signup);
    }
  }

  void _navigateToForgotPassword() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder:
            (context) => ForgotPasswordScreen(
              initialEmail: _emailController.text.trim(),
            ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 800;

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).scaffoldBackgroundColor,
              Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            child: ConstrainedBox(
              constraints: BoxConstraints(
                minHeight:
                    MediaQuery.of(context).size.height -
                    MediaQuery.of(context).padding.top -
                    MediaQuery.of(context).padding.bottom,
              ),
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: ConstrainedBox(
                    constraints: BoxConstraints(
                      maxWidth: isDesktop ? 400 : double.infinity,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _buildHeader(context),
                        const SizedBox(height: 48),
                        _buildLoginForm(context),
                        const SizedBox(height: 24),
                        _buildDivider(context),
                        const SizedBox(height: 24),
                        _buildGoogleSignIn(context),
                        const SizedBox(height: 32),
                        _buildSignUpPrompt(context),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Column(
      children: [
        // Logo
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(20),
          ),
          child: ThemeLogo(size: 64),
        ),

        const SizedBox(height: 24),

        // Title
        Text(
          'Welcome Back',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.primary,
          ),
        ),

        const SizedBox(height: 8),

        // Subtitle
        Text(
          'Sign in to continue your learning journey',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: Theme.of(
              context,
            ).textTheme.bodyLarge?.color?.withValues(alpha: 0.7),
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildLoginForm(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        return AutofillGroup(
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                // Error message
                if (authProvider.errorMessage != null)
                  AuthErrorMessage(
                    message: authProvider.errorMessage!,
                    onDismiss: authProvider.clearError,
                  ),

                const SizedBox(height: 16),

                // Email field
                EmailFormField(
                  controller: _emailController,
                  focusNode: _emailFocusNode,
                  nextFocusNode: _passwordFocusNode,
                  enabled: !authProvider.isLoading,
                ),

                const SizedBox(height: 16),

                // Password field
                PasswordFormField(
                  controller: _passwordController,
                  focusNode: _passwordFocusNode,
                  obscureText: _obscurePassword,
                  autofillHints: const [AutofillHints.password],
                  onToggleObscure: () {
                    setState(() {
                      _obscurePassword = !_obscurePassword;
                    });
                  },
                  onSubmitted: (_) => _handleEmailSignIn(),
                  enabled: !authProvider.isLoading,
                ),

                const SizedBox(height: 8),

                // Forgot password link
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed:
                        authProvider.isLoading
                            ? null
                            : _navigateToForgotPassword,
                    child: Text(
                      'Forgot Password?',
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 24),

                // Sign in button
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed:
                        authProvider.isLoading ? null : _handleEmailSignIn,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child:
                        authProvider.isLoading
                            ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(
                                  Colors.white,
                                ),
                              ),
                            )
                            : Text(
                              'Sign In',
                              style: Theme.of(
                                context,
                              ).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildDivider(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Divider(
            color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Text(
            'OR',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(
                context,
              ).textTheme.bodyLarge?.color?.withValues(alpha: 0.6),
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        Expanded(
          child: Divider(
            color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
          ),
        ),
      ],
    );
  }

  Widget _buildGoogleSignIn(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        return GoogleSignInButton(
          onPressed: authProvider.isLoading ? null : _handleGoogleSignIn,
          isLoading: authProvider.isLoading,
        );
      },
    );
  }

  Widget _buildSignUpPrompt(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              "Don't have an account? ",
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(
                  context,
                ).textTheme.bodyLarge?.color?.withValues(alpha: 0.7),
              ),
            ),
            TextButton(
              onPressed: authProvider.isLoading ? null : _navigateToSignUp,
              child: Text(
                'Sign Up',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.primary,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}
