import os
import logging
import requests
from telegram import Bot

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
POSTS_FILE = "public/data/posts.json"

# Fetch posts from Telegram channel
def fetch_posts():
    bot = Bot(BOT_TOKEN)
    updates = bot.get_updates()
    posts = []

    for update in updates:
        if update.channel_post and update.channel_post.chat.id == int(CHANNEL_ID):
            post_content = update.channel_post.text or ""
            post_image = None

            if update.channel_post.photo:
                file_id = update.channel_post.photo[-1].file_id  # Get the highest resolution image
                file_info = bot.get_file(file_id)
                post_image = file_info.file_path

            post = {
                "title": post_content.split("\n")[0][:50],  # Use first line as title, limit to 50 chars
                "content": post_content,
                "image": post_image,
                "link": f"https://t.me/{update.channel_post.chat.username}/{update.channel_post.message_id}"
            }
            posts.append(post)

    return posts

# Save posts to a JSON file
def save_posts(posts):
    try:
        os.makedirs(os.path.dirname(POSTS_FILE), exist_ok=True)
        with open(POSTS_FILE, "w") as file:
            import json
            json.dump(posts, file, indent=4)
        logger.info("Posts saved successfully.")
    except Exception as e:
        logger.error(f"Error saving posts: {e}")

# Main execution
def main():
    logger.info("Fetching posts...")
    posts = fetch_posts()

    if posts:
        logger.info(f"Fetched {len(posts)} posts.")
        save_posts(posts)
    else:
        logger.warning("No new posts found.")

if __name__ == "__main__":
    main()
