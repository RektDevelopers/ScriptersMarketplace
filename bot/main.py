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
    Validate required environment variables with comprehensive error checking.
    
    Raises:
        ValueError: If any required environment variables are missing
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
    Sanitize and clean text content for safe storage and display.
    
    Args:
        text (str): Input text to sanitize
    
    Returns:
        str: Sanitized text with HTML special characters escaped
    """
    if not text:
        return ""
    
    # Escape HTML special characters and truncate
    sanitized = text.replace("<", "&lt;").replace(">", "&gt;")
    return sanitized[:1000].strip()

async def download_media(bot, file_id, file_type):
    """
    Download media from Telegram and save locally.
    
    Args:
        bot: Telegram bot instance
        file_id (str): Unique file identifier
        file_type (str): Type of file to download (e.g., 'jpg', 'mp4')
    
    Returns:
        str or None: Path to saved media or None if download fails
    """
    try:
        # Ensure media directory exists
        media_dir = "public/media"
        os.makedirs(media_dir, exist_ok=True)
        
        # Get file information
        file = await bot.get_file(file_id)
        
        # Construct local file path
        file_path = os.path.join(media_dir, f"{file_id}.{file_type}")
        
        # Download file
        response = requests.get(file.file_path)
        
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Return relative path
            return file_path.replace('public/', '')
        
        logger.warning(f"Failed to download media. Status code: {response.status_code}")
        return None
    
    except Exception as e:
        logger.error(f"Media download error for file {file_id}: {e}")
        return None

async def fetch_posts(hours_back=48):
    """
    Fetch recent posts from a Telegram channel.
    
    Args:
        hours_back (int): Number of hours to look back for posts
    
    Returns:
        list: Processed posts from the channel
    """
    # Validate environment variables before proceeding
    validate_environment_variables()
    
    posts = []
    
    try:
        # Create bot application
        application = Application.builder().token(BOT_TOKEN).build()
        bot = application.bot
        
        # Determine cutoff time for posts
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Fetch recent messages
        try:
            # Note: This method may vary depending on exact library version
            # You might need to adjust based on your specific library version
            recent_messages = await bot.get_chat_messages(chat_id=CHANNEL_ID, limit=20)
        except Exception as e:
            logger.error(f"Error fetching channel messages: {e}")
            return []
        
        for message in recent_messages:
            # Skip messages older than cutoff time
            if message.date < cutoff_time:
                continue
            
            # Extract post content
            post_content = sanitize_text(message.text or message.caption or "")
            
            # Initialize media variables
            post_image = None
            post_video = None
            
            # Handle different media types
            try:
                if message.photo:
                    # Get the largest photo
                    file_id = message.photo[-1].file_id
                    post_image = await download_media(bot, file_id, 'jpg')
                elif message.video:
                    file_id = message.video.file_id
                    post_video = await download_media(bot, file_id, 'mp4')
                elif message.document and 'video' in str(message.document.mime_type).lower():
                    file_id = message.document.file_id
                    post_video = await download_media(bot, file_id, 'mp4')
            except Exception as media_error:
                logger.error(f"Media processing error: {media_error}")
            
            # Construct post object
            post = {
                "title": (post_content.split("\n")[0][:50] if post_content else "Untitled Post"),
                "content": post_content,
                "image": post_image or DEFAULT_IMAGE,
                "video": post_video,
                "link": f"https://t.me/{CHANNEL_USERNAME}/{message.message_id}",
                "timestamp": message.date.isoformat()
            }
            
            posts.append(post)
        
        # Sort posts by timestamp, most recent first
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Return most recent 10 posts
        return posts[:10]
    
    except TelegramError as te:
        logger.error(f"Telegram API error: {te}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in fetch_posts: {e}")
        return []

def save_posts(posts):
    """
    Save processed posts to a JSON file.
    
    Args:
        posts (list): List of post dictionaries to save
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(POSTS_FILE), exist_ok=True)
        
        # Write posts to JSON file
        with open(POSTS_FILE, "w", encoding='utf-8') as file:
            json.dump(posts, file, indent=4, ensure_ascii=False)
        
        logger.info(f"Successfully saved {len(posts)} posts to {POSTS_FILE}")
    except Exception as e:
        logger.error(f"Error saving posts to file: {e}")

async def main():
    """
    Main async function to fetch and save Telegram channel posts.
    Provides comprehensive error handling and logging.
    """
    logger.info("Starting Telegram channel post collection process...")
    
    try:
        # Fetch posts
        posts = await fetch_posts()
        
        # Save posts if any are found
        if posts:
            save_posts(posts)
        else:
            logger.warning("No new posts found in the specified time range.")
    
    except Exception as e:
        logger.error(f"Critical error in main process: {e}")
        raise

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
