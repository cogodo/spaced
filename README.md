# Spaced Repetition App

A modern web app for spaced repetition learning built with Flutter. This app helps you remember important information using scientifically proven spaced repetition techniques.

## Features

- Create flashcards or review items
- Smart scheduling based on your recall performance
- Track progress and learning efficiency
- Clean, responsive interface for both mobile and desktop

## Deployment on Vercel

This app is configured for easy deployment on Vercel. To deploy:

1. Fork or clone this repository
2. Connect it to your Vercel account
3. Deploy with default settings

The application will automatically build and deploy the Flutter web application.

## Local Development

To run this project locally:

```bash
# Get dependencies
flutter pub get

# Run in debug mode
flutter run -d chrome

# Build for production
flutter build web --release
```

## Technology

- Flutter Web for the UI
- SharedPreferences for local data persistence
- Provider for state management
