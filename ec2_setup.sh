#!/bin/bash
################################################################################
# EC2 Setup Script for WordPress to S3 Video Uploader
# This script sets up everything needed on a fresh EC2 instance
################################################################################

set -e  # Exit on error

echo "=========================================="
echo "EC2 Setup for Video Uploader"
echo "=========================================="

# Update system
echo ""
echo "[1/7] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Python 3 and pip
echo ""
echo "[2/7] Installing Python 3 and pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install required system dependencies
echo ""
echo "[3/7] Installing system dependencies..."
sudo apt-get install -y git wget curl ffmpeg

# Create project directory
echo ""
echo "[4/7] Setting up project directory..."
cd ~
mkdir -p sardar-tv
cd sardar-tv

# Create virtual environment
echo ""
echo "[5/7] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo ""
echo "[6/7] Installing Python packages..."
pip install --upgrade pip
pip install yt-dlp boto3 botocore python-dotenv requests flask flask-cors

# Create systemd service file
echo ""
echo "[7/7] Creating systemd service (optional)..."
cat > ~/sardar-tv/uploader.service << 'EOF'
[Unit]
Description=WordPress to S3 Video Uploader
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/sardar-tv
Environment="PATH=/home/$USER/sardar-tv/venv/bin"
ExecStart=/home/$USER/sardar-tv/venv/bin/python youtube_to_s3_api.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/$USER/sardar-tv/uploader.log
StandardError=append:/home/$USER/sardar-tv/uploader.error.log

[Install]
WantedBy=multi-user.target
EOF

# Replace $USER with actual username
sed -i "s/\$USER/$USER/g" ~/sardar-tv/uploader.service

echo ""
echo "=========================================="
echo "✓ EC2 Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Upload your project files to ~/sardar-tv/"
echo "2. Create .env file with AWS credentials"
echo "3. Run: python youtube_to_s3_api.py"
echo ""
echo "Optional - Run as background service:"
echo "  sudo cp ~/sardar-tv/uploader.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable uploader.service"
echo "  sudo systemctl start uploader.service"
echo ""
echo "Monitor logs:"
echo "  tail -f ~/sardar-tv/uploader.log"
echo ""

