#!/bin/bash
# Restart Pablos AI bot

echo "🔄 Restarting Pablos AI bot..."

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 is not installed!"
    echo "Install it with: npm install -g pm2"
    exit 1
fi

# Restart the bot
pm2 restart pablos-ai

echo "✅ Pablos AI bot restarted!"
echo ""
echo "View logs with: pm2 logs pablos-ai"

