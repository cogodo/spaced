import 'package:flutter/material.dart';
import 'package:spaced/themes/theme_data.dart';
import 'package:provider/provider.dart';
import 'package:spaced/main.dart';
import 'package:spaced/screens/auth/login_screen.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/logger_service.dart';
import '../providers/auth_provider.dart';
import '../widgets/theme_logo.dart';
import '../widgets/theme_toggle.dart';

class LandingScreen extends StatelessWidget {
  static final _logger = getLogger('LandingScreen');
  final VoidCallback onNavigateToLogin;

  const LandingScreen({super.key, required this.onNavigateToLogin});

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 800;
    final isMobile = MediaQuery.of(context).size.width < 600;

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
            child: Column(
              children: [
                // Header
                _buildHeader(context, isDesktop),

                // Hero Section
                _buildHeroSection(context, isDesktop, isMobile),

                // Features Section
                _buildFeaturesSection(context, isDesktop, isMobile),

                // About Section
                _buildAboutSection(context, isDesktop),

                // Call to Action Section
                _buildCallToActionSection(context, isDesktop),

                // Footer
                _buildFooter(context),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, bool isDesktop) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        return Container(
          padding: EdgeInsets.symmetric(
            horizontal: isDesktop ? 80 : 20,
            vertical: 20,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Logo/Brand
              Row(
                children: [
                  ThemeLogo(size: 32),
                  const SizedBox(width: 12),
                  Text(
                    'Spaced',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                ],
              ),

              // Header buttons
              Row(
                children: [
                  // Theme Toggle (replace the dropdown)
                  ThemeToggle(),

                  const SizedBox(width: 16),

                  // Dynamic button based on auth status
                  OutlinedButton(
                    onPressed: onNavigateToLogin,
                    child: Text(
                      authProvider.isSignedIn
                          ? 'Back to App'
                          : 'Login / Sign Up',
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildHeroSection(
    BuildContext context,
    bool isDesktop,
    bool isMobile,
  ) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isDesktop ? 80 : 20,
        vertical: isDesktop ? 100 : 60,
      ),
      child: Column(
        children: [
          // Main hero content
          if (isDesktop)
            Row(
              children: [
                Expanded(flex: 3, child: _buildHeroText(context, isDesktop)),
                const SizedBox(width: 60),
                Expanded(flex: 2, child: _buildHeroVisual(context)),
              ],
            )
          else
            Column(
              children: [
                _buildHeroText(context, isDesktop),
                const SizedBox(height: 40),
                _buildHeroVisual(context),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildHeroText(BuildContext context, bool isDesktop) {
    return Column(
      crossAxisAlignment:
          isDesktop ? CrossAxisAlignment.start : CrossAxisAlignment.center,
      children: [
        // Main tagline with animation
        TweenAnimationBuilder<double>(
          duration: const Duration(milliseconds: 1000),
          tween: Tween(begin: 0.0, end: 1.0),
          builder: (context, value, child) {
            return Transform.translate(
              offset: Offset(0, 50 * (1 - value)),
              child: Opacity(opacity: value, child: child),
            );
          },
          child: Text(
            'learn things,\nforever.',
            style: Theme.of(context).textTheme.displayLarge?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
              height: 1.1,
            ),
            textAlign: isDesktop ? TextAlign.left : TextAlign.center,
          ),
        ),

        const SizedBox(height: 24),

        // Subtitle with delay animation
        TweenAnimationBuilder<double>(
          duration: const Duration(milliseconds: 1200),
          tween: Tween(begin: 0.0, end: 1.0),
          builder: (context, value, child) {
            return Transform.translate(
              offset: Offset(0, 30 * (1 - value)),
              child: Opacity(opacity: value, child: child),
            );
          },
          child: Text(
            'Master any subject with intelligent spaced repetition.\nNever forget what you learn.',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              color: Theme.of(
                context,
              ).textTheme.bodyLarge?.color?.withValues(alpha: 0.8),
              height: 1.4,
            ),
            textAlign: isDesktop ? TextAlign.left : TextAlign.center,
          ),
        ),

        const SizedBox(height: 40),

        // CTA Button with delay animation
        TweenAnimationBuilder<double>(
          duration: const Duration(milliseconds: 1400),
          tween: Tween(begin: 0.0, end: 1.0),
          builder: (context, value, child) {
            return Transform.scale(
              scale: 0.8 + (0.2 * value),
              child: Opacity(opacity: value, child: child),
            );
          },
          child: _buildGetSpacedButton(context),
        ),
      ],
    );
  }

  Widget _buildHeroVisual(BuildContext context) {
    return Container(
      height: 300,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.2),
            blurRadius: 30,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
                Theme.of(context).colorScheme.secondary.withValues(alpha: 0.2),
              ],
            ),
          ),
          child: Stack(
            children: [
              // Animated floating elements representing spaced repetition
              ...List.generate(
                5,
                (index) => TweenAnimationBuilder<double>(
                  duration: Duration(milliseconds: 2000 + (index * 200)),
                  tween: Tween(begin: 0.0, end: 1.0),
                  builder: (context, value, child) {
                    return Positioned(
                      left: 50 + (index * 40.0),
                      top: 50 + (value * 100) + (index * 30.0),
                      child: Transform.scale(
                        scale: 0.5 + (value * 0.5),
                        child: Container(
                          width: 60,
                          height: 40,
                          decoration: BoxDecoration(
                            color: Theme.of(
                              context,
                            ).colorScheme.primary.withValues(alpha: 0.3),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Icon(
                            Icons.lightbulb_outline,
                            color: Theme.of(context).colorScheme.primary,
                            size: 20,
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),

              // Central brain icon
              Center(
                child: TweenAnimationBuilder<double>(
                  duration: const Duration(milliseconds: 1500),
                  tween: Tween(begin: 0.0, end: 1.0),
                  builder: (context, value, child) {
                    return Transform.scale(
                      scale: value,
                      child: Icon(
                        Icons.psychology,
                        size: 80,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGetSpacedButton(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        final buttonText =
            authProvider.isSignedIn ? 'BACK TO APP' : 'GET SPACED';
        final iconData =
            authProvider.isSignedIn ? Icons.arrow_back : Icons.arrow_forward;

        return Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(30),
            boxShadow: [
              BoxShadow(
                color: Theme.of(
                  context,
                ).colorScheme.primary.withValues(alpha: 0.3),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: ElevatedButton(
            onPressed: onNavigateToLogin,
            style: ElevatedButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 20),
              textStyle: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
                fontSize: 20,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(30),
              ),
              elevation: 0,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(buttonText),
                const SizedBox(width: 12),
                Icon(iconData, size: 24),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildFeaturesSection(
    BuildContext context,
    bool isDesktop,
    bool isMobile,
  ) {
    final features = [
      {
        'icon': Icons.schedule,
        'title': 'Smart Scheduling',
        'description':
            'AI-powered spaced repetition algorithm adapts to your learning pace.',
      },
      {
        'icon': Icons.psychology,
        'title': 'Memory Optimization',
        'description':
            'Scientific approach to maximize retention and minimize forgetting.',
      },
      {
        'icon': Icons.chat_bubble_outline,
        'title': 'Interactive Learning',
        'description':
            'Engage with an AI tutor that helps reinforce your knowledge.',
      },
      {
        'icon': Icons.trending_up,
        'title': 'Progress Tracking',
        'description':
            'Monitor your learning journey with detailed analytics and insights.',
      },
    ];

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isDesktop ? 80 : 20,
        vertical: 80,
      ),
      child: Column(
        children: [
          // Section header
          Text(
            'Why Choose Spaced?',
            style: Theme.of(context).textTheme.displaySmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: 16),

          Text(
            'Built on decades of cognitive science research',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              color: Theme.of(
                context,
              ).textTheme.bodyLarge?.color?.withValues(alpha: 0.7),
            ),
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: 60),

          // Features grid
          if (isDesktop)
            Row(
              children:
                  features
                      .map(
                        (feature) => Expanded(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 20),
                            child: _buildFeatureCard(context, feature),
                          ),
                        ),
                      )
                      .toList(),
            )
          else
            Column(
              children:
                  features
                      .map(
                        (feature) => Padding(
                          padding: const EdgeInsets.only(bottom: 30),
                          child: _buildFeatureCard(context, feature),
                        ),
                      )
                      .toList(),
            ),
        ],
      ),
    );
  }

  Widget _buildFeatureCard(BuildContext context, Map<String, dynamic> feature) {
    return Card(
      elevation: 0,
      color: Theme.of(context).cardColor.withValues(alpha: 0.7),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(30),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Theme.of(
                  context,
                ).colorScheme.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Icon(
                feature['icon'],
                size: 40,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),

            const SizedBox(height: 20),

            Text(
              feature['title'],
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 12),

            Text(
              feature['description'],
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: Theme.of(
                  context,
                ).textTheme.bodyLarge?.color?.withValues(alpha: 0.8),
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAboutSection(BuildContext context, bool isDesktop) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isDesktop ? 80 : 20,
        vertical: 80,
      ),
      child: Column(
        children: [
          Text(
            'Powered by Science',
            style: Theme.of(context).textTheme.displaySmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: 16),

          Text(
            'Built on the Free Spaced Repetition Scheduler (FSRS)',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              color: Theme.of(context).colorScheme.primary,
              fontWeight: FontWeight.w600,
            ),
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: 32),

          Text(
            'FSRS is a cutting-edge, evidence-based algorithm developed by cognitive scientists and backed by extensive research. Unlike traditional spaced repetition systems, FSRS uses sophisticated mathematical models to predict when you\'ll forget information and schedules reviews at the optimal moment.',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Theme.of(
                context,
              ).textTheme.bodyLarge?.color?.withValues(alpha: 0.8),
              height: 1.6,
            ),
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: 40),

          // Key benefits grid
          if (isDesktop)
            Row(
              children: [
                Expanded(
                  child: _buildFSRSBenefit(
                    context,
                    Icons.science,
                    'Research-Backed',
                    'Validated by peer-reviewed studies and real-world data from millions of reviews',
                  ),
                ),
                const SizedBox(width: 30),
                Expanded(
                  child: _buildFSRSBenefit(
                    context,
                    Icons.psychology,
                    'Adaptive Learning',
                    'Personalizes to your memory patterns and adjusts difficulty dynamically',
                  ),
                ),
                const SizedBox(width: 30),
                Expanded(
                  child: _buildFSRSBenefit(
                    context,
                    Icons.trending_up,
                    'Proven Results',
                    'Users report 40% better retention compared to traditional flashcard methods',
                  ),
                ),
              ],
            )
          else
            Column(
              children: [
                _buildFSRSBenefit(
                  context,
                  Icons.science,
                  'Research-Backed',
                  'Validated by peer-reviewed studies and real-world data from millions of reviews',
                ),
                const SizedBox(height: 20),
                _buildFSRSBenefit(
                  context,
                  Icons.psychology,
                  'Adaptive Learning',
                  'Personalizes to your memory patterns and adjusts difficulty dynamically',
                ),
                const SizedBox(height: 20),
                _buildFSRSBenefit(
                  context,
                  Icons.trending_up,
                  'Proven Results',
                  'Users report 40% better retention compared to traditional flashcard methods',
                ),
              ],
            ),

          const SizedBox(height: 40),

          // Learn more button
          OutlinedButton.icon(
            onPressed:
                () => _launchURL(
                  'https://github.com/open-spaced-repetition/fsrs4anki/wiki',
                ),
            icon: const Icon(Icons.launch),
            label: const Text('Learn More About FSRS'),
            style: OutlinedButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.primary,
              side: BorderSide(color: Theme.of(context).colorScheme.primary),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFSRSBenefit(
    BuildContext context,
    IconData icon,
    String title,
    String description,
  ) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.2),
        ),
      ),
      child: Column(
        children: [
          Icon(icon, size: 32, color: Theme.of(context).colorScheme.primary),
          const SizedBox(height: 12),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            description,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(
                context,
              ).textTheme.bodyLarge?.color?.withValues(alpha: 0.7),
              height: 1.4,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  // Helper method to launch URLs
  void _launchURL(String url) async {
    try {
      final Uri uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        throw 'Could not launch $url';
      }
    } catch (e) {
      // Log error - URL launching failed
      _logger.severe('Failed to launch URL: $e');
    }
  }

  Widget _buildCallToActionSection(BuildContext context, bool isDesktop) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isDesktop ? 80 : 20,
        vertical: 80,
      ),
      child: Container(
        padding: const EdgeInsets.all(60),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).colorScheme.primary,
              Theme.of(context).colorScheme.secondary,
            ],
          ),
          borderRadius: BorderRadius.circular(30),
          boxShadow: [
            BoxShadow(
              color: Theme.of(
                context,
              ).colorScheme.primary.withValues(alpha: 0.3),
              blurRadius: 30,
              offset: const Offset(0, 15),
            ),
          ],
        ),
        child: Column(
          children: [
            Text(
              'Ready to Transform Your Learning?',
              style: Theme.of(context).textTheme.displaySmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 20),

            Text(
              'Join thousands of learners who have revolutionized their study habits',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: Colors.white.withValues(alpha: 0.9),
              ),
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 40),

            ElevatedButton(
              onPressed: onNavigateToLogin,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: Theme.of(context).colorScheme.primary,
                padding: const EdgeInsets.symmetric(
                  horizontal: 50,
                  vertical: 20,
                ),
                textStyle: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
                elevation: 0,
              ),
              child: Consumer<AuthProvider>(
                builder: (context, authProvider, child) {
                  return Text(
                    authProvider.isSignedIn
                        ? 'BACK TO APP'
                        : 'START LEARNING TODAY',
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFooter(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 30),
      child: Column(
        children: [
          Divider(
            color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.2),
          ),

          const SizedBox(height: 20),

          Text(
            '© 2025 Spaced. Built with ❤️ for learners everywhere.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Theme.of(
                context,
              ).textTheme.bodyLarge?.color?.withValues(alpha: 0.6),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
