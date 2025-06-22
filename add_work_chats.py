#!/usr/bin/env python3
"""
Add work-related chats by various patterns
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.supabase_bot')

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Common work-related keywords
WORK_KEYWORDS = [
    "10netzero", "10 net zero", "10net",
    "mining", "bitcoin", "btc", "crypto",
    "energy", "power", "heat", "core",
    "digital carpenter", "dc ",
    "business", "biz", "work",
    "partner", "client", "deal",
    "finance", "funding", "investor"
]

async def add_work_chats():
    """Add work-related chats using various patterns"""
    
    # Get user session
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table('user_sessions').select('*').eq('user_id', '5751758169').execute()
    
    if not result.data:
        print("❌ No session found.")
        return
        
    session_string = result.data[0].get('session_string')
    monitored_chats = set(result.data[0].get('monitored_chats', []))
    
    print(f"📊 Currently monitoring: {len(monitored_chats)} chats")
    
    # Connect client
    client = TelegramClient(StringSession(session_string), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.connect()
    
    print("🔍 Searching for work-related chats...")
    print(f"📝 Keywords: {', '.join(WORK_KEYWORDS[:5])}...")
    
    # Get all dialogs
    all_chats = []
    work_chats = []
    
    async for dialog in client.iter_dialogs():
        chat_info = {
            "id": dialog.id,
            "title": dialog.title or dialog.name or "Unknown",
            "is_user": dialog.is_user,
            "is_group": dialog.is_group,
            "is_channel": dialog.is_channel,
        }
        all_chats.append(chat_info)
        
        # Check if it matches work patterns
        title_lower = chat_info['title'].lower()
        
        # Check for work keywords
        is_work = any(keyword in title_lower for keyword in WORK_KEYWORDS)
        
        # Also check for specific patterns
        if not is_work:
            # Company names you work with
            companies = ["luxor", "heatcore", "bigsur", "cryptoeq", "bitfrontier", "ptc", "acs", "jendrik", "connor", "bryan", "mark"]
            is_work = any(company in title_lower for company in companies)
        
        # Exclude personal chats unless they have work keywords
        if is_work and not (chat_info['is_user'] and not any(kw in title_lower for kw in ['10netzero', 'work', 'biz', 'business'])):
            work_chats.append(chat_info)
    
    print(f"\n📊 Found {len(all_chats)} total chats")
    print(f"💼 Found {len(work_chats)} work-related chats")
    
    # Group by type
    groups = [c for c in work_chats if c['is_group']]
    channels = [c for c in work_chats if c['is_channel']]
    users = [c for c in work_chats if c['is_user']]
    
    print(f"\n📊 Breakdown:")
    print(f"  👥 Groups: {len(groups)}")
    print(f"  📢 Channels: {len(channels)}")
    print(f"  👤 Work contacts: {len(users)}")
    
    # Show all work chats
    print("\n💼 Work-related chats found:")
    for chat in sorted(work_chats, key=lambda x: (not x['is_group'], x['title'])):
        chat_type = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
        already_selected = "✅" if str(chat['id']) in monitored_chats else "➕"
        print(f"  {already_selected} {chat_type} {chat['title']}")
    
    # Ask for confirmation
    print(f"\n🤔 Found {len(work_chats)} work chats. Current selection has {len(monitored_chats)} chats.")
    print("Options:")
    print("1. Add ALL work chats")
    print("2. Add only GROUP chats (recommended)")
    print("3. Skip")
    
    # For non-interactive, let's add all groups
    print("\n➡️ Auto-selecting option 2: Adding work GROUPS only...")
    
    # Add all work groups
    new_additions = 0
    for chat in groups:
        chat_id = str(chat['id'])
        if chat_id not in monitored_chats:
            monitored_chats.add(chat_id)
            new_additions += 1
            print(f"  ➕ Added: {chat['title']}")
    
    print(f"\n✅ Added {new_additions} new work groups")
    
    # Save
    print(f"\n💾 Saving selection ({len(monitored_chats)} total chats)...")
    supabase.table("user_sessions").update({
        "monitored_chats": list(monitored_chats)
    }).eq("user_id", "5751758169").execute()
    
    print("✅ Done!")
    print(f"\n📊 Total chats selected: {len(monitored_chats)}")
    
    # Show what's missing
    if len(monitored_chats) < 39:
        print(f"\n⚠️ You mentioned having 39 chats in your 10NetZero folder.")
        print(f"   Currently selected: {len(monitored_chats)}")
        print(f"   Missing: {39 - len(monitored_chats)}")
        print("\nThe missing chats might be:")
        print("- Personal/direct messages without work keywords")
        print("- Chats with names that don't match our patterns")
        print("- Archived or inactive chats")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(add_work_chats())