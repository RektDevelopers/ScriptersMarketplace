import logging
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
import os

# Bot Token and Channel ID from Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_USERNAME = "@ScriptersMarketplace"

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command handler
def start(update: Update, context: CallbackContext):
    """Sends a welcome message."""
    user = update.effective_user
    welcome_text = (
        f"Hello, {user.first_name}!\n\n"
        "Welcome to the Scripters Marketplace Bot! Use /help to explore features."
    )
    update.message.reply_text(welcome_text)

# Help command handler
def help_command(update: Update, context: CallbackContext):
    """Sends a help message."""
    help_text = (
        "Available Commands:\n"
        "/start - Start the bot\n"
        "/post - Post to the channel\n"
        "/fetch - Fetch channel posts\n"
        "/generate - Generate GitHub SEO index"
    )
    update.message.reply_text(help_text)

# Post to the channel
def post(update: Update, context: CallbackContext):
    """Posts a message to the Telegram channel with inline buttons."""
    message = "\ud83d\udcb0 Get the Real Flash BTC & USDT! \ud83c\udf1f\n\n\u25cb BTC Flash & USDT Flash - Starting from $30 - $50!"
    keyboard = [
        [InlineKeyboardButton("Free Software", url="https://t.me/FreeUSDTSender")],
        [InlineKeyboardButton("Consultation", url="https://t.me/PyCommander")],
        [InlineKeyboardButton("Reviews", url="https://t.me/ScriptersBuyBot")],
        [InlineKeyboardButton("Shop Crypto Goods", url="https://www.scripters.shop")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=CHANNEL_USERNAME, text=message, reply_markup=reply_markup)
    update.message.reply_text("Posted to the channel!")

# Fetch all channel posts
def fetch(update: Update, context: CallbackContext):
    """Fetches recent posts from the Telegram channel."""
    bot = Bot(BOT_TOKEN)
    updates = bot.get_updates()
    messages = []

    for update in updates:
        if update.channel_post and update.channel_post.chat.id == CHANNEL_ID:
            messages.append(update.channel_post.text)

    if messages:
        update.message.reply_text("\n\n".join(messages[:5]))  # Display the 5 most recent posts
    else:
        update.message.reply_text("No posts found.")

# Generate GitHub Pages index
def generate(update: Update, context: CallbackContext):
    """Generates an SEO-friendly index for GitHub Pages."""
    posts = [
        "<html>",
        "<head>",
        "<title>Scripters Marketplace</title>",
        "<meta name=\"description\" content=\"Discover, buy, and sell high-quality scripts, tools, and resources at Scripters Marketplace.\">",
        "<meta name=\"keywords\" content=\"scripts, buy scripts, sell scripts, marketplace, tools\">",
        "<meta name=\"author\" content=\"Rekt Developer\">",
        "</head>",
        "<body>",
        "<h1>Scripters Marketplace</h1>",
        "<p>Buy, sell, and share scripts and tools for developers.</p>"
    ]

    bot = Bot(BOT_TOKEN)
    updates = bot.get_updates()

    for update in updates:
        if update.channel_post and update.channel_post.chat.id == CHANNEL_ID:
            posts.append(f"<p>{update.channel_post.text}</p>")

    posts.append("</body>")
    posts.append("</html>")

    index_content = "\n".join(posts)
    with open("index.html", "w") as file:
        file.write(index_content)

    update.message.reply_text("GitHub Pages index generated successfully!")

# Main function
def main():
    """Start the bot."""
    updater = Updater(BOT_TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("post", post))
    dp.add_handler(CommandHandler("fetch", fetch))
    dp.add_handler(CommandHandler("generate", generate))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
