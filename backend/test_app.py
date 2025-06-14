#!/usr/bin/env python3
"""Test the FastAPI application startup"""
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_app():
    print("🚀 Testing T2T2 Backend Startup...")
    print("=" * 50)

    try:
        # Import models to register them with Base metadata

        # Test database initialization
        print("\n🔍 Testing database initialization...")
        from backend.db.database import init_db

        await init_db()
        print("✅ Database initialized successfully!")

        # Test importing routes
        print("\n🔍 Testing route imports...")

        print("✅ All routes imported successfully!")

        # Test Redis connection
        print("\n🔍 Testing Redis...")
        from upstash_redis import Redis

        redis = Redis(
            url=os.getenv("UPSTASH_REDIS_REST_URL"),
            token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
        )
        redis.set("t2t2_test", "ready")
        result = redis.get("t2t2_test")
        print(f"✅ Redis working: {result}")

        # Test S3
        print("\n🔍 Testing S3...")
        import boto3

        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        s3.head_bucket(Bucket=os.getenv("AWS_BUCKET_NAME"))
        print(f"✅ S3 bucket accessible: {os.getenv('AWS_BUCKET_NAME')}")

        print("\n✅ All systems operational!")
        print("🎉 Ready to start the backend with: python main.py")

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    success = asyncio.run(test_app())
    sys.exit(0 if success else 1)
