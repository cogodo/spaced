# Spaced - Flutter Frontend

This directory contains the Flutter frontend application for the Spaced Repetition Learning System.

## Getting Started

To run this Flutter app:

1. Navigate to this directory:
   ```bash
   cd flutter_app
   ```

2. Install dependencies:
   ```bash
   flutter pub get
   
   # For iOS/macOS development (requires Xcode)
   cd ios && pod install && cd ..
   ```

3. Run the app:
   ```bash
   # For web
   flutter run -d chrome
   
   # For mobile (requires device/emulator)
   flutter run
   ```

## Project Structure

- `lib/` - Main source code
  - `lib/screens/` - UI screens (Home, Add, Chat, Settings, About, etc.)
  - `lib/models/` - Data models and business logic
  - `lib/services/` - Services (storage, logging, etc.)
  - `lib/themes/` - App theming and styling
  - `lib/widgets/` - Reusable UI components
  - `lib/utils/` - Utility functions

- `web/` - Web-specific assets and configuration
- `android/`, `ios/`, `macos/`, `windows/`, `linux/` - Platform-specific code
- `test/` - Unit and widget tests
- `assets/` - Images, fonts, and other static assets

### Dependencies & Configuration
- `pubspec.yaml` - Flutter package dependencies
- `analysis_options.yaml` - Dart/Flutter linting rules
- `Podfile` - iOS/macOS native dependencies
- `Gemfile` - Ruby dependencies for CocoaPods (iOS/macOS)

## Features

- **Spaced Repetition Learning**: Smart review scheduling using FSRS algorithm
- **Cross-Platform**: Works on web, mobile, and desktop
- **Multiple Themes**: Light, Dark, Red, and Green themes
- **AI Chat Assistant**: Built-in chat interface for learning guidance
- **Responsive Design**: Adaptive UI for different screen sizes

## Building for Production

```bash
# Web
flutter build web --release

# Android
flutter build apk --release

# iOS (on macOS)
flutter build ios --release
```

## Development Notes

- For iOS/macOS development, CocoaPods is required (`gem install cocoapods`)
- The app uses Material 3 design principles
- All screens follow the established navigation patterns
- State management uses Provider pattern 