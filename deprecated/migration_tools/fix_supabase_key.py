#!/usr/bin/env python3
"""
Fix Supabase API key issue - guide to using the correct key
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

print("🔧 Supabase API Key Fix")
print("=" * 50)

print("\n❌ Problem: The Python client doesn't support the new sb_secret_ format yet")
print("✅ Solution: Use the JWT-based service_role key instead")

print("\n📍 Step-by-step instructions:")
print("\n1. Go to your Supabase Dashboard")
print("2. Navigate to: Settings → API Keys (NOT Configuration → Data API)")
print("3. Find the 'service_role' key in the 'Project API keys' section")
print("   - It should start with 'eyJ'")
print("   - It should be 200+ characters long")
print("   - Click 'Reveal' to see the full key")
print("4. Copy the ENTIRE key")

response = input("\nHave you copied the service_role key? (y/n): ")
if response.lower() != "y":
    print("Please follow the steps above and run this script again.")
    sys.exit(0)

print("\nPaste the service_role key here (it will be hidden):")
import getpass

new_key = getpass.getpass("Key: ").strip()

# Validate the key
if not new_key.startswith("eyJ"):
    print("❌ Error: The key should start with 'eyJ'")
    print("Make sure you're copying the service_role key, not the JWT Secret")
    sys.exit(1)

if len(new_key) < 200:
    print(f"❌ Error: The key seems too short ({len(new_key)} chars)")
    print("Make sure you copied the entire key")
    sys.exit(1)

print("\n✅ Key validation passed!")
print("   - Format: JWT (starts with 'eyJ')")
print(f"   - Length: {len(new_key)} characters")

# Update the .env file
env_file = Path(".env.supabase_bot")
if env_file.exists():
    # Read the file
    lines = env_file.read_text().splitlines()

    # Update the SUPABASE_SERVICE_KEY line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("SUPABASE_SERVICE_KEY="):
            lines[i] = f"SUPABASE_SERVICE_KEY={new_key}"
            updated = True
            break

    if updated:
        # Write back
        env_file.write_text("\n".join(lines) + "\n")
        print("\n✅ Updated SUPABASE_SERVICE_KEY in .env.supabase_bot")

        # Test the connection
        print("\nTesting connection...")
        load_dotenv(".env.supabase_bot", override=True)

        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_KEY", "")

        try:
            client = create_client(url, key)
            # Try a simple query
            result = client.table("documents").select("id").limit(1).execute()
            print("✅ Connection successful!")
        except Exception as e:
            if "does not exist" in str(e):
                print(
                    "✅ Connection successful! (Table doesn't exist yet, which is expected)"
                )
            else:
                print(f"❌ Connection failed: {e}")
    else:
        print("❌ Could not find SUPABASE_SERVICE_KEY in .env.supabase_bot")
else:
    print("❌ .env.supabase_bot file not found")
