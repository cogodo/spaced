// Performance optimizations for Flutter web
// This file contains configurations to improve loading performance

// Web-specific optimizations
import 'dart:html' as html;
import 'dart:js' as js;

class WebPerformanceOptimizer {
  static void initialize() {
    // Preload critical resources
    _preloadCriticalResources();

    // Optimize rendering
    _optimizeRendering();

    // Setup performance monitoring
    _setupPerformanceMonitoring();
  }

  static void _preloadCriticalResources() {
    // Preload fonts that might be used
    final linkElement =
        html.LinkElement()
          ..rel = 'preload'
          ..href =
              'https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600;700&display=swap'
          ..as = 'style';
    html.document.head?.append(linkElement);
  }

  static void _optimizeRendering() {
    // Reduce layout thrashing
    html.document.documentElement?.style.setProperty(
      '--flutter-view-height',
      '100vh',
    );

    // Optimize scroll performance
    html.document.body?.style.setProperty('overscroll-behavior', 'none');
    html.document.body?.style.setProperty('touch-action', 'pan-x pan-y');
  }

  static void _setupPerformanceMonitoring() {
    // Monitor performance metrics
    js.context.callMethod('setTimeout', [
      () {
        final performance = html.window.performance;
        if (performance != null) {
          final loadTime =
              performance.timing?.loadEventEnd ??
              0 - (performance.timing?.navigationStart ?? 0);
          print('Page load time: ${loadTime}ms');
        }
      },
      1000,
    ]);
  }
}
