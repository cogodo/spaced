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
import 'login_screen.dart';

/// Sign up screen with email/password and Google OAuth options
class SignUpScreen extends StatefulWidget {
  final VoidCallback onNavigateToLogin;
  final VoidCallback onBackToLanding;

  const SignUpScreen({
    super.key,
    required this.onNavigateToLogin,
    required this.onBackToLanding,
  });

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _emailFocusNode = FocusNode();
  final _passwordFocusNode = FocusNode();
  final _confirmPasswordFocusNode = FocusNode();

  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void initState() {
    super.initState();
    // Clear any existing errors when entering the signup screen
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<AuthProvider>(context, listen: false).clearError();
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _emailFocusNode.dispose();
    _passwordFocusNode.dispose();
    _confirmPasswordFocusNode.dispose();
    super.dispose();
  }

  /// Get return URL from current route query parameters
  String? get _returnUrl {
    final state = GoRouterState.of(context);
    return state.uri.queryParameters['returnTo'];
  }

  Future<void> _handleEmailSignUp() async {
    if (_formKey.currentState!.validate()) {
      final authProvider = context.read<AuthProvider>();
      await authProvider.signUpWithEmail(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );

      // Complete autofill context after successful signup
      TextInput.finishAutofillContext();

      // Router will automatically handle redirect to return URL via DomainGuard
      // No need to manually navigate here - the auth state change will trigger routing
    }
  }

  Future<void> _handleGoogleSignIn() async {
    final authProvider = context.read<AuthProvider>();
    await authProvider.signInWithGoogle();

    // Complete autofill context after successful login
    TextInput.finishAutofillContext();

    // Router will automatically handle redirect to return URL via DomainGuard
    // No need to manually navigate here - the auth state change will trigger routing
  }

  void _navigateToLogin() {
    // Preserve return URL when navigating to login
    final returnUrl = _returnUrl;
    if (returnUrl != null) {
      final encodedReturnUrl = Uri.encodeComponent(returnUrl);
      context.go('${Routes.login}?returnTo=$encodedReturnUrl');
    } else {
      context.go(Routes.login);
    }
  }

  String? _validateConfirmPassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please confirm your password';
    }

    if (value != _passwordController.text) {
      return 'Passwords do not match';
    }

    return null;
  }

  String? _validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Password is required';
    }

    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }

    if (!RegExp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)').hasMatch(value)) {
      return 'Password must contain uppercase, lowercase, and number';
    }

    return null;
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
                        _buildSignUpForm(context),
                        const SizedBox(height: 24),
                        _buildDivider(context),
                        const SizedBox(height: 24),
                        _buildGoogleSignIn(context),
                        const SizedBox(height: 32),
                        _buildLoginPrompt(context),
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
          'Create Account',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: Theme.of(context).colorScheme.primary,
          ),
        ),

        const SizedBox(height: 8),

        // Subtitle
        Text(
          'Start your personalized learning journey',
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

  Widget _buildSignUpForm(BuildContext context) {
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
                  validator: _validatePassword,
                  showRequirements: true,
                  autofillHints: const [AutofillHints.newPassword],
                  onToggleObscure: () {
                    setState(() {
                      _obscurePassword = !_obscurePassword;
                    });
                  },
                  enabled: !authProvider.isLoading,
                ),

                const SizedBox(height: 16),

                // Confirm password field
                PasswordFormField(
                  controller: _confirmPasswordController,
                  focusNode: _confirmPasswordFocusNode,
                  obscureText: _obscureConfirmPassword,
                  labelText: 'Confirm Password',
                  hintText: 'Confirm your password',
                  validator: _validateConfirmPassword,
                  autofillHints: const [],
                  onToggleObscure: () {
                    setState(() {
                      _obscureConfirmPassword = !_obscureConfirmPassword;
                    });
                  },
                  onSubmitted: (_) => _handleEmailSignUp(),
                  enabled: !authProvider.isLoading,
                ),

                const SizedBox(height: 24),

                // Sign up button
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed:
                        authProvider.isLoading ? null : _handleEmailSignUp,
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
                              'Create Account',
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

  Widget _buildLoginPrompt(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        return Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              "Already have an account? ",
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(
                  context,
                ).textTheme.bodyLarge?.color?.withValues(alpha: 0.7),
              ),
            ),
            TextButton(
              onPressed: authProvider.isLoading ? null : _navigateToLogin,
              child: Text(
                'Sign In',
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
