#!/bin/bash
# Check Pablos AI bot status

echo "📊 Pablos AI Bot Status"
echo "======================="
echo ""

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 is not installed!"
    echo "Install it with: npm install -g pm2"
    exit 1
fi

# Show bot status
pm2 status pablos-ai

echo ""
echo "For detailed logs, use: pm2 logs pablos-ai"
echo "For monitoring, use: pm2 monit"

