#!/usr/bin/env python3
"""
Start both T2T2 services:
1. The Telegram bot (t2t2_chat_indexer.py)
2. The authentication web server (t2t2_qr_auth.py)
"""

import subprocess
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor
import signal

processes = []

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    print("\n🛑 Shutting down services...")
    for p in processes:
        try:
            p.terminate()
        except:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_service(script_name):
    """Run a Python script and capture output"""
    print(f"🚀 Starting {script_name}...")
    try:
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        processes.append(process)
        
        # Stream output
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[{script_name}] {line.rstrip()}")
                
        process.wait()
        return f"{script_name} exited with code {process.returncode}"
    except Exception as e:
        return f"{script_name} error: {str(e)}"

if __name__ == "__main__":
    print("🤖 T2T2 Service Manager")
    print("=" * 50)
    
    # Check if running on Railway
    if os.getenv("RAILWAY_ENVIRONMENT"):
        print("📍 Running on Railway")
    else:
        print("📍 Running locally")
    
    print("\nStarting services...")
    print("1. Telegram Bot (t2t2_chat_indexer.py)")
    print("2. Auth Web Server (t2t2_qr_auth.py)")
    print("=" * 50)
    
    # Run both services concurrently
    with ThreadPoolExecutor(max_workers=2) as executor:
        bot_future = executor.submit(run_service, "t2t2_chat_indexer.py")
        web_future = executor.submit(run_service, "t2t2_qr_auth.py")
        
        # Wait for both to complete (they shouldn't unless there's an error)
        try:
            while True:
                time.sleep(1)
                if bot_future.done() or web_future.done():
                    print("\n⚠️ One of the services stopped unexpectedly!")
                    if bot_future.done():
                        print(f"Bot result: {bot_future.result()}")
                    if web_future.done():
                        print(f"Web result: {web_future.result()}")
                    break
        except KeyboardInterrupt:
            signal_handler(None, None)