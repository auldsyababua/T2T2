#!/usr/bin/env python3
"""
Add the specific missing chats from 10NetZero folder
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

# All chats from the 10NetZero folder (from screenshots)
TENNETZERO_CHATS = [
    # From first screenshot
    "Malama deal DD - 10NZ & Giga",
    "Gary Testa", 
    "Zexiang, William 戏 Joel",
    "Jeff & Aulds bros",
    "10NZ <> BF",
    "DC <> ACS <> 10NetZero <> BitFrontier",
    "Vlad / Billfodl",
    "Unhashed + Anton",
    "Mark X 10NetZero",
    "Alana M 🏔️",
    "10NetZeroPR", 
    "EZ <> 10NZ",
    "Jendrik // 10netzero",
    "Immersion PSU - ACS X EV",
    "TX BTC BOIZ",
    "BTC Mining Deals",
    "Supply Bit (Jay) <> Emissary (Aulds Bros) Intro",
    "BBWW // PP",
    
    # From second screenshot
    "Digital Carpenters <> 10NetZero",
    "Work",
    "Talk2Telegram",
    "PrivacyPros OPS",
    "BigSur Energy ~ 10NetZero",
    "Buetnaels Management", 
    "10NetZero Founders",
    "10NZ Summer 2025",
    "Joel, Bryan |, Lance and Lu",
    "Texas Site: 10NZ <> Upstream",
    "10NetZero <> Luxor",
    "DC/TNZ Collaboration", 
    "Mario + 10NZ",
    "Bitbo // Billfodl",
    "Malama x 10NZ",
    "HeatCore <> 10NetZero",
    "10NetZero biz chat",
    "10NetZero x CryptoEQ",
    "PSU",
    "PP/DB affiliate",
    "Jingke Liu"
]

async def add_missing_chats():
    """Add the specific missing chats"""
    
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
    
    print("🔍 Looking for specific 10NetZero folder chats...")
    
    # Get all dialogs and match by name
    found_chats = []
    missing_names = set(TENNETZERO_CHATS)
    
    async for dialog in client.iter_dialogs():
        title = dialog.title or dialog.name or ""
        
        # Check if this is one of our target chats
        for target_name in TENNETZERO_CHATS:
            # Flexible matching - handle slight variations
            if (target_name.lower() in title.lower() or 
                title.lower() in target_name.lower() or
                # Handle special cases
                (target_name == "Jingke Liu" and "Jingke" in title) or
                (target_name == "Alana M 🏔️" and "Alana M" in title) or
                (target_name == "Gary Testa" and "Gary Testa" in title) or
                (target_name == "Talk2Telegram" and dialog.entity and hasattr(dialog.entity, 'username') and dialog.entity.username == "Talk2Telegram_bot")):
                
                found_chats.append({
                    "id": dialog.id,
                    "title": title,
                    "target_name": target_name,
                    "is_user": dialog.is_user,
                    "is_group": dialog.is_group,
                    "is_channel": dialog.is_channel,
                })
                missing_names.discard(target_name)
                break
    
    print(f"\n✅ Found {len(found_chats)} of {len(TENNETZERO_CHATS)} 10NetZero folder chats")
    
    # Show what we found
    print("\n📋 Matched chats:")
    for chat in sorted(found_chats, key=lambda x: x['title']):
        chat_type = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
        already_selected = "✅" if str(chat['id']) in monitored_chats else "➕"
        print(f"  {already_selected} {chat_type} {chat['title']}")
    
    if missing_names:
        print(f"\n❌ Could not find {len(missing_names)} chats:")
        for name in sorted(missing_names):
            print(f"  • {name}")
    
    # Add all found chats
    new_additions = 0
    for chat in found_chats:
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
    
    print("✅ Done!")
    print(f"\n📊 Total chats selected: {len(monitored_chats)}")
    print(f"📁 10NetZero folder has 39 chats, you now have {len(monitored_chats)} selected")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(add_missing_chats())