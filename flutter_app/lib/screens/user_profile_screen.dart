import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/logger_service.dart';
import '../models/schedule_manager.dart';
import '../screens/settings_screen.dart';
import '../screens/about_screen.dart';

class UserProfileScreen extends StatefulWidget {
  const UserProfileScreen({super.key});

  @override
  State<UserProfileScreen> createState() => _UserProfileScreenState();
}

class _UserProfileScreenState extends State<UserProfileScreen> {
  final _logger = getLogger('UserProfileScreen');
  bool _isSigningOut = false;

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
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // User Info Section
                _buildUserInfoSection(context, user, authProvider),

                const SizedBox(height: 32),

                // Sync Status Section
                _buildSyncStatusSection(context),

                const SizedBox(height: 32),

                // Account Actions Section
                _buildAccountActionsSection(context, authProvider),

                const SizedBox(height: 32),

                // App Actions Section
                _buildAppActionsSection(context),
              ],
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

  Widget _buildSyncStatusSection(BuildContext context) {
    return Consumer<ScheduleManager>(
      builder: (context, scheduleManager, child) {
        return Card(
          elevation: 2,
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Data Sync',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),

                FutureBuilder<bool>(
                  future: scheduleManager.hasPendingSync(),
                  builder: (context, snapshot) {
                    final hasPending = snapshot.data ?? false;
                    final isConnected = scheduleManager.storage.supportsSync;

                    return Column(
                      children: [
                        Row(
                          children: [
                            Icon(
                              isConnected ? Icons.cloud_done : Icons.cloud_off,
                              color: isConnected ? Colors.green : Colors.orange,
                              size: 20,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              isConnected
                                  ? 'Connected to Cloud'
                                  : 'Using Local Storage',
                              style: TextStyle(
                                color:
                                    isConnected ? Colors.green : Colors.orange,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),

                        if (hasPending) ...[
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              const Icon(
                                Icons.sync,
                                color: Colors.blue,
                                size: 20,
                              ),
                              const SizedBox(width: 8),
                              const Expanded(
                                child: Text(
                                  'Changes pending sync',
                                  style: TextStyle(color: Colors.blue),
                                ),
                              ),
                              TextButton(
                                onPressed: () async {
                                  await scheduleManager.triggerSync();
                                  if (mounted) {
                                    setState(() {}); // Refresh the UI
                                  }
                                },
                                child: const Text('Sync Now'),
                              ),
                            ],
                          ),
                        ],

                        const SizedBox(height: 12),
                        Text(
                          isConnected
                              ? 'Your data is automatically synced to the cloud'
                              : 'Your data is stored locally. It will sync when cloud connection is available.',
                          style: Theme.of(
                            context,
                          ).textTheme.bodySmall?.copyWith(
                            color: Theme.of(
                              context,
                            ).colorScheme.onSurface.withValues(alpha: 0.6),
                          ),
                        ),
                      ],
                    );
                  },
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

  Widget _buildAppActionsSection(BuildContext context) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'App Settings',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),

            // Settings Button
            ListTile(
              leading: Icon(
                Icons.settings,
                color: Theme.of(context).colorScheme.primary,
              ),
              title: const Text('Settings'),
              subtitle: const Text('App preferences and configuration'),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
              onTap: () {
                final scheduleManager = Provider.of<ScheduleManager>(
                  context,
                  listen: false,
                );
                final navigator = Navigator.of(context);
                navigator.push(
                  MaterialPageRoute(
                    builder:
                        (context) =>
                            ChangeNotifierProvider<ScheduleManager>.value(
                              value: scheduleManager,
                              child: const SettingsScreen(),
                            ),
                  ),
                );
              },
            ),

            const Divider(),

            // About Button
            ListTile(
              leading: Icon(
                Icons.info_outline,
                color: Theme.of(context).colorScheme.primary,
              ),
              title: const Text('About'),
              subtitle: const Text('App information and help'),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
              onTap: () {
                final navigator = Navigator.of(context);
                navigator.push(
                  MaterialPageRoute(builder: (context) => const AboutScreen()),
                );
              },
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
        _logger.info('User initiated sign out');
        await authProvider.signOut();
        _logger.info('Sign out successful');

        // Don't show success message since user will be redirected to landing page
        // The success will be evident by the redirect itself
      } catch (e) {
        _logger.severe('Sign out failed: $e');

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
