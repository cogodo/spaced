import 'dart:ui' as ui;
import 'package:flutter/material.dart';

/// Spaced design tokens for colors, spacing, radii, and motion.
class SpacedTokens extends ThemeExtension<SpacedTokens> {
  // Brand
  final Color brandPrimary;
  final Color brandSecondary;
  final Color brandAccent;
  final Color brandOnPrimary;

  // Semantic
  final Color success;
  final Color warning;
  final Color error;
  final Color info;

  // Surfaces
  final Color background;
  final Color surface;
  final Color surfaceAlt;
  final Color surfaceElevated;
  final Color onBackground;
  final Color onSurface;
  final Color outline;

  // Spacing scale (4pt grid)
  final double spaceXs; // 4
  final double spaceSm; // 8
  final double spaceMd; // 12
  final double spaceLg; // 16
  final double spaceXl; // 24
  final double space2Xl; // 32

  // Radii
  final double radiusSm;
  final double radiusMd;
  final double radiusLg;
  final double radiusFull;

  // Motion
  final Duration fast;
  final Duration normal;
  final Duration slow;

  const SpacedTokens({
    // Brand
    required this.brandPrimary,
    required this.brandSecondary,
    required this.brandAccent,
    required this.brandOnPrimary,
    // Semantic
    required this.success,
    required this.warning,
    required this.error,
    required this.info,
    // Surfaces
    required this.background,
    required this.surface,
    required this.surfaceAlt,
    required this.surfaceElevated,
    required this.onBackground,
    required this.onSurface,
    required this.outline,
    // Spacing
    this.spaceXs = 4,
    this.spaceSm = 8,
    this.spaceMd = 12,
    this.spaceLg = 16,
    this.spaceXl = 24,
    this.space2Xl = 32,
    // Radii
    this.radiusSm = 6,
    this.radiusMd = 10,
    this.radiusLg = 14,
    this.radiusFull = 999,
    // Motion
    this.fast = const Duration(milliseconds: 120),
    this.normal = const Duration(milliseconds: 220),
    this.slow = const Duration(milliseconds: 360),
  });

  @override
  SpacedTokens copyWith({
    Color? brandPrimary,
    Color? brandSecondary,
    Color? brandAccent,
    Color? brandOnPrimary,
    Color? success,
    Color? warning,
    Color? error,
    Color? info,
    Color? background,
    Color? surface,
    Color? surfaceAlt,
    Color? surfaceElevated,
    Color? onBackground,
    Color? onSurface,
    Color? outline,
    double? spaceXs,
    double? spaceSm,
    double? spaceMd,
    double? spaceLg,
    double? spaceXl,
    double? space2Xl,
    double? radiusSm,
    double? radiusMd,
    double? radiusLg,
    double? radiusFull,
    Duration? fast,
    Duration? normal,
    Duration? slow,
  }) {
    return SpacedTokens(
      brandPrimary: brandPrimary ?? this.brandPrimary,
      brandSecondary: brandSecondary ?? this.brandSecondary,
      brandAccent: brandAccent ?? this.brandAccent,
      brandOnPrimary: brandOnPrimary ?? this.brandOnPrimary,
      success: success ?? this.success,
      warning: warning ?? this.warning,
      error: error ?? this.error,
      info: info ?? this.info,
      background: background ?? this.background,
      surface: surface ?? this.surface,
      surfaceAlt: surfaceAlt ?? this.surfaceAlt,
      surfaceElevated: surfaceElevated ?? this.surfaceElevated,
      onBackground: onBackground ?? this.onBackground,
      onSurface: onSurface ?? this.onSurface,
      outline: outline ?? this.outline,
      spaceXs: spaceXs ?? this.spaceXs,
      spaceSm: spaceSm ?? this.spaceSm,
      spaceMd: spaceMd ?? this.spaceMd,
      spaceLg: spaceLg ?? this.spaceLg,
      spaceXl: spaceXl ?? this.spaceXl,
      space2Xl: space2Xl ?? this.space2Xl,
      radiusSm: radiusSm ?? this.radiusSm,
      radiusMd: radiusMd ?? this.radiusMd,
      radiusLg: radiusLg ?? this.radiusLg,
      radiusFull: radiusFull ?? this.radiusFull,
      fast: fast ?? this.fast,
      normal: normal ?? this.normal,
      slow: slow ?? this.slow,
    );
  }

  @override
  SpacedTokens lerp(ThemeExtension<SpacedTokens>? other, double t) {
    if (other is! SpacedTokens) return this;
    return SpacedTokens(
      brandPrimary: Color.lerp(brandPrimary, other.brandPrimary, t)!,
      brandSecondary: Color.lerp(brandSecondary, other.brandSecondary, t)!,
      brandAccent: Color.lerp(brandAccent, other.brandAccent, t)!,
      brandOnPrimary: Color.lerp(brandOnPrimary, other.brandOnPrimary, t)!,
      success: Color.lerp(success, other.success, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      error: Color.lerp(error, other.error, t)!,
      info: Color.lerp(info, other.info, t)!,
      background: Color.lerp(background, other.background, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surfaceAlt: Color.lerp(surfaceAlt, other.surfaceAlt, t)!,
      surfaceElevated: Color.lerp(surfaceElevated, other.surfaceElevated, t)!,
      onBackground: Color.lerp(onBackground, other.onBackground, t)!,
      onSurface: Color.lerp(onSurface, other.onSurface, t)!,
      outline: Color.lerp(outline, other.outline, t)!,
      spaceXs: ui.lerpDouble(spaceXs, other.spaceXs, t)!,
      spaceSm: ui.lerpDouble(spaceSm, other.spaceSm, t)!,
      spaceMd: ui.lerpDouble(spaceMd, other.spaceMd, t)!,
      spaceLg: ui.lerpDouble(spaceLg, other.spaceLg, t)!,
      spaceXl: ui.lerpDouble(spaceXl, other.spaceXl, t)!,
      space2Xl: ui.lerpDouble(space2Xl, other.space2Xl, t)!,
      radiusSm: ui.lerpDouble(radiusSm, other.radiusSm, t)!,
      radiusMd: ui.lerpDouble(radiusMd, other.radiusMd, t)!,
      radiusLg: ui.lerpDouble(radiusLg, other.radiusLg, t)!,
      radiusFull: ui.lerpDouble(radiusFull, other.radiusFull, t)!,
      fast: Duration(
        milliseconds:
            ui
                .lerpDouble(
                  fast.inMilliseconds.toDouble(),
                  other.fast.inMilliseconds.toDouble(),
                  t,
                )!
                .round(),
      ),
      normal: Duration(
        milliseconds:
            ui
                .lerpDouble(
                  normal.inMilliseconds.toDouble(),
                  other.normal.inMilliseconds.toDouble(),
                  t,
                )!
                .round(),
      ),
      slow: Duration(
        milliseconds:
            ui
                .lerpDouble(
                  slow.inMilliseconds.toDouble(),
                  other.slow.inMilliseconds.toDouble(),
                  t,
                )!
                .round(),
      ),
    );
  }

  LinearGradient brandGradient({
    Alignment begin = Alignment.topLeft,
    Alignment end = Alignment.bottomRight,
  }) => LinearGradient(
    begin: begin,
    end: end,
    colors: [brandAccent, brandPrimary],
  );
}
