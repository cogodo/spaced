# Docker Setup for Spaced Repetition Learning App

This project uses Docker Compose to orchestrate multiple services for development and production.

## Architecture

- **Backend**: Python FastAPI application
- **Redis**: Session management and caching
- **Flutter**: Web frontend (development and production builds)
- **Nginx**: Reverse proxy for production

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose installed
- Choose the appropriate environment configuration:
  - **Docker development**: `cp env.docker.example .env`
  - **Local development**: `cp env.local.example .env`
  - **Production**: `cp env.production.example .env`
- Add your actual API keys and configuration to `.env`

### 2. Development Mode
```bash
# Start backend and Redis (uses Docker Redis)
docker-compose up backend redis

# Or start everything including Flutter dev server
docker-compose --profile dev up
```

### 3. Local Development (outside Docker)
```bash
# Start only Redis in Docker
docker-compose up redis

# Run backend locally (needs local Python environment)
cd backend && python -m uvicorn main:app --reload
```

### 4. Production Mode
```bash
# Build Flutter app
docker-compose --profile build run flutter-build

# Start production services
docker-compose --profile prod up
```

## Available Commands

### Development
```bash
# Start backend + Redis only
docker-compose up backend redis

# Start with Flutter development server
docker-compose --profile dev up

# View logs
docker-compose logs -f backend

# Rebuild services
docker-compose build backend
```

### Production
```bash
# Build Flutter production app
docker-compose --profile build run flutter-build

# Start production stack with Nginx
docker-compose --profile prod up -d

# Scale backend (if needed)
docker-compose --profile prod up -d --scale backend=3
```

### Maintenance
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (careful - loses Redis data!)
docker-compose down -v

# View service status
docker-compose ps

# Execute commands in running containers
docker-compose exec backend bash
docker-compose exec redis redis-cli
```

## Service URLs

- **Backend API**: http://localhost:8000
- **Backend Docs**: http://localhost:8000/docs
- **Flutter Dev**: http://localhost:3000 (dev profile only)
- **Production**: http://localhost:80 (prod profile only)
- **Redis**: localhost:6379

## Environment Variables

### Redis Configuration

The Redis URL changes depending on your deployment scenario:

```env
# Docker Compose (backend and Redis both in Docker)
REDIS_URL=redis://redis:6379

# Local development (backend local, Redis in Docker)
REDIS_URL=redis://localhost:6379

# Production (Render managed Redis)
REDIS_URL=rediss://red-xxxxx:xxxxx@oregon-redis.render.com:6380
```

### Required Variables

All environments need these variables in `.env`:

```env
OPENAI_API_KEY=your_key_here
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_SERVICE_ACCOUNT_JSON={"your":"json_config"}
REDIS_URL=redis://redis:6379  # or appropriate Redis URL
ENVIRONMENT=development  # or production
LOG_LEVEL=INFO
```

### Environment Files

Use the appropriate template:
- `env.docker.example` → Full Docker development
- `env.local.example` → Local backend with Docker Redis
- `env.production.example` → Production deployment

## Profiles

Docker Compose uses profiles to manage different environments:

- **Default**: Backend + Redis (minimum for API development)
- **dev**: Adds Flutter development server
- **prod**: Adds Nginx reverse proxy
- **build**: Flutter production build service

## Troubleshooting

### Backend Issues
```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Rebuild if dependencies changed
docker-compose build backend
```

### Redis Issues
```bash
# Check Redis connectivity
docker-compose exec redis redis-cli ping

# View Redis logs
docker-compose logs redis
```

### Flutter Issues
```bash
# Rebuild Flutter containers
docker-compose build flutter-dev flutter-build

# Clear Flutter cache
docker volume rm spaced_flutter_pub_cache
```

### Network Issues
```bash
# Check container network
docker network ls
docker network inspect spaced_spaced_network
```

## Development Workflows

### 1. Full Docker Development
**Best for**: Complete isolation, team consistency
```bash
cp env.docker.example .env
docker-compose --profile dev up
```
- Backend runs in Docker with hot reload
- Redis runs in Docker
- Flutter dev server runs in Docker
- Everything isolated and consistent

### 2. Hybrid Development (Recommended)
**Best for**: Backend development with faster iteration
```bash
cp env.local.example .env
# Start only Redis in Docker
docker-compose up redis

# Run backend locally for faster development
cd backend && python -m uvicorn main:app --reload

# Run Flutter locally for faster hot reload
cd flutter_app && flutter run -d web-server --web-port 3000
```
- Redis runs in Docker (consistent, no setup)
- Backend runs locally (faster restart, easier debugging)
- Flutter runs locally (faster hot reload)

### 3. Production Testing
**Best for**: Testing production builds
```bash
cp env.production.example .env
# Edit .env with actual production Redis URL

docker-compose --profile build run flutter-build
docker-compose --profile prod up
```

## Common Development Patterns

### Pattern 1: Backend Development
```bash
# Start Redis only
docker-compose up redis

# Develop backend locally
cd backend && python -m uvicorn main:app --reload
```

### Pattern 2: Full Stack Development
```bash
# Start all services for development
cp env.docker.example .env
docker-compose --profile dev up
```

### Pattern 3: Production Simulation
```bash
# Test production build locally
docker-compose --profile build run flutter-build
docker-compose --profile prod up
```

## Production Deployment

For production deployment:

1. Set production environment variables
2. Build Flutter app: `docker-compose --profile build run flutter-build`
3. Start production stack: `docker-compose --profile prod up -d`
4. Configure SSL certificates in `nginx/ssl/`
5. Update domain names in nginx configuration

## File Structure

```
├── docker-compose.yml          # Main orchestration file
├── backend/
│   ├── Dockerfile             # Backend container definition
│   └── ...
├── flutter_app/
│   ├── Dockerfile.dev         # Flutter development
│   ├── Dockerfile.build       # Flutter production build
│   └── ...
├── nginx/
│   └── nginx.conf            # Nginx configuration
└── env.example               # Environment variables template
```

## Benefits

- **Consistent Environment**: Same setup for all developers
- **Easy Onboarding**: New developers run one command
- **Production Parity**: Development matches production
- **Isolated Services**: Each service runs independently
- **Scalable**: Easy to scale individual services
- **Health Checks**: Built-in service monitoring 