# Scripters Marketplace Telegram Bot

## Overview
This Telegram bot automatically processes channel posts, saves them as structured JSON files, and generates SEO-optimized HTML pages for each post.

## Features
- Captures Telegram channel posts
- Saves post data as JSON files
- Generates individual HTML pages for each post
- SEO-friendly meta tags
- Deployable on Vercel

## Prerequisites
- Node.js (v16+)
- Telegram Bot Token
- Vercel Account (optional)

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/RektDevelopers/ScriptersMarketplace.git
cd ScriptersMarketplace
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure Environment
1. Create a Telegram bot via BotFather on Telegram
2. Copy the bot token
3. Edit `.env` file:
   ```
   BOT_TOKEN=your_telegram_bot_token
   ```

### 4. Local Development
```bash
# Start development server
npm run dev

# Start production server
npm start
```

### 5. Deployment to Vercel
```bash
# Install Vercel CLI globally
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel deploy
```

## Project Structure
- `index.js`: Main bot script
- `.env`: Environment configuration
- `vercel.json`: Vercel deployment settings
- `public/data/posts/`: JSON post storage
- `public/html/posts/`: Generated HTML pages

## Security Notes
- Keep your bot token confidential
- Use environment variables for sensitive information
- Sanitize user inputs to prevent XSS

## Troubleshooting
- Ensure bot has necessary channel permissions
- Check Telegram API limits
- Verify environment configurations

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License
