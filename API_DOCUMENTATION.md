# WordPress to S3 Video Uploader - API Documentation

## Overview

This REST API provides endpoints to manage and monitor the process of uploading YouTube videos from WordPress posts to AWS S3 buckets.

## Running the API Server

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your environment variables in `.env` file:
```env
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=your-bucket-name

# WordPress API
WORDPRESS_API_URL=https://sardertv.com/wp-json/wp/v2/posts

# API Server Configuration (optional)
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
```

3. Start the API server:
```bash
python api_server.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### 1. Health Check

Check if the API server is running.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-27T10:30:00.123456",
  "service": "WordPress to S3 Video Uploader API"
}
```

**Example:**
```bash
curl http://localhost:5000/api/health
```

---

### 2. Get Pending Videos

Get a list of videos that will be uploaded to S3 (not yet uploaded).

**Endpoint:** `GET /api/videos/pending`

**Query Parameters:**
- `max_posts` (optional): Maximum number of posts to return

**Response:**
```json
{
  "success": true,
  "count": 5,
  "posts": [
    {
      "id": "12345",
      "title": "Video Title",
      "youtube_url": "https://www.youtube.com/watch?v=abc123",
      "date": "2025-10-27T10:00:00"
    }
  ],
  "s3_bucket": "your-bucket-name",
  "timestamp": "2025-10-27T10:30:00.123456"
}
```

**Examples:**
```bash
# Get all pending videos
curl http://localhost:5000/api/videos/pending

# Get only 10 pending videos
curl http://localhost:5000/api/videos/pending?max_posts=10
```

---

### 3. Get Uploaded Videos

Get a list of post IDs that have already been uploaded to S3.

**Endpoint:** `GET /api/videos/uploaded`

**Response:**
```json
{
  "success": true,
  "count": 150,
  "uploaded_post_ids": ["12345", "12346", "12347"],
  "timestamp": "2025-10-27T10:30:00.123456"
}
```

**Example:**
```bash
curl http://localhost:5000/api/videos/uploaded
```

---

### 4. Get Statistics

Get statistics about uploaded and pending videos.

**Endpoint:** `GET /api/videos/stats`

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_uploaded": 150,
    "pending_uploads": 25,
    "s3_bucket": "your-bucket-name",
    "aws_region": "us-east-1"
  },
  "timestamp": "2025-10-27T10:30:00.123456"
}
```

**Example:**
```bash
curl http://localhost:5000/api/videos/stats
```

---

### 5. Get Upload Status

Get the current status of the upload process.

**Endpoint:** `GET /api/upload/status`

**Response:**
```json
{
  "success": true,
  "status": {
    "is_running": true,
    "current_post_index": 3,
    "total_posts": 10,
    "successful_uploads": 2,
    "failed_uploads": 0,
    "current_post": {
      "id": "12347",
      "title": "Current Video Title",
      "youtube_url": "https://www.youtube.com/watch?v=xyz789"
    },
    "started_at": "2025-10-27T10:25:00.000000",
    "completed_at": null
  },
  "timestamp": "2025-10-27T10:30:00.123456"
}
```

**Example:**
```bash
curl http://localhost:5000/api/upload/status
```

---

### 6. Start Upload Process

Start the background upload process to upload videos to S3.

**Endpoint:** `POST /api/upload/start`

**Request Body (JSON, optional):**
```json
{
  "max_posts": 10
}
```

**Response:**
```json
{
  "success": true,
  "message": "Upload process started",
  "max_posts": 10,
  "timestamp": "2025-10-27T10:30:00.123456"
}
```

**Examples:**
```bash
# Start uploading all pending videos
curl -X POST http://localhost:5000/api/upload/start

# Start uploading only 5 videos
curl -X POST http://localhost:5000/api/upload/start \
  -H "Content-Type: application/json" \
  -d '{"max_posts": 5}'
```

---

### 7. Get Configuration

Get the current configuration (without sensitive data).

**Endpoint:** `GET /api/config`

**Response:**
```json
{
  "success": true,
  "config": {
    "wordpress_api_url": "https://sardertv.com/wp-json/wp/v2/posts",
    "s3_bucket_name": "your-bucket-name",
    "aws_region": "us-east-1",
    "max_posts_default": null
  },
  "timestamp": "2025-10-27T10:30:00.123456"
}
```

**Example:**
```bash
curl http://localhost:5000/api/config
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK` - Request succeeded
- `202 Accepted` - Upload process started (async operation)
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Endpoint not found
- `409 Conflict` - Upload process already running
- `500 Internal Server Error` - Server error

---

## Example Workflow

### 1. Check API Health
```bash
curl http://localhost:5000/api/health
```

### 2. Get List of Pending Videos
```bash
curl http://localhost:5000/api/videos/pending?max_posts=5
```

### 3. Start Upload Process
```bash
curl -X POST http://localhost:5000/api/upload/start \
  -H "Content-Type: application/json" \
  -d '{"max_posts": 5}'
```

### 4. Monitor Upload Progress
```bash
# Keep checking status until upload is complete
curl http://localhost:5000/api/upload/status
```

### 5. Check Statistics
```bash
curl http://localhost:5000/api/videos/stats
```

---

## Using with JavaScript/Frontend

### Fetch Pending Videos
```javascript
fetch('http://localhost:5000/api/videos/pending?max_posts=10')
  .then(response => response.json())
  .then(data => {
    console.log('Pending videos:', data.posts);
  });
```

### Start Upload Process
```javascript
fetch('http://localhost:5000/api/upload/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ max_posts: 5 })
})
  .then(response => response.json())
  .then(data => {
    console.log('Upload started:', data);
  });
```

### Monitor Upload Status
```javascript
function checkUploadStatus() {
  fetch('http://localhost:5000/api/upload/status')
    .then(response => response.json())
    .then(data => {
      console.log('Status:', data.status);
      
      if (data.status.is_running) {
        // Still running, check again in 5 seconds
        setTimeout(checkUploadStatus, 5000);
      } else {
        console.log('Upload complete!');
      }
    });
}

checkUploadStatus();
```

---

## Notes

- The upload process runs in the background, so you can continue making other API calls
- Only one upload process can run at a time
- The API tracks already uploaded videos to avoid duplicates
- CORS is enabled by default, so you can call the API from web browsers
- Videos are uploaded directly to S3 without storing locally (efficient streaming)

---

## Troubleshooting

### API won't start
- Check if port 5000 is already in use
- Verify all environment variables are set correctly in `.env`
- Ensure dependencies are installed: `pip install -r requirements.txt`

### Can't fetch pending videos
- Verify `WORDPRESS_API_URL` is correct
- Check internet connection
- Ensure WordPress API is accessible

### Upload fails
- Verify AWS credentials are correct
- Check S3 bucket exists and you have write permissions
- Ensure sufficient disk space for temporary files
- Verify YouTube videos are accessible

---

## Security Recommendations

- Run the API behind a reverse proxy (nginx, Apache) in production
- Use HTTPS for production deployments
- Implement authentication/authorization for sensitive endpoints
- Never expose AWS credentials in API responses
- Consider rate limiting for production use

