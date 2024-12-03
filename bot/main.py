import os
import logging
import json
from datetime import datetime, timedelta
import requests
from telegram import Bot

# Logging configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POSTS_FILE = "public/data/posts.json"

def sanitize_text(text):
    """
    Sanitize post content to remove potentially problematic characters
    and limit length.
    """
    if not text:
        return ""
    # Limit content length to prevent extremely long posts
    return text[:1000].replace('\n', ' ').strip()

def download_image(bot, file_id):
    """
    Download image from Telegram and save locally.
    Returns path to saved image or None if download fails.
    """
    try:
        file_info = bot.get_file(file_id)
        file_path = f"public/images/{file_id}.jpg"
        
        # Ensure images directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Download file
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        response = requests.get(file_url)
        
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return file_path.replace('public/', '')  # Relative path for web
        return None
    except Exception as e:
        logger.error(f"Image download error: {e}")
        return None

def fetch_posts(hours_back=48):
    """
    Fetch posts from Telegram channel, focusing on recent posts.
    
    :param hours_back: Number of hours to look back for posts
    :return: List of processed posts
    """
    try:
        bot = Bot(BOT_TOKEN)
        
        # Get updates from the last 48 hours
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Fetch updates
        updates = bot.get_updates()
        posts = []

        for update in updates:
            # Check if it's a channel post and within the channel
            if (update.channel_post and 
                update.channel_post.chat.id == int(CHANNEL_ID)):
                
                # Convert message date to datetime
                message_date = update.channel_post.date
                
                # Skip old messages
                if message_date < cutoff_time:
                    continue

                # Extract post details
                post_content = sanitize_text(update.channel_post.text)
                post_image = None

                # Handle image
                if update.channel_post.photo:
                    file_id = update.channel_post.photo[-1].file_id
                    post_image = download_image(bot, file_id)

                # Construct post object
                post = {
                    "title": post_content.split("\n")[0][:50] if post_content else "Untitled Post",
                    "content": post_content,
                    "image": post_image or "default-banner.png",
                    "link": f"https://t.me/{update.channel_post.chat.username}/{update.channel_post.message_id}",
                    "timestamp": message_date.isoformat()
                }
                
                posts.append(post)

        # Sort posts by timestamp, most recent first
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit to most recent 10 posts
        return posts[:10]

    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        return []

def save_posts(posts):
    """
    Save posts to JSON file with error handling.
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(POSTS_FILE), exist_ok=True)
        
        with open(POSTS_FILE, "w", encoding='utf-8') as file:
            json.dump(posts, file, indent=4, ensure_ascii=False)
        
        logger.info(f"Successfully saved {len(posts)} posts to {POSTS_FILE}")
    except Exception as e:
        logger.error(f"Error saving posts: {e}")

def main():
    """
    Main execution function to fetch and save posts.
    """
    logger.info("Starting post collection process...")
    
    posts = fetch_posts()
    
    if posts:
        save_posts(posts)
    else:
        logger.warning("No new posts found in the last 48 hours.")

if __name__ == "__main__":
    main()
