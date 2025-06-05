# Spaced Repetition Learning System

A modern spaced repetition learning application built with Flutter frontend and Python backend.

## Project Structure

- **`flutter_app/`** - Flutter frontend application
  - Cross-platform mobile and web app
  - AI chat assistant for learning guidance
  - Multiple themes and responsive design
  - See `flutter_app/README.md` for frontend-specific instructions

- **`backend/`** - Python backend services (if applicable)
  - API endpoints and business logic
  - Database management
  - Authentication and user management

- **`.github/workflows/`** - CI/CD configuration
  - Automated deployment to GitHub Pages
  - Build and test workflows

- **Root configuration files:**
  - `alt-index.html` - Optimized web page template
  - `CNAME` - Custom domain configuration for getspaced.app
  - `requirements.txt` - Backend Python dependencies

## Quick Start

### Frontend (Flutter App)
```bash
cd flutter_app
flutter pub get
flutter run -d chrome
```

### Deployment
The app automatically deploys to [getspaced.app](https://getspaced.app) via GitHub Actions when changes are pushed to the main branch.

## Features

- **Spaced Repetition Algorithm**: Smart scheduling using FSRS
- **AI Chat Assistant**: Get learning tips and guidance
- **Multi-Platform**: Web, mobile, and desktop support
- **Modern UI**: Multiple themes with responsive design
- **Performance Optimized**: Fast loading and smooth interactions

## Live Demo

Visit the app: [https://getspaced.app](https://getspaced.app)

## About

Spaced uses scientifically proven spaced repetition techniques to help you remember information more effectively. Add items you want to remember, and the app will schedule reviews at optimal intervals based on your recall performance.

- No account required
- Data stored locally on your device
- Simple, distraction-free interface
