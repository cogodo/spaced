#!/usr/bin/env python3
"""
Main entry point for the Spaced Learning API
This file allows the backend to be run from the repository root.
"""

import sys
import os

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Import and expose the FastAPI app
try:
    from my_agent.agent import app
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        uvicorn.run(app, host=host, port=port)
        
except ImportError as e:
    print(f"Error importing backend: {e}")
    print(f"Make sure the backend dependencies are installed and the backend directory exists.")
    sys.exit(1) 