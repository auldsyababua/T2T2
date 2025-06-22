#!/usr/bin/env python3
"""
Enhanced chat selector for T2T2 bot with folder filtering
Specifically designed to help select chats from the 10NetZero folder
"""

import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetDialogFiltersRequest
from supabase import create_client
from dotenv import load_dotenv
import logging

# Load environment
load_dotenv('.env.supabase_bot')

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def select_chats_by_folder():
    """Interactive chat selector with folder support"""
    
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
    
    print("🔍 Loading your chats and folders...")
    
    # Get folders
    folders = {}
    try:
        filters = await client(GetDialogFiltersRequest())
        for f in filters.filters:
            if hasattr(f, 'title') and hasattr(f, 'include_peers'):
                chat_ids = []
                for p in f.include_peers:
                    if hasattr(p, 'user_id'):
                        chat_ids.append(p.user_id)
                    elif hasattr(p, 'channel_id'):
                        chat_ids.append(-100 - p.channel_id)  # Telegram's channel ID format
                    elif hasattr(p, 'chat_id'):
                        chat_ids.append(-p.chat_id)  # Group chat ID format
                folders[f.title] = chat_ids
                print(f"📁 Found folder: {f.title} ({len(chat_ids)} chats)")
    except Exception as e:
        logger.error(f"Could not get folders: {e}")
    
    # Get all dialogs
    dialogs = []
    async for dialog in client.iter_dialogs(limit=300):
        chat_info = {
            "id": dialog.id,
            "title": dialog.title or dialog.name or "Unknown",
            "is_user": dialog.is_user,
            "is_group": dialog.is_group,
            "is_channel": dialog.is_channel,
            "folder": None
        }
        
        # Check which folder this chat belongs to
        for folder_name, chat_ids in folders.items():
            if dialog.id in chat_ids:
                chat_info["folder"] = folder_name
                break
                
        dialogs.append(chat_info)
    
    print(f"\n📊 Total chats found: {len(dialogs)}")
    
    # Check for 10NetZero folder
    if '10NetZero' in folders:
        print("\n✅ Found 10NetZero folder!")
        ten_net_chats = [d for d in dialogs if d.get('folder') == '10NetZero']
        print(f"📋 10NetZero contains {len(ten_net_chats)} chats")
        
        print("\nWould you like to:")
        print("1. Select ALL 10NetZero chats")
        print("2. View and select individual 10NetZero chats")
        print("3. View all chats")
        print("4. Keep current selection")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            # Add all 10NetZero chats
            for chat in ten_net_chats:
                monitored_chats.add(str(chat['id']))
            print(f"✅ Added all {len(ten_net_chats)} 10NetZero chats!")
            
        elif choice == "2":
            # Show 10NetZero chats for selection
            print("\n10NetZero chats:")
            for i, chat in enumerate(ten_net_chats, 1):
                status = "✅" if str(chat['id']) in monitored_chats else "⬜"
                print(f"{i:3d}. {status} {chat['title'][:50]}")
            
            print("\nEnter chat numbers to toggle (comma-separated) or 'all':")
            selection = input("> ").strip()
            
            if selection.lower() == 'all':
                for chat in ten_net_chats:
                    monitored_chats.add(str(chat['id']))
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',') if x.strip()]
                    for idx in indices:
                        if 0 <= idx < len(ten_net_chats):
                            chat_id = str(ten_net_chats[idx]['id'])
                            if chat_id in monitored_chats:
                                monitored_chats.remove(chat_id)
                                print(f"❌ Removed: {ten_net_chats[idx]['title']}")
                            else:
                                monitored_chats.add(chat_id)
                                print(f"✅ Added: {ten_net_chats[idx]['title']}")
                except:
                    print("Invalid input")
                    
        elif choice == "3":
            # Show all chats
            print("\nAll chats (showing first 50):")
            for i, chat in enumerate(dialogs[:50], 1):
                status = "✅" if str(chat['id']) in monitored_chats else "⬜"
                folder = f"[{chat['folder']}]" if chat['folder'] else ""
                print(f"{i:3d}. {status} {folder:15} {chat['title'][:40]}")
    
    # Save updated selection
    print(f"\n💾 Saving selection ({len(monitored_chats)} chats)...")
    supabase.table("user_sessions").update({
        "monitored_chats": list(monitored_chats)
    }).eq("user_id", "5751758169").execute()
    
    print("✅ Selection saved!")
    print(f"\n📊 Summary: {len(monitored_chats)} chats selected for indexing")
    
    # Show what's selected
    if monitored_chats:
        print("\nSelected chats:")
        selected_dialogs = [d for d in dialogs if str(d['id']) in monitored_chats]
        for chat in selected_dialogs[:20]:
            folder = f"[{chat['folder']}]" if chat['folder'] else ""
            print(f"  • {folder} {chat['title']}")
        if len(selected_dialogs) > 20:
            print(f"  ... and {len(selected_dialogs) - 20} more")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(select_chats_by_folder())