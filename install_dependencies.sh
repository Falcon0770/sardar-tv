#!/bin/bash
# Quick dependency installer for EC2

echo "Installing Python dependencies..."

# Update system
sudo apt-get update -y

# Install Python, pip, and required system packages
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg screen

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install yt-dlp boto3 botocore python-dotenv requests flask flask-cors

echo ""
echo "✓ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure your .env file"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python youtube_to_s3_api.py"

