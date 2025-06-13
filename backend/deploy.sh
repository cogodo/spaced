#!/bin/bash

# Spaced Learning API Deployment Script
# Usage: ./deploy.sh [platform] [environment]
# Platforms: docker, cloud-run, railway, heroku, digitalocean
# Environments: dev, staging, prod

set -e

PLATFORM=${1:-docker}
ENVIRONMENT=${2:-dev}

echo "🚀 Deploying Spaced Learning API with LangGraph"
echo "Platform: $PLATFORM"
echo "Environment: $ENVIRONMENT"
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

case $PLATFORM in
    "docker")
        echo "📦 Building and running with Docker..."
        docker-compose down 2>/dev/null || true
        docker-compose build --no-cache
        docker-compose up -d
        echo "✅ API running at http://localhost:8000"
        echo "🔍 Health check: curl http://localhost:8000/health"
        ;;
        
    "cloud-run")
        echo "☁️ Deploying to Google Cloud Run..."
        
        # Build and push to Container Registry
        PROJECT_ID=${GOOGLE_CLOUD_PROJECT_ID:-"your-project-id"}
        IMAGE_NAME="gcr.io/$PROJECT_ID/spaced-api"
        
        echo "Building container image..."
        docker build -t $IMAGE_NAME .
        docker push $IMAGE_NAME
        
        echo "Deploying to Cloud Run..."
        gcloud run deploy spaced-api \
            --image $IMAGE_NAME \
            --region us-central1 \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY,ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" \
            --memory 1Gi \
            --cpu 1 \
            --max-instances 10
        
        echo "✅ Deployed to Cloud Run!"
        ;;
        
    "railway")
        echo "🚂 Deploying to Railway..."
        
        # Install Railway CLI if not present
        if ! command -v railway &> /dev/null; then
            echo "Installing Railway CLI..."
            npm install -g @railway/cli
        fi
        
        echo "Deploying to Railway..."
        railway login
        railway up --detach
        
        echo "✅ Deployed to Railway!"
        ;;
        
    "render")
        echo "🎨 Setting up for Render deployment..."
        
        # Create render.yaml if it doesn't exist
        if [ ! -f render.yaml ]; then
            cat > render.yaml << EOF
services:
  - type: web
    name: spaced-api
    env: python
    buildCommand: pip install -r requirements-production.txt
    startCommand: uvicorn my_agent.agent:app --host 0.0.0.0 --port \$PORT
    envVars:
      - key: OPENAI_API_KEY
        fromService: spaced-api
        value: \$OPENAI_API_KEY
      - key: ANTHROPIC_API_KEY  
        fromService: spaced-api
        value: \$ANTHROPIC_API_KEY
      - key: FIREBASE_ADMIN_CREDENTIALS
        fromService: spaced-api
        value: \$FIREBASE_ADMIN_CREDENTIALS
EOF
        fi
        
        echo "✅ Render configuration created. Connect your GitHub repo to Render."
        echo "📝 Use render.yaml for automatic deployment."
        ;;
        
    "heroku")
        echo "📱 Deploying to Heroku..."
        
        # Create Procfile if it doesn't exist
        if [ ! -f Procfile ]; then
            echo "web: uvicorn my_agent.agent:app --host 0.0.0.0 --port \$PORT" > Procfile
        fi
        
        # Create runtime.txt
        echo "python-3.11.6" > runtime.txt
        
        # Deploy
        git add .
        git commit -m "Deploy LangGraph API to Heroku" || true
        
        heroku create spaced-learning-api-$(date +%s) || true
        heroku config:set OPENAI_API_KEY="$OPENAI_API_KEY"
        heroku config:set ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
        heroku config:set FIREBASE_ADMIN_CREDENTIALS="$FIREBASE_ADMIN_CREDENTIALS"
        
        git push heroku main
        
        echo "✅ Deployed to Heroku!"
        ;;
        
    *)
        echo "❌ Unknown platform: $PLATFORM"
        echo "Available platforms: docker, cloud-run, railway, render, heroku"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test the health endpoint: GET /health"
echo "2. Test session creation: POST /start_session"
echo "3. Update your Flutter app to use the new URL"
echo "4. Configure environment variables if deploying to cloud"
echo ""
echo "🔗 API Endpoints:"
echo "  - Health: GET /health"
echo "  - Start Session: POST /start_session"
echo "  - Answer Question: POST /answer"
echo "  - Due Tasks: GET /due_tasks/{user_id}"
echo "  - Dashboard: GET /dashboard/{user_id}" 