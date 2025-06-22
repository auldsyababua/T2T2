#!/usr/bin/env python3
"""
Simple indexing monitor - just shows message count
"""

import os
import time
from supabase import create_client
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.supabase_bot')

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

def monitor():
    """Simple monitoring"""
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("📊 Simple Indexing Monitor")
    print("=" * 50)
    
    # Check all relevant tables
    tables_to_check = ["messages", "message_embeddings", "telegram_files", "documents"]
    
    start_counts = {}
    for table in tables_to_check:
        try:
            result = supabase.table(table).select("id", count="exact").execute()
            start_counts[table] = result.count
            print(f"📈 {table}: {result.count:,} rows")
        except:
            start_counts[table] = 0
            print(f"❌ {table}: Not accessible")
    
    print("\n⏱️  Checking every 5 seconds... (Ctrl+C to stop)")
    print("-" * 50)
    
    while True:
        try:
            time.sleep(5)
            
            for table in tables_to_check:
                try:
                    result = supabase.table(table).select("id", count="exact").execute()
                    current = result.count
                    if current > start_counts[table]:
                        diff = current - start_counts[table]
                        print(f"\n🆕 {table}: {current:,} rows (+{diff})")
                        start_counts[table] = current
                except:
                    pass
                    
        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped")
            break

if __name__ == "__main__":
    monitor()