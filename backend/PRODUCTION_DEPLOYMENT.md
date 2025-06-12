# 🚀 Production Deployment Guide

## 📋 Current Setup
- **Local Development**: Uses `firebase-service-account.json` file
- **Production**: Must use environment variables for security

## 🔧 Render Deployment

### 1. **Firebase Configuration**
**⚠️ IMPORTANT**: Before deploying to production, switch from file-based to environment variable-based Firebase credentials.

#### Steps for Render:
1. **Get your Firebase service account JSON content** (the entire file content)
2. **In Render Dashboard**:
   - Go to your service settings
   - Navigate to **"Environment"** tab
   - Add environment variable:
     - **Key**: `FIREBASE_SERVICE_ACCOUNT_JSON`
     - **Value**: Paste the entire JSON content (as a single line string)

#### Example:
```
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://token.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
```

### 2. **Other Environment Variables for Render**
Set these in your Render environment:

```bash
# Required
FIREBASE_SERVICE_ACCOUNT_JSON=<your-firebase-json>
OPENAI_API_KEY=<your-openai-key>

# Optional (with defaults)
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=https://getspaced.app,https://www.getspaced.app,http://localhost:3000
```

### 3. **Build & Deploy Settings**
In your `render.yaml` or Render dashboard:

```yaml
services:
  - type: web
    name: spaced-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python my_agent/agent.py
    envVars:
      - key: FIREBASE_SERVICE_ACCOUNT_JSON
        value: <your-firebase-json>
      - key: OPENAI_API_KEY
        value: <your-openai-key>
```

## 🔒 Security Best Practices

### ✅ Do:
- Use environment variables for all sensitive data in production
- Keep service account files in `.gitignore`
- Use Render's secret management for environment variables
- Rotate service account keys periodically

### ❌ Don't:
- Commit `firebase-service-account.json` to git
- Put credentials in code or config files
- Use the same credentials for dev and prod
- Share service account keys in plain text

## 🧪 Testing Deployment

### Local Testing with Production Config:
```bash
# Test with environment variable locally
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
unset FIREBASE_SERVICE_ACCOUNT_PATH  # Disable file-based auth
python my_agent/agent.py
```

### Verify Firebase Connection:
```bash
curl https://your-app.onrender.com/health
# Should return: {"status": "healthy", "sessions_count": 0}
```

## 📝 TODO for Production Migration

- [ ] Copy Firebase service account JSON content
- [ ] Set `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable in Render
- [ ] Test deployment with environment variable auth
- [ ] Remove local `firebase-service-account.json` dependency
- [ ] Update CI/CD pipeline if applicable
- [ ] Set up monitoring and logging
- [ ] Configure error tracking (Sentry, etc.)

## 🆘 Troubleshooting

### Common Issues:

1. **"Default credentials not found"**
   - Solution: Set `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable

2. **"Invalid JSON in service account"**
   - Solution: Ensure JSON is properly escaped as single line string

3. **"Permission denied" errors**
   - Solution: Verify service account has proper Firebase roles

4. **CORS errors**
   - Solution: Update `CORS_ORIGINS` environment variable with your domain

### Debug Commands:
```bash
# Check environment variables (in production)
echo $FIREBASE_SERVICE_ACCOUNT_JSON | jq .project_id

# Test API endpoints
curl -X POST https://your-app.onrender.com/start_session \
  -H "Content-Type: application/json" \
  -d '{"session_type": "custom_topics", "topics": ["test"]}'
``` 