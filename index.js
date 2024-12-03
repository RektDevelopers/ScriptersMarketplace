const { Telegraf } = require('telegraf');
const fs = require('fs').promises;
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Initialize bot
const bot = new Telegraf(process.env.BOT_TOKEN);

// Directories for data storage
const DATA_DIR = path.join(__dirname, 'public/data/posts');
const HTML_DIR = path.join(__dirname, 'public/html/posts');

// Ensure directories exist
async function ensureDirectories() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.mkdir(HTML_DIR, { recursive: true });
}

// Utility function to generate SEO-optimized HTML from JSON post
function generateHTML(post) {
  const { message_id, sender_chat, chat, caption, media, caption_entities } = post;
  
  // Sanitize HTML to prevent XSS
  const sanitizeHTML = (str) => {
    return str ? str.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;')
               .replace(/"/g, '&quot;')
               .replace(/'/g, '&#39;') 
               : '';
  };

  const ogImage = media?.[media.length - 1]?.file_id;
  const channelTitle = sanitizeHTML(sender_chat?.title || chat?.title || 'Scripters Marketplace');
  const channelUsername = sender_chat?.username || chat?.username;
  
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="${sanitizeHTML(caption || 'Check out this post on Scripters Marketplace!')}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="${channelTitle}">
  <meta property="og:description" content="${sanitizeHTML(caption || 'Explore this amazing post!')}">
  ${ogImage ? `<meta property="og:image" content="https://api.telegram.org/file/bot${process.env.BOT_TOKEN}/${ogImage}">` : ''}
  <meta property="og:url" content="https://scriptersmarketplace.vercel.app/html/posts/${message_id}.html">
  <title>${channelTitle}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
    img { max-width: 100%; height: auto; }
    ul { list-style-type: none; padding: 0; }
  </style>
</head>
<body>
  <h1>${channelTitle}</h1>
  ${caption ? `<p>${sanitizeHTML(caption)}</p>` : ''}
  <ul>
    ${media?.map(m => `<li><img src="https://api.telegram.org/file/bot${process.env.BOT_TOKEN}/${m.file_id}" alt="Post image"></li>`).join('') || ''}
  </ul>
  ${channelUsername ? `<a href="https://t.me/${channelUsername}">View on Telegram</a>` : ''}
</body>
</html>`;
}

// Main post handler
async function handleChannelPost(ctx) {
  try {
    const post = ctx.channelPost;
    
    // Ensure directories exist
    await ensureDirectories();

    // Save post as JSON
    const filePath = path.join(DATA_DIR, `${post.message_id}.json`);
    await fs.writeFile(filePath, JSON.stringify(post, null, 2));
    console.log(`Saved channel post to ${filePath}`);

    // Generate HTML
    const html = generateHTML(post);
    const htmlPath = path.join(HTML_DIR, `${post.message_id}.html`);
    await fs.writeFile(htmlPath, html);
    console.log(`Generated HTML file at ${htmlPath}`);
  } catch (error) {
    console.error('Error processing channel post:', error);
  }
}

// Set up bot event handler
bot.on('channel_post', handleChannelPost);

// Error handling and bot launch
bot.launch()
  .then(() => {
    console.log('Bot is running.');
  })
  .catch(console.error);

// Graceful shutdown
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));

// Export for serverless deployment
module.exports = bot;
