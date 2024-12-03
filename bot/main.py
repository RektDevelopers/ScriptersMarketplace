import os
import logging
import json
from datetime import datetime, timedelta
import asyncio
import requests
from telegram import Update
from telegram.ext import Application
from telegram.error import TelegramError

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
    Validate required environment variables.
    """
    missing_vars = []
    if not BOT_TOKEN:
        missing_vars.append("BOT_TOKEN")
    if not CHANNEL_ID:
        missing_vars.append("CHANNEL_ID")
    if not CHANNEL_USERNAME:
        missing_vars.append("CHANNEL_USERNAME")
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def sanitize_text(text):
    """
    Sanitize and truncate text content.
    """
    if not text:
        return ""
    sanitized = text.replace("<", "&lt;").replace(">", "&gt;")
    return sanitized[:1000].strip()

async def download_media(bot, file_id, file_type):
    """
    Download media from Telegram.
    """
    try:
        media_dir = "public/media"
        os.makedirs(media_dir, exist_ok=True)
        file = await bot.get_file(file_id)
        file_path = os.path.join(media_dir, f"{file_id}.{file_type}")
        response = requests.get(file.file_path)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            return file_path.replace("public/", "")
        logger.warning(f"Failed to download media. Status code: {response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Media download error: {e}")
        return None

async def fetch_posts(hours_back=48):
    """
    Fetch recent Telegram posts.
    """
    validate_environment_variables()
    posts = []
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        bot = application.bot
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_messages = await bot.get_chat(CHANNEL_ID).get_history(limit=50)
        for message in recent_messages:
            if message.date < cutoff_time:
                continue
            post_content = sanitize_text(message.text or message.caption or "")
            post_image = None
            try:
                if message.photo:
                    file_id = message.photo[-1].file_id
                    post_image = await download_media(bot, file_id, "jpg")
            except Exception as media_error:
                logger.error(f"Media error: {media_error}")
            post = {
                "title": post_content.split("\n")[0][:50] if post_content else "Untitled Post",
                "content": post_content,
                "image": post_image or DEFAULT_IMAGE,
                "link": f"https://t.me/{CHANNEL_USERNAME}/{message.message_id}",
                "timestamp": message.date.isoformat(),
            }
            posts.append(post)
        posts.sort(key=lambda x: x["timestamp"], reverse=True)
        return posts[:10]
    except TelegramError as te:
        logger.error(f"Telegram API error: {te}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

def save_posts(posts):
    """
    Save posts to a JSON file.
    """
    try:
        os.makedirs(os.path.dirname(POSTS_FILE), exist_ok=True)
        with open(POSTS_FILE, "w", encoding="utf-8") as file:
            json.dump(posts, file, indent=4, ensure_ascii=False)
        logger.info(f"Saved {len(posts)} posts to {POSTS_FILE}")
    except Exception as e:
        logger.error(f"Error saving posts: {e}")

async def main():
    """
    Main function to fetch and save Telegram posts.
    """
    logger.info("Starting Telegram channel post collection process...")
    try:
        posts = await fetch_posts()
        if posts:
            save_posts(posts)
        else:
            logger.warning("No new posts found.")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
