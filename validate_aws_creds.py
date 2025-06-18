#!/usr/bin/env python3
"""Validate AWS credentials and S3 bucket access"""

import os
import boto3
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.supabase_bot')

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "t2t2imagestorage")

print("🔍 AWS Credential Validation")
print("=" * 50)

print(f"\nCredentials found:")
print(f"Access Key ID: {AWS_ACCESS_KEY_ID[:10]}..." if AWS_ACCESS_KEY_ID else "Access Key ID: NOT SET")
print(f"Secret Key: {'*' * 10}..." if AWS_SECRET_ACCESS_KEY else "Secret Key: NOT SET")
print(f"Region: {AWS_REGION}")
print(f"Bucket: {S3_BUCKET_NAME}")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    print("\n❌ AWS credentials missing!")
    print("\nTo get valid AWS credentials:")
    print("1. Log in to AWS Console")
    print("2. Go to IAM → Users → Your User")
    print("3. Security credentials tab → Create access key")
    print("4. Update .env.supabase_bot with the new credentials")
    exit(1)

print("\nTesting AWS connection...")
try:
    # Create S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    
    # Test 1: List buckets
    buckets = s3.list_buckets()
    print(f"✅ AWS credentials valid! Found {len(buckets['Buckets'])} buckets")
    
    # Test 2: Check specific bucket
    try:
        s3.head_bucket(Bucket=S3_BUCKET_NAME)
        print(f"✅ Bucket '{S3_BUCKET_NAME}' accessible")
        
        # List some objects
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=5)
        if 'Contents' in response:
            print(f"\nFound {response['KeyCount']} objects:")
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
        else:
            print("\nBucket is empty (ready for images)")
            
        print("\n✅ AWS credentials are valid and bucket is accessible!")
        print("\nYou can now:")
        print("1. Configure S3 wrapper in Supabase with these credentials")
        print("2. Use the same Access Key ID and Secret Key")
        
    except Exception as e:
        if "404" in str(e):
            print(f"❌ Bucket '{S3_BUCKET_NAME}' not found")
            print("\nCreate the bucket first or update S3_BUCKET_NAME in .env")
        else:
            print(f"❌ Bucket error: {e}")
            
except Exception as e:
    print(f"❌ AWS credential error: {e}")
    print("\nThe Access Key ID doesn't exist or is invalid")
    print("Please get new credentials from AWS IAM")