# Quick Start Guide

## 🎯 Which Script Should I Use?

You now have **TWO** scripts for different use cases:

### Option 1: WordPress API Mode ⭐ **(Recommended for your workflow)**
**File:** `youtube_to_s3_api.py`

✅ **Use this when:**
- You want to upload videos from specific WordPress posts
- You need filenames based on your application's Post IDs
- You want application-level control over which videos to backup
- You're working with sardertv.com or similar WordPress sites

**How it works:**
```
WordPress API → Get Posts → Extract YouTube URLs → Download → Upload to S3
```

**Filename format:** `45424.mp4` (WordPress Post ID)

---

### Option 2: YouTube Channel Mode
**File:** `youtube_to_s3.py`

✅ **Use this when:**
- You want to backup an entire YouTube channel
- You want all videos from a channel
- Filenames can be YouTube video IDs

**How it works:**
```
YouTube Channel → Get All Videos → Download → Upload to S3
```

**Filename format:** `VIDEO_ID.mp4` (YouTube Video ID)

---

## 🚀 Quick Setup (WordPress API Mode)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create Configuration
```bash
cp env.example .env
```

### Step 3: Edit `.env` File
```env
# Your WordPress API (already configured for sardertv.com)
WORDPRESS_API_URL=https://sardertv.com/wp-json/wp/v2/posts

# Your S3 bucket
S3_BUCKET_NAME=your-actual-bucket-name

# Your AWS credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# How many posts to process (optional)
MAX_POSTS=10
```

### Step 4: Run the Script
```bash
python youtube_to_s3_api.py
```

That's it! 🎉

---

## 📋 What You Need

1. **AWS S3 Bucket** - Create one in AWS console
2. **AWS Credentials** - Get from AWS IAM
3. **Internet connection** - For downloading videos
4. **Disk space** - Only temporary space needed (auto-cleaned)

---

## 📊 Expected Behavior

### First Run:
- Fetches ALL posts from WordPress API
- Finds posts with YouTube videos
- Uploads videos to S3 with Post ID as filename
- Creates `uploaded_videos.json` tracking file

### Subsequent Runs:
- Only processes NEW posts (not in tracking file)
- Skips already uploaded videos
- Updates tracking file

---

## 🗂️ Where Videos Go

Your S3 bucket structure:
```
your-bucket-name/
└── wordpress_videos/
    ├── 45424.mp4    ← Post ID 45424
    ├── 45283.mp4    ← Post ID 45283
    └── 45100.mp4    ← Post ID 45100
```

---

## 💡 Common Use Cases

### Process Latest 10 Posts Only
```env
MAX_POSTS=10
```

### Process ALL Posts
```env
MAX_POSTS=
```
(Leave empty or remove the line)

### Re-upload a Specific Post
1. Open `uploaded_videos.json`
2. Remove the post ID
3. Run the script again

---

## ✅ Verification

After running, check:
1. ✅ Videos appear in S3 bucket under `wordpress_videos/`
2. ✅ Filenames match Post IDs (e.g., `45424.mp4`)
3. ✅ `uploaded_videos.json` is created/updated
4. ✅ No files left in downloads folder (auto-cleaned)

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "S3_BUCKET_NAME not set" | Edit `.env` and set your bucket name |
| "AWS credentials not found" | Add AWS keys to `.env` file |
| "No new posts to process" | Posts already uploaded or no YouTube videos |
| Script runs but no uploads | Check AWS credentials and S3 bucket permissions |

---

## 📚 More Information

- **WordPress API Mode:** Read `README_API.md`
- **YouTube Channel Mode:** Read `README.md`
- **Both modes:** Use `requirements.txt` for dependencies

---

## 🎯 Your Specific Workflow

Based on your requirements:
1. ✅ Fetches from WordPress API (sardertv.com)
2. ✅ Gets Post ID and YouTube URL
3. ✅ Downloads video
4. ✅ Names file with Post ID
5. ✅ Uploads to S3
6. ✅ No local storage (auto-cleanup)

**You should use:** `youtube_to_s3_api.py`

---

## 🚦 Status Indicators

While running, you'll see:
- `✓` = Success
- `✗` = Error/Failed
- Progress bars for downloads and uploads
- Summary at the end

---

## 🔗 Quick Links

- AWS S3 Console: https://console.aws.amazon.com/s3/
- AWS IAM Console: https://console.aws.amazon.com/iam/
- WordPress API Docs: https://developer.wordpress.org/rest-api/

---

**Ready to start? Run:**
```bash
python youtube_to_s3_api.py
```

