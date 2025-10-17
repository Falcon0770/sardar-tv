#!/usr/bin/env python3
"""
YouTube Channel Video Downloader and S3 Uploader

This script downloads videos from a specified YouTube channel and uploads them to an AWS S3 bucket.
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from yt_dlp import YoutubeDL
from pathlib import Path
from datetime import datetime
import json
import subprocess
import tempfile
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class YouTubeToS3:
    def __init__(self, channel_url, s3_bucket_name, aws_region='us-east-1', download_dir='downloads'):
        """
        Initialize the YouTube to S3 uploader.
        
        Args:
            channel_url (str): YouTube channel URL or ID
            s3_bucket_name (str): Name of the S3 bucket
            aws_region (str): AWS region for S3 bucket
            download_dir (str): Local directory to temporarily store downloaded videos
        """
        self.channel_url = channel_url
        self.s3_bucket_name = s3_bucket_name
        self.aws_region = aws_region
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            region_name=aws_region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Track uploaded videos to avoid duplicates
        self.uploaded_videos_file = Path('uploaded_videos.json')
        self.uploaded_videos = self.load_uploaded_videos()
    
    def load_uploaded_videos(self):
        """Load the list of already uploaded video IDs."""
        if self.uploaded_videos_file.exists():
            with open(self.uploaded_videos_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_uploaded_videos(self):
        """Save the list of uploaded video IDs."""
        with open(self.uploaded_videos_file, 'w') as f:
            json.dump(self.uploaded_videos, f, indent=2)
    
    def get_channel_videos(self, max_videos=None):
        """
        Get list of videos from the YouTube channel.
        
        Args:
            max_videos (int): Maximum number of videos to fetch (None for all)
            
        Returns:
            list: List of video information dictionaries
        """
        ydl_opts = {
            'quiet': False,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        
        print(f"Fetching videos from channel: {self.channel_url}")
        
        with YoutubeDL(ydl_opts) as ydl:
            try:
                playlist_info = ydl.extract_info(self.channel_url, download=False)
                
                if 'entries' not in playlist_info:
                    print("No videos found in the channel.")
                    return []
                
                videos = []
                for entry in playlist_info['entries']:
                    if entry is None:
                        continue
                    
                    video_id = entry.get('id')
                    if video_id and video_id not in self.uploaded_videos:
                        videos.append({
                            'id': video_id,
                            'title': entry.get('title', 'Unknown'),
                            'url': f"https://www.youtube.com/watch?v={video_id}"
                        })
                    
                    if max_videos and len(videos) >= max_videos:
                        break
                
                print(f"Found {len(videos)} new videos to process.")
                return videos
                
            except Exception as e:
                print(f"Error fetching channel videos: {e}")
                return []
    
    def download_and_stream_to_s3(self, video_url, video_id, video_title):
        """
        Download video and stream directly to S3 without storing locally.
        Uses a temporary file that is automatically cleaned up.
        
        Args:
            video_url (str): URL of the video to download
            video_id (str): YouTube video ID
            video_title (str): Title of the video
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\nStreaming video directly to S3: {video_url}")
        
        # Create temporary file that will be auto-deleted
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Download to temporary file
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': tmp_path,
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [self.download_progress_hook],
            }
            
            print("Downloading video...")
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                if not os.path.exists(tmp_path):
                    print(f"✗ Download failed: File not created")
                    return False
                
                # Get the actual extension from the downloaded file
                actual_ext = info.get('ext', 'mp4')
                
                print(f"✓ Downloaded to temporary file")
                
                # Create S3 key
                timestamp = datetime.now().strftime("%Y%m%d")
                s3_key = f"youtube_videos/{timestamp}/{video_id}.{actual_ext}"
                
                print(f"Uploading to S3: {s3_key}")
                
                # Get file size for progress
                file_size = os.path.getsize(tmp_path)
                
                # Upload directly from temp file with streaming
                with open(tmp_path, 'rb') as f:
                    self.s3_client.upload_fileobj(
                        f,
                        self.s3_bucket_name,
                        s3_key,
                        Callback=self.upload_progress_callback(file_size),
                        ExtraArgs={
                            'Metadata': {
                                'video_id': video_id,
                                'video_title': video_title[:1000],  # Metadata has size limits
                                'upload_date': datetime.now().isoformat()
                            }
                        }
                    )
                
                print(f"\n✓ Streamed successfully to s3://{self.s3_bucket_name}/{s3_key}")
                return True
                
        except Exception as e:
            print(f"✗ Error during streaming: {e}")
            return False
        finally:
            # Always clean up the temporary file
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    print(f"✓ Cleaned up temporary file")
            except Exception as e:
                print(f"Warning: Could not delete temporary file: {e}")
    
    def download_video(self, video_url, video_id):
        """
        Download a single video from YouTube.
        
        Args:
            video_url (str): URL of the video to download
            video_id (str): YouTube video ID
            
        Returns:
            str: Path to the downloaded video file, or None if failed
        """
        output_template = str(self.download_dir / f"{video_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self.download_progress_hook],
        }
        
        print(f"\nDownloading video: {video_url}")
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                
                if os.path.exists(filename):
                    print(f"✓ Downloaded: {filename}")
                    return filename
                else:
                    print(f"✗ Download failed: File not found")
                    return None
                    
        except Exception as e:
            print(f"✗ Error downloading video: {e}")
            return None
    
    def download_progress_hook(self, d):
        """Hook to display download progress."""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"\rProgress: {percent} | Speed: {speed} | ETA: {eta}", end='')
        elif d['status'] == 'finished':
            print("\nDownload completed, now processing...")
    
    def upload_to_s3(self, file_path, video_id, video_title):
        """
        Upload a file to S3 bucket.
        
        Args:
            file_path (str): Path to the file to upload
            video_id (str): YouTube video ID
            video_title (str): Title of the video
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        file_path = Path(file_path)
        
        # Create a clean S3 key (path in bucket)
        timestamp = datetime.now().strftime("%Y%m%d")
        s3_key = f"youtube_videos/{timestamp}/{video_id}_{file_path.name}"
        
        print(f"\nUploading to S3: {s3_key}")
        
        try:
            # Get file size for progress
            file_size = file_path.stat().st_size
            
            # Upload with progress callback
            self.s3_client.upload_file(
                str(file_path),
                self.s3_bucket_name,
                s3_key,
                Callback=self.upload_progress_callback(file_size),
                ExtraArgs={
                    'Metadata': {
                        'video_id': video_id,
                        'video_title': video_title,
                        'upload_date': datetime.now().isoformat()
                    }
                }
            )
            
            print(f"\n✓ Uploaded successfully to s3://{self.s3_bucket_name}/{s3_key}")
            return True
            
        except NoCredentialsError:
            print("✗ AWS credentials not found. Please configure your credentials.")
            return False
        except ClientError as e:
            print(f"✗ Error uploading to S3: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error during upload: {e}")
            return False
    
    def upload_progress_callback(self, file_size):
        """Create a callback function for upload progress."""
        uploaded_bytes = [0]
        
        def callback(bytes_amount):
            uploaded_bytes[0] += bytes_amount
            percent = (uploaded_bytes[0] / file_size) * 100
            print(f"\rUpload progress: {percent:.1f}%", end='')
        
        return callback
    
    def cleanup_local_file(self, file_path):
        """Delete the local video file after upload."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✓ Cleaned up local file: {file_path}")
        except Exception as e:
            print(f"✗ Error cleaning up file: {e}")
    
    def process_videos(self, max_videos=None, keep_local=False, direct_stream=True):
        """
        Main process to download and upload videos.
        
        Args:
            max_videos (int): Maximum number of videos to process
            keep_local (bool): Keep local files after upload (only used if direct_stream=False)
            direct_stream (bool): Stream directly to S3 without local storage (default: True)
        """
        videos = self.get_channel_videos(max_videos)
        
        if not videos:
            print("No new videos to process.")
            return
        
        print(f"\n{'='*60}")
        print(f"Starting to process {len(videos)} videos")
        print(f"Mode: {'Direct streaming to S3' if direct_stream else 'Download then upload'}")
        print(f"{'='*60}\n")
        
        successful_uploads = 0
        failed_uploads = 0
        
        for idx, video in enumerate(videos, 1):
            print(f"\n[{idx}/{len(videos)}] Processing: {video['title']}")
            print(f"Video ID: {video['id']}")
            
            if direct_stream:
                # Stream directly to S3 without local storage
                success = self.download_and_stream_to_s3(video['url'], video['id'], video['title'])
                
                if success:
                    successful_uploads += 1
                    # Mark as uploaded
                    self.uploaded_videos.append(video['id'])
                    self.save_uploaded_videos()
                else:
                    failed_uploads += 1
            else:
                # Traditional download then upload approach
                file_path = self.download_video(video['url'], video['id'])
                
                if file_path:
                    # Upload to S3
                    upload_success = self.upload_to_s3(file_path, video['id'], video['title'])
                    
                    if upload_success:
                        successful_uploads += 1
                        # Mark as uploaded
                        self.uploaded_videos.append(video['id'])
                        self.save_uploaded_videos()
                        
                        # Cleanup local file unless user wants to keep it
                        if not keep_local:
                            self.cleanup_local_file(file_path)
                    else:
                        failed_uploads += 1
                else:
                    failed_uploads += 1
            
            print(f"\n{'-'*60}")
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total videos processed: {len(videos)}")
        print(f"Successful uploads: {successful_uploads}")
        print(f"Failed uploads: {failed_uploads}")
        print(f"{'='*60}\n")


def main():
    """Main entry point for the script."""
    
    # Get configuration from environment variables
    CHANNEL_URL = os.getenv('YOUTUBE_CHANNEL_URL')
    S3_BUCKET = os.getenv('S3_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    MAX_VIDEOS = os.getenv('MAX_VIDEOS')
    KEEP_LOCAL = os.getenv('KEEP_LOCAL_FILES', 'false').lower() == 'true'
    DIRECT_STREAM = os.getenv('DIRECT_STREAM', 'true').lower() == 'true'
    
    # Validate required environment variables
    if not CHANNEL_URL:
        print("Error: YOUTUBE_CHANNEL_URL not set in environment variables.")
        print("Please set it in your .env file or environment.")
        sys.exit(1)
    
    if not S3_BUCKET:
        print("Error: S3_BUCKET_NAME not set in environment variables.")
        print("Please set it in your .env file or environment.")
        sys.exit(1)
    
    # Convert MAX_VIDEOS to int if set
    max_videos = None
    if MAX_VIDEOS:
        try:
            max_videos = int(MAX_VIDEOS)
        except ValueError:
            print(f"Warning: Invalid MAX_VIDEOS value '{MAX_VIDEOS}', processing all videos.")
    
    print("YouTube to S3 Video Uploader")
    print("="*60)
    print(f"Channel URL: {CHANNEL_URL}")
    print(f"S3 Bucket: {S3_BUCKET}")
    print(f"AWS Region: {AWS_REGION}")
    print(f"Max Videos: {max_videos if max_videos else 'All'}")
    print(f"Direct Stream: {DIRECT_STREAM}")
    print(f"Keep Local Files: {KEEP_LOCAL if not DIRECT_STREAM else 'N/A (streaming mode)'}")
    print("="*60)
    
    # Create and run the uploader
    uploader = YouTubeToS3(
        channel_url=CHANNEL_URL,
        s3_bucket_name=S3_BUCKET,
        aws_region=AWS_REGION
    )
    
    try:
        uploader.process_videos(max_videos=max_videos, keep_local=KEEP_LOCAL, direct_stream=DIRECT_STREAM)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

