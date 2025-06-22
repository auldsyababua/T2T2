#!/usr/bin/env python3
"""
Quick script to add all chats containing '10NetZero' to monitored list
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

async def add_10netzero_chats():
    """Add all 10NetZero chats to monitoring"""
    
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
    
    print("🔍 Searching for 10NetZero chats...")
    
    # Find all chats with 10NetZero in the name
    ten_net_chats = []
    async for dialog in client.iter_dialogs():
        title = dialog.title or dialog.name or ""
        if "10netzero" in title.lower() or "10 net zero" in title.lower():
            ten_net_chats.append({
                "id": dialog.id,
                "title": title,
                "is_user": dialog.is_user,
                "is_group": dialog.is_group,
                "is_channel": dialog.is_channel,
            })
    
    print(f"\n✅ Found {len(ten_net_chats)} chats with '10NetZero' in the name:")
    
    # Show what we found
    for chat in ten_net_chats:
        chat_type = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
        already_selected = "✅" if str(chat['id']) in monitored_chats else "➕"
        print(f"  {already_selected} {chat_type} {chat['title']}")
    
    # Add them all
    new_additions = 0
    for chat in ten_net_chats:
        chat_id = str(chat['id'])
        if chat_id not in monitored_chats:
            monitored_chats.add(chat_id)
            new_additions += 1
    
    print(f"\n➕ Added {new_additions} new chats to monitoring")
    
    # Save
    print(f"💾 Saving selection ({len(monitored_chats)} total chats)...")
    supabase.table("user_sessions").update({
        "monitored_chats": list(monitored_chats)
    }).eq("user_id", "5751758169").execute()
    
    print("✅ Done! All 10NetZero chats are now selected for indexing.")
    print(f"\n📊 Total chats selected: {len(monitored_chats)}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(add_10netzero_chats())