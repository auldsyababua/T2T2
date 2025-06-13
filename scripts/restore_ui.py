#!/usr/bin/env python3
"""
Script to restore UI files from GitHub repository
"""
import os
import requests
import base64
from pathlib import Path

# GitHub repository details
OWNER = "auldsyababua"
REPO = "Telegram-Chat-History-Manager"
BRANCH = "main"

# Local UI directory
UI_DIR = Path("/Users/colinaulds/Desktop/projects/T2T2/UI")

def get_github_token():
    """Get GitHub token from environment"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN not set, using unauthenticated requests (may hit rate limits)")
    return token

def download_file(path, local_path):
    """Download a file from GitHub"""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    headers = {}
    token = get_github_token()
    if token:
        headers["Authorization"] = f"token {token}"
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    if data["type"] == "file":
        # Decode base64 content
        content = base64.b64decode(data["content"]).decode("utf-8")
        
        # Create directory if it doesn't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"✓ Downloaded: {path}")
        return True
    return False

def download_directory(path="", local_base=UI_DIR):
    """Recursively download all files from a GitHub directory"""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    headers = {}
    token = get_github_token()
    if token:
        headers["Authorization"] = f"token {token}"
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    items = response.json()
    
    for item in items:
        if item["type"] == "file":
            # Calculate local path
            local_path = local_base / item["path"]
            download_file(item["path"], local_path)
        elif item["type"] == "dir":
            # Recursively download directory
            download_directory(item["path"], local_base)

def main():
    """Main function"""
    print(f"Restoring UI files from GitHub repository: {OWNER}/{REPO}")
    print(f"Target directory: {UI_DIR}")
    print()
    
    try:
        # Download all files
        download_directory()
        
        print("\n✅ UI restoration complete!")
        print("\nNext steps:")
        print("1. cd UI")
        print("2. npm install")
        print("3. Update the API endpoint in the code to point to http://localhost:8000")
        print("4. npm run dev")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())