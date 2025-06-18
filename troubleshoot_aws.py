#!/usr/bin/env python3
"""Troubleshoot AWS credentials - detailed error checking"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv
import sys

# Load environment
load_dotenv('.env.supabase_bot')

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

print("🔍 AWS Credential Troubleshooting")
print("=" * 50)

print(f"\n1. Checking environment variables:")
print(f"   AWS_ACCESS_KEY_ID: {AWS_ACCESS_KEY_ID}")
print(f"   AWS_SECRET_ACCESS_KEY: {'*' * len(AWS_SECRET_ACCESS_KEY) if AWS_SECRET_ACCESS_KEY else 'NOT SET'}")
print(f"   Length of secret: {len(AWS_SECRET_ACCESS_KEY)} chars")
print(f"   AWS_REGION: {AWS_REGION}")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    print("\n❌ Missing credentials!")
    sys.exit(1)

print("\n2. Testing different AWS services to isolate the issue:")

# Test 1: Try STS (Security Token Service) - most basic test
print("\n   Testing STS (get caller identity)...")
try:
    sts = boto3.client(
        'sts',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    identity = sts.get_caller_identity()
    print(f"   ✅ STS Success!")
    print(f"   Account: {identity['Account']}")
    print(f"   UserID: {identity['UserId']}")
    print(f"   ARN: {identity['Arn']}")
except ClientError as e:
    error_code = e.response['Error']['Code']
    error_msg = e.response['Error']['Message']
    print(f"   ❌ STS Error: {error_code} - {error_msg}")
    
    if error_code == 'InvalidClientTokenId':
        print("\n   📋 This means the Access Key ID doesn't exist")
        print("   Possible reasons:")
        print("   1. The key was deleted")
        print("   2. Wrong AWS account")
        print("   3. Typo in the Access Key ID")
    elif error_code == 'SignatureDoesNotMatch':
        print("\n   📋 This means the Secret Access Key is wrong")
        print("   Check if there are any extra spaces or characters")

# Test 2: Try IAM to see user info
print("\n   Testing IAM (get current user)...")
try:
    iam = boto3.client(
        'iam',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    user = iam.get_user()
    print(f"   ✅ IAM Success!")
    print(f"   Username: {user['User']['UserName']}")
    print(f"   Created: {user['User']['CreateDate']}")
except ClientError as e:
    print(f"   ❌ IAM Error: {e.response['Error']['Code']} - {e.response['Error']['Message']}")

# Test 3: Try S3 with specific bucket
print(f"\n   Testing S3 access...")
try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    
    # First try to list buckets
    try:
        buckets = s3.list_buckets()
        print(f"   ✅ Can list buckets: {len(buckets['Buckets'])} found")
    except ClientError as e:
        print(f"   ❌ Cannot list buckets: {e.response['Error']['Code']}")
        
    # Try specific bucket
    bucket_name = os.getenv("S3_BUCKET_NAME", "t2t2imagestorage")
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"   ✅ Can access bucket: {bucket_name}")
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"   ❌ Bucket '{bucket_name}' doesn't exist")
        else:
            print(f"   ❌ Bucket error: {e.response['Error']['Code']}")
            
except Exception as e:
    print(f"   ❌ S3 client error: {e}")

print("\n" + "=" * 50)
print("\n📋 Recommendations:")
print("\n1. If you see 'InvalidClientTokenId':")
print("   - Delete one of your existing access keys in AWS IAM")
print("   - Create a new access key")
print("   - Make sure you're in the right AWS account")
print("\n2. If you see 'SignatureDoesNotMatch':")
print("   - The secret key has extra spaces or is corrupted")
print("   - Try retrieving it from 1Password again")
print("   - Make sure there are no line breaks in the key")
print("\n3. To delete an old key:")
print("   - AWS Console → IAM → Users → Your User")
print("   - Security credentials tab")
print("   - Find old access key → Delete")
print("   - Then create new one")