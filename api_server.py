#!/usr/bin/env python3
"""
REST API Server for WordPress to S3 Video Uploader

This API provides endpoints to:
- Get list of videos that will be uploaded
- Trigger upload process
- Check upload status
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from youtube_to_s3_api import WordPressToS3
import threading
import json
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables for tracking upload status
upload_status = {
    "is_running": False,
    "current_post_index": 0,
    "total_posts": 0,
    "successful_uploads": 0,
    "failed_uploads": 0,
    "current_post": None,
    "started_at": None,
    "completed_at": None
}


def get_uploader_instance():
    """Create and return a WordPressToS3 instance with environment configuration."""
    API_URL = os.getenv('WORDPRESS_API_URL', 'https://sardertv.com/wp-json/wp/v2/posts')
    S3_BUCKET = os.getenv('S3_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    if not S3_BUCKET:
        raise ValueError("S3_BUCKET_NAME not set in environment variables")
    
    return WordPressToS3(
        api_url=API_URL,
        s3_bucket_name=S3_BUCKET,
        aws_region=AWS_REGION
    )


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "WordPress to S3 Video Uploader API"
    }), 200


@app.route('/api/videos/pending', methods=['GET'])
def get_pending_videos():
    """
    Get list of videos that will be uploaded to S3.
    
    Query Parameters:
    - max_posts: Maximum number of posts to return (optional)
    
    Returns:
        JSON list of posts with YouTube videos that haven't been uploaded yet
    """
    try:
        # Get max_posts from query parameters
        max_posts = request.args.get('max_posts', type=int)
        
        # Create uploader instance
        uploader = get_uploader_instance()
        
        # Fetch pending posts
        posts = uploader.fetch_posts_from_api(max_posts=max_posts)
        
        return jsonify({
            "success": True,
            "count": len(posts),
            "posts": posts,
            "s3_bucket": uploader.s3_bucket_name,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to fetch pending videos: {str(e)}"
        }), 500


@app.route('/api/videos/uploaded', methods=['GET'])
def get_uploaded_videos():
    """
    Get list of video post IDs that have already been uploaded to S3.
    
    Returns:
        JSON list of uploaded post IDs
    """
    try:
        uploader = get_uploader_instance()
        
        return jsonify({
            "success": True,
            "count": len(uploader.uploaded_videos),
            "uploaded_post_ids": uploader.uploaded_videos,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to fetch uploaded videos: {str(e)}"
        }), 500


@app.route('/api/videos/stats', methods=['GET'])
def get_stats():
    """
    Get statistics about videos and uploads.
    
    Returns:
        JSON with statistics about uploaded and pending videos
    """
    try:
        uploader = get_uploader_instance()
        
        # Get pending posts
        pending_posts = uploader.fetch_posts_from_api()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_uploaded": len(uploader.uploaded_videos),
                "pending_uploads": len(pending_posts),
                "s3_bucket": uploader.s3_bucket_name,
                "aws_region": uploader.aws_region
            },
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to fetch stats: {str(e)}"
        }), 500


@app.route('/api/upload/status', methods=['GET'])
def get_upload_status():
    """
    Get current upload process status.
    
    Returns:
        JSON with current upload status
    """
    return jsonify({
        "success": True,
        "status": upload_status,
        "timestamp": datetime.now().isoformat()
    }), 200


def upload_worker(max_posts=None):
    """Background worker to process uploads."""
    global upload_status
    
    try:
        upload_status["is_running"] = True
        upload_status["started_at"] = datetime.now().isoformat()
        
        uploader = get_uploader_instance()
        posts = uploader.fetch_posts_from_api(max_posts=max_posts)
        
        upload_status["total_posts"] = len(posts)
        
        for idx, post in enumerate(posts, 1):
            upload_status["current_post_index"] = idx
            upload_status["current_post"] = {
                "id": post["id"],
                "title": post["title"],
                "youtube_url": post["youtube_url"]
            }
            
            success = uploader.download_and_stream_to_s3(
                post['youtube_url'],
                post['id'],
                post['title']
            )
            
            if success:
                upload_status["successful_uploads"] += 1
                uploader.uploaded_videos.append(post['id'])
                uploader.save_uploaded_videos()
            else:
                upload_status["failed_uploads"] += 1
        
        upload_status["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        print(f"Upload worker error: {e}")
    finally:
        upload_status["is_running"] = False
        upload_status["current_post"] = None


@app.route('/api/upload/start', methods=['POST'])
def start_upload():
    """
    Start the upload process in the background.
    
    Request Body (JSON):
    - max_posts: Maximum number of posts to process (optional)
    
    Returns:
        JSON with upload start status
    """
    global upload_status
    
    if upload_status["is_running"]:
        return jsonify({
            "success": False,
            "error": "Upload process is already running"
        }), 409
    
    try:
        # Reset status
        upload_status = {
            "is_running": False,
            "current_post_index": 0,
            "total_posts": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "current_post": None,
            "started_at": None,
            "completed_at": None
        }
        
        # Get max_posts from request body
        data = request.get_json() or {}
        max_posts = data.get('max_posts')
        
        # Start upload in background thread
        thread = threading.Thread(target=upload_worker, args=(max_posts,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "message": "Upload process started",
            "max_posts": max_posts,
            "timestamp": datetime.now().isoformat()
        }), 202
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to start upload: {str(e)}"
        }), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """
    Get current configuration (without sensitive data).
    
    Returns:
        JSON with current configuration
    """
    return jsonify({
        "success": True,
        "config": {
            "wordpress_api_url": os.getenv('WORDPRESS_API_URL', 'https://sardertv.com/wp-json/wp/v2/posts'),
            "s3_bucket_name": os.getenv('S3_BUCKET_NAME'),
            "aws_region": os.getenv('AWS_REGION', 'us-east-1'),
            "max_posts_default": os.getenv('MAX_POSTS')
        },
        "timestamp": datetime.now().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


def main():
    """Run the Flask API server."""
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'False').lower() == 'true'
    host = os.getenv('API_HOST', '0.0.0.0')
    
    print("=" * 60)
    print("WordPress to S3 Video Uploader API Server")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("\nAvailable Endpoints:")
    print("  GET  /api/health                - Health check")
    print("  GET  /api/videos/pending        - Get pending videos")
    print("  GET  /api/videos/uploaded       - Get uploaded videos")
    print("  GET  /api/videos/stats          - Get statistics")
    print("  GET  /api/upload/status         - Get upload status")
    print("  POST /api/upload/start          - Start upload process")
    print("  GET  /api/config                - Get configuration")
    print("=" * 60)
    print(f"\nAPI is running at: http://{host}:{port}")
    print("\nExample usage:")
    print(f"  curl http://localhost:{port}/api/videos/pending")
    print(f"  curl http://localhost:{port}/api/videos/pending?max_posts=10")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()

