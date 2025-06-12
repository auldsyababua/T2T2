#!/usr/bin/env python3
"""Test individual services"""
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Testing Redis...")
try:
    from upstash_redis import Redis
    redis = Redis(
        url=os.getenv("UPSTASH_REDIS_REST_URL"),
        token=os.getenv("UPSTASH_REDIS_REST_TOKEN")
    )
    redis.set("test", "hello")
    result = redis.get("test")
    print(f"✅ Redis working: {result}")
except Exception as e:
    print(f"❌ Redis error: {e}")

print("\n🔍 Testing S3...")
try:
    import boto3
    s3 = boto3.client('s3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    # Test access to our specific bucket
    bucket_name = os.getenv("AWS_BUCKET_NAME")
    s3.head_bucket(Bucket=bucket_name)
    print(f"✅ S3 connected, can access bucket: {bucket_name}")
except Exception as e:
    print(f"❌ S3 error: {e}")