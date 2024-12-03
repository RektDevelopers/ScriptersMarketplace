import os
import logging
import json
from datetime import datetime, timedelta
import asyncio
import requests
from telegram import Update
from telegram.ext import Application
from telegram.error import BadRequestError, TelegramError

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
POSTS_FILE = "public/data/posts.json"
DEFAULT_IMAGE = "default-banner.png"

def validate_environment_variables():
    """
    Validate required environment variables for GitHub Actions compatibility.
    Provides clear error messages if variables are missing.
    """
    errors = []
    if not BOT_TOKEN:
        errors.append("Missing BOT_TOKEN environment variable")
    if not CHANNEL_ID:
        errors.append("Missing CHANNEL_ID environment variable")
    if not CHANNEL_USERNAME:
        errors.append("Missing CHANNEL_USERNAME environment variable")
    
    if errors:
        error_message = "Environment Variable Validation Failed:\n" + "\n".join(f"- {error}" for error in errors)
        logger.error(error_message)
        raise ValueError(error_message)

def sanitize_text(text):
    """
    Sanitize post content to remove HTML tags, escape special characters,
    and limit length.
    
    :param text: Input text to sanitize
    :return: Sanitized text
    """
    if not text:
        return ""
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text[:1000].strip()

async def download_media(bot, file_id, file_type):
    """
    Download media from Telegram and save locally.
    
    :param bot: Telegram bot instance
    :param file_id: Unique file identifier
    :param file_type: Type of file to download (e.g., 'jpg', 'mp4')
    :return: Path to saved media or None if download fails
    """
    try:
        file = await bot.get_file(file_id)
        file_path = f"public/media/{file_id}.{file_type}"
        
        # Ensure media directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Download file
        file_url = file.file_path
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
    :return: List of processed posts
    """
    validate_environment_variables()

    try:
        # Use Application builder for modern python-telegram-bot approach
        application = Application.builder().token(BOT_TOKEN).build()
        bot = application.bot

        # Fetch channel messages directly
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        posts = []

        # Attempt to get messages from the channel
        try:
            channel_messages = await bot.get_chat_messages(chat_id=CHANNEL_ID, limit=10)
        except Exception as e:
            logger.error(f"Error fetching channel messages: {e}")
            channel_messages = []

        for message in channel_messages:
            message_date = message.date

            # Skip old messages
            if message_date < cutoff_time:
                continue

            # Extract post details
            post_content = sanitize_text(message.text or message.caption or "")
            post_image = None
            post_video = None

            # Handle media
            if message.photo:
                file_id = message.photo[-1].file_id
                post_image = await download_media(bot, file_id, 'jpg')
            elif message.video:
                file_id = message.video.file_id
                post_video = await download_media(bot, file_id, 'mp4')
            elif message.document and 'video' in message.document.mime_type:
                file_id = message.document.file_id
                post_video = await download_media(bot, file_id, 'mp4')

            # Construct post object
            post = {
                "title": post_content.split("\n")[0][:50] if post_content else "Untitled Post",
                "content": post_content,
                "image": post_image or DEFAULT_IMAGE,
                "video": post_video,
                "link": f"https://t.me/{CHANNEL_USERNAME}/{message.message_id}",
                "timestamp": message_date.isoformat()
            }
            posts.append(post)

        # Sort posts by timestamp, most recent first
        posts.sort(key=lambda x: x['timestamp'], reverse=True)

        # Limit to most recent 10 posts
        return posts[:10]

    except (BadRequestError, TelegramError) as e:
        logger.error(f"Telegram API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching posts: {e}")
        return []

def save_posts(posts):
    """
    Save posts to JSON file with comprehensive error handling.
    
    :param posts: List of posts to save
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(POSTS_FILE), exist_ok=True)

        # Write posts to JSON file with UTF-8 encoding and pretty formatting
        with open(POSTS_FILE, "w", encoding='utf-8') as file:
            json.dump(posts, file, indent=4, ensure_ascii=False)

        logger.info(f"Successfully saved {len(posts)} posts to {POSTS_FILE}")
    except Exception as e:
        logger.error(f"Error saving posts: {e}")
        # Optionally, you could add additional error handling here
        # such as sending an alert or attempting to retry

async def main():
    """
    Async main function to fetch and save posts.
    Designed to work with GitHub Actions and provide clear logging.
    """
    logger.info("Starting Telegram channel post collection process...")

    try:
        posts = await fetch_posts()

        if posts:
            save_posts(posts)
        else:
            logger.warning("No new posts found in the last 48 hours.")
    except Exception as e:
        logger.error(f"Critical error during post collection: {e}")
        # In a GitHub Actions context, this will cause the workflow to fail
        raise

if __name__ == "__main__":
    # Use asyncio to run the async main function
    asyncio.run(main())
