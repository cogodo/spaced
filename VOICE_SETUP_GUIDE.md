# Voice Setup Guide - Fix Voice Functionality

This guide will help you fix the voice functionality issues step by step.

## Issues Identified
- ❌ Environment variables not set (API keys missing)
- ❌ Backend server not running
- ❌ Voice agent worker not running

## Step-by-Step Fix

### 1. Set Up Environment Variables

First, copy the example environment file:
```bash
cd src/backend
cp env.example .env
```

Then edit `.env` and add your API keys:

#### 1.1 Get LiveKit Credentials (Required)
1. Go to [LiveKit Cloud](https://cloud.livekit.io)
2. Sign up/login for free
3. Create a new project
4. Go to Settings > Keys
5. Copy your API Key, API Secret, and Server URL

Add to `.env`:
```bash
LIVEKIT_API_KEY="your-api-key-here"
LIVEKIT_API_SECRET="your-api-secret-here"
LIVEKIT_SERVER_URL="wss://your-project.livekit.cloud"
```

#### 1.2 Get OpenAI API Key (Required)
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env`:
```bash
OPENAI_API_KEY="sk-your-openai-key-here"
```

#### 1.3 Get Cartesia API Key (Required)
1. Go to [Cartesia](https://cartesia.ai)
2. Sign up for an account
3. Get your API key from the dashboard
4. Add to `.env`:
```bash
CARTESIA_API_KEY="your-cartesia-key-here"
```

#### 1.4 Optional: Get Deepgram API Key (Better STT)
1. Go to [Deepgram](https://deepgram.com)
2. Sign up for free credits
3. Get API key and add to `.env`:
```bash
DEEPGRAM_API_KEY="your-deepgram-key-here"
```

### 2. Verify Setup

Run the debugging script to check your configuration:
```bash
python debug_voice_setup.py
```

You should see ✅ for all required items.

### 3. Start Backend Server

```bash
# Install dependencies if needed
pip install -e .

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Keep this terminal open and running.

### 4. Start Voice Agent Worker

Open a **new terminal** and run:
```bash
cd src/backend
python voice_agent_worker.py
```

You should see:
```
🚀 Starting LiveKit Voice Agent Worker
✓ LIVEKIT_API_KEY: ********... (32 chars)
✓ OPENAI_API_KEY: ********... (51 chars)
...
🎯 Voice agent starting for room: ...
```

Keep this terminal open and running too.

### 5. Test Voice Functionality

Now test the voice functionality in your Flutter app:

1. **Flutter logs**: Open Flutter logs to see detailed voice connection info:
   ```bash
   cd flutter_app
   flutter logs
   ```

2. **Press mic button**: In your Flutter app, press the microphone button

3. **Check logs**: You should see:
   ```
   [LiveKitVoiceService] Creating room for user: ...
   [LiveKitVoiceService] Room created successfully: ...
   [LiveKitVoiceService] Connected to room: ...
   ```

## Troubleshooting

### If Backend Server Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill any process using port 8000 if needed
kill -9 <PID>

# Try different port
uvicorn app.main:app --reload --port 8001
```

### If Voice Agent Worker Fails
- Check all environment variables are set correctly
- Verify API keys are valid
- Check internet connection
- Look at the error messages for specific issues

### If Flutter Can't Connect
- Make sure backend server is running on correct port
- Check Flutter console for detailed error logs
- Verify the `_baseUrl` in LiveKitVoiceService matches your backend

### Common Error Messages

#### "Failed to create room: 500"
- Backend server has configuration issues
- Check environment variables are set
- Check backend logs for errors

#### "Connection failed"
- LiveKit credentials are invalid
- Check your LiveKit server URL format
- Verify internet connection

#### "Microphone permission denied"
- Grant microphone permission in your browser/app
- Check device microphone access

## Architecture Overview

```
Flutter App → Backend API → LiveKit Room → Voice Agent
     ↓              ↓              ↓           ↓
  Mic Input → Create Room → Audio Stream → STT + LLM + TTS
```

## Next Steps After Setup

1. **Test with real speech**: Speak into your microphone and verify transcription appears
2. **Check AI responses**: Verify the AI responds to your speech
3. **Monitor logs**: Watch both backend and voice agent logs for any issues
4. **Production deployment**: Consider hosting options for your LiveKit server

## Cost Estimates

- **LiveKit Cloud**: Free tier includes 5,000 participant minutes/month
- **OpenAI**: ~$0.03-0.06 per minute of conversation 
- **Cartesia**: ~$0.05-0.10 per minute of speech synthesis
- **Deepgram**: ~$0.01-0.02 per minute of transcription

**Total**: ~$0.10-0.22 per minute of voice conversation

## Support

If you're still having issues:
1. Run `python debug_voice_setup.py` and share the output
2. Check Flutter and backend logs for error messages
3. Verify all API keys are correctly set and valid
4. Make sure both backend server and voice agent worker are running 