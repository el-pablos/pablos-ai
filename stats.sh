#!/bin/bash
# Show Pablos AI bot statistics

echo "📈 Pablos AI Bot Statistics"
echo "==========================="
echo ""

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 is not installed!"
    echo "Install it with: npm install -g pm2"
    exit 1
fi

# Show detailed info
pm2 show pablos-ai

echo ""
echo "==========================="
echo "📊 Process List:"
pm2 list

echo ""
echo "For real-time monitoring, use: pm2 monit"
echo "For logs, use: pm2 logs pablos-ai"

