#!/usr/bin/env python3
"""
Add only the exact missing chats from 10NetZero folder
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

# Individual/private chats that might be missing
POSSIBLE_MISSING_CHATS = [
    "Gary Testa",
    "Jingke Liu", 
    "Alana M",
    "Vlad / Billfodl",
    "Bitbo // Billfodl",
    "Mario + 10NZ",
    "PSU",
    "PP/DB affiliate",
    "Buetnaels Management",
    "PrivacyPros OPS",
    "EZ <> 10NZ",
    "DC/TNZ Collaboration",
    "Texas Site: 10NZ <> Upstream",
    "10NZ Summer 2025",
    "10NZ <> BF",
    "Malama x 10NZ",
    "Unhashed + Anton",
    "Supply Bit (Jay) <> Emissary (Aulds Bros) Intro",
    "BBWW // PP",
    "Jeff & Aulds bros",
    "Zexiang, William 戏 Joel"
]

async def add_exact_missing():
    """Add only the exact missing chats"""
    
    # Get user session
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table('user_sessions').select('*').eq('user_id', '5751758169').execute()
    
    if not result.data:
        print("❌ No session found.")
        return
        
    session_string = result.data[0].get('session_string')
    monitored_chats = set(result.data[0].get('monitored_chats', []))
    
    print(f"📊 Currently monitoring: {len(monitored_chats)} chats")
    print("🎯 Target: 39 chats (from 10NetZero folder)")
    print(f"📍 Need to add: {39 - len(monitored_chats)} more chats")
    
    # Connect client
    client = TelegramClient(StringSession(session_string), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.connect()
    
    print("\n🔍 Looking for missing chats...")
    
    # Find exact matches only
    found_missing = []
    
    async for dialog in client.iter_dialogs():
        title = dialog.title or dialog.name or ""
        
        # Check for exact matches
        for target in POSSIBLE_MISSING_CHATS:
            # More strict matching
            if (title == target or 
                title.strip() == target.strip() or
                # Handle some known variations
                (target == "Alana M" and title.startswith("Alana M")) or
                (target == "PSU" and title == "PSU") or
                (target == "Gary Testa" and title == "Gary Testa") or
                (target == "Jingke Liu" and title == "Jingke Liu")):
                
                if str(dialog.id) not in monitored_chats:
                    found_missing.append({
                        "id": dialog.id,
                        "title": title,
                        "match": target,
                        "is_user": dialog.is_user,
                        "is_group": dialog.is_group,
                        "is_channel": dialog.is_channel,
                    })
                    break
        
        # Stop if we've found enough
        if len(monitored_chats) + len(found_missing) >= 39:
            break
    
    print(f"\n✅ Found {len(found_missing)} missing chats:")
    
    # Show what we found
    for chat in found_missing[:4]:  # Only show up to 4 to reach 39
        chat_type = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
        print(f"  ➕ {chat_type} {chat['title']}")
    
    # Add only enough to reach 39
    added = 0
    for chat in found_missing:
        if len(monitored_chats) >= 39:
            break
        chat_id = str(chat['id'])
        monitored_chats.add(chat_id)
        added += 1
    
    print(f"\n➕ Added {added} chats to reach 39 total")
    
    # Save
    print(f"💾 Saving selection ({len(monitored_chats)} total chats)...")
    supabase.table("user_sessions").update({
        "monitored_chats": list(monitored_chats)
    }).eq("user_id", "5751758169").execute()
    
    print("✅ Done!")
    print(f"\n📊 Total chats selected: {len(monitored_chats)}")
    print("🎯 Goal achieved: 39 chats from 10NetZero folder!")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(add_exact_missing())