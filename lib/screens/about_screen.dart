import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:url_launcher/url_launcher.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 600;
    final contentWidth = isDesktop ? 800.0 : double.infinity;

    return Scaffold(
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Center(
            child: Container(
              width: contentWidth,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // App Info Section
                  _buildSection(
                    context,
                    title: 'About Spaced',
                    icon: Icons.app_shortcut,
                    children: [
                      Text(
                        'Spaced is a spaced repetition application designed to help you remember what matters. Using advanced algorithms, it optimizes your learning and memory retention by scheduling reviews at precisely the right intervals.',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      SizedBox(height: 12),
                      Text(
                        'How to use this app:',
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 8),
                      _buildBulletPoint(
                        context,
                        'Add items you want to remember in the "Add" tab',
                      ),
                      _buildBulletPoint(
                        context,
                        'Review items due today in the "Today" tab',
                      ),
                      _buildBulletPoint(
                        context,
                        'Rate how well you remembered each item',
                      ),
                      _buildBulletPoint(
                        context,
                        'The algorithm will schedule your next review based on your rating',
                      ),
                      _buildBulletPoint(
                        context,
                        'View all your items in the "All Items" tab',
                      ),
                    ],
                  ),

                  Divider(height: 48),

                  // FSRS Algorithm Section
                  _buildSection(
                    context,
                    title: 'FSRS Algorithm',
                    icon: Icons.psychology,
                    children: [
                      Text(
                        'Spaced uses the Free Spaced Repetition Scheduler (FSRS) algorithm to determine optimal review intervals.',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      SizedBox(height: 12),
                      Text(
                        'Key FSRS concepts:',
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 8),
                      _buildDefinition(
                        context,
                        term: 'Stability',
                        definition:
                            'How resistant a memory is to being forgotten over time. Higher stability means the memory will last longer.',
                      ),
                      _buildDefinition(
                        context,
                        term: 'Difficulty',
                        definition:
                            'How challenging an item is to remember. Higher difficulty means more frequent reviews are needed.',
                      ),
                      _buildDefinition(
                        context,
                        term: 'Retrievability',
                        definition:
                            'The probability of successfully recalling an item at a given time. It decreases as time passes since the last review.',
                      ),
                      SizedBox(height: 16),
                      Text(
                        'FSRS dynamically adjusts review intervals based on:',
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 8),
                      _buildBulletPoint(
                        context,
                        'Your performance on each review (rating from 0-5)',
                      ),
                      _buildBulletPoint(
                        context,
                        'The calculated stability of each memory',
                      ),
                      _buildBulletPoint(
                        context,
                        'The individual difficulty of each item',
                      ),
                      _buildBulletPoint(
                        context,
                        'Mathematical models of human memory decay',
                      ),
                      SizedBox(height: 16),
                      _buildLinkText(
                        context,
                        text: 'Learn more about FSRS algorithm',
                        url:
                            'https://github.com/open-spaced-repetition/fsrs4anki',
                      ),
                    ],
                  ),

                  Divider(height: 48),

                  // Developer Section
                  _buildSection(
                    context,
                    title: 'Development',
                    icon: Icons.code,
                    children: [
                      Text(
                        'Spaced is an open-source application built with Flutter.',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      SizedBox(height: 16),
                      _buildLinkText(
                        context,
                        text: 'View source code on GitHub',
                        url: 'https://github.com/cogodo/spaced',
                      ),
                      SizedBox(height: 12),
                      Text(
                        'If you encounter any issues or have suggestions, please submit them on GitHub.',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),

                  // Version information at the bottom
                  SizedBox(height: 48),
                  Center(
                    child: Text(
                      'Version 1.0.0',
                      style: Theme.of(
                        context,
                      ).textTheme.bodySmall?.copyWith(color: Colors.grey),
                    ),
                  ),
                  SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 28, color: Theme.of(context).colorScheme.primary),
            SizedBox(width: 12),
            Text(
              title,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
          ],
        ),
        SizedBox(height: 16),
        ...children,
      ],
    );
  }

  Widget _buildBulletPoint(BuildContext context, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '•',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
          SizedBox(width: 8),
          Expanded(
            child: Text(text, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
      ),
    );
  }

  Widget _buildDefinition(
    BuildContext context, {
    required String term,
    required String definition,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 100,
            child: Text(
              term,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
          ),
          Expanded(
            child: Text(
              definition,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLinkText(
    BuildContext context, {
    required String text,
    required String url,
  }) {
    return RichText(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: Theme.of(context).colorScheme.primary,
          decoration: TextDecoration.underline,
          fontSize: 16,
        ),
        recognizer:
            TapGestureRecognizer()
              ..onTap = () async {
                final Uri uri = Uri.parse(url);
                if (await canLaunchUrl(uri)) {
                  await launchUrl(uri);
                }
              },
      ),
    );
  }
}
