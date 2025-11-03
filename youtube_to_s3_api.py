#!/usr/bin/env python3
"""
WordPress Posts to S3 Video Uploader

This script fetches posts from a WordPress API, extracts YouTube videos,
and uploads them to S3 using the WordPress post ID as the filename.
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from yt_dlp import YoutubeDL
from pathlib import Path
from datetime import datetime
import json
import tempfile
import re
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class WordPressToS3:
    def __init__(self, api_url, s3_bucket_name, aws_region='us-east-1'):
        """
        Initialize the WordPress to S3 uploader.
        
        Args:
            api_url (str): WordPress API endpoint
            s3_bucket_name (str): Name of the S3 bucket
            aws_region (str): AWS region for S3 bucket
        """
        self.api_url = api_url
        self.s3_bucket_name = s3_bucket_name
        self.aws_region = aws_region
        
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
        """Load the list of already uploaded post IDs."""
        if self.uploaded_videos_file.exists():
            with open(self.uploaded_videos_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_uploaded_videos(self):
        """Save the list of uploaded post IDs."""
        with open(self.uploaded_videos_file, 'w') as f:
            json.dump(self.uploaded_videos, f, indent=2)
    
    def extract_youtube_url(self, html_content):
        """
        Extract YouTube video URL from HTML content.
        Handles various formats including malformed URLs.
        
        Args:
            html_content (str): HTML content from WordPress post
            
        Returns:
            str: YouTube video URL or None if not found
        """
        # Pattern 1: YouTube embed iframe
        # Example: https://www.youtube.com/embed/1ArkKtDlGOc
        embed_pattern = r'youtube\.com/embed/([a-zA-Z0-9_-]{11})'
        match = re.search(embed_pattern, html_content)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
        
        # Pattern 2: YouTube short URL (standard)
        # Example: https://youtu.be/1ArkKtDlGOc
        short_pattern = r'youtu\.be/([a-zA-Z0-9_-]{11})'
        match = re.search(short_pattern, html_content)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
        
        # Pattern 3: Full YouTube watch URL
        # Example: https://www.youtube.com/watch?v=1ArkKtDlGOc
        watch_pattern = r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})'
        match = re.search(watch_pattern, html_content)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
        
        # Pattern 4: Malformed youtu.be with watch?v= format
        # Example: http://youtu.be/watch?v=iDtprDhz4v8
        malformed_short = r'youtu\.be/watch\?v=([a-zA-Z0-9_-]{11})'
        match = re.search(malformed_short, html_content)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
        
        # Pattern 5: Extract any YouTube video ID (11 chars alphanumeric)
        # This catches most edge cases
        video_id_pattern = r'(?:youtube\.com|youtu\.be)(?:/|/watch\?v=|/embed/)([a-zA-Z0-9_-]{11})'
        match = re.search(video_id_pattern, html_content)
        if match:
            video_id = match.group(1)
            # Validate it's not a known invalid ID
            if video_id not in ['watch', 'embed', 'https', 'http']:
                return f"https://www.youtube.com/watch?v={video_id}"
        
        return None
    
    def fetch_posts_from_api(self, max_posts=None):
        """
        Fetch posts from WordPress API.
        
        Args:
            max_posts (int): Maximum number of posts to fetch (None for all available)
            
        Returns:
            list: List of post dictionaries with id, title, and youtube_url
        """
        posts = []
        page = 1
        per_page = 100  # Fetch 100 posts per page
        
        print(f"Fetching posts from: {self.api_url}")
        
        while True:
            try:
                params = {
                    "page": str(page),
                    "per_page": str(per_page),
                    "orderby": "date",
                    "order": "desc"
                }
                
                print(f"Fetching page {page}...", end=' ')
                response = requests.get(self.api_url, params=params, timeout=30)
                
                if response.status_code != 200:
                    print(f"\nError: API returned status code {response.status_code}")
                    break
                
                page_posts = response.json()
                
                if not page_posts:
                    print("(no more posts)")
                    break
                
                print(f"({len(page_posts)} posts)")
                
                for post in page_posts:
                    post_id = str(post.get('id'))
                    
                    # Skip if already uploaded
                    if post_id in self.uploaded_videos:
                        continue
                    
                    # Extract YouTube URL from content
                    content = post.get('content', {}).get('rendered', '')
                    youtube_url = self.extract_youtube_url(content)
                    
                    if youtube_url:
                        posts.append({
                            'id': post_id,
                            'title': post.get('title', {}).get('rendered', 'Unknown'),
                            'youtube_url': youtube_url,
                            'date': post.get('date', '')
                        })
                        
                        if max_posts and len(posts) >= max_posts:
                            break
                
                if max_posts and len(posts) >= max_posts:
                    break
                
                # Check if there are more pages
                total_pages = response.headers.get('X-WP-TotalPages')
                if total_pages and page >= int(total_pages):
                    break
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"\nError fetching posts: {e}")
                break
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                break
        
        print(f"\nFound {len(posts)} new posts with YouTube videos to process.")
        return posts
    
    def download_and_stream_to_s3(self, youtube_url, post_id, post_title):
        """
        Download video and stream directly to S3 without storing locally.
        Uses a temporary file that is automatically cleaned up.
        
        Args:
            youtube_url (str): YouTube video URL
            post_id (str): WordPress post ID (used for filename)
            post_title (str): Title of the post
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\nStreaming video directly to S3: {youtube_url}")
        
        # Create temporary file that will be auto-deleted
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Download to temporary file
            # Use 'best' format to avoid needing ffmpeg for merging
            ydl_opts = {
                'format': 'best[ext=mp4]/best',  # Download best single file (no merging needed)
                'outtmpl': tmp_path,
                'quiet': False,
                'no_warnings': False,
                'progress_hooks': [self.download_progress_hook],
                'overwrites': True,  # Always overwrite existing files
                'nopart': True,  # Don't use .part files
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            # Use cookies if available
            cookies_file = Path('cookies.txt')
            if cookies_file.exists():
                ydl_opts['cookiefile'] = str(cookies_file)
            
            print("Downloading video...")
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
                if not os.path.exists(tmp_path):
                    print(f"[ERROR] Download failed: File not created")
                    return False
                
                # Verify file has content
                file_size = os.path.getsize(tmp_path)
                if file_size == 0:
                    print(f"[ERROR] Download failed: File is empty (0 bytes)")
                    return False
                
                # Get the actual extension from the downloaded file
                actual_ext = info.get('ext', 'mp4')
                
                print(f"[OK] Downloaded to temporary file ({file_size / 1024 / 1024:.2f} MB)")
                
                # Create S3 key using post ID
                s3_key = f"videos/{post_id}.{actual_ext}"
                
                print(f"Uploading to S3: {s3_key}")
                
                # Sanitize metadata to remove non-ASCII characters
                def sanitize_metadata(text):
                    """Remove non-ASCII characters for S3 metadata"""
                    return text.encode('ascii', errors='ignore').decode('ascii')
                
                # Upload directly from temp file with streaming
                with open(tmp_path, 'rb') as f:
                    self.s3_client.upload_fileobj(
                        f,
                        self.s3_bucket_name,
                        s3_key,
                        Callback=self.upload_progress_callback(file_size),
                        ExtraArgs={
                            'Metadata': {
                                'post-id': post_id,
                                'post-title': sanitize_metadata(post_title[:1000]),
                                'youtube-url': youtube_url[:1000],
                                'upload-date': datetime.now().isoformat()
                            }
                        }
                    )
                
                print(f"\n[OK] Streamed successfully to s3://{self.s3_bucket_name}/{s3_key}")
                return True
                
        except Exception as e:
            print(f"[ERROR] Error during streaming: {e}")
            return False
        finally:
            # Always clean up the temporary file
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    print(f"[OK] Cleaned up temporary file")
            except Exception as e:
                print(f"Warning: Could not delete temporary file: {e}")
    
    def download_progress_hook(self, d):
        """Hook to display download progress."""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            print(f"\rProgress: {percent} | Speed: {speed} | ETA: {eta}", end='')
        elif d['status'] == 'finished':
            print("\nDownload completed, now processing...")
    
    def upload_progress_callback(self, file_size):
        """Create a callback function for upload progress."""
        uploaded_bytes = [0]
        
        def callback(bytes_amount):
            uploaded_bytes[0] += bytes_amount
            percent = (uploaded_bytes[0] / file_size) * 100
            print(f"\rUpload progress: {percent:.1f}%", end='')
        
        return callback
    
    def process_posts(self, max_posts=None):
        """
        Main process to fetch posts, download videos, and upload to S3.
        
        Args:
            max_posts (int): Maximum number of posts to process
        """
        posts = self.fetch_posts_from_api(max_posts)
        
        if not posts:
            print("No new posts to process.")
            return
        
        print(f"\n{'='*60}")
        print(f"Starting to process {len(posts)} posts")
        print(f"Mode: Direct streaming to S3")
        print(f"{'='*60}\n")
        
        successful_uploads = 0
        failed_uploads = 0
        
        for idx, post in enumerate(posts, 1):
            print(f"\n[{idx}/{len(posts)}] Processing Post ID: {post['id']}")
            print(f"Title: {post['title']}")
            print(f"YouTube URL: {post['youtube_url']}")
            
            # Stream directly to S3
            success = self.download_and_stream_to_s3(
                post['youtube_url'],
                post['id'],
                post['title']
            )
            
            if success:
                successful_uploads += 1
                # Mark as uploaded
                self.uploaded_videos.append(post['id'])
                self.save_uploaded_videos()
            else:
                failed_uploads += 1
            
            print(f"\n{'-'*60}")
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Total posts processed: {len(posts)}")
        print(f"Successful uploads: {successful_uploads}")
        print(f"Failed uploads: {failed_uploads}")
        print(f"{'='*60}\n")


def main():
    """Main entry point for the script."""
    
    # Get configuration from environment variables
    API_URL = os.getenv('WORDPRESS_API_URL', 'https://sardertv.com/wp-json/wp/v2/posts')
    S3_BUCKET = os.getenv('S3_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    MAX_POSTS = os.getenv('MAX_POSTS')
    
    # Validate required environment variables
    if not S3_BUCKET:
        print("Error: S3_BUCKET_NAME not set in environment variables.")
        print("Please set it in your .env file or environment.")
        sys.exit(1)
    
    # Convert MAX_POSTS to int if set
    max_posts = None
    if MAX_POSTS:
        try:
            max_posts = int(MAX_POSTS)
        except ValueError:
            print(f"Warning: Invalid MAX_POSTS value '{MAX_POSTS}', processing all posts.")
    
    print("WordPress to S3 Video Uploader")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"S3 Bucket: {S3_BUCKET}")
    print(f"AWS Region: {AWS_REGION}")
    print(f"Max Posts: {max_posts if max_posts else 'All'}")
    print("="*60)
    
    # Create and run the uploader
    uploader = WordPressToS3(
        api_url=API_URL,
        s3_bucket_name=S3_BUCKET,
        aws_region=AWS_REGION
    )
    
    try:
        uploader.process_posts(max_posts=max_posts)
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
