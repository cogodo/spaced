# Spaced Repetition App

A modern web app for spaced repetition learning built with Flutter. This app helps you remember important information using scientifically proven spaced repetition techniques.

## Features

- Create flashcards or review items
- Smart scheduling based on your recall performance
- Track progress and learning efficiency
- Clean, responsive interface for both mobile and desktop

## Deployment with GitHub Actions

This app is configured for automatic deployment to GitHub Pages using GitHub Actions.

### Automated Deployment

When you push changes to the `main` branch, GitHub Actions will automatically:
1. Build the Flutter web app
2. Deploy it to GitHub Pages
3. Make it available at `https://cogodo.github.io/spaced/`

You can also manually trigger the workflow from the Actions tab in your GitHub repository.

### Configuration

The deployment is configured in `.github/workflows/deploy.yml`. The workflow:

1. Sets up Flutter on a GitHub-hosted runner
2. Builds the web app with the correct base path
3. Creates a `.nojekyll` file and adds a `404.html` for SPA routing
4. Deploys the built app to the `gh-pages` branch

### Repository Setup

For the GitHub Actions deployment to work:

1. Go to your repository Settings → Pages
2. Set "Source" to "GitHub Actions"
3. Ensure the repository has permission to create the `GITHUB_TOKEN` for deployment

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
