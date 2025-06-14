"""
Root entry point for Railway deployment
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the FastAPI app from backend
    from backend.main import app
    print("Successfully imported FastAPI app")
except Exception as e:
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()
    raise

# This is what uvicorn will import
__all__ = ["app"]