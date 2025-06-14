"""
Root entry point for Railway deployment
"""
import sys
import os

print("Starting Railway app...")
print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Attempting to import backend.main...")
    # Import the FastAPI app from backend
    from backend.main import app
    print("Successfully imported FastAPI app")
except Exception as e:
    print(f"Error importing app: {e}")
    import traceback
    traceback.print_exc()
    # Check if backend directory exists
    if os.path.exists('backend'):
        print(f"Backend directory contents: {os.listdir('backend')}")
    raise

# This is what uvicorn will import
__all__ = ["app"]