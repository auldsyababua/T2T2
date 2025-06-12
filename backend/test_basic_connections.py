#!/usr/bin/env python3
"""
Basic connection test for core services
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

print("🔍 Testing environment variables...")
print(f"DATABASE_URL: {'✅' if os.getenv('DATABASE_URL') else '❌'}")
print(f"UPSTASH_REDIS_REST_URL: {'✅' if os.getenv('UPSTASH_REDIS_REST_URL') else '❌'}")
print(f"AWS_ACCESS_KEY_ID: {'✅' if os.getenv('AWS_ACCESS_KEY_ID') else '❌'}")
print(f"OPENAI_API_KEY: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")

# Test basic imports
print("\n🔍 Testing basic imports...")
try:
    import asyncpg

    print("✅ asyncpg imported")
except:
    print("❌ asyncpg not installed")

try:

    print("✅ upstash_redis imported")
except:
    print("❌ upstash_redis not installed")

try:

    print("✅ boto3 imported")
except:
    print("❌ boto3 not installed")


# Quick connection tests
async def quick_db_test():
    try:
        # Convert SQLAlchemy URL to asyncpg format
        db_url = os.getenv("DATABASE_URL")
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(db_url)
        version = await conn.fetchval("SELECT version()")
        print(f"\n✅ PostgreSQL connected: {version[:30]}...")

        # Check pgvector
        has_vector = await conn.fetchval(
            "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'"
        )
        print(f"✅ pgvector: {'installed' if has_vector else 'NOT installed'}")

        await conn.close()
        return True
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(quick_db_test())
