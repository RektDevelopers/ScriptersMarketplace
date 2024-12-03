import os
import logging
import json
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Optional

import telegram
from telegram import Update
from telegram.ext import Application
from telegram.error import TelegramError

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration with default values and type hints
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME", "")
    POSTS_FILE: str = os.getenv("POSTS_FILE", "public/data/posts.json")
    MEDIA_DIR: str = os.getenv("MEDIA_DIR", "public/media")
    FETCH_HOURS_BACK: int = int(os.getenv("FETCH_HOURS_BACK", "48"))
    MAX_POSTS: int = int(os.getenv("MAX_POSTS", "10"))


def validate_environment_variables() -> None:
    """
    Validate required environment variables with comprehensive checks.
    
    Raises:
        ValueError: If required configuration is missing or invalid.
    """
    missing_vars = []
    if not Config.BOT_TOKEN:
        missing_vars.append("BOT_TOKEN")
    if not Config.CHANNEL_USERNAME:
        missing_vars.append("CHANNEL_USERNAME")
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def sanitize_text(text: Optional[str], max_length: int = 1000) -> str:
    """
    Sanitize and truncate text content with improved handling.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text string
    """
    if not text:
        return ""
    
    # Replace potentially dangerous characters and truncate
    sanitized = text.replace("<", "&lt;").replace(">", "&gt;")
    return sanitized[:max_length].strip()


async def fetch_channel_posts(
    bot: telegram.Bot, 
    hours_back: Optional[int] = None, 
    max_posts: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Asynchronously fetch recent posts from a Telegram channel.
    
    Args:
        bot: Telegram bot instance
        hours_back: Number of hours to look back for posts
        max_posts: Maximum number of posts to retrieve
    
    Returns:
        List of processed posts
    """
    validate_environment_variables()
    posts: List[Dict[str, str]] = []
    
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours_back or Config.FETCH_HOURS_BACK)
        logger.info(f"Fetching messages from {Config.CHANNEL_USERNAME}...")

        # Fetch channel updates
        updates = await bot.get_updates(allowed_updates=['channel_post'])
        
        filtered_posts = []
        for update in updates:
            # Ensure it's a channel post and within time range
            if (not update.channel_post or 
                update.channel_post.date < cutoff_time):
                continue
            
            message = update.channel_post
            
            # Extract content
            post_content = sanitize_text(message.text or message.caption or "")
            
            # Generate title with intelligent fallback
            title = (
                post_content.split("\n")[0][:50] if post_content 
                else f"Post from {message.date.strftime('%Y-%m-%d')}"
            )

            # Create post dictionary
            post = {
                "post_id": str(message.message_id),
                "title": title,
                "content": post_content,
                "link": f"https://t.me/{Config.CHANNEL_USERNAME}/{message.message_id}",
                "timestamp": message.date.isoformat(),
            }
            filtered_posts.append(post)

        # Sort posts by timestamp in descending order
        filtered_posts.sort(key=lambda x: x["timestamp"], reverse=True)
        return filtered_posts[:max_posts or Config.MAX_POSTS]

    except TelegramError as e:
        logger.error(f"Telegram API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in fetch_channel_posts: {e}")
        return []


def save_posts(posts: List[Dict[str, str]]) -> None:
    """
    Save posts to a JSON file with improved error handling and directory creation.
    
    Args:
        posts: List of post dictionaries to save
    """
    try:
        # Ensure directory exists with parents
        os.makedirs(os.path.dirname(Config.POSTS_FILE), exist_ok=True)
        
        # Create a dictionary with post_id as key for easier lookup
        posts_dict = {post['post_id']: post for post in posts}
        
        with open(Config.POSTS_FILE, "w", encoding="utf-8") as file:
            json.dump(posts_dict, file, indent=4, ensure_ascii=False)
        
        logger.info(f"Saved {len(posts)} posts to {Config.POSTS_FILE}")
    
    except PermissionError:
        logger.error(f"Permission denied when writing to {Config.POSTS_FILE}")
    except OSError as e:
        logger.error(f"File system error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error saving posts: {e}")


async def main() -> None:
    """
    Main asynchronous function to coordinate post collection.
    Includes comprehensive error handling and logging.
    """
    try:
        validate_environment_variables()
        logger.info("Starting Telegram channel post collection process...")
        
        async with Application.builder().token(Config.BOT_TOKEN).build() as application:
            bot = application.bot
            posts = await fetch_channel_posts(bot)
            
            if posts:
                save_posts(posts)
            else:
                logger.warning("No new posts found.")
    
    except Exception as e:
        logger.error(f"Critical error in main process: {e}", exc_info=True)


if __name__ == "__main__":
    # Use asyncio.run with error handling
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process manually interrupted.")
    except Exception as e:
        logger.error(f"Unhandled error in script: {e}", exc_info=True)
