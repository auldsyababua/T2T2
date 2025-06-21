#!/usr/bin/env python3
"""Verify Supabase API key format and completeness"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv(".env.supabase_bot")

key = os.getenv("SUPABASE_SERVICE_KEY", "")

print("🔍 Supabase API Key Verification")
print("=" * 50)

print("\n1. Key Analysis:")
print(f"   Length: {len(key)} characters")
print(f"   Prefix: {key[:15] if key else 'N/A'}...")
print(f"   Last 4: ...{key[-4:] if len(key) > 4 else 'N/A'}")

# Check key format
if key.startswith("sb_secret_"):
    print("   ✅ Has correct prefix (sb_secret_)")

    # Typical sb_secret_ keys are around 223 characters
    if len(key) < 100:
        print(f"   ❌ Key appears incomplete (expected ~223 chars, got {len(key)})")
        print("   ⚠️  The key may have been truncated during copy/paste")
    else:
        print("   ✅ Key length seems reasonable")

elif key.startswith("eyJ"):
    print("   ⚠️  Legacy JWT format detected")
    print("   ℹ️  You may need to generate new API keys in Supabase dashboard")
else:
    print("   ❌ Unknown key format")

print("\n2. Recommendations:")
if len(key) < 100:
    print("   1. Go to your Supabase dashboard")
    print("   2. Navigate to Settings > API")
    print("   3. Under 'Secret keys', copy the full secret key")
    print("   4. Make sure to copy the ENTIRE key (it should be ~223 characters)")
    print("   5. Update the SUPABASE_SERVICE_KEY in .env.supabase_bot")
    print("\n   The key should look like:")
    print("   sb_secret_[long string of characters, about 200+ chars total]")
