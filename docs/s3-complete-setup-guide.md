# Complete S3 Configuration Guide for T2T2 Bot

## Overview
This guide covers all necessary configurations for AWS S3 bucket and IAM permissions to work with:
1. Direct S3 access from the T2T2 bot (upload/download images)
2. Supabase S3 wrapper integration (read-only access for foreign tables)

## 1. S3 Bucket Configuration

### Bucket Settings
- **Bucket Name**: `t2t2imagestorage` ✅ (already created)
- **Region**: `us-east-1` ✅
- **Versioning**: Enabled (recommended for data protection)
- **Access Points**: Not required for this use case

### Bucket Structure
```
t2t2imagestorage/
├── images/           # Telegram images
├── documents/        # Other documents
└── temp/            # Temporary files
```

### Bucket Policy (Optional but Recommended)
No bucket policy needed if using IAM user permissions only. If you want to restrict access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowT2T2UserFullAccess",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::940790439928:user/t2t2-s3-user"
            },
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::t2t2imagestorage",
                "arn:aws:s3:::t2t2imagestorage/*"
            ]
        }
    ]
}
```

## 2. IAM User Permissions

### Current User
- **User**: `t2t2-s3-user`
- **Account**: 940790439928

### Required IAM Policy for Full Functionality

Create a custom policy with these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListBucketPermissions",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:GetBucketVersioning",
                "s3:ListBucketVersions"
            ],
            "Resource": "arn:aws:s3:::t2t2imagestorage"
        },
        {
            "Sid": "ObjectPermissions",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectAttributes",
                "s3:GetObjectVersion",
                "s3:GetObjectVersionAttributes",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:DeleteObjectVersion"
            ],
            "Resource": "arn:aws:s3:::t2t2imagestorage/*"
        },
        {
            "Sid": "MultipartUploadPermissions",
            "Effect": "Allow",
            "Action": [
                "s3:ListMultipartUploadParts",
                "s3:AbortMultipartUpload"
            ],
            "Resource": "arn:aws:s3:::t2t2imagestorage/*"
        }
    ]
}
```

### Minimal Permissions for Supabase S3 Wrapper Only

If you only need read access for Supabase wrapper:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectAttributes",
                "s3:GetObjectVersion",
                "s3:GetObjectVersionAttributes",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::t2t2imagestorage",
                "arn:aws:s3:::t2t2imagestorage/*"
            ]
        }
    ]
}
```

## 3. Steps to Apply IAM Policy

1. **Go to AWS Console** → IAM → Users → `t2t2-s3-user`

2. **Add Permissions** → Create Inline Policy

3. **Choose JSON** and paste the full policy above

4. **Review and Create** with name: `T2T2-S3-Access-Policy`

## 4. Supabase S3 Wrapper Configuration

After IAM permissions are set:

1. **In Supabase Dashboard** → Database → Wrappers

2. **Add new wrapper** with:
   ```
   Server name: s3_wrapper
   Type: S3
   
   Options:
   - aws_access_key_id: AKIA5WC32374N5FFMOVI
   - aws_secret_access_key: [your secret key]
   - aws_region: us-east-1
   ```

3. **Create Foreign Tables** using `create_s3_tables.sql`

## 5. Additional Security Recommendations

### Enable Server-Side Encryption
```bash
aws s3api put-bucket-encryption \
    --bucket t2t2imagestorage \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
```

### Enable Access Logging (Optional)
- Create a logging bucket
- Enable logging to track access

### Set Lifecycle Rules (Optional)
- Auto-delete temp/ folder items after 7 days
- Move old images to Glacier after 90 days

## 6. Testing Checklist

- [ ] IAM user can list bucket contents
- [ ] IAM user can upload objects
- [ ] IAM user can download objects
- [ ] IAM user can delete objects
- [ ] Supabase wrapper can read objects
- [ ] Foreign tables work in Supabase

## Summary

The key requirements are:
1. **S3 Bucket**: Already created ✅
2. **IAM Permissions**: Need to add the policy above
3. **Supabase Wrapper**: Configure after IAM is set
4. **No Access Points needed** - Direct bucket access works fine
5. **No bucket policy needed** - IAM permissions are sufficient