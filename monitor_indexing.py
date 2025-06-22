#!/usr/bin/env python3
"""
Monitor indexing progress in real-time
"""

import os
import asyncio
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
import time

# Load environment
load_dotenv('.env.supabase_bot')

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

async def monitor_indexing():
    """Monitor indexing progress"""
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("📊 T2T2 Indexing Monitor")
    print("=" * 50)
    
    # Get current stats - check both possible tables
    try:
        initial_count = supabase.table("messages").select("id", count="exact").execute()
        initial_messages = initial_count.count
        table_name = "messages"
    except:
        # Try message_embeddings table instead
        initial_count = supabase.table("message_embeddings").select("id", count="exact").execute()
        initial_messages = initial_count.count
        table_name = "message_embeddings"
    
    print(f"📈 Starting message count: {initial_messages:,}")
    print("\nMonitoring... (Press Ctrl+C to stop)\n")
    
    last_count = initial_messages
    start_time = time.time()
    
    while True:
        try:
            # Get current count
            current = supabase.table(table_name).select("id", count="exact").execute()
            current_count = current.count
            
            # Get recent messages to see which chats are being indexed
            # First, let's see what columns are available
            if current_count > 0 and not hasattr(monitor_indexing, 'checked_columns'):
                sample = supabase.table(table_name).select("*").limit(1).execute()
                if sample.data:
                    monitor_indexing.checked_columns = True
                    available_cols = list(sample.data[0].keys())
                    # Find the right columns
                    chat_col = next((c for c in available_cols if 'chat' in c.lower()), None)
                    time_col = next((c for c in available_cols if 'created' in c.lower() or 'time' in c.lower()), 'id')
                else:
                    chat_col = None
                    time_col = 'id'
            else:
                chat_col = getattr(monitor_indexing, 'chat_col', None)
                time_col = getattr(monitor_indexing, 'time_col', 'id')
            
            recent = None
            if chat_col:
                try:
                    recent = supabase.table(table_name)\
                        .select(f"{chat_col}, {time_col}")\
                        .order(time_col, desc=True)\
                        .limit(5)\
                        .execute()
                except:
                    recent = None
            
            # Calculate progress
            new_messages = current_count - initial_messages
            rate = new_messages / (time.time() - start_time) * 60 if time.time() > start_time else 0
            
            # Clear screen and show update
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("📊 T2T2 Indexing Monitor")
            print("=" * 50)
            print(f"⏱️  Running for: {int(time.time() - start_time)}s")
            print(f"📈 Total messages: {current_count:,}")
            print(f"✨ New messages: {new_messages:,}")
            print(f"⚡ Rate: {rate:.0f} messages/minute")
            
            if current_count > last_count:
                print(f"\n🆕 Added {current_count - last_count} messages!")
            
            print("\n📍 Recent activity:")
            if recent and recent.data:
                seen_chats = set()
                for msg in recent.data:
                    # Use whatever chat column we found
                    chat = msg.get(chat_col, 'Unknown') if chat_col else 'Unknown'
                    if chat not in seen_chats:
                        seen_chats.add(chat)
                        print(f"  • {str(chat)[:50]}")
            else:
                print("  No recent activity to show")
            
            # For now, skip unique chat counting until we know the schema
            unique_chats = set()
            
            print(f"\n📁 Unique chats indexed: {len(unique_chats)}")
            
            last_count = current_count
            
            # Wait before next check
            await asyncio.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")
            print(f"📊 Final stats:")
            print(f"   • Total messages: {current_count:,}")
            print(f"   • Messages added: {new_messages:,}")
            print(f"   • Unique chats: {len(unique_chats)}")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(monitor_indexing())