import requests
import re
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def extract_youtube_url(html_content):
    """Extract YouTube video URL from HTML content."""
    patterns = [
        r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'youtu\.be/([a-zA-Z0-9_-]+)',
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        if re.search(pattern, html_content):
            return True
    return False

# Create a session with retry strategy
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

print("Getting EXACT count of videos (robust method with auto-retry)...")
print("=" * 80)

url = "https://sardertv.com/wp-json/wp/v2/posts"
video_count = 0
total_posts = 0
page = 1
per_page = 100

try:
    # First request to get totals
    print("\n🔍 Getting total post count...")
    response = session.get(url, params={"page": "1", "per_page": str(per_page)}, timeout=60)
    total_posts = int(response.headers.get('X-WP-Total', 0))
    total_pages = int(response.headers.get('X-WP-TotalPages', 0))
    
    print(f"📊 WordPress has {total_posts} total posts across {total_pages} pages")
    print(f"🔄 Scanning all posts for YouTube videos...\n")
    
    page = 1
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while page <= total_pages:
        try:
            response = session.get(
                url, 
                params={"page": str(page), "per_page": str(per_page), "orderby": "date", "order": "desc"},
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"⚠️  Page {page}: HTTP {response.status_code} - Retrying...")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    print(f"❌ Too many consecutive errors. Stopping at page {page}.")
                    break
                time.sleep(2)
                continue
            
            posts = response.json()
            if not posts:
                break
            
            videos_in_page = 0
            for post in posts:
                content = post.get('content', {}).get('rendered', '')
                if extract_youtube_url(content):
                    video_count += 1
                    videos_in_page += 1
            
            # Reset error counter on success
            consecutive_errors = 0
            
            # Progress update every page
            percent = (page / total_pages) * 100
            print(f"✓ Page {page}/{total_pages} ({percent:.1f}%) - Found {videos_in_page} videos | Total: {video_count}")
            
            page += 1
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
            
        except requests.exceptions.Timeout:
            print(f"⏱️  Page {page}: Timeout - Retrying in 3 seconds...")
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                print(f"❌ Too many timeouts. Stopping at page {page}.")
                break
            time.sleep(3)
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Page {page}: Connection error - {str(e)[:50]} - Retrying in 3 seconds...")
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                print(f"❌ Too many consecutive errors. Stopping at page {page}.")
                break
            time.sleep(3)
    
    print("\n" + "=" * 80)
    print(f"\n🎯 RESULT:")
    print(f"   Pages scanned: {page - 1} out of {total_pages}")
    print(f"   Videos found: {video_count}")
    
    if page - 1 < total_pages:
        # Estimate based on current rate
        avg_videos_per_page = video_count / (page - 1) if page > 1 else 0
        estimated_total = int(avg_videos_per_page * total_pages)
        print(f"   Estimated total: ~{estimated_total} videos (based on {avg_videos_per_page:.1f} videos/page)")
    else:
        print(f"   ✅ EXACT COUNT: {video_count} videos will be uploaded to S3!")
        print(f"   Out of {total_posts} total posts")
        print(f"   That's {(video_count/total_posts*100):.1f}% of posts with videos")
    
    print("\n" + "=" * 80)

except KeyboardInterrupt:
    print("\n\n⚠️  Interrupted by user!")
    print(f"   Scanned {page - 1} pages")
    print(f"   Found {video_count} videos so far")
    if page > 1:
        avg_videos_per_page = video_count / (page - 1)
        estimated_total = int(avg_videos_per_page * total_pages)
        print(f"   Estimated total: ~{estimated_total} videos")

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    print(f"   Scanned {page - 1} pages, found {video_count} videos")
    import traceback
    traceback.print_exc()

