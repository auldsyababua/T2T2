#!/usr/bin/env python3
"""
Simple chat selector with search functionality
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

async def select_chats_with_search():
    """Interactive chat selector with search"""
    
    # Get user session
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table('user_sessions').select('*').eq('user_id', '5751758169').execute()
    
    if not result.data:
        print("❌ No session found. Run authentication first.")
        return
        
    session_string = result.data[0].get('session_string')
    monitored_chats = set(result.data[0].get('monitored_chats', []))
    
    # Connect client
    client = TelegramClient(StringSession(session_string), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.connect()
    
    print("🔍 Loading all your chats...")
    
    # Get ALL dialogs
    dialogs = []
    async for dialog in client.iter_dialogs():  # No limit - get all
        chat_info = {
            "id": dialog.id,
            "title": dialog.title or dialog.name or "Unknown",
            "is_user": dialog.is_user,
            "is_group": dialog.is_group,
            "is_channel": dialog.is_channel,
        }
        dialogs.append(chat_info)
    
    print(f"📊 Total chats found: {len(dialogs)}")
    print(f"✅ Currently monitoring: {len(monitored_chats)} chats")
    
    while True:
        print("\n" + "="*50)
        print("Options:")
        print("1. Search for chats by name (e.g., '10NetZero')")
        print("2. View currently selected chats")
        print("3. Select from recent chats")
        print("4. Clear all selections")
        print("5. Save and exit")
        print("="*50)
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            search_term = input("Enter search term: ").strip().lower()
            if search_term:
                matching = [d for d in dialogs if search_term in d['title'].lower()]
                print(f"\nFound {len(matching)} chats matching '{search_term}':")
                
                for i, chat in enumerate(matching[:50], 1):  # Show max 50
                    status = "✅" if str(chat['id']) in monitored_chats else "⬜"
                    chat_type = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
                    print(f"{i:3d}. {status} {chat_type} {chat['title'][:60]}")
                
                if matching:
                    print("\nEnter numbers to toggle (comma-separated), 'all' to select all, or 'none' to go back:")
                    selection = input("> ").strip()
                    
                    if selection.lower() == 'all':
                        for chat in matching:
                            monitored_chats.add(str(chat['id']))
                        print(f"✅ Added all {len(matching)} matching chats!")
                    elif selection.lower() != 'none':
                        try:
                            indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip()]
                            for idx in indices:
                                if 0 <= idx < len(matching):
                                    chat_id = str(matching[idx]['id'])
                                    if chat_id in monitored_chats:
                                        monitored_chats.remove(chat_id)
                                        print(f"❌ Removed: {matching[idx]['title']}")
                                    else:
                                        monitored_chats.add(chat_id)
                                        print(f"✅ Added: {matching[idx]['title']}")
                        except:
                            print("Invalid input")
                            
        elif choice == "2":
            # View selected
            if monitored_chats:
                print(f"\n📋 Currently selected ({len(monitored_chats)} chats):")
                selected = [d for d in dialogs if str(d['id']) in monitored_chats]
                for i, chat in enumerate(selected, 1):
                    chat_type = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
                    print(f"{i:3d}. {chat_type} {chat['title']}")
            else:
                print("\n❌ No chats selected yet")
                
        elif choice == "3":
            # Recent chats
            print("\nRecent chats (last 30):")
            for i, chat in enumerate(dialogs[:30], 1):
                status = "✅" if str(chat['id']) in monitored_chats else "⬜"
                chat_type = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
                print(f"{i:3d}. {status} {chat_type} {chat['title'][:60]}")
                
        elif choice == "4":
            # Clear all
            if input("Are you sure you want to clear all selections? (y/n): ").lower() == 'y':
                monitored_chats.clear()
                print("✅ All selections cleared")
                
        elif choice == "5":
            # Save and exit
            break
    
    # Save updated selection
    print(f"\n💾 Saving selection ({len(monitored_chats)} chats)...")
    supabase.table("user_sessions").update({
        "monitored_chats": list(monitored_chats)
    }).eq("user_id", "5751758169").execute()
    
    print("✅ Selection saved!")
    print(f"\n📊 Final selection: {len(monitored_chats)} chats")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(select_chats_with_search())