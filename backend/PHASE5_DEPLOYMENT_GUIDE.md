# 🚀 Phase 5 Deployment Guide

## ✅ Pre-Deployment Checklist

### 1. **Firebase Credentials Setup**
Your code is already ready! The Firebase service supports both methods:

**For Local Development (.env):**
```bash
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
```

**For Staging/Production (.env):**
```bash
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"spaced-b571d","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://token.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
```

### 2. **Environment Variables for Staging**
Update your `.env` file with these variables:

```bash
# Firebase (choose one method)
FIREBASE_SERVICE_ACCOUNT_JSON=your-firebase-json-string
# OR
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json

# OpenAI (optional for enhanced features)
OPENAI_API_KEY=your-openai-api-key

# Server Configuration
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=https://getspaced.app,https://www.getspaced.app,http://localhost:3000,http://localhost:8080
```

### 3. **Phase 5 Features Verification**
✅ All Phase 5 tests passed - no additional setup required!

## 🔧 Deployment Steps

### **Option A: Render Deployment**

1. **Environment Variables in Render:**
   - Go to your Render service dashboard
   - Add these environment variables:
   ```
   FIREBASE_SERVICE_ACCOUNT_JSON=<your-complete-json-string>
   OPENAI_API_KEY=<your-openai-key>
   PORT=8000
   HOST=0.0.0.0
   CORS_ORIGINS=https://getspaced.app,https://www.getspaced.app
   ```

2. **Deploy Command:**
   ```bash
   git add .
   git commit -m "Deploy Phase 5: Advanced Learning Features"
   git push origin main
   ```

### **Option B: Local Testing with Production Config**

1. **Update your .env with JSON string:**
   ```bash
   # Remove or comment out the file path
   # FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
   
   # Add the JSON string
   FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
   ```

2. **Test locally:**
   ```bash
   python my_agent/agent.py
   # In another terminal:
   python test_api_phase5.py
   ```

## 🆕 Phase 5 New Endpoints

Your staging deployment will include these new advanced features:

### **New API Endpoints:**
- `POST /optimize_session` - Personalized session optimization
- `GET /session_analytics/{session_id}` - Real-time session insights

### **Enhanced Existing Endpoints:**
- `POST /start_session` - Now supports adaptive features
- `POST /complete_session` - Now includes advanced analytics

### **Sample Usage:**

```bash
# Optimize session for user
curl -X POST "https://your-app.onrender.com/optimize_session?user_id=test-user&session_type=custom_topics"

# Get real-time analytics
curl "https://your-app.onrender.com/session_analytics/session-id-here"

# Start adaptive session
curl -X POST "https://your-app.onrender.com/start_session" \
  -H "Content-Type: application/json" \
  -d '{
    "session_type": "custom_topics",
    "topics": ["python", "machine learning"],
    "adaptive_session_length": true,
    "performance_threshold": 4.5,
    "struggle_threshold": 2.0
  }'
```

## 🧪 Testing Phase 5 in Staging

### **Health Check:**
```bash
curl https://your-staging-url.onrender.com/health
# Expected: {"status": "healthy", "sessions_count": 0}
```

### **Phase 5 Feature Test:**
```bash
# Test session optimization
curl -X POST "https://your-staging-url.onrender.com/optimize_session?user_id=test&session_type=custom_topics"

# Should return optimized settings based on user performance
```

### **Firebase Connection Test:**
```bash
curl "https://your-staging-url.onrender.com/due_tasks/test-user-id"
# Should return due tasks or "no tasks" message
```

## 🎯 Phase 5 Features Live in Staging

Once deployed, your staging environment will have:

### **🧠 Adaptive Learning:**
- Performance-based early completion (4.5+ average)
- Automatic session extension for struggling learners (<2.0 average)
- Personalized difficulty thresholds

### **📊 Advanced Analytics:**
- Real-time learning momentum tracking
- Answer confidence analysis
- Cross-topic connection detection
- Retention prediction algorithms

### **💡 Intelligent Recommendations:**
- Next session optimization based on performance history
- Duration estimation (10-20 minutes based on performance)
- Learning strategy suggestions
- Connected topic suggestions

### **⚡ Real-time Session Intelligence:**
- Performance monitoring during sessions
- Question difficulty progression tracking
- Adaptive scoring with difficulty bonuses
- Comprehensive session summaries

## 🚨 Troubleshooting

### **Common Issues:**

1. **"Default credentials not found"**
   - Ensure `FIREBASE_SERVICE_ACCOUNT_JSON` is set correctly
   - Verify JSON string is properly escaped

2. **"Invalid JSON in service account"**
   - Check that JSON is on a single line
   - Ensure all quotes are properly escaped

3. **Phase 5 features not working**
   - All Phase 5 features are enabled by default
   - No additional configuration required

### **Debug Commands:**
```bash
# Check Firebase connection
curl https://your-app.onrender.com/health

# Test Phase 5 optimization
curl -X POST "https://your-app.onrender.com/optimize_session?user_id=debug&session_type=custom_topics"

# Verify CORS settings
curl -H "Origin: https://getspaced.app" https://your-app.onrender.com/health
```

## ✅ Deployment Success Criteria

Your Phase 5 deployment is successful when:

- [ ] Health check returns 200 status
- [ ] Firebase authentication works
- [ ] Session optimization endpoint returns personalized settings
- [ ] Session analytics endpoint provides real-time insights
- [ ] Adaptive session length features are working
- [ ] CORS allows your frontend domain
- [ ] All Phase 5 advanced features are operational

## 🎉 Ready to Deploy!

Your Phase 5 implementation is production-ready with:
- ✅ All tests passing
- ✅ Firebase credentials configurable via environment
- ✅ Advanced adaptive learning features
- ✅ Comprehensive analytics and insights
- ✅ Intelligent session optimization
- ✅ Real-time performance tracking

**Just update your .env with the Firebase JSON string and push to staging!** 🚀 