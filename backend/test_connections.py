#!/usr/bin/env python3
"""
Test all cloud service connections for T2T2
"""
import asyncio
import os
from dotenv import load_dotenv
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def test_database():
    """Test Supabase PostgreSQL connection"""
    print("\n🔍 Testing Supabase PostgreSQL...")
    try:
        from db.database import engine, init_db
        from sqlalchemy import text
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL connected: {version[:50]}...")
            
            # Check pgvector
            result = await conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            if result.rowcount > 0:
                print("✅ pgvector extension is installed")
            else:
                print("❌ pgvector extension NOT found")
                
        # Test table creation
        await init_db()
        print("✅ Database tables initialized")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    return True


async def test_redis():
    """Test Upstash Redis connection"""
    print("\n🔍 Testing Upstash Redis...")
    try:
        from upstash_redis import Redis
        
        redis = Redis(
            url=os.getenv("UPSTASH_REDIS_REST_URL"),
            token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
        )
        
        # Test set/get
        test_key = "t2t2_test"
        test_value = "connection_successful"
        
        redis.set(test_key, test_value)
        result = redis.get(test_key)
        
        if result == test_value:
            print(f"✅ Redis connected and working")
            redis.delete(test_key)
        else:
            print(f"❌ Redis read/write failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False
    return True


async def test_s3():
    """Test AWS S3 connection"""
    print("\n🔍 Testing AWS S3...")
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        
        bucket_name = os.getenv("AWS_BUCKET_NAME")
        
        # Test bucket access
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ S3 bucket '{bucket_name}' accessible")
        
        # Test upload permissions
        test_key = "test/connection_test.txt"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=b"T2T2 connection test"
        )
        print(f"✅ S3 upload successful")
        
        # Test download
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
        content = response['Body'].read()
        print(f"✅ S3 download successful")
        
        # Cleanup
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"✅ S3 delete successful")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ S3 error ({error_code}): {e}")
        return False
    except Exception as e:
        print(f"❌ S3 error: {e}")
        return False
    return True


async def test_openai():
    """Test OpenAI API connection"""
    print("\n🔍 Testing OpenAI API...")
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Test embeddings
        response = await client.embeddings.create(
            model="text-embedding-3-large",
            input="Test connection to OpenAI"
        )
        
        embedding_dim = len(response.data[0].embedding)
        if embedding_dim == 3072:
            print(f"✅ OpenAI connected - embedding dimension: {embedding_dim}")
        else:
            print(f"❌ Unexpected embedding dimension: {embedding_dim}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        return False
    return True


async def main():
    """Run all connection tests"""
    print("🚀 T2T2 Connection Test Suite")
    print("=" * 50)
    
    results = {
        "Database": await test_database(),
        "Redis": await test_redis(),
        "S3": await test_s3(),
        "OpenAI": await test_openai()
    }
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    all_passed = True
    for service, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {service}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All services connected successfully!")
    else:
        print("\n⚠️  Some services failed. Check the errors above.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)