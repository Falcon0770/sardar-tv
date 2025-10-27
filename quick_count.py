import requests
import re

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

print("Getting EXACT count of videos (fast method)...")
print("=" * 80)

url = "https://sardertv.com/wp-json/wp/v2/posts"
video_count = 0
total_posts = 0
page = 1
per_page = 100

try:
    # First request to get totals
    response = requests.get(url, params={"page": "1", "per_page": "1"}, timeout=30)
    total_posts = int(response.headers.get('X-WP-Total', 0))
    total_pages = int(response.headers.get('X-WP-TotalPages', 0))
    
    print(f"\n📊 WordPress has {total_posts} total posts across {total_pages} pages")
    print(f"🔄 Scanning all posts for YouTube videos...\n")
    
    page = 1
    while page <= total_pages:
        response = requests.get(
            url, 
            params={"page": str(page), "per_page": str(per_page), "orderby": "date", "order": "desc"},
            timeout=30
        )
        
        if response.status_code != 200:
            break
        
        posts = response.json()
        if not posts:
            break
        
        for post in posts:
            content = post.get('content', {}).get('rendered', '')
            if extract_youtube_url(content):
                video_count += 1
        
        print(f"✓ Page {page}/{total_pages} - Videos found: {video_count}")
        page += 1
    
    print("\n" + "=" * 80)
    print(f"\n🎯 EXACT COUNT: {video_count} videos will be uploaded to S3!")
    print(f"   Out of {total_posts} total posts")
    print(f"   That's {(video_count/total_posts*100):.1f}% of posts with videos")
    print("\n" + "=" * 80)

except Exception as e:
    print(f"❌ Error: {e}")

