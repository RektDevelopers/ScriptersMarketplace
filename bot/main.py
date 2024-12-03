import os
import logging
import json
from datetime import datetime, timedelta
import asyncio
import requests
from telegram import Bot, Update
from telegram.error import BadRequest, Unauthorized as TelegramUnauthorized

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POSTS_FILE = "public/data/posts.json"
DEFAULT_IMAGE = "default-banner.png"

if not BOT_TOKEN or not CHANNEL_ID:
    logger.error("Missing BOT_TOKEN or CHANNEL_ID environment variable.")
    exit(1)

def sanitize_text(text):
    """
    Sanitize post content to remove HTML tags, escape special characters,
    and limit length.
    """
    if not text:
        return ""
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text[:1000].strip()

async def download_media(bot, file_id, file_type):
    """
    Download media from Telegram and save locally.
    Returns path to saved media or None if download fails.
    """
    try:
        file_info = await bot.get_file(file_id)
        file_path = f"public/media/{file_id}.{file_type}"
        
        # Ensure media directory exists
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
        logger.error(f"Media download error: {e}")
        return None

async def fetch_posts(hours_back=48):
    """
    Fetch posts from Telegram channel, focusing on recent posts.

    :param hours_back: Number of hours to look back for posts
    :return: List of processedposts
    """
    try:
        bot = Bot(BOT_TOKEN)
        updates = await bot.get_updates()
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        posts = []

        for update in updates:
            # Check if it's a channel post and within the desired channel
            if (isinstance(update, Update) and
                update.effective_chat and
                update.effective_chat.type == 'channel' and
                update.effective_chat.id == int(CHANNEL_ID)):

                message_date = update.effective_message.date

                # Skip old messages
                if message_date < cutoff_time:
                    continue

                # Extract post details
                post_content = sanitize_text(update.effective_message.text)
                post_image = None
                post_video = None

                # Handlemedia
                if update.effective_message.photo:
                    file_id = update.effective_message.photo[-1].file_id
                    post_image = awaitdownload_media(bot, file_id,'jpg')
                elif update.effective_message.document and 'video' in update.effective_message.document.mime_type:
                    file_id = update.effective_message.document.file_id
                    post_video = awaitdownloadmedia(bot, file_id, 'mp4')

                # Constructpostobject
                post = {
                    "title": post_content.split("\n")[0][:50] if post_content else "Untitled Post",
                    "content": post_content,
                    "image": post_image or DEFAULT_IMAGE,
                    "video": post_video,
                    "link": f"https://t.me/{update.effective_chat.username}/{update.effective_message.message_id}",
                    "timestamp": message_date.isoformat()
                }
                posts.append(post)

        # Sortpostsbytimestamp, most recent first
        posts.sort(key=lambda x: x['timestamp'], reverse=True)

        # Limit to most recent 10posts
        return posts[:10]

    except (BadRequest, TelegramUnauthorized) as e:
        logger.error(f"Telegram API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching posts: {e}")
        return []

def save_posts(posts):
    """
    Save posts to JSON file with error handling.
    """
    try:
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

    try:
        posts = asyncio.run(fetch_posts())

        if posts:
            save_posts(posts)
        else:
            logger.warning("No new posts found in the last 48 hours.")
    except Exception as e:
        logger.error(f"Unexpected error during execution: {e}")

if __name__ == "__main__":
    main()
