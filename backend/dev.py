#!/usr/bin/env python3
"""
Development server script for local backend development.
Starts the FastAPI app with optimal settings for development.
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def main():
    """Start the development server with optimal settings."""
    
    # Check if .env exists
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("❌ No .env file found!")
        print("📝 Please copy env.example to .env and configure your settings:")
        print(f"   cp {backend_dir}/env.example {backend_dir}/.env")
        print("   # Then edit .env with your actual API keys")
        sys.exit(1)
    
    print("🚀 Starting Spaced Learning Backend (Development Mode)")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print("🔄 Auto-reload enabled - code changes will restart the server")
    print("🗃️  Make sure Redis is running: docker-compose -f docker-compose.redis.yml up -d")
    print("=" * 60)
    
    # Start the server with development-optimized settings
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Accept connections from any interface
        port=8000,
        reload=True,     # Auto-reload on code changes
        log_level="debug",  # Verbose logging for development
        access_log=True,    # Log all requests
        reload_dirs=[str(backend_dir)],  # Only watch backend directory
        reload_excludes=[
            "*.pyc", "__pycache__", ".env", "*.log", 
            ".git", ".pytest_cache", "htmlcov"
        ]
    )

if __name__ == "__main__":
    main() 