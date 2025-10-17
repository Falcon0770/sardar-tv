# YouTube to S3 Video Uploader

A Python script that automatically downloads videos from a specified YouTube channel and uploads them to an AWS S3 bucket.

## Features

- 🎥 Download videos from any YouTube channel
- ☁️ Automatic upload to AWS S3 bucket
- ⚡ **Direct streaming to S3** - No local storage required! Videos stream directly to S3
- 📊 Progress tracking for downloads and uploads
- 🔄 Duplicate prevention (tracks already uploaded videos)
- 🗑️ Automatic cleanup of temporary files
- ⚙️ Configurable via environment variables
- 📝 Detailed logging and error handling
- 🔀 Two modes: Direct streaming (default) or traditional download-then-upload

## Prerequisites

- Python 3.7 or higher
- AWS account with S3 access
- AWS credentials (Access Key ID and Secret Access Key)
- An S3 bucket created in your AWS account

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

```env
YOUTUBE_CHANNEL_URL=https://www.youtube.com/@yourchannelname
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
MAX_VIDEOS=10
KEEP_LOCAL_FILES=false
```

## Configuration

### Required Environment Variables

- `YOUTUBE_CHANNEL_URL`: The URL of the YouTube channel you want to download from
  - Format examples:
    - `https://www.youtube.com/@channelname`
    - `https://www.youtube.com/channel/CHANNEL_ID`
    - `https://www.youtube.com/c/channelname/videos`

- `S3_BUCKET_NAME`: Name of your AWS S3 bucket

- `AWS_ACCESS_KEY_ID`: Your AWS access key ID

- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key

### Optional Environment Variables

- `AWS_REGION`: AWS region where your S3 bucket is located (default: `us-east-1`)

- `MAX_VIDEOS`: Maximum number of videos to process (leave empty for all videos)

- `DIRECT_STREAM`: Set to `true` to stream videos directly to S3 without storing locally (default: `true`)
  - When enabled, videos are downloaded to a temporary file and immediately streamed to S3, then the temp file is deleted
  - This saves disk space as videos don't accumulate on your machine
  - Recommended for most use cases

- `KEEP_LOCAL_FILES`: Set to `true` to keep downloaded files locally after upload (default: `false`)
  - Only applies when `DIRECT_STREAM=false`

## Usage

Run the script:

```bash
python youtube_to_s3.py
```

The script will:
1. Fetch all videos from the specified YouTube channel
2. Filter out videos that have already been uploaded (tracked in `uploaded_videos.json`)
3. **Direct Streaming Mode (default):**
   - Download each video to a temporary file
   - Immediately stream it to S3 at `youtube_videos/YYYYMMDD/VIDEO_ID.ext`
   - Automatically delete the temporary file
   - **No permanent local storage used!**
4. Traditional Mode (`DIRECT_STREAM=false`):
   - Download each video to the `downloads/` folder
   - Upload to S3
   - Clean up local files (unless `KEEP_LOCAL_FILES=true`)
5. Display a summary of successful and failed uploads

## AWS Credentials

You have three options for providing AWS credentials:

1. **Environment variables** (in `.env` file):
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

2. **AWS CLI configuration**:
   ```bash
   aws configure
   ```

3. **IAM Role** (if running on EC2 or other AWS services)

## S3 Bucket Structure

Videos are uploaded to your S3 bucket with the following structure:

```
your-bucket-name/
└── youtube_videos/
    └── 20241015/              # Date (YYYYMMDD)
        ├── VIDEO_ID1_video.mp4
        ├── VIDEO_ID2_video.mp4
        └── ...
```

Each video file includes metadata:
- `video_id`: YouTube video ID
- `video_title`: Original video title
- `upload_date`: Timestamp of when it was uploaded to S3

## Tracking Uploaded Videos

The script maintains a `uploaded_videos.json` file that tracks which videos have already been uploaded. This prevents duplicate uploads if you run the script multiple times.

To re-upload a video, remove its ID from `uploaded_videos.json`.

## Error Handling

The script includes comprehensive error handling for:
- Invalid YouTube URLs
- Network issues during download
- AWS credential problems
- S3 upload failures
- Missing environment variables

Errors are logged to the console with descriptive messages.

## Examples

### Stream videos directly to S3 (default, no local storage)

```bash
# In .env file:
YOUTUBE_CHANNEL_URL=https://www.youtube.com/@TechChannel
DIRECT_STREAM=true
```

This is the recommended mode - videos stream directly to S3 through a temporary file that's automatically deleted.

### Download all videos from a channel

```bash
# In .env file:
YOUTUBE_CHANNEL_URL=https://www.youtube.com/@TechChannel
MAX_VIDEOS=
```

### Download only the latest 5 videos

```bash
# In .env file:
MAX_VIDEOS=5
```

### Traditional mode - Keep local copies after upload

```bash
# In .env file:
DIRECT_STREAM=false
KEEP_LOCAL_FILES=true
```

## Troubleshooting

### "No videos found in the channel"
- Verify the channel URL is correct
- Make sure the channel has public videos

### "AWS credentials not found"
- Check that `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set correctly
- Or configure AWS CLI with `aws configure`

### "Error uploading to S3"
- Verify your S3 bucket name is correct
- Check that your AWS credentials have permission to write to the bucket
- Ensure the bucket exists in the specified region

### Download errors
- Check your internet connection
- Some videos may be restricted or unavailable in your region
- The video might be private or deleted

## AWS IAM Permissions

Your AWS user/role needs the following S3 permissions:

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

## Notes

- The script uses `yt-dlp` which is actively maintained and supports a wide range of video formats
- Videos are downloaded in the best available quality (MP4 format preferred)
- **Direct streaming mode (default)** uses minimal disk space - only a temporary file during transfer
- Large channels with many videos may take significant time to process
- Make sure you have sufficient S3 storage quota
- When using traditional mode (`DIRECT_STREAM=false`), ensure you have sufficient disk space for downloads

## License

This project is provided as-is for educational and personal use.

## Disclaimer

- Respect YouTube's Terms of Service
- Only download videos you have permission to download
- Be aware of copyright restrictions
- This tool is for personal backup and archival purposes

