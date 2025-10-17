# WordPress to S3 Video Uploader (API Mode)

A Python script that fetches posts from a WordPress API, extracts YouTube videos, and uploads them to AWS S3 using the **WordPress post ID** as the filename.

## 🎯 What This Does

This script is designed for your specific workflow:
1. **Fetches posts** from your WordPress site (sardertv.com) via REST API
2. **Extracts YouTube video URLs** from the post content
3. **Downloads videos** and streams them directly to S3
4. **Names files using WordPress Post IDs** (e.g., `45424.mp4`, `45283.mp4`)
5. **No local storage** - uses temporary files that are auto-deleted
6. **Tracks uploaded posts** to prevent duplicates

## ✨ Key Differences from Channel Mode

| Feature | Channel Mode (`youtube_to_s3.py`) | API Mode (`youtube_to_s3_api.py`) |
|---------|-----------------------------------|-----------------------------------|
| **Source** | Entire YouTube channel | WordPress API posts |
| **Filename** | YouTube video ID | WordPress post ID |
| **Selection** | All channel videos | Only posts with YouTube videos |
| **Control** | Channel-based | Application-based |

## 📋 Prerequisites

- Python 3.7 or higher
- AWS account with S3 access
- AWS credentials (Access Key ID and Secret Access Key)
- An S3 bucket created in your AWS account
- Access to WordPress REST API (public or authenticated)

## 🚀 Installation

1. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure environment variables**

Copy `env.example` to `.env`:

```bash
cp env.example .env
```

Then edit `.env` with your values:

```env
# WordPress API Configuration
WORDPRESS_API_URL=https://sardertv.com/wp-json/wp/v2/posts
MAX_POSTS=10

# AWS S3 Configuration
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## ⚙️ Configuration

### Required Environment Variables

- `S3_BUCKET_NAME`: Name of your AWS S3 bucket
- `AWS_ACCESS_KEY_ID`: Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key

### Optional Environment Variables

- `WORDPRESS_API_URL`: WordPress REST API endpoint (default: `https://sardertv.com/wp-json/wp/v2/posts`)
- `AWS_REGION`: AWS region where your S3 bucket is located (default: `us-east-1`)
- `MAX_POSTS`: Maximum number of posts to process (leave empty for all posts)

## 📖 Usage

Run the script:

```bash
python youtube_to_s3_api.py
```

### What Happens:

1. **Fetches posts from WordPress API**
   - Fetches 100 posts per page
   - Continues until all posts are retrieved or MAX_POSTS is reached

2. **Extracts YouTube URLs**
   - Parses HTML content from `content.rendered`
   - Supports multiple URL formats:
     - Embedded iframes: `youtube.com/embed/VIDEO_ID`
     - Short URLs: `youtu.be/VIDEO_ID`
     - Full URLs: `youtube.com/watch?v=VIDEO_ID`

3. **Filters already uploaded**
   - Checks `uploaded_videos.json` for processed post IDs
   - Skips posts that have already been uploaded

4. **Streams to S3**
   - Downloads video to temporary file
   - Uploads to S3 as `wordpress_videos/POST_ID.ext`
   - Automatically deletes temporary file

5. **Displays summary**
   - Shows successful and failed uploads
   - Updates tracking file

## 📁 S3 Structure

Videos are organized in your S3 bucket:

```
your-bucket-name/
└── wordpress_videos/
    ├── 45424.mp4          # Post ID 45424
    ├── 45283.mp4          # Post ID 45283
    ├── 45100.mp4          # Post ID 45100
    └── ...
```

Each file includes metadata:
- `post_id`: WordPress post ID
- `post_title`: Post title
- `youtube_url`: Original YouTube URL
- `upload_date`: Upload timestamp

## 📊 Examples

### Process all posts with YouTube videos

```bash
# In .env file:
WORDPRESS_API_URL=https://sardertv.com/wp-json/wp/v2/posts
MAX_POSTS=
```

### Process only the latest 10 posts

```bash
# In .env file:
MAX_POSTS=10
```

### Use a different WordPress site

```bash
# In .env file:
WORDPRESS_API_URL=https://yoursite.com/wp-json/wp/v2/posts
```

## 🔍 WordPress API Details

The script expects WordPress REST API v2 format with posts containing:

```json
{
  "id": 45424,
  "title": {
    "rendered": "Post Title"
  },
  "content": {
    "rendered": "<iframe src='https://www.youtube.com/embed/VIDEO_ID'></iframe>"
  }
}
```

### API Pagination

- Fetches 100 posts per page automatically
- Respects `X-WP-TotalPages` header
- Stops when no more posts or MAX_POSTS reached

### Supported YouTube URL Formats

The script automatically detects:
- ✅ `https://www.youtube.com/embed/VIDEO_ID`
- ✅ `https://youtu.be/VIDEO_ID`
- ✅ `https://www.youtube.com/watch?v=VIDEO_ID`

## 🛡️ Duplicate Prevention

The script maintains `uploaded_videos.json` tracking:

```json
[
  "45424",
  "45283",
  "45100"
]
```

To re-upload a post, remove its ID from this file.

## 🐛 Troubleshooting

### "Error: API returned status code 404"
- Verify the WordPress API URL is correct
- Check if the site has public API access enabled
- Try accessing the URL in your browser

### "No new posts to process"
- All posts may already be uploaded (check `uploaded_videos.json`)
- Posts may not contain YouTube videos
- API may be returning no results

### "Error during streaming"
- Check YouTube URL is valid and video is available
- Verify your internet connection
- Some videos may be region-restricted

### YouTube Extraction Failed
- Post content may not contain YouTube videos
- Video might be embedded using a different method
- Check the `content.rendered` field format

## 🔐 AWS IAM Permissions

Your AWS user/role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```

## 📝 Notes

- **No local storage** - Uses system temp directory
- **Automatic cleanup** - Temp files always deleted
- **Resume capability** - Can stop and restart anytime
- **Post ID naming** - Files named by WordPress post ID, not YouTube ID
- **Metadata preserved** - S3 objects include post information
- **Public API** - No authentication required for sardertv.com API

## 🔄 Workflow Comparison

### Traditional Channel Mode:
```
YouTube Channel → All Videos → S3 (named by YouTube ID)
```

### API Mode (Your Workflow):
```
WordPress API → Posts with Videos → S3 (named by Post ID)
```

This gives you **application-level control** over which videos to back up!

## 📞 Support

Common issues:
1. **Missing videos**: Not all posts have YouTube embeds
2. **Slow uploads**: Large videos take time, be patient
3. **API limits**: WordPress may rate limit requests

## ⚡ Performance

- **API fetching**: ~1-2 seconds per 100 posts
- **Video download**: Depends on video size and internet speed
- **S3 upload**: Simultaneous with download (streaming)
- **Total time**: Mainly limited by video download speed

## 🎓 Example Output

```
WordPress to S3 Video Uploader
============================================================
API URL: https://sardertv.com/wp-json/wp/v2/posts
S3 Bucket: my-videos-bucket
AWS Region: us-east-1
Max Posts: All
============================================================
Fetching posts from: https://sardertv.com/wp-json/wp/v2/posts
Fetching page 1... (100 posts)
Fetching page 2... (45 posts)

Found 12 new posts with YouTube videos to process.

============================================================
Starting to process 12 posts
Mode: Direct streaming to S3
============================================================

[1/12] Processing Post ID: 45424
Title: Full Interview – Sebastien Page
YouTube URL: https://www.youtube.com/watch?v=1ArkKtDlGOc

Streaming video directly to S3: https://www.youtube.com/watch?v=1ArkKtDlGOc
Downloading video...
Progress: 100% | Speed: 5.2MiB/s | ETA: 00:00
Download completed, now processing...
✓ Downloaded to temporary file
Uploading to S3: wordpress_videos/45424.mp4
Upload progress: 100.0%
✓ Streamed successfully to s3://my-videos-bucket/wordpress_videos/45424.mp4
✓ Cleaned up temporary file

------------------------------------------------------------

============================================================
SUMMARY
============================================================
Total posts processed: 12
Successful uploads: 11
Failed uploads: 1
============================================================
```

## 📄 License

This project is provided as-is for educational and personal use.

## ⚠️ Disclaimer

- Respect YouTube's Terms of Service
- Only download videos you have permission to download
- Be aware of copyright restrictions
- Ensure WordPress API usage complies with site policies

