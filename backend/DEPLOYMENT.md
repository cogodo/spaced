# 🚀 Spaced Learning API Deployment Guide

This guide covers deploying your LangGraph-powered Spaced Learning API to various platforms.

## 📋 Prerequisites

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in:
   ```bash
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
   FIREBASE_ADMIN_CREDENTIALS=path/to/firebase-credentials.json
   ```

2. **Dependencies**: Install Docker (for containerized deployment)

## 🎯 Quick Start

```bash
# Make deployment script executable
chmod +x deploy.sh

# Deploy locally with Docker
./deploy.sh docker

# Deploy to cloud platforms
./deploy.sh railway    # Railway (recommended)
./deploy.sh render     # Render
./deploy.sh cloud-run  # Google Cloud Run
./deploy.sh heroku     # Heroku
```

## ☁️ Platform-Specific Instructions

### 🚂 Railway (Recommended - Easy & Fast)

Railway is the easiest platform for deploying Python apps:

1. **Setup**:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Deploy**:
   ```bash
   ./deploy.sh railway
   ```

3. **Configure Environment**:
   - Go to Railway dashboard
   - Add environment variables:
     - `OPENAI_API_KEY`
     - `ANTHROPIC_API_KEY` 
     - `FIREBASE_ADMIN_CREDENTIALS`

4. **Custom Domain** (optional):
   - Add your domain in Railway dashboard
   - Update Flutter app to use new URL

### 🎨 Render (Free Tier Available)

1. **GitHub Integration**:
   - Push your code to GitHub
   - Connect GitHub repo to Render

2. **Auto-deployment**:
   ```bash
   ./deploy.sh render  # Creates render.yaml
   ```

3. **Manual Setup**:
   - Go to render.com
   - Create new Web Service
   - Connect GitHub repo
   - Use these settings:
     - **Build Command**: `pip install -r requirements-production.txt`
     - **Start Command**: `uvicorn my_agent.agent:app --host 0.0.0.0 --port $PORT`

### ☁️ Google Cloud Run (Auto-scaling)

1. **Setup Google Cloud**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth configure-docker
   ```

2. **Deploy**:
   ```bash
   export GOOGLE_CLOUD_PROJECT_ID=your-project-id
   ./deploy.sh cloud-run
   ```

### 📱 Heroku (Classic Platform)

1. **Setup**:
   ```bash
   heroku login
   ```

2. **Deploy**:
   ```bash
   ./deploy.sh heroku
   ```

## 🔧 Manual Docker Deployment

If you prefer manual control:

```bash
# Build the image
docker build -t spaced-api .

# Run locally
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e FIREBASE_ADMIN_CREDENTIALS=$FIREBASE_ADMIN_CREDENTIALS \
  spaced-api

# Push to a registry
docker tag spaced-api your-registry/spaced-api
docker push your-registry/spaced-api
```

## 📱 Update Flutter App

Once deployed, update your Flutter app to use the new API URL:

```dart
// In your Flutter app
const String API_BASE_URL = 'https://your-api-url.railway.app';
// or https://your-api-url.onrender.com
// or https://your-api-url.run.app
```

## 🧪 Testing Your Deployment

```bash
# Health check
curl https://your-api-url/health

# Start a session
curl -X POST https://your-api-url/start_session \
  -H "Content-Type: application/json" \
  -d '{
    "session_type": "custom_topics",
    "topics": ["Machine Learning"],
    "max_topics": 1,
    "max_questions": 5
  }'
```

## 🔍 Monitoring & Debugging

### Logs
- **Railway**: View logs in Railway dashboard
- **Render**: View logs in Render dashboard  
- **Cloud Run**: `gcloud logs read`
- **Heroku**: `heroku logs --tail`

### Health Monitoring
All platforms support the health endpoint: `GET /health`

### Performance
- The API includes built-in rate limiting
- Redis caching for improved performance
- Automatic scaling on Cloud Run

## 🛠 Troubleshooting

### Common Issues

1. **Import Errors**: 
   - Use `requirements-production.txt` instead of `requirements.txt`
   - This has tested, compatible versions

2. **Firebase Credentials**:
   - For cloud deployment, use environment variable with JSON string
   - For local, use file path

3. **CORS Issues**:
   - Update `CORS_ORIGINS` environment variable
   - Include your frontend domain

4. **Memory Issues**:
   - LangGraph can be memory-intensive
   - Use at least 1GB RAM (most platforms provide this)

### Environment Variables

Essential variables for production:

```bash
OPENAI_API_KEY=sk-...           # Required for LangGraph
FIREBASE_ADMIN_CREDENTIALS={}   # Required for user data
CORS_ORIGINS=https://your-app   # Required for frontend
PORT=8000                       # Platform will set this
```

## 🎉 Success!

Your LangGraph-powered Spaced Learning API is now live! The system includes:

- ✅ **Adaptive Intelligence**: Real-time difficulty adjustment
- ✅ **Question Generation**: Auto-creates questions for custom topics  
- ✅ **State Persistence**: Firebase integration
- ✅ **Rate Limiting**: Production-ready API protection
- ✅ **Auto-scaling**: Handles traffic spikes
- ✅ **Health Monitoring**: Built-in status endpoints

## 📞 Support

If you encounter issues:

1. Check the logs on your deployment platform
2. Verify environment variables are set correctly
3. Test the health endpoint
4. Ensure Firebase credentials are valid

The API is designed to be production-ready with proper error handling and graceful fallbacks. 