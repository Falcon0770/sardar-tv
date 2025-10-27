#!/usr/bin/env python3
"""
Sync uploaded_videos.json from S3 bucket
This script checks what's already in S3 and creates/updates the tracking file
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def sync_uploaded_videos_from_s3():
    """
    Check S3 bucket and create uploaded_videos.json with all already uploaded post IDs.
    """
    S3_BUCKET = os.getenv('S3_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    if not S3_BUCKET:
        print("❌ Error: S3_BUCKET_NAME not set in .env file")
        return
    
    print("=" * 80)
    print("Syncing uploaded videos from S3 bucket...")
    print("=" * 80)
    print(f"\n🪣 S3 Bucket: {S3_BUCKET}")
    print(f"🌍 Region: {AWS_REGION}")
    print(f"\n🔍 Checking what's already uploaded to S3...\n")
    
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # List all objects in the videos/ prefix
        uploaded_post_ids = []
        continuation_token = None
        page = 1
        
        while True:
            # List objects
            list_params = {
                'Bucket': S3_BUCKET,
                'Prefix': 'videos/'
            }
            
            if continuation_token:
                list_params['ContinuationToken'] = continuation_token
            
            response = s3_client.list_objects_v2(**list_params)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Extract post ID from filename
                    # Format: videos/12345.mp4 -> 12345
                    key = obj['Key']
                    if key.startswith('videos/') and '.' in key:
                        filename = key.split('/')[-1]  # Get filename
                        post_id = filename.split('.')[0]  # Get ID without extension
                        
                        if post_id.isdigit():  # Make sure it's a valid post ID
                            uploaded_post_ids.append(post_id)
                
                print(f"📄 Page {page}: Found {len(response['Contents'])} files (Total: {len(uploaded_post_ids)} videos)")
                page += 1
            
            # Check if there are more pages
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
        
        print(f"\n✅ Found {len(uploaded_post_ids)} videos already uploaded to S3")
        
        # Save to uploaded_videos.json
        with open('uploaded_videos.json', 'w') as f:
            json.dump(uploaded_post_ids, f, indent=2)
        
        print(f"💾 Saved to uploaded_videos.json")
        print("\n" + "=" * 80)
        print("🎯 RESULT:")
        print(f"   Videos already in S3: {len(uploaded_post_ids)}")
        print(f"   These videos will be SKIPPED on next upload run")
        print("=" * 80)
        
        # Show some examples
        if uploaded_post_ids:
            print(f"\n📋 Sample of uploaded post IDs:")
            for post_id in uploaded_post_ids[:10]:
                print(f"   - {post_id}")
            if len(uploaded_post_ids) > 10:
                print(f"   ... and {len(uploaded_post_ids) - 10} more")
        
        return uploaded_post_ids
        
    except NoCredentialsError:
        print("❌ Error: AWS credentials not found")
        print("   Please check your .env file has AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    except ClientError as e:
        print(f"❌ Error accessing S3: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    sync_uploaded_videos_from_s3()

