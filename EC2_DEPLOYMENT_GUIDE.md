# EC2 Deployment Guide for Video Uploader

## Overview
This guide helps you deploy the WordPress to S3 video uploader on AWS EC2 for continuous, reliable processing of ~4,294 videos.

---

## Why EC2?

✅ **Faster uploads** - EC2 in same region as S3 = ultra-fast transfers  
✅ **No local resources** - Doesn't use your PC's disk/bandwidth  
✅ **24/7 operation** - Can run for days without interruption  
✅ **Cost-effective** - ~$0.10-0.30/hour, total cost ~$20-60 for all videos  
✅ **Auto-resume** - Can stop/start instance, progress is saved  

---

## Step-by-Step Setup

### Phase 1: Create EC2 Instance

#### 1. Launch EC2 Instance

Go to AWS Console → EC2 → Launch Instance

**Recommended Configuration:**

| Setting | Value | Why |
|---------|-------|-----|
| **AMI** | Ubuntu 22.04 LTS | Free tier eligible, stable |
| **Instance Type** | t3.medium or t3.large | Enough CPU/RAM for video processing |
| **Storage** | 30 GB gp3 | Temporary storage for videos |
| **Region** | **Same as your S3 bucket!** | Faster uploads, lower costs |
| **Security Group** | SSH (port 22) only | We only need SSH access |

**Cost Estimate:**
- t3.medium: ~$0.0416/hour × 200 hours = ~$8.32
- t3.large: ~$0.0832/hour × 150 hours = ~$12.48

#### 2. Connect to EC2

```bash
# Download your .pem key file from AWS
# Set permissions
chmod 400 your-key.pem

# Connect via SSH
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

---

### Phase 2: Setup Environment

#### 1. Run Automated Setup

On your EC2 instance:

```bash
# Download setup script
wget https://raw.githubusercontent.com/YOUR_REPO/ec2_setup.sh
# OR upload it manually

# Make executable
chmod +x ec2_setup.sh

# Run setup
./ec2_setup.sh
```

This installs:
- Python 3 + pip
- Required packages (yt-dlp, boto3, etc.)
- FFmpeg for video processing
- Creates virtual environment

#### 2. Upload Project Files

**Option A: Using SCP (from your local machine)**

```bash
# Upload entire project
scp -i your-key.pem -r "C:\AI_certs repos\sardar-tv\*" ubuntu@YOUR_EC2_IP:~/sardar-tv/

# Upload just the necessary files
scp -i your-key.pem youtube_to_s3_api.py ubuntu@YOUR_EC2_IP:~/sardar-tv/
scp -i your-key.pem .env ubuntu@YOUR_EC2_IP:~/sardar-tv/
scp -i your-key.pem uploaded_videos.json ubuntu@YOUR_EC2_IP:~/sardar-tv/  # If exists
```

**Option B: Using Git**

```bash
# On EC2
cd ~/sardar-tv
git clone YOUR_REPO_URL .
```

#### 3. Configure .env File

On EC2, create/edit `.env`:

```bash
cd ~/sardar-tv
nano .env
```

Add your credentials:

```env
# AWS S3 Configuration
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1

# AWS Credentials (use IAM role if possible)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# WordPress API
WORDPRESS_API_URL=https://sardertv.com/wp-json/wp/v2/posts

# Leave empty to process ALL videos
MAX_POSTS=
```

**🔒 BETTER: Use IAM Role (Recommended)**

Instead of hardcoding credentials:

1. Create IAM role with S3 write permissions
2. Attach role to EC2 instance
3. Remove AWS credentials from `.env` (boto3 auto-detects role)

---

### Phase 3: Run the Uploader

#### Option A: Run in Foreground (Simple)

```bash
cd ~/sardar-tv
source venv/bin/activate
python youtube_to_s3_api.py
```

#### Option B: Run in Background with Screen (Recommended)

```bash
# Install screen
sudo apt-get install -y screen

# Start a screen session
screen -S uploader

# Run the script
cd ~/sardar-tv
source venv/bin/activate
python youtube_to_s3_api.py

# Detach: Press Ctrl+A then D
# Reattach: screen -r uploader
# Kill: screen -X -S uploader quit
```

#### Option C: Run as Systemd Service (Production)

```bash
# Copy service file
sudo cp ~/sardar-tv/uploader.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable uploader.service
sudo systemctl start uploader.service

# Check status
sudo systemctl status uploader.service

# View logs
sudo journalctl -u uploader.service -f

# Or direct log files
tail -f ~/sardar-tv/uploader.log
tail -f ~/sardar-tv/uploader.error.log
```

---

## Monitoring Progress

### 1. Check Uploaded Videos Count

```bash
# Count how many videos uploaded
cat ~/sardar-tv/uploaded_videos.json | grep -o '\"' | wc -l
# Divide result by 2 to get actual count

# Or use Python
python -c "import json; print(len(json.load(open('uploaded_videos.json'))))"
```

### 2. Monitor Real-Time Progress

```bash
# If running in screen
screen -r uploader

# If running as service
tail -f ~/sardar-tv/uploader.log
```

### 3. Create Progress Monitor Script

```bash
cd ~/sardar-tv
nano monitor_progress.sh
```

```bash
#!/bin/bash
while true; do
    clear
    echo "=========================================="
    echo "Video Upload Progress Monitor"
    echo "=========================================="
    echo ""
    
    # Count uploaded
    if [ -f uploaded_videos.json ]; then
        uploaded=$(python3 -c "import json; print(len(json.load(open('uploaded_videos.json'))))" 2>/dev/null || echo "0")
        total=4294
        percent=$((uploaded * 100 / total))
        remaining=$((total - uploaded))
        
        echo "Uploaded: $uploaded / $total ($percent%)"
        echo "Remaining: $remaining videos"
        echo ""
        
        # Estimate time (assuming 4 min per video)
        minutes=$((remaining * 4))
        hours=$((minutes / 60))
        days=$((hours / 24))
        
        echo "Estimated time remaining: $days days, $((hours % 24)) hours"
    else
        echo "No progress file found yet"
    fi
    
    echo ""
    echo "Last update: $(date)"
    echo "Press Ctrl+C to exit"
    
    sleep 30
done
```

```bash
chmod +x monitor_progress.sh
./monitor_progress.sh
```

---

## Cost Optimization

### 1. Use Spot Instances (Save 70%)

- Spot instances are much cheaper
- Your script auto-resumes if interrupted
- Perfect for this use case!

**How to:**
1. Launch as Spot Instance instead of On-Demand
2. Enable "Persistent request"
3. Script will resume from `uploaded_videos.json`

### 2. Stop Instance When Done

```bash
# Auto-shutdown after completion
echo "sudo shutdown -h now" >> youtube_to_s3_api.py  # (modify script to add this at end)

# Or manually stop from AWS Console
```

### 3. Use S3 Transfer Acceleration

If your S3 bucket has it enabled, uploads are even faster:

```python
# In youtube_to_s3_api.py, modify S3 client:
self.s3_client = boto3.client(
    's3',
    region_name=aws_region,
    config=Config(s3={'use_accelerate_endpoint': True})
)
```

---

## Troubleshooting

### Issue: Downloads are slow

```bash
# Check internet speed
curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3 -
```

**Solution:** Use larger instance type (t3.large or t3.xlarge)

### Issue: Running out of disk space

```bash
# Check disk usage
df -h

# Clean up if needed
sudo apt-get clean
```

**Solution:** Increase EBS volume size

### Issue: Script crashes/stops

The script auto-resumes! Just run it again:

```bash
cd ~/sardar-tv
source venv/bin/activate
python youtube_to_s3_api.py
```

It will skip already uploaded videos.

### Issue: YouTube rate limiting

```bash
# Add delay between downloads (edit youtube_to_s3_api.py)
# After each video, add: time.sleep(10)  # 10 second delay
```

---

## Security Best Practices

### 1. Use IAM Role (No hardcoded keys)

```bash
# In AWS Console:
# 1. Create IAM role with S3 write policy
# 2. Attach to EC2 instance
# 3. Remove credentials from .env
```

### 2. Restrict Security Group

Only allow SSH from your IP:

```
Type: SSH
Port: 22
Source: YOUR_IP_ADDRESS/32
```

### 3. Enable CloudWatch Monitoring

Track CPU, network, and disk usage in AWS Console.

---

## Quick Reference Commands

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Start script in background
screen -S uploader
cd ~/sardar-tv && source venv/bin/activate && python youtube_to_s3_api.py

# Detach from screen
Ctrl+A then D

# Reattach to screen
screen -r uploader

# Check progress
python3 -c "import json; print(len(json.load(open('uploaded_videos.json'))))"

# View logs (if using systemd)
tail -f ~/sardar-tv/uploader.log

# Stop instance (from local machine)
aws ec2 stop-instances --instance-ids i-YOUR_INSTANCE_ID
```

---

## Summary

**Total Steps:**
1. ✅ Launch EC2 instance (t3.medium, Ubuntu, same region as S3)
2. ✅ Run `ec2_setup.sh`
3. ✅ Upload project files
4. ✅ Configure `.env`
5. ✅ Run in `screen` session
6. ✅ Detach and let it run
7. ✅ Check back periodically
8. ✅ Stop instance when complete

**Estimated Timeline:**
- Setup: 15-30 minutes
- Uploading 4,294 videos: 6-9 days
- Total cost: $15-60 (depending on instance type)

**Benefits:**
- 🚀 Fast and reliable
- 💰 Cost-effective
- 🔄 Auto-resumes if interrupted
- 📊 Easy to monitor
- 🛡️ Secure

---

## Need Help?

Common issues and solutions are in the Troubleshooting section above.

For AWS-specific issues, check:
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS CLI Setup](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)

