import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/settings_provider.dart';
import '../widgets/theme_toggle.dart';

/// User profile screen showing account information and settings
class UserProfileScreen extends StatefulWidget {
  const UserProfileScreen({super.key});

  @override
  State<UserProfileScreen> createState() => _UserProfileScreenState();
}

class _UserProfileScreenState extends State<UserProfileScreen> {
  bool _isSigningOut = false;
  late TextEditingController _maxRepsController;

  @override
  void initState() {
    super.initState();
    _maxRepsController = TextEditingController(
      text: '5', // Default value, as the ScheduleManager is removed
    );
  }

  @override
  void dispose() {
    _maxRepsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        final user = authProvider.user;

        if (user == null) {
          return const Scaffold(
            body: Center(child: Text('No user information available')),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: const Text('Profile'),
            centerTitle: true,
            backgroundColor: Theme.of(context).scaffoldBackgroundColor,
            foregroundColor: Theme.of(context).textTheme.bodyLarge?.color,
            elevation: 0,
          ),
          body: SelectableRegion(
            focusNode: FocusNode(),
            selectionControls: materialTextSelectionControls,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // User Info Section
                  _buildUserInfoSection(context, user, authProvider),

                  const SizedBox(height: 32),

                  // Theme Settings Section
                  _buildThemeSettingsSection(context),

                  const SizedBox(height: 32),

                  // Voice Settings Section
                  _buildVoiceSettingsSection(context),

                  const SizedBox(height: 32),

                  // STT Settings Section
                  _buildSttSettingsSection(context),

                  const SizedBox(height: 32),

                  // Account Actions Section
                  _buildAccountActionsSection(context, authProvider),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildUserInfoSection(
    BuildContext context,
    user,
    AuthProvider authProvider,
  ) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 32,
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  child: Text(
                    authProvider.displayName.substring(0, 1).toUpperCase(),
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).colorScheme.onPrimary,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        authProvider.displayName,
                        style: Theme.of(context).textTheme.headlineSmall
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        authProvider.email ?? 'No email',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Theme.of(
                            context,
                          ).colorScheme.onSurface.withValues(alpha: 0.7),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color:
                              authProvider.isEmailVerified
                                  ? Colors.green.withValues(alpha: 0.1)
                                  : Colors.orange.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color:
                                authProvider.isEmailVerified
                                    ? Colors.green
                                    : Colors.orange,
                            width: 1,
                          ),
                        ),
                        child: Text(
                          authProvider.isEmailVerified
                              ? 'Email Verified'
                              : 'Email Not Verified',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color:
                                authProvider.isEmailVerified
                                    ? Colors.green
                                    : Colors.orange,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (!authProvider.isEmailVerified) ...[
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () async {
                    // Store the messenger reference before async operation
                    final messenger = ScaffoldMessenger.of(context);

                    try {
                      await authProvider.sendEmailVerification();
                      if (mounted) {
                        messenger.showSnackBar(
                          const SnackBar(
                            content: Text('Verification email sent!'),
                            backgroundColor: Colors.green,
                          ),
                        );
                      }
                    } catch (e) {
                      if (mounted) {
                        messenger.showSnackBar(
                          SnackBar(
                            content: Text(
                              'Failed to send verification email: $e',
                            ),
                            backgroundColor: Colors.red,
                          ),
                        );
                      }
                    }
                  },
                  icon: const Icon(Icons.email_outlined),
                  label: const Text('Send Verification Email'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildThemeSettingsSection(BuildContext context) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Theme Settings',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            const ThemeToggle(),
          ],
        ),
      ),
    );
  }

  Widget _buildVoiceSettingsSection(BuildContext context) {
    return Consumer<SettingsProvider>(
      builder: (context, settingsProvider, child) {
        return Card(
          elevation: 2,
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Voice Settings',
                  style: Theme.of(
                    context,
                  ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Icon(
                      Icons.mic,
                      size: 20,
                      color: settingsProvider.voiceEnabled
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Voice-to-Voice Chat',
                            style: Theme.of(context).textTheme.bodyLarge,
                          ),
                          Text(
                            'Enable microphone button for voice conversations',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                            ),
                          ),
                        ],
                      ),
                    ),
                    Switch(
                      value: settingsProvider.voiceEnabled,
                      onChanged: (bool value) {
                        settingsProvider.setVoiceEnabled(value);
                      },
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildSttSettingsSection(BuildContext context) {
    return Consumer<SettingsProvider>(
      builder: (context, settingsProvider, child) {
        return Card(
          elevation: 2,
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Speech-to-Text Settings',
                  style: Theme.of(
                    context,
                  ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Icon(
                      Icons.keyboard_voice,
                      size: 20,
                      color: settingsProvider.sttEnabled
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Speech-to-Text',
                            style: Theme.of(context).textTheme.bodyLarge,
                          ),
                          Text(
                            'Enable STT button for voice input to text',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
                            ),
                          ),
                        ],
                      ),
                    ),
                    Switch(
                      value: settingsProvider.sttEnabled,
                      onChanged: (bool value) {
                        settingsProvider.setSttEnabled(value);
                      },
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildAccountActionsSection(
    BuildContext context,
    AuthProvider authProvider,
  ) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Account Actions',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),

            // Sign Out Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed:
                    _isSigningOut
                        ? null
                        : () => _handleSignOut(context, authProvider),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.error,
                  foregroundColor: Theme.of(context).colorScheme.onError,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                icon:
                    _isSigningOut
                        ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                        : const Icon(Icons.logout),
                label: Text(_isSigningOut ? 'Signing Out...' : 'Sign Out'),
              ),
            ),

            const SizedBox(height: 12),

            // Reload User Data Button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () async {
                  await authProvider.reloadUser();
                  if (mounted) {
                    setState(() {}); // Refresh the UI
                  }
                },
                icon: const Icon(Icons.refresh),
                label: const Text('Refresh Profile'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _handleSignOut(
    BuildContext context,
    AuthProvider authProvider,
  ) async {
    // Store all context references before async operations
    final messenger = ScaffoldMessenger.of(context);
    final theme = Theme.of(context);

    // Show confirmation dialog
    final shouldSignOut = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Sign Out'),
          content: const Text('Are you sure you want to sign out?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(true),
              style: TextButton.styleFrom(
                foregroundColor: theme.colorScheme.error,
              ),
              child: const Text('Sign Out'),
            ),
          ],
        );
      },
    );

    if (shouldSignOut == true) {
      setState(() {
        _isSigningOut = true;
      });

      try {
        await authProvider.signOut();
      } catch (e) {
        if (mounted) {
          messenger.showSnackBar(
            SnackBar(
              content: Text('Failed to sign out: $e'),
              backgroundColor: Colors.red,
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isSigningOut = false;
          });
        }
      }
    }
  }
}
