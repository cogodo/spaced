# Spaced Repetition Learning System

A modern spaced repetition learning application built with Flutter frontend and Python backend.

## Project Structure

- **`flutter_app/`** - Flutter frontend application
  - Cross-platform mobile and web app
  - AI chat assistant for learning guidance
  - **Voice-to-Voice Chatbot**: Natural voice conversations with AI tutor
  - Multiple themes and responsive design
  - See `flutter_app/README.md` for frontend-specific instructions

- **`src/backend/`** - Python backend services
  - API endpoints and business logic
  - Database management
  - Authentication and user management
  - **Voice Agent Worker**: Real-time voice processing pipeline

- **`.github/workflows/`** - CI/CD configuration
  - Automated deployment to GitHub Pages
  - Build and test workflows

- **Root configuration files:**
  - `bootstrap.sh` - Production deployment script with voice-to-voice support
  - `alt-index.html` - Optimized web page template
  - `CNAME` - Custom domain configuration for getspaced.app
  - `VOICE_TO_VOICE_README.md` - Comprehensive voice feature documentation

## Quick Start

### Frontend (Flutter App)
```bash
cd flutter_app
API_PORT=8000
flutter run -d web-server \
  --web-port 8080 \
  --web-hostname localhost \
  --web-tls-cert-path certs/cert.pem \
  --web-tls-cert-key-path certs/key.pem
```

### Backend
```bash
cd src/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### Voice Services (Development)
```bash
cd src/backend
# Start voice agent worker
python voice_agent_worker.py

# Or use the convenience script
./start_voice_services.sh
```

### Production Deployment
```bash
# Set voice environment variables
export LIVEKIT_API_KEY="your-key"
export LIVEKIT_API_SECRET="your-secret"
export LIVEKIT_SERVER_URL="wss://your-server.livekit.cloud"
export CARTESIA_API_KEY="your-cartesia-key"
export DEEPGRAM_API_KEY="your-deepgram-key"  # Optional

# Run bootstrap script
sudo ./bootstrap.sh
```

The app automatically deploys to [getspaced.app](https://getspaced.app) via GitHub Actions when changes are pushed to the main branch.

## Features

- **Spaced Repetition Algorithm**: Smart scheduling using FSRS
- **AI Chat Assistant**: Get learning tips and guidance
- **🎤 Voice-to-Voice Chatbot**: Natural voice conversations with AI tutor
  - Real-time speech-to-text and text-to-speech
  - LiveKit-powered voice rooms
  - Voice activity detection and noise cancellation
- **Multi-Platform**: Web, mobile, and desktop support
- **Modern UI**: Multiple themes with responsive design
- **Performance Optimized**: Fast loading and smooth interactions

## Voice-to-Voice Feature

The voice-to-voice chatbot allows users to have natural voice conversations with the AI tutor. See [VOICE_TO_VOICE_README.md](VOICE_TO_VOICE_README.md) for:

- **Architecture Overview**: How voice processing works
- **Deployment Guide**: Setting up voice services in production
- **Service Management**: Managing voice agent worker
- **Health Monitoring**: Checking service status
- **Troubleshooting**: Common issues and solutions

### Quick Voice Setup

1. **Get API Keys**:
   - LiveKit Cloud account (or self-hosted server)
   - Cartesia API key for text-to-speech
   - Deepgram API key for speech-to-text (optional)

2. **Configure Environment**:
   ```bash
   # Add to your .env file
   LIVEKIT_API_KEY="your-key"
   LIVEKIT_API_SECRET="your-secret"
   LIVEKIT_SERVER_URL="wss://your-server.livekit.cloud"
   CARTESIA_API_KEY="your-cartesia-key"
   DEEPGRAM_API_KEY="your-deepgram-key"  # Optional
   ```

3. **Start Services**:
   ```bash
   # Development
   ./src/backend/start_voice_services.sh
   
   # Production
   sudo ./bootstrap.sh
   ```

4. **Test Voice Feature**:
   - Open the Flutter app
   - Start a chat session
   - Click the microphone button
   - Speak naturally to the AI tutor

## Live Demo

Visit the app: [https://getspaced.app](https://getspaced.app)

## About

Spaced uses scientifically proven spaced repetition techniques to help you remember information more effectively. Add items you want to remember, and the app will schedule reviews at optimal intervals based on your recall performance.

- No account required
- Data stored locally on your device
- Simple, distraction-free interface
- **Natural voice interaction** with AI tutor
