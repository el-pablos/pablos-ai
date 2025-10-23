#!/bin/bash
# Start Pablos AI bot with PM2

echo "🚀 Starting Pablos AI bot..."

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 is not installed!"
    echo "Install it with: npm install -g pm2"
    exit 1
fi

# Start the bot with PM2
pm2 start ecosystem.config.js

# Save PM2 process list
pm2 save

echo "✅ Pablos AI bot started!"
echo ""
echo "Use these commands to manage the bot:"
echo "  ./status.sh  - Check bot status"
echo "  ./restart.sh - Restart the bot"
echo "  ./stats.sh   - View bot statistics"
echo "  pm2 logs pablos-ai - View live logs"
echo "  pm2 stop pablos-ai - Stop the bot"

