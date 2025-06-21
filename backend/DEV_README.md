# Backend Development Setup

## Quick Start

```bash
# 1. Setup environment
cp env.example .env
# Edit .env with your actual API keys

# 2. Start Redis
docker-compose -f docker-compose.redis.yml up -d

# 3. Start backend
python dev.py
```

Your API will be available at:
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Environment Configuration

### ✅ CORS Setup
CORS is pre-configured for common development scenarios:
- `localhost:3000` (Flutter dev server)
- `localhost:8080` (alternative Flutter port)
- `127.0.0.1:*` (localhost alternative)
- `10.0.2.2:*` (Android emulator host)

If you need additional origins, edit `CORS_ORIGINS` in your `.env`:
```env
CORS_ORIGINS=["http://localhost:3000","http://your-custom-port:8080"]
```

### ✅ SSL/HTTPS
**Local Development**: HTTP only (no SSL needed)
- Backend runs on `http://localhost:8000`
- No certificate configuration required
- Flutter can connect directly to HTTP endpoints

**Production**: HTTPS handled by Render deployment
- Render automatically provides SSL certificates
- Your production app uses `https://spaced-1.onrender.com`

### ✅ Logging & Debug
Development logging is optimized for debugging:
- **Log Level**: `DEBUG` (see all requests/responses)
- **Access Logs**: Enabled (all HTTP requests logged)
- **Request Bodies**: Not logged (for security)
- **Auto-reload**: Enabled (restart on code changes)

To see even more detail:
```bash
# Start with extra verbose logging
uvicorn main:app --reload --log-level debug --access-log
```

### ✅ Environment Parity
Your local environment mirrors production:
- Same FastAPI app structure
- Same Redis for session management
- Same Firebase configuration
- Same OpenAI API integration
- Same logging format

## Development Workflow

### 1. Daily Development
```bash
# Start Redis (once per day)
docker-compose -f docker-compose.redis.yml up -d

# Start backend (with auto-reload)
python dev.py

# Your code changes will auto-restart the server
```

### 2. Testing API Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Test chat endpoint (with auth)
curl -X POST http://localhost:8000/api/v1/chat/start_session \
  -H "Authorization: Bearer your_firebase_token" \
  -H "Content-Type: application/json" \
  -d '{"topics": ["Python"], "session_type": "custom_topics"}'
```

### 3. Flutter Integration
Your Flutter app should connect to:
```dart
const String backendUrl = 'http://localhost:8000';
```

Common Flutter dev scenarios:
- **Flutter Web**: `localhost:3000` → `localhost:8000` ✅
- **Flutter Mobile (iOS Simulator)**: `localhost:8000` ✅
- **Flutter Mobile (Android Emulator)**: `10.0.2.2:8000` ✅

## Troubleshooting

### CORS Issues
```bash
# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS http://localhost:8000/api/v1/chat/start_session
```

Should return CORS headers. If not, check your `CORS_ORIGINS` in `.env`.

### Redis Connection Issues
```bash
# Check if Redis is running
docker ps | grep redis

# Test Redis connection
docker exec spaced_redis_dev redis-cli ping
# Should return: PONG

# Check Redis logs
docker logs spaced_redis_dev
```

### Backend Issues
```bash
# Check backend logs (verbose)
python dev.py  # Look for ERROR messages

# Test backend health
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# Check environment variables
python -c "from app.config import settings; print(settings.redis_url)"
```

### Network Debugging
```bash
# Check what's listening on port 8000
lsof -i :8000

# Check if backend is accessible from network
curl -v http://localhost:8000/health

# For Flutter web dev server on different port
curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

## Development Tips

### Hot Reload
- Backend auto-reloads on `.py` file changes
- Config changes in `.env` require manual restart
- Database schema changes may need Redis restart

### Performance
- Redis runs in Docker for consistency
- Backend runs natively for speed
- Use `DEBUG=true` for development, `false` for performance testing

### Debugging
- FastAPI automatic docs: http://localhost:8000/docs
- Interactive API testing available in docs
- All requests logged with `LOG_LEVEL=DEBUG`
- Use VS Code debugger with launch configuration

### Testing
```bash
# Run backend tests
pytest tests/

# Test with curl
curl -X POST http://localhost:8000/api/v1/chat/start_session \
  -H "Content-Type: application/json" \
  -d '{"topics": ["Test Topic"]}'
```

## Production Parity Checklist

✅ **Redis**: Same version (7-alpine)  
✅ **Python**: Same version (3.11)  
✅ **Environment Variables**: Same structure  
✅ **Logging**: Same format (structured JSON)  
✅ **API Structure**: Identical endpoints  
✅ **Authentication**: Same Firebase integration  
✅ **CORS**: Production uses specific origins  

## Files Overview

- `dev.py` - Development server script
- `env.example` - Environment template
- `docker-compose.redis.yml` - Redis for development
- `main.py` - FastAPI application
- `app/config.py` - Configuration management 