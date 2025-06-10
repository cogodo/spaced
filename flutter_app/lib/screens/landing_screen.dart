import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/logger_service.dart';
import '../providers/auth_provider.dart';
import '../widgets/theme_logo.dart';
import '../widgets/theme_toggle.dart';
import 'dart:math' as math;

class LandingScreen extends StatefulWidget {
  final VoidCallback onNavigateToLogin;

  const LandingScreen({super.key, required this.onNavigateToLogin});

  @override
  State<LandingScreen> createState() => _LandingScreenState();
}

class _LandingScreenState extends State<LandingScreen>
    with TickerProviderStateMixin {
  late ScrollController _scrollController;
  late AnimationController _featuresHeaderController;
  late AnimationController _featuresCardsController;
  late AnimationController _aboutHeaderController;
  late AnimationController _aboutCardsController;
  late AnimationController _logoSpinController;

  late Animation<double> _featuresHeaderAnimation;
  late Animation<double> _featuresCardsAnimation;
  late Animation<double> _aboutHeaderAnimation;
  late Animation<double> _aboutCardsAnimation;

  // Keys to track section positions
  final GlobalKey _featuresSectionKey = GlobalKey();
  final GlobalKey _aboutSectionKey = GlobalKey();

  // Animation states
  bool _featuresHeaderAnimated = false;
  bool _featuresCardsAnimated = false;
  bool _aboutHeaderAnimated = false;
  bool _aboutCardsAnimated = false;

  // Logo interaction
  double _baseRotation = 0.0; // Current settled rotation
  double _additionalRotation = 0.0; // New rotation being animated
  final math.Random _random = math.Random();

  @override
  void initState() {
    super.initState();

    _scrollController = ScrollController();
    _scrollController.addListener(_onScroll);

    // Initialize animation controllers
    _featuresHeaderController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _featuresCardsController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _aboutHeaderController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _aboutCardsController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _logoSpinController = AnimationController(
      duration: const Duration(
        milliseconds: 1500,
      ), // Longer duration for more natural feel
      vsync: this,
    );

    // Listen for animation completion to update base rotation
    _logoSpinController.addStatusListener((status) {
      if (status == AnimationStatus.completed) {
        setState(() {
          _baseRotation += _additionalRotation;
          _additionalRotation = 0.0;
        });
      }
    });

    // Create animations
    _featuresHeaderAnimation = CurvedAnimation(
      parent: _featuresHeaderController,
      curve: Curves.easeOutCubic,
    );
    _featuresCardsAnimation = CurvedAnimation(
      parent: _featuresCardsController,
      curve: Curves.easeOutCubic,
    );
    _aboutHeaderAnimation = CurvedAnimation(
      parent: _aboutHeaderController,
      curve: Curves.easeOutCubic,
    );
    _aboutCardsAnimation = CurvedAnimation(
      parent: _aboutCardsController,
      curve: Curves.easeOutCubic,
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _featuresHeaderController.dispose();
    _featuresCardsController.dispose();
    _aboutHeaderController.dispose();
    _aboutCardsController.dispose();
    _logoSpinController.dispose();
    super.dispose();
  }

  void _onScroll() {
    final screenHeight = MediaQuery.of(context).size.height;

    // Check if features section is in view
    if (!_featuresHeaderAnimated) {
      final featuresRenderBox =
          _featuresSectionKey.currentContext?.findRenderObject() as RenderBox?;
      if (featuresRenderBox != null) {
        final featuresPosition = featuresRenderBox.localToGlobal(Offset.zero);
        if (featuresPosition.dy < screenHeight * 0.8) {
          _featuresHeaderAnimated = true;
          _featuresHeaderController.forward();

          // Start cards animation 300ms after header
          Future.delayed(const Duration(milliseconds: 300), () {
            if (!_featuresCardsAnimated) {
              _featuresCardsAnimated = true;
              _featuresCardsController.forward();
            }
          });
        }
      }
    }

    // Check if about section is in view
    if (!_aboutHeaderAnimated) {
      final aboutRenderBox =
          _aboutSectionKey.currentContext?.findRenderObject() as RenderBox?;
      if (aboutRenderBox != null) {
        final aboutPosition = aboutRenderBox.localToGlobal(Offset.zero);
        if (aboutPosition.dy < screenHeight * 0.8) {
          _aboutHeaderAnimated = true;
          _aboutHeaderController.forward();

          // Start cards animation 300ms after header
          Future.delayed(const Duration(milliseconds: 300), () {
            if (!_aboutCardsAnimated) {
              _aboutCardsAnimated = true;
              _aboutCardsController.forward();
            }
          });
        }
      }
    }
  }

  void _onLogoTap() {
    // If animation is running, calculate current position and use as new base
    if (_logoSpinController.isAnimating) {
      final curvedValue = Curves.easeOutQuart.transform(
        _logoSpinController.value,
      );
      _baseRotation += (_additionalRotation * curvedValue);
    }

    // Generate very small random rotation between 0.2-0.5 rotations (keep under 2 total)
    _additionalRotation = 0.2 + (_random.nextDouble() * 0.3);

    _logoSpinController.reset();
    _logoSpinController.forward();
  }

  @override
  Widget build(BuildContext context) {
    final isDesktop = MediaQuery.of(context).size.width > 800;
    final isMobile = MediaQuery.of(context).size.width < 600;

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient:
              isMobile
                  ? null // Remove gradient on mobile for better performance
                  : LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Theme.of(context).scaffoldBackgroundColor,
                      Theme.of(
                        context,
                      ).colorScheme.primary.withValues(alpha: 0.1),
                    ],
                  ),
          color: isMobile ? Theme.of(context).scaffoldBackgroundColor : null,
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            controller: _scrollController,
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
    final isMobile = MediaQuery.of(context).size.width < 600;

    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        return Container(
          padding: EdgeInsets.symmetric(
            horizontal: isDesktop ? 80 : 20,
            vertical: 20,
          ),
          child:
              isMobile
                  ? Column(
                    children: [
                      // First row: Logo and Login button
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          // Logo/Brand
                          Row(
                            children: [
                              ThemeLogo(size: 32),
                              const SizedBox(width: 12),
                              Text(
                                'Spaced',
                                style: Theme.of(
                                  context,
                                ).textTheme.headlineMedium?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                              ),
                            ],
                          ),

                          // Login button only
                          OutlinedButton(
                            onPressed: widget.onNavigateToLogin,
                            child: Text(
                              authProvider.isSignedIn
                                  ? 'Back to App'
                                  : 'Login / Sign Up',
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 12),

                      // Second row: Theme toggle right-aligned
                      Row(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [ThemeToggle()],
                      ),
                    ],
                  )
                  : Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      // Logo/Brand
                      Row(
                        children: [
                          ThemeLogo(size: 32),
                          const SizedBox(width: 12),
                          Text(
                            'Spaced',
                            style: Theme.of(
                              context,
                            ).textTheme.headlineMedium?.copyWith(
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
                            onPressed: widget.onNavigateToLogin,
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
                Expanded(flex: 2, child: _buildHeroText(context, isDesktop)),
                const SizedBox(width: 40),
                Expanded(flex: 3, child: _buildHeroVisual(context)),
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
    final isMobile = MediaQuery.of(context).size.width < 600;
    final containerHeight = isMobile ? 350.0 : 500.0; // Smaller on mobile

    return Container(
      height: containerHeight,
      child: Center(child: _buildAnimatedLogo(context)),
    );
  }

  Widget _buildAnimatedLogo(BuildContext context) {
    return _buildRotatingLogoAnimation(context);
  }

  Widget _buildRotatingLogoAnimation(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 600;

    return TweenAnimationBuilder<double>(
      duration: const Duration(
        milliseconds: 3000,
      ), // Total: 1s appear + 0.5s wait + 1.5s rotate
      tween: Tween(begin: 0.0, end: 1.0),
      curve: Curves.easeOutBack,
      builder: (context, animationValue, child) {
        // Phase 1 (0-0.33): Logo appears and scales up
        // Phase 2 (0.33-0.5): Logo waits in static position (0.5s)
        // Phase 3 (0.5-1.0): Logo rotates

        double opacity;
        double logoScale;
        double rotationProgress;

        if (animationValue <= 0.33) {
          // Phase 1: Appearing (1s)
          final phaseProgress = animationValue / 0.33;
          opacity = phaseProgress;
          logoScale = 0.2 + (phaseProgress * 0.8);
          rotationProgress = 0.0;
        } else if (animationValue <= 0.5) {
          // Phase 2: Waiting (0.5s)
          opacity = 1.0;
          logoScale = 1.0;
          rotationProgress = 0.0;
        } else {
          // Phase 3: Rotating (1.5s)
          final phaseProgress = (animationValue - 0.5) / 0.5;
          opacity = 1.0;
          logoScale = 1.0;
          rotationProgress = phaseProgress * 1.0; // 1 full rotation
        }

        return AnimatedBuilder(
          animation: _logoSpinController,
          builder: (context, child) {
            // Apply deceleration curve to the interactive spin for natural slowdown
            final curvedValue = Curves.easeOutQuart.transform(
              _logoSpinController.value,
            );
            final totalRotation =
                rotationProgress +
                _baseRotation +
                (_additionalRotation * curvedValue);

            // Smaller logo size on mobile to prevent clipping
            final logoSize = isMobile ? 300.0 : 500.0;
            final glowSize = isMobile ? 320.0 : 500.0;
            final glowBlur = isMobile ? 15.0 : 30.0;
            final glowSpread = isMobile ? 5.0 : 10.0;

            return GestureDetector(
              onTap: _onLogoTap,
              child: MouseRegion(
                cursor: SystemMouseCursors.click,
                child: Transform.scale(
                  scale: logoScale,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // Reduced glow effect on mobile for better performance
                      if (!isMobile) // Only show glow on desktop
                        Opacity(
                          opacity: opacity,
                          child: Container(
                            width: glowSize,
                            height: glowSize,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.primary.withValues(alpha: 0.3),
                                  blurRadius: glowBlur * opacity,
                                  spreadRadius: glowSpread * opacity,
                                ),
                              ],
                            ),
                          ),
                        ),
                      // Rotating logo
                      Transform.rotate(
                        angle: totalRotation * 2 * math.pi,
                        origin: Offset(
                          -5,
                          10,
                        ), // Use final coordinates (-5, 10)
                        child: Opacity(
                          opacity: opacity,
                          child: ThemeLogo(size: logoSize),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
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
            onPressed: widget.onNavigateToLogin,
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
      key: _featuresSectionKey,
      padding: EdgeInsets.symmetric(
        horizontal: isDesktop ? 80 : 20,
        vertical: 120, // Increased padding to push section down initially
      ),
      child: Column(
        children: [
          // Animated section header
          RepaintBoundary(
            child: AnimatedBuilder(
              animation: _featuresHeaderAnimation,
              builder: (context, child) {
                return Transform.translate(
                  offset: Offset(0, 30 * (1 - _featuresHeaderAnimation.value)),
                  child: Opacity(
                    opacity: _featuresHeaderAnimation.value,
                    child: Column(
                      children: [
                        Text(
                          'Why Choose Spaced?',
                          style: Theme.of(
                            context,
                          ).textTheme.displaySmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                          textAlign: TextAlign.center,
                        ),

                        const SizedBox(height: 16),

                        Text(
                          'Built on decades of cognitive science research',
                          style: Theme.of(
                            context,
                          ).textTheme.titleLarge?.copyWith(
                            color: Theme.of(context).textTheme.bodyLarge?.color
                                ?.withValues(alpha: 0.7),
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),

          const SizedBox(height: 60),

          // Animated features grid
          RepaintBoundary(
            child: AnimatedBuilder(
              animation: _featuresCardsAnimation,
              builder: (context, child) {
                return Transform.translate(
                  offset: Offset(0, 40 * (1 - _featuresCardsAnimation.value)),
                  child: Opacity(
                    opacity: _featuresCardsAnimation.value,
                    child:
                        isDesktop
                            ? Row(
                              children:
                                  features
                                      .asMap()
                                      .entries
                                      .map(
                                        (entry) => Expanded(
                                          child: Padding(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 20,
                                            ),
                                            child: _buildFeatureCard(
                                              context,
                                              entry.value,
                                              entry.key,
                                            ),
                                          ),
                                        ),
                                      )
                                      .toList(),
                            )
                            : Column(
                              children:
                                  features
                                      .asMap()
                                      .entries
                                      .map(
                                        (entry) => Padding(
                                          padding: const EdgeInsets.only(
                                            bottom: 30,
                                          ),
                                          child: _buildFeatureCard(
                                            context,
                                            entry.value,
                                            entry.key,
                                          ),
                                        ),
                                      )
                                      .toList(),
                            ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureCard(
    BuildContext context,
    Map<String, dynamic> feature,
    int index,
  ) {
    return TweenAnimationBuilder<double>(
      duration: Duration(
        milliseconds: 300 + (index * 100),
      ), // Stagger animation
      tween: Tween(begin: 0.0, end: _featuresCardsAnimation.value),
      builder: (context, value, child) {
        return Transform.translate(
          offset: Offset(0, 20 * (1 - value)),
          child: Opacity(
            opacity: value,
            child: SizedBox(
              height: 280, // Fixed height for consistent card sizing
              child: Card(
                elevation: 0,
                color: Theme.of(context).cardColor.withValues(alpha: 0.7),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                  side: BorderSide(
                    color: Theme.of(
                      context,
                    ).colorScheme.primary.withValues(alpha: 0.1),
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(30),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
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
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                        textAlign: TextAlign.center,
                      ),

                      const SizedBox(height: 12),

                      Expanded(
                        child: Text(
                          feature['description'],
                          style: Theme.of(
                            context,
                          ).textTheme.bodyLarge?.copyWith(
                            color: Theme.of(context).textTheme.bodyLarge?.color
                                ?.withValues(alpha: 0.8),
                            height: 1.5,
                          ),
                          textAlign: TextAlign.center,
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildAboutSection(BuildContext context, bool isDesktop) {
    return Container(
      key: _aboutSectionKey,
      padding: EdgeInsets.symmetric(
        horizontal: isDesktop ? 80 : 20,
        vertical: 120, // Increased padding to push section down initially
      ),
      child: Column(
        children: [
          // Animated section header
          RepaintBoundary(
            child: AnimatedBuilder(
              animation: _aboutHeaderAnimation,
              builder: (context, child) {
                return Transform.translate(
                  offset: Offset(0, 30 * (1 - _aboutHeaderAnimation.value)),
                  child: Opacity(
                    opacity: _aboutHeaderAnimation.value,
                    child: Column(
                      children: [
                        Text(
                          'Powered by Science',
                          style: Theme.of(
                            context,
                          ).textTheme.displaySmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                          textAlign: TextAlign.center,
                        ),

                        const SizedBox(height: 16),

                        Text(
                          'Built on the Free Spaced Repetition Scheduler (FSRS)',
                          style: Theme.of(
                            context,
                          ).textTheme.titleLarge?.copyWith(
                            color: Theme.of(context).textTheme.bodyLarge?.color
                                ?.withValues(alpha: 0.7),
                          ),
                          textAlign: TextAlign.center,
                        ),

                        const SizedBox(height: 32),

                        Text(
                          'FSRS is a cutting-edge, evidence-based algorithm developed by cognitive scientists and backed by extensive research. Unlike traditional spaced repetition systems, FSRS uses sophisticated mathematical models to predict when you\'ll forget information and schedules reviews at the optimal moment.',
                          style: Theme.of(
                            context,
                          ).textTheme.titleMedium?.copyWith(
                            color: Theme.of(context).textTheme.bodyLarge?.color
                                ?.withValues(alpha: 0.8),
                            height: 1.6,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),

          const SizedBox(height: 40),

          // Animated key benefits grid
          AnimatedBuilder(
            animation: _aboutCardsAnimation,
            builder: (context, child) {
              return Transform.translate(
                offset: Offset(0, 40 * (1 - _aboutCardsAnimation.value)),
                child: Opacity(
                  opacity: _aboutCardsAnimation.value,
                  child: Column(
                    children: [
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
                          foregroundColor:
                              Theme.of(context).colorScheme.primary,
                          side: BorderSide(
                            color: Theme.of(context).colorScheme.primary,
                          ),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 24,
                            vertical: 16,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
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
    return SizedBox(
      height: 200, // Fixed height for consistent benefit card sizing
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor.withValues(alpha: 0.7),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.2),
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
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
            Expanded(
              child: Text(
                description,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(
                    context,
                  ).textTheme.bodyLarge?.color?.withValues(alpha: 0.7),
                  height: 1.4,
                ),
                textAlign: TextAlign.center,
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
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
      print('Failed to launch URL: $e');
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
              onPressed: widget.onNavigateToLogin,
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
