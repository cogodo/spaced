import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

/// Privacy Policy screen for the Spaced app
class PrivacyPolicyScreen extends StatelessWidget {
  const PrivacyPolicyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Privacy Policy'), centerTitle: true),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Column(
                  children: [
                    Text(
                      'Privacy Policy for Spaced',
                      style: Theme.of(
                        context,
                      ).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Effective Date: ${DateTime.now().toIso8601String().split('T').first}',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(
                          context,
                        ).textTheme.bodyMedium?.color?.withValues(alpha: 0.7),
                      ),
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),

              _buildSection(
                context,
                'Introduction',
                'Welcome to Spaced, a spaced repetition learning application. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our mobile application and web service. Please read this privacy policy carefully. If you do not agree with the terms of this privacy policy, please do not access the application.',
              ),

              _buildSection(
                context,
                'Information We Collect',
                '''We may collect information about you in a variety of ways:

**Personal Data**
• Email address (when you sign up or use Google OAuth)
• Name and profile picture (from Google account, if provided)
• Account preferences and settings

**Study Data**
• Your learning topics and subjects
• Study session data and progress
• Quiz answers and performance metrics
• Learning statistics and achievements

**Usage Data**
• App usage patterns and feature interactions
• Device information (type, operating system, browser)
• IP address and general location (city/region level)
• Session duration and frequency of use

**Automatically Collected Information**
• Log data and error reports for app improvement
• Analytics data to understand user behavior
• Performance metrics for service optimization''',
              ),

              _buildSection(
                context,
                'How We Use Your Information',
                '''We use the information we collect to:

• **Provide and maintain our service** - Enable core spaced repetition functionality
• **Personalize your experience** - Customize learning content and recommendations
• **Track your progress** - Save and sync your learning data across devices
• **Improve our service** - Analyze usage patterns to enhance features
• **Communicate with you** - Send important updates and notifications
• **Ensure security** - Protect against fraud and unauthorized access
• **Comply with legal obligations** - Meet regulatory and legal requirements''',
              ),

              _buildSection(
                context,
                'Information Sharing and Disclosure',
                '''We do not sell, trade, or otherwise transfer your personal information to third parties except in the following circumstances:

**Service Providers**
• Cloud hosting services (for data storage and processing)
• Analytics providers (for app improvement, with anonymized data)
• Authentication services (Google OAuth for secure login)

**Legal Requirements**
• When required by law, regulation, or legal process
• To protect our rights, privacy, safety, or property
• To enforce our terms of service

**Business Transfers**
• In connection with a merger, acquisition, or sale of assets

We never share your study data or personal information for marketing purposes.''',
              ),

              _buildSection(
                context,
                'Data Security',
                '''We implement appropriate security measures to protect your information:

• **Encryption** - Data is encrypted in transit and at rest
• **Authentication** - Secure login via Google OAuth
• **Access Controls** - Limited access to personal data
• **Regular Updates** - Security patches and system updates
• **Monitoring** - Continuous monitoring for security threats

However, no method of transmission over the internet is 100% secure, and we cannot guarantee absolute security.''',
              ),

              _buildSection(
                context,
                'Data Retention',
                '''We retain your information only as long as necessary to:

• Provide our services to you
• Comply with legal obligations
• Resolve disputes and enforce agreements

**Account Data**: Retained while your account is active and for up to 30 days after deletion
**Study Data**: Retained while your account is active and permanently deleted upon account deletion
**Analytics Data**: Anonymized data may be retained indefinitely for service improvement''',
              ),

              _buildSection(
                context,
                'Your Privacy Rights',
                '''Depending on your location, you may have the following rights:

• **Access** - Request a copy of your personal data
• **Correction** - Update or correct inaccurate information
• **Deletion** - Request deletion of your personal data
• **Portability** - Receive your data in a portable format
• **Opt-out** - Withdraw consent for data processing
• **Object** - Object to certain types of data processing

To exercise these rights, please contact us using the information provided below.''',
              ),

              _buildSection(
                context,
                'Third-Party Services',
                '''Our app integrates with third-party services:

**Google Services**
• Google OAuth for authentication
• Google Cloud Platform for hosting
• Subject to Google\'s Privacy Policy

**Analytics Services**
• Usage analytics for app improvement
• Data is anonymized and aggregated

We are not responsible for the privacy practices of these third-party services.''',
              ),

              _buildSection(
                context,
                'Children\'s Privacy',
                '''Our service is not directed to children under 13 years of age. We do not knowingly collect personal information from children under 13. If you become aware that a child has provided us with personal information, please contact us immediately.''',
              ),

              _buildSection(
                context,
                'International Data Transfers',
                '''Your information may be transferred to and processed in countries other than your own. We ensure appropriate safeguards are in place to protect your information in accordance with applicable privacy laws.''',
              ),

              _buildSection(
                context,
                'Changes to This Privacy Policy',
                '''We may update this Privacy Policy from time to time. We will notify you of any changes by:

• Posting the new Privacy Policy on this page
• Updating the "Effective Date" at the top
• Sending you a notification for significant changes

Your continued use of the service after changes constitutes acceptance of the updated policy.''',
              ),

              _buildSection(
                context,
                'Contact Us',
                '''If you have any questions about this Privacy Policy or our data practices, please contact us:

**Email**: Coming soon
**Website**: https://getspaced.app
**Address**: Available upon request

For data protection inquiries in the EU, you may also contact your local data protection authority.''',
              ),

              const SizedBox(height: 40),

              Center(
                child: Column(
                  children: [
                    Text(
                      'Thank you for trusting Spaced with your learning journey.',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontStyle: FontStyle.italic,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Back to App'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSection(BuildContext context, String title, String content) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            content,
            style: Theme.of(
              context,
            ).textTheme.bodyMedium?.copyWith(height: 1.6),
          ),
        ],
      ),
    );
  }
}
