#!/usr/bin/env python3
"""
Select just a few chats for testing indexing
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

async def select_test_chats():
    """Select just a few chats for testing"""
    
    # Get user session
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table('user_sessions').select('*').eq('user_id', '5751758169').execute()
    
    if not result.data:
        print("❌ No session found.")
        return
        
    session_string = result.data[0].get('session_string')
    current_monitored = result.data[0].get('monitored_chats', [])
    
    print(f"📊 Currently monitoring: {len(current_monitored)} chats")
    
    # Connect client
    client = TelegramClient(StringSession(session_string), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.connect()
    
    # Get some small chats for testing
    print("\n🔍 Finding good test chats (smaller, active groups)...")
    
    test_chats = []
    async for dialog in client.iter_dialogs(limit=100):
        # Look for smaller groups or specific test chats
        if dialog.is_group and not dialog.is_channel:
            # Estimate size based on last message ID
            size_estimate = dialog.message.id if dialog.message else 0
            
            # Look for smaller chats (< 10k messages)
            if size_estimate < 10000 and size_estimate > 100:
                test_chats.append({
                    "id": str(dialog.id),
                    "title": dialog.title or dialog.name or "Unknown",
                    "size_estimate": size_estimate,
                    "is_10net": "10net" in (dialog.title or "").lower()
                })
    
    # Sort by 10NetZero chats first, then by size
    test_chats.sort(key=lambda x: (not x['is_10net'], x['size_estimate']))
    
    print("\n📋 Good test chats (smaller, manageable):")
    for i, chat in enumerate(test_chats[:10], 1):
        indicator = "🏢" if chat['is_10net'] else "👥"
        print(f"{i:2d}. {indicator} {chat['title'][:40]} (~{chat['size_estimate']:,} messages)")
    
    # Select top 5
    selected = [chat['id'] for chat in test_chats[:5]]
    
    print(f"\n✅ Selected {len(selected)} test chats")
    
    # Save
    print("💾 Saving test selection...")
    supabase.table("user_sessions").update({
        "monitored_chats": selected
    }).eq("user_id", "5751758169").execute()
    
    print("\n📊 Test chats selected:")
    for chat in test_chats[:5]:
        print(f"  • {chat['title']}")
    
    print("\n💡 Next steps:")
    print("1. Send /chats to the bot")
    print("2. Click 'Start Indexing'")
    print("3. Run: python monitor_indexing.py")
    print("4. Watch the progress in real-time!")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(select_test_chats())