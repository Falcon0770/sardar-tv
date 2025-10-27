import requests
import json
import re
import time

def extract_youtube_url(html_content):
    """Extract YouTube video URL from HTML content."""
    # Pattern 1: YouTube embed iframe
    embed_pattern = r'youtube\.com/embed/([a-zA-Z0-9_-]+)'
    match = re.search(embed_pattern, html_content)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # Pattern 2: YouTube short URL
    short_pattern = r'youtu\.be/([a-zA-Z0-9_-]+)'
    match = re.search(short_pattern, html_content)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    
    # Pattern 3: Full YouTube watch URL
    watch_pattern = r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'
    match = re.search(watch_pattern, html_content)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    
    return None

print("Testing WordPress API to get EXACT count of ALL posts with YouTube videos...")
print("=" * 80)

url = "https://sardertv.com/wp-json/wp/v2/posts"

all_posts_with_videos = []
page = 1
per_page = 100  # Fetch 100 posts per page for efficiency
total_pages = None

payload = ""

start_time = time.time()

print("\n🔄 Fetching all posts from WordPress API...\n")

try:
    while True:
        querystring = {
            "page": str(page),
            "per_page": str(per_page),
            "orderby": "date",
            "order": "desc"
        }
        
        response = requests.request("GET", url, data=payload, params=querystring, timeout=30)
        
        if response.status_code != 200:
            print(f"\n❌ Error: API returned status code {response.status_code}")
            break
        
        posts = response.json()
        
        if not posts:
            break
        
        # Get total pages from headers on first request
        if page == 1:
            total_pages = response.headers.get('X-WP-TotalPages')
            total_posts = response.headers.get('X-WP-Total')
            print(f"📊 Total posts in WordPress: {total_posts}")
            print(f"📄 Total pages to fetch: {total_pages}\n")
        
        # Process posts and extract YouTube URLs
        videos_in_page = 0
        for post in posts:
            post_id = post.get('id')
            title = post.get('title', {}).get('rendered', 'Unknown')
            content = post.get('content', {}).get('rendered', '')
            date = post.get('date', '')
            
            # Extract YouTube URL
            youtube_url = extract_youtube_url(content)
            
            if youtube_url:
                videos_in_page += 1
                all_posts_with_videos.append({
                    'id': post_id,
                    'title': title,
                    'youtube_url': youtube_url,
                    'date': date
                })
        
        # Show progress
        progress = f"Page {page}/{total_pages}" if total_pages else f"Page {page}"
        print(f"✓ {progress} - Found {videos_in_page} videos (Total so far: {len(all_posts_with_videos)})")
        
        # Check if there are more pages
        if total_pages and page >= int(total_pages):
            break
        
        page += 1
    
    print("\n" + "=" * 80)
    print("\n📹 ALL Posts with YouTube Videos that will be uploaded to S3:\n")
    
    # Show first 20 videos as sample
    for idx, video in enumerate(all_posts_with_videos[:20], 1):
        print(f"{idx}. Post ID: {video['id']}")
        print(f"   Title: {video['title']}")
        print(f"   YouTube URL: {video['youtube_url']}")
        print(f"   Published: {video['date']}")
        print(f"   Will be uploaded as: videos/{video['id']}.mp4")
        print()
    
    if len(all_posts_with_videos) > 20:
        print(f"... and {len(all_posts_with_videos) - 20} more videos\n")
    
    elapsed_time = time.time() - start_time
    
    print("=" * 80)
    print(f"\n📊 FINAL SUMMARY:")
    print(f"   Total pages fetched: {page}")
    print(f"   Total posts with YouTube videos: {len(all_posts_with_videos)}")
    print(f"   Time taken: {elapsed_time:.2f} seconds")
    
    if len(all_posts_with_videos) > 0:
        print(f"\n✅ EXACT COUNT: {len(all_posts_with_videos)} videos will be uploaded to your S3 bucket!")
    else:
        print("\n⚠️  No YouTube videos found in the posts.")
    
    # Show all post IDs that will be uploaded
    print(f"\n💾 Saving full list to 'videos_to_upload.json'...")
    with open('videos_to_upload.json', 'w') as f:
        json.dump(all_posts_with_videos, f, indent=2)
    print(f"✅ Full list saved! You can view all {len(all_posts_with_videos)} videos in videos_to_upload.json")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error testing API: {e}")

