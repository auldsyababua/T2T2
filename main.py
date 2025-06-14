"""
Root entry point for Railway deployment
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app from backend
from backend.main import app

# This is what uvicorn will import
__all__ = ["app"]