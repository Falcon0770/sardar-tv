# Quick Start - EC2 Deployment

Get your video uploader running on EC2 in **15 minutes**! ⚡

---

## Prerequisites

- ✅ AWS Account
- ✅ AWS credentials (Access Key + Secret Key)
- ✅ S3 bucket created
- ✅ EC2 key pair (.pem file)

---

## Step 1: Launch EC2 Instance (5 min)

### Via AWS Console:

1. Go to **EC2 Dashboard** → **Launch Instance**
2. Configure:
   ```
   Name: video-uploader
   AMI: Ubuntu Server 22.04 LTS
   Instance type: t3.medium (or t3.large for faster)
   Key pair: Select or create new
   Storage: 30 GB gp3
   ```
3. **Important:** Select the **same region as your S3 bucket**!
4. Click **Launch Instance**
5. Note your **Public IP address**

### Cost: ~$0.05/hour = ~$10 for entire job

---

## Step 2: Connect to EC2 (2 min)

```bash
# Set key permissions (first time only)
chmod 400 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

---

## Step 3: Setup Environment (5 min)

### On EC2, run these commands:

```bash
# Update system
sudo apt-get update -y

# Install Python and dependencies
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg screen

# Create project directory
mkdir -p ~/sardar-tv
cd ~/sardar-tv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install yt-dlp boto3 python-dotenv requests
```

---

## Step 4: Upload Files (3 min)

### Option A: From your local machine

Open **new terminal** (not EC2):

```bash
# Navigate to your project
cd "C:\AI_certs repos\sardar-tv"

# Upload files (replace YOUR_KEY.pem and YOUR_EC2_IP)
scp -i YOUR_KEY.pem youtube_to_s3_api.py ubuntu@YOUR_EC2_IP:~/sardar-tv/
scp -i YOUR_KEY.pem .env ubuntu@YOUR_EC2_IP:~/sardar-tv/

# If you already uploaded some videos, also copy the tracking file:
scp -i YOUR_KEY.pem uploaded_videos.json ubuntu@YOUR_EC2_IP:~/sardar-tv/

# Optional: Upload monitor script
scp -i YOUR_KEY.pem monitor_progress.py ubuntu@YOUR_EC2_IP:~/sardar-tv/
```

### Option B: Create files on EC2

```bash
# On EC2
cd ~/sardar-tv

# Create the Python script
nano youtube_to_s3_api.py
# Copy/paste content from your local file, save with Ctrl+X, Y, Enter

# Create .env file
nano .env
# Add your credentials (see below), save
```

---

## Step 5: Configure .env (2 min)

```bash
# On EC2
cd ~/sardar-tv
nano .env
```

Add this content:

```env
# AWS Configuration
S3_BUCKET_NAME=your-actual-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_actual_key
AWS_SECRET_ACCESS_KEY=your_actual_secret

# WordPress API
WORDPRESS_API_URL=https://sardertv.com/wp-json/wp/v2/posts

# Process ALL videos (leave empty or remove line)
MAX_POSTS=
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

---

## Step 6: Start Upload (1 min)

```bash
# On EC2
cd ~/sardar-tv
source venv/bin/activate

# Start screen session
screen -S uploader

# Run the script
python youtube_to_s3_api.py

# Wait for first video to start uploading to confirm it works

# Detach from screen: Press Ctrl+A, then D
```

**🎉 Done! Your videos are now uploading!**

---

## Monitoring Progress

### Reattach to see live progress:

```bash
screen -r uploader
```

**Detach again:** `Ctrl+A` then `D`

### Check count of uploaded videos:

```bash
cd ~/sardar-tv
python3 -c "import json; print(f'Uploaded: {len(json.load(open(\"uploaded_videos.json\")))} videos')"
```

### Run progress monitor (if uploaded):

```bash
cd ~/sardar-tv
python monitor_progress.py
```

---

## Important Commands

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# View running upload
screen -r uploader

# Check if screen is running
screen -ls

# Kill screen (stops upload)
screen -X -S uploader quit

# Check disk space
df -h

# View last 50 lines of output
cd ~/sardar-tv
# (output is shown in screen session)
```

---

## What Happens Next?

- ⏱️ **Total time:** ~6-9 days for all 4,294 videos
- 💾 **Progress saved:** Can stop/restart anytime
- 🔄 **Auto-resume:** Skips already uploaded videos
- 💰 **Cost:** ~$10-30 total (depending on instance type)

---

## When Complete

### Stop the EC2 instance:

**Option 1: From AWS Console**
- Go to EC2 → Instances
- Select your instance
- Actions → Stop Instance

**Option 2: From command line**
```bash
aws ec2 stop-instances --instance-ids i-YOUR_INSTANCE_ID
```

**Option 3: Auto-stop when done**

Add to end of `youtube_to_s3_api.py`:

```python
# At the very end of main() function
print("All uploads complete! Shutting down in 60 seconds...")
time.sleep(60)
os.system('sudo shutdown -h now')
```

---

## Troubleshooting

### Script stopped/crashed?

Just run it again! It will resume:

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
cd ~/sardar-tv
source venv/bin/activate
screen -S uploader
python youtube_to_s3_api.py
# Ctrl+A then D to detach
```

### Connection lost?

Screen keeps it running! Just reconnect:

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
screen -r uploader
```

### Check if process is running:

```bash
ps aux | grep python
```

### Out of disk space?

```bash
df -h
# If needed, increase EBS volume in AWS Console
```

---

## Cost Optimization

### Use Spot Instance (70% cheaper!):

1. Launch as **Spot Instance** instead of On-Demand
2. If interrupted, just restart - progress is saved!
3. Total cost: ~$3-10 instead of $10-30

### Smaller instance for overnight:

- t3.small during low-priority times
- t3.large when you want speed

---

## Summary

```bash
# 1. Launch EC2 (t3.medium, Ubuntu, same region as S3)
# 2. Connect via SSH
# 3. Install dependencies
# 4. Upload files
# 5. Configure .env
# 6. Run in screen
# 7. Detach and disconnect
# 8. Check back in a week!
```

**That's it! 🚀**

Your videos are uploading continuously. Check progress anytime, and stop the EC2 instance when done.

---

## Need More Help?

See the full guide: `EC2_DEPLOYMENT_GUIDE.md`

