#!/usr/bin/env python3
"""
Progress Monitor for Video Upload
Shows real-time progress of video uploads to S3
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def get_uploaded_count():
    """Get count of uploaded videos"""
    try:
        if Path('uploaded_videos.json').exists():
            with open('uploaded_videos.json', 'r') as f:
                return len(json.load(f))
    except:
        pass
    return 0

def format_time(seconds):
    """Format seconds into readable time"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds/60)} minutes"
    elif seconds < 86400:
        hours = int(seconds/3600)
        mins = int((seconds % 3600)/60)
        return f"{hours}h {mins}m"
    else:
        days = int(seconds/86400)
        hours = int((seconds % 86400)/3600)
        return f"{days}d {hours}h"

def main():
    """Main monitoring loop"""
    total_videos = 4294  # Approximate total
    start_count = get_uploaded_count()
    start_time = time.time()
    
    print("Starting progress monitor...")
    print(f"Initial count: {start_count} videos")
    time.sleep(2)
    
    last_count = start_count
    last_update_time = start_time
    
    while True:
        try:
            clear_screen()
            
            current_count = get_uploaded_count()
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Calculate progress
            percent = (current_count / total_videos) * 100
            remaining = total_videos - current_count
            
            # Calculate rate
            videos_since_start = current_count - start_count
            videos_since_last = current_count - last_count
            time_since_last = current_time - last_update_time
            
            # Calculate speeds
            if elapsed > 0:
                overall_rate = videos_since_start / elapsed * 60  # videos per minute
            else:
                overall_rate = 0
            
            if time_since_last > 0 and videos_since_last > 0:
                recent_rate = videos_since_last / time_since_last * 60
            else:
                recent_rate = overall_rate
            
            # Estimate remaining time
            if overall_rate > 0:
                eta_seconds = (remaining / overall_rate) * 60
                eta = format_time(eta_seconds)
            else:
                eta = "Calculating..."
            
            # Display
            print("=" * 70)
            print("          VIDEO UPLOAD PROGRESS MONITOR")
            print("=" * 70)
            print()
            
            # Progress bar
            bar_width = 50
            filled = int(bar_width * current_count / total_videos)
            bar = "█" * filled + "░" * (bar_width - filled)
            print(f"Progress: [{bar}] {percent:.1f}%")
            print()
            
            # Statistics
            print(f"Uploaded:        {current_count:,} / {total_videos:,} videos")
            print(f"Remaining:       {remaining:,} videos")
            print()
            
            print(f"Running time:    {format_time(elapsed)}")
            print(f"Overall rate:    {overall_rate:.2f} videos/minute")
            print(f"Recent rate:     {recent_rate:.2f} videos/minute")
            print()
            
            print(f"ETA:             {eta}")
            print()
            
            # Session stats
            print(f"Session start:   {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Current time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if videos_since_last > 0:
                print(f"Last update:     {int(time_since_last)} seconds ago (+{videos_since_last} videos)")
            else:
                print(f"Last update:     No new uploads in {int(time_since_last)} seconds")
            
            print()
            print("=" * 70)
            print("Press Ctrl+C to exit monitor (upload will continue)")
            print("Refreshing in 30 seconds...")
            
            # Update tracking
            if videos_since_last > 0:
                last_count = current_count
                last_update_time = current_time
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n\nMonitor stopped. Upload process is still running.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()

