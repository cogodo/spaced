# 🎤 Voice Chat Quick Start - WORKING SOLUTION

## Prerequisites
Make sure you have set up your LiveKit credentials in `src/backend/.env`:
```
LIVEKIT_API_KEY=your-key
LIVEKIT_API_SECRET=your-secret
LIVEKIT_SERVER_URL=wss://your-project.livekit.cloud
OPENAI_API_KEY=your-openai-key
CARTESIA_API_KEY=your-cartesia-key
DEEPGRAM_API_KEY=your-deepgram-key
```

## Start Voice Services

### 1. Start the Voice Agent Worker (Required!)
Open a terminal and run:
```bash
cd src/backend
LIVEKIT_SERVER_URL=wss://spaced-3zrvc2b8.livekit.cloud LIVEKIT_API_KEY=APIzCnE2dZJx2EL LIVEKIT_API_SECRET=gljyQPehxHDcu6raQVtxRWQSmJMsoWWZyDEuQDHV53b python voice_agent_worker.py
```

You should see:
```
🚀 Starting LiveKit Voice Agent Worker
✅ All required environment variables are set
🎧 Voice agent worker is now listening for rooms...
✨ Ready to handle voice interactions!
Set LIVEKIT_URL to: wss://spaced-3zrvc2b8.livekit.cloud
starting worker
```

Keep this running in the background.

### 2. Backend Server
Your backend should already be running on port 8000. If not:
```bash
cd src/backend
uvicorn app.main:app --reload
```

### 3. Flutter App
```bash
cd flutter_app
flutter run -d chrome
```

## Testing Voice Chat

1. **Start a chat session** - Click "New Items" or select a topic
2. **Look for the microphone button** - Bottom right corner (floating button)
3. **Click the mic button** - You'll see it connecting
4. **Allow microphone access** - Browser will prompt for permission
5. **Start speaking** - The button will pulse when detecting speech
6. **Your speech is transcribed** - Text appears in the chat
7. **AI responds with voice** - You'll hear the response

## ✅ SOLUTIONS IMPLEMENTED

### Fixed Issues:
- ❌ ~~CLI interface taking over~~ → ✅ **Bypassed CLI system**
- ❌ ~~Worker constructor errors~~ → ✅ **Fixed parameter passing**
- ❌ ~~Missing turn detector models~~ → ✅ **Disabled turn detection**
- ❌ ~~Environment variables not loading~~ → ✅ **Explicit variable setting**
- ❌ ~~localhost:7880 connection~~ → ✅ **Now connecting to LiveKit Cloud**

### What Was Wrong:
1. **LiveKit Agents CLI Override**: The framework was hijacking script execution
2. **API Parameter Mismatch**: Worker constructor expects only WorkerOptions
3. **Environment Variable Scope**: Variables weren't visible to the Worker process
4. **Model Dependencies**: Turn detector required downloaded models

## Troubleshooting

### No Audio/Voice Not Working?
1. **Check voice agent is running** - Look for "starting worker" message
2. **Check browser console** (F12) - Look for `[LiveKitVoiceService]` logs
3. **Verify microphone permissions** - Check browser address bar
4. **Test room creation**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/voice/create-room \
   -H "Content-Type: application/json" \
   -d '{"user_id": "test", "topic": "Test"}'
   ```

### Common Issues:
- **"Connection failed"** - Voice agent worker not running properly
- **No microphone button** - Not in an active chat session
- **No audio output** - Click anywhere on the page first (browser requirement)

## Architecture
```
User speaks → LiveKit Cloud → Voice Agent → STT → LLM → TTS → User hears response
```

The voice agent worker now properly connects to your LiveKit Cloud server and automatically handles all voice rooms. 