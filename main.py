"""
Root entry point for Railway deployment
"""
import sys
import os

print("Starting Railway app...")
print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")
print(f"Environment PORT: {os.environ.get('PORT', 'not set')}")

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check environment variables
required_env_vars = ['DATABASE_URL', 'JWT_SECRET_KEY', 'OPENAI_API_KEY']
missing_vars = []
for var in required_env_vars:
    if not os.environ.get(var):
        missing_vars.append(var)
        print(f"WARNING: Missing environment variable: {var}")

if missing_vars:
    print(f"Missing required environment variables: {missing_vars}")
    # Create a minimal app that shows the error
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {
            "error": "Missing environment variables",
            "missing": missing_vars,
            "message": "Please set these in Railway dashboard"
        }
    
    @app.get("/health")
    async def health():
        return {"status": "unhealthy", "reason": "Missing environment variables"}
else:
    try:
        print("All required environment variables present")
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
        
        # Create a minimal error app
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/")
        async def root():
            return {
                "error": "Failed to import main app",
                "details": str(e),
                "message": "Check Railway logs for full traceback"
            }

# This is what uvicorn will import
__all__ = ["app"]