import 'package:flutter/material.dart';

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
                      'Effective Date: June 11, 2025',
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
                '1. Introduction',
                'Welcome to Spaced, a spaced repetition learning application. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our mobile application and web service. If you do not agree with the terms of this Privacy Policy, please do not access the application.',
              ),

              _buildSection(
                context,
                '2. Information We Collect',
                '''**2.1 Personal Data**
• Email address (when you sign up or use Google OAuth)
• Name and profile picture (from Google account, if provided)
• Account preferences and settings

**2.2 Study Data**
• Your learning topics and subjects
• Study session data and progress
• Quiz answers and performance metrics
• Learning statistics and achievements

**2.3 Usage Data**
• App usage patterns and feature interactions
• Device information (type, operating system, browser)
• IP address and general location (city/region level)
• Session duration and frequency of use

**2.4 Automatically Collected Information**
• Log data and error reports for app improvement
• Analytics data to understand user behavior
• Performance metrics for service optimization''',
              ),

              _buildSection(
                context,
                '3. Legal Basis for Processing (GDPR)',
                '''If you are an EU resident, we process your personal data under one or more of the following lawful bases:

• **Consent:** You have given clear consent for us to process your personal data for a specific purpose.
• **Contract:** Processing is necessary for the performance of a contract with you (e.g., providing the Spaced service).
• **Legitimate Interests:** Processing is necessary for our legitimate interests (e.g., improving the service) and does not override your rights.
• **Legal Obligation:** Processing is necessary to comply with a legal obligation to which we are subject.''',
              ),

              _buildSection(
                context,
                '4. How We Use Your Information',
                '''• **Provide and maintain our service:** Enable core functionality of spaced repetition.
• **Personalize your experience:** Customize learning content and recommendations.
• **Track your progress:** Save and sync learning data across devices.
• **Improve our service:** Analyze usage patterns to enhance features.
• **Communicate with you:** Send important updates, notifications, and support messages.
• **Ensure security:** Protect against fraud, unauthorized access, and abuse.
• **Comply with legal obligations:** Meet regulatory and legal requirements.''',
              ),

              _buildSection(
                context,
                '5. Cookies and Similar Technologies',
                '''We use cookies and similar tracking technologies to collect and store information. Types of technologies:

• **Cookies:** Small text files placed on your device.
• **Local Storage:** Data stored within your browser.
• **Mobile Identifiers:** Advertising and analytics identifiers on mobile devices.

You can manage or disable cookies via your browser settings or device preferences. To opt out of mobile analytics, use the standard opt-out mechanisms provided by your operating system.''',
              ),

              _buildSection(
                context,
                '6. Information Sharing and Disclosure',
                '''**6.1 Service Providers**
We share personal data with third-party service providers who perform services on our behalf:
• Cloud hosting services (data storage & processing)
• Analytics providers (anonymized data)
• Authentication services (Google OAuth)

We maintain a current list of our major subprocessors and will provide it upon request.

**6.2 Legal Requirements**
We may disclose your information when required by law, regulation, or legal process, or to protect our rights, privacy, safety, or property.

**6.3 Business Transfers**
In the event of a merger, acquisition, or sale of assets, your personal information may be transferred. We will notify you before your data is transferred and becomes subject to a different Privacy Policy.''',
              ),

              _buildSection(
                context,
                '7. International Data Transfers',
                '''Your information may be transferred to and processed in countries outside your own. We rely on the European Commission's Standard Contractual Clauses and other appropriate safeguards to ensure protection of your data.''',
              ),

              _buildSection(
                context,
                '8. Data Retention',
                '''• **Account Data:** Retained while your account is active; deleted within 30 days after you request account deletion.
• **Study Data:** Deleted along with your account data within 30 days of deletion request.
• **Analytics Data:** Anonymized and aggregated data may be retained indefinitely for service improvement.''',
              ),

              _buildSection(
                context,
                '9. Your Privacy Rights',
                '''Depending on your jurisdiction, you may have the following rights:

• **Access:** Request a copy of your personal data.
• **Correction:** Update or correct inaccurate information.
• **Deletion:** Request deletion of your personal data.
• **Portability:** Receive your data in a portable format.
• **Withdraw Consent:** Withdraw your consent at any time.
• **Object:** Object to certain types of processing.

To exercise your rights, please contact us at spacedhelpbot@gmail.com. We will respond within 30 days (with a possible 30-day extension if necessary).

**California Privacy Rights (CCPA/CPRA)**
California residents have additional rights under the CCPA/CPRA:
• Right to know, delete, and opt-out of sale/sharing of personal information.
• To exercise these rights, please email spacedhelpbot@gmail.com or visit our Do Not Sell My Personal Information page.''',
              ),

              _buildSection(
                context,
                '10. Children\'s Privacy',
                '''Our service is not directed to children under 13 years of age. We do not knowingly collect personal information from children under 13. If we learn we have collected personal information from a child under 13, we will delete it within 48 hours without undue delay.''',
              ),

              _buildSection(
                context,
                '11. Policy Updates and Notifications',
                '''We may update this Privacy Policy from time to time. We will post the updated policy on this page and update the "Effective Date" at the top. For material changes that affect your rights or how we use your data, we will notify you via email and/or in-app notification.''',
              ),

              _buildSection(
                context,
                '12. Contact Us',
                '''If you have any questions about this Privacy Policy or our data practices, please contact us:

• **Email:** spacedhelpbot@gmail.com
• **Mailing Address:** P.O. Box 1234, City, State ZIP (please contact for full address)
• **Website:** https://getspaced.app''',
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
