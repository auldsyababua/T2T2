#!/usr/bin/env python3
"""
Test using the JWT-based service_role key instead of sb_secret_
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv('.env.supabase_bot')

url = os.getenv("SUPABASE_URL", "")

print("🔍 Finding the correct API key to use")
print("=" * 50)

print("\nCurrent situation:")
print("1. You have a new sb_secret_ key (41 chars) in API Keys section")
print("2. But the Python client expects the old JWT format (starts with 'eyJ')")
print("3. You need to find the service_role key in JWT format")

print("\n📋 Where to find the JWT service_role key:")
print("1. Go to Supabase Dashboard")
print("2. Go to Settings -> API (not Configuration -> Data API)")
print("3. Look for 'Project API keys' section")
print("4. Find the 'service_role' key (should start with 'eyJ')")
print("5. This key should be much longer (200+ characters)")

print("\n⚠️  Important:")
print("- Don't use the JWT Secret from Configuration -> Data API")
print("- That's for signing JWTs, not for API access")
print("- You need the service_role key from Settings -> API")

print("\nOnce you have the correct key, update SUPABASE_SERVICE_KEY in .env.supabase_bot")