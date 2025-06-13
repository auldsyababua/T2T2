#!/usr/bin/env python3
"""
Start the T2T2 backend server
"""
import subprocess
import sys

# Start the backend
subprocess.run([
    sys.executable, "-m", "uvicorn", 
    "main:app", 
    "--reload", 
    "--host", "0.0.0.0", 
    "--port", "8000"
], cwd="backend")