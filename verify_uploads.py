#!/usr/bin/env python3
"""
Verify Uploads - Check uploaded_videos.json against actual S3 bucket
This script finds videos marked as uploaded but missing from S3
"""

import os
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

def verify_uploads():
    """
    Verify which videos in uploaded_videos.json are actually in S3.
    Remove entries that are NOT in S3 so they can be re-uploaded.
    """
    
    # Configuration
    S3_BUCKET = os.getenv('S3_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    uploaded_videos_file = Path('uploaded_videos.json')
    
    if not S3_BUCKET:
        print("❌ Error: S3_BUCKET_NAME not set in .env file")
        return
    
    print("=" * 80)
    print("Verifying Uploaded Videos Against S3 Bucket")
    print("=" * 80)
    print(f"\n🪣 S3 Bucket: {S3_BUCKET}")
    print(f"🌍 Region: {AWS_REGION}")
    print()
    
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Load uploaded_videos.json
        if not uploaded_videos_file.exists():
            print("❌ No uploaded_videos.json found. Nothing to verify.")
            return
        
        with open(uploaded_videos_file, 'r') as f:
            uploaded_post_ids = json.load(f)
        
        print(f"📄 Loaded {len(uploaded_post_ids)} post IDs from uploaded_videos.json")
        print(f"🔍 Checking each video in S3...\n")
        
        # Get all files in S3 videos/ directory
        print("📥 Fetching S3 file list...")
        s3_video_ids = set()
        continuation_token = None
        
        while True:
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
                        filename = key.split('/')[-1]
                        post_id = filename.split('.')[0]
                        
                        if post_id.isdigit():
                            s3_video_ids.add(post_id)
            
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
        
        print(f"✅ Found {len(s3_video_ids)} videos in S3\n")
        
        # Compare JSON vs S3
        missing_in_s3 = []
        verified_in_s3 = []
        
        print("🔍 Verifying each post ID...\n")
        
        for post_id in uploaded_post_ids:
            if post_id in s3_video_ids:
                verified_in_s3.append(post_id)
            else:
                missing_in_s3.append(post_id)
                print(f"⚠️  Post {post_id}: Marked as uploaded but NOT in S3!")
        
        # Results
        print("\n" + "=" * 80)
        print("VERIFICATION RESULTS")
        print("=" * 80)
        print(f"Total in JSON:          {len(uploaded_post_ids)}")
        print(f"✅ Verified in S3:      {len(verified_in_s3)}")
        print(f"❌ Missing from S3:     {len(missing_in_s3)}")
        print("=" * 80)
        
        if missing_in_s3:
            print(f"\n⚠️  Found {len(missing_in_s3)} videos marked as uploaded but missing from S3!")
            print(f"\nMissing Post IDs:")
            for post_id in missing_in_s3[:20]:  # Show first 20
                print(f"  - {post_id}")
            if len(missing_in_s3) > 20:
                print(f"  ... and {len(missing_in_s3) - 20} more")
            
            print(f"\n🔧 FIX OPTIONS:")
            print(f"1. Clean JSON (remove missing entries so they can be re-uploaded)")
            print(f"2. Keep JSON as-is (if you know these videos were intentionally skipped)")
            print()
            
            choice = input("Do you want to clean the JSON file? (yes/no): ").strip().lower()
            
            if choice in ['yes', 'y']:
                # Create backup
                backup_file = 'uploaded_videos_backup.json'
                with open(backup_file, 'w') as f:
                    json.dump(uploaded_post_ids, f, indent=2)
                print(f"\n💾 Backup saved to: {backup_file}")
                
                # Clean the JSON - keep only verified entries
                with open(uploaded_videos_file, 'w') as f:
                    json.dump(verified_in_s3, f, indent=2)
                
                print(f"✅ Cleaned uploaded_videos.json")
                print(f"   Removed {len(missing_in_s3)} missing entries")
                print(f"   Kept {len(verified_in_s3)} verified entries")
                print(f"\n🔄 These {len(missing_in_s3)} videos will be re-uploaded on next run!")
            else:
                print("\n⏭️  No changes made to uploaded_videos.json")
        else:
            print("\n✅ Perfect! All videos in JSON are verified in S3!")
            print("   No cleanup needed.")
        
        # Show extra videos in S3 (not in JSON)
        extra_in_s3 = s3_video_ids - set(uploaded_post_ids)
        if extra_in_s3:
            print(f"\n📊 Note: Found {len(extra_in_s3)} videos in S3 not tracked in JSON")
            print("   (This is normal if you uploaded directly or from another machine)")
        
        print("\n" + "=" * 80)
        
    except NoCredentialsError:
        print("❌ Error: AWS credentials not found")
        print("   Please check your .env file")
    except ClientError as e:
        print(f"❌ Error accessing S3: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_uploads()

