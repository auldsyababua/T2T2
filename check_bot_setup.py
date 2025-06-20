#!/usr/bin/env python3
"""Check if bot is properly set up"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv(".env.supabase_bot")

print("🔍 Checking T2T2 Team Bot Setup...")
print("=" * 50)

# Check environment variables
checks = {
    "TELEGRAM_API_ID": os.getenv("TELEGRAM_API_ID"),
    "TELEGRAM_API_HASH": os.getenv("TELEGRAM_API_HASH"),
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY"),
    "ADMIN_TELEGRAM_ID": os.getenv("ADMIN_TELEGRAM_ID"),
}

all_good = True
for key, value in checks.items():
    if value and value != "your_service_key_here":
        print(f"✅ {key}: {'*' * 10} (set)")
    else:
        print(f"❌ {key}: Missing!")
        all_good = False

if not all_good:
    print("\n❌ Missing required environment variables!")
    sys.exit(1)

# Check Supabase connection
print("\n🔗 Checking Supabase connection...")
try:
    supabase = create_client(
        os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
    )

    # Try to query documents table
    result = supabase.table("documents").select("id").limit(1).execute()
    print("✅ Supabase connected and documents table exists!")

except Exception as e:
    if "documents" in str(e):
        print("❌ Documents table not found!")
        print("\nTo fix this:")
        print(
            "1. Go to: https://supabase.com/dashboard/project/tzsfkbwpgklwvsyypacc/sql/new"
        )
        print("2. Copy and run the SQL from: supabase_setup.sql")
    else:
        print(f"❌ Supabase error: {e}")

print("\n📱 Admin Setup:")
print(f"Admin Telegram ID: {os.getenv('ADMIN_TELEGRAM_ID')} (@Colin_10NetZero)")

print("\n🤖 Bot Info:")
bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
if bot_token:
    bot_username = bot_token.split(":")[0]
    print(f"Bot Token ID: {bot_username}")
    print("Bot Link: https://t.me/talk2telegrambot (if this is your bot)")

print("\n✨ If everything looks good, run: python supabase_team_bot.py")
