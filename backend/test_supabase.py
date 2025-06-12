#!/usr/bin/env python3
"""Test Supabase connection with detailed diagnostics"""
import os
import asyncio
import asyncpg
from dotenv import load_dotenv
import time

load_dotenv()

async def test_connection():
    db_url = os.getenv('DATABASE_URL')
    print(f"🔍 Original URL: {db_url[:50]}...")
    
    # Convert SQLAlchemy format to asyncpg format
    asyncpg_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    print(f"🔍 AsyncPG URL: {asyncpg_url[:50]}...")
    
    # Parse connection details
    try:
        from urllib.parse import urlparse
        parsed = urlparse(asyncpg_url)
        print(f"\n📊 Connection Details:")
        print(f"  Host: {parsed.hostname}")
        print(f"  Port: {parsed.port}")
        print(f"  Database: {parsed.path.lstrip('/')}")
        print(f"  User: {parsed.username}")
        print(f"  SSL: Transaction pooler uses SSL by default")
    except Exception as e:
        print(f"❌ URL parsing error: {e}")
    
    # Test connection with different timeouts
    print(f"\n🔍 Testing connection (30s timeout)...")
    start_time = time.time()
    
    try:
        # Supabase pooler requires SSL
        conn = await asyncpg.connect(
            asyncpg_url,
            timeout=30,
            command_timeout=10,
            ssl='require'  # Supabase requires SSL
        )
        
        print(f"✅ Connected in {time.time() - start_time:.2f}s")
        
        # Test query
        version = await conn.fetchval('SELECT version()')
        print(f"✅ PostgreSQL version: {version[:50]}...")
        
        # Test pgvector
        has_vector = await conn.fetchval(
            "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
        )
        print(f"✅ pgvector: {'Installed' if has_vector else 'Not installed'}")
        
        await conn.close()
        print("✅ Connection closed successfully")
        
    except asyncpg.exceptions.ConnectionDoesNotExistError as e:
        print(f"❌ Connection pool error: {e}")
        print("💡 This might be a transient error. Try again.")
        
    except asyncpg.exceptions.InvalidPasswordError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check your password in the .env file")
        
    except asyncio.TimeoutError:
        print(f"❌ Connection timeout after {time.time() - start_time:.2f}s")
        print("💡 Possible causes:")
        print("   - Firewall blocking connection")
        print("   - Supabase project paused")
        print("   - Network issues")
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        print(f"⏱️  Failed after {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    print("🚀 Supabase Connection Test")
    print("=" * 50)
    asyncio.run(test_connection())