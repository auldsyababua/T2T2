#!/usr/bin/env python3
"""
Add all chats from a specific Telegram folder
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

async def add_folder_chats(folder_name="10NetZero"):
    """Add all chats from a specific folder"""
    
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
    
    print(f"🔍 Looking for folder: {folder_name}")
    
    # Get dialog filters (folders)
    folder_chat_ids = set()
    found_folder = False
    
    try:
        result = await client(GetDialogFiltersRequest())
        
        for dialog_filter in result.chats:
            # Skip if not a folder
            if not hasattr(dialog_filter, 'title'):
                continue
                
            if dialog_filter.title == folder_name:
                found_folder = True
                print(f"✅ Found folder: {folder_name}")
                
                # Get all included peers
                if hasattr(dialog_filter, 'include_peers'):
                    for peer in dialog_filter.include_peers:
                        if hasattr(peer, 'user_id'):
                            folder_chat_ids.add(peer.user_id)
                        elif hasattr(peer, 'channel_id'):
                            # Telegram uses negative IDs for channels
                            folder_chat_ids.add(peer.channel_id)
                        elif hasattr(peer, 'chat_id'):
                            # And different negative IDs for group chats
                            folder_chat_ids.add(-peer.chat_id)
                
                print(f"📁 Folder contains {len(folder_chat_ids)} chat IDs")
                break
    except Exception as e:
        print(f"❌ Error getting folders: {e}")
        print("Let me try a different approach...")
        
        # Alternative approach - get the filter list
        try:
            from telethon.tl.functions.messages import GetDialogFiltersRequest
            filters = await client(GetDialogFiltersRequest())
            
            for f in filters.filters:
                if hasattr(f, 'title') and f.title == folder_name:
                    found_folder = True
                    print(f"✅ Found folder: {folder_name}")
                    
                    # Process included peers
                    if hasattr(f, 'include_peers'):
                        for peer in f.include_peers:
                            # Get the actual chat ID
                            if hasattr(peer, 'user_id'):
                                folder_chat_ids.add(peer.user_id)
                            elif hasattr(peer, 'channel_id'):
                                folder_chat_ids.add(peer.channel_id)
                            elif hasattr(peer, 'chat_id'):
                                folder_chat_ids.add(peer.chat_id)
                    
                    print(f"📁 Found {len(folder_chat_ids)} chat IDs in folder")
                    break
        except Exception as e2:
            print(f"❌ Alternative approach also failed: {e2}")
    
    if not found_folder:
        print(f"❌ Folder '{folder_name}' not found")
        print("\nAvailable folders:")
        try:
            filters = await client(GetDialogFiltersRequest())
            for f in filters.filters:
                if hasattr(f, 'title'):
                    print(f"  • {f.title}")
        except:
            print("  (Could not list folders)")
        return
    
    # Now get all dialogs to match IDs with names
    print("\n🔄 Matching folder chats with dialog info...")
    
    folder_chats = []
    all_dialogs = []
    
    async for dialog in client.iter_dialogs():
        all_dialogs.append(dialog)
        
        # Check if this dialog is in our folder
        # Need to check various ID formats
        dialog_id = dialog.id
        
        # Also check the entity ID if available
        if dialog.entity:
            entity_id = dialog.entity.id
            
            # Check if any form of this ID is in our folder
            if (dialog_id in folder_chat_ids or 
                entity_id in folder_chat_ids or
                -dialog_id in folder_chat_ids or
                -entity_id in folder_chat_ids or
                -100 - entity_id in folder_chat_ids):  # Supergroup format
                
                folder_chats.append({
                    "id": dialog.id,
                    "title": dialog.title or dialog.name or "Unknown",
                    "is_user": dialog.is_user,
                    "is_group": dialog.is_group,
                    "is_channel": dialog.is_channel,
                })
    
    print(f"\n✅ Matched {len(folder_chats)} chats from {folder_name} folder:")
    print(f"   (Folder had {len(folder_chat_ids)} IDs, found {len(folder_chats)} matching dialogs)")
    
    # Show what we found
    for chat in sorted(folder_chats, key=lambda x: x['title']):
        chat_type = "👤" if chat['is_user'] else "👥" if chat['is_group'] else "📢"
        already_selected = "✅" if str(chat['id']) in monitored_chats else "➕"
        print(f"  {already_selected} {chat_type} {chat['title']}")
    
    # Add them all
    new_additions = 0
    for chat in folder_chats:
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
    
    print(f"✅ Done! All {folder_name} folder chats are now selected for indexing.")
    print(f"\n📊 Total chats selected: {len(monitored_chats)}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(add_folder_chats("10NetZero"))