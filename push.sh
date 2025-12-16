#!/bin/bash

# Script to push code to GitHub
# This will prompt for credentials if needed

echo "🚀 Pushing to GitHub..."
echo ""

cd /Users/xingdaniel/Claude/claude-daily-digest

# Show current status
echo "Current status:"
git status
echo ""

# Push to GitHub
echo "Pushing to origin/main..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "🔗 View your repository: https://github.com/danielxing/claude-daily-digest"
    echo ""
    echo "📋 Next steps:"
    echo "1. Configure GitHub Secrets at:"
    echo "   https://github.com/danielxing/claude-daily-digest/settings/secrets/actions"
    echo ""
    echo "2. Add these secrets:"
    echo "   - EMAIL_USERNAME: your Gmail address"
    echo "   - EMAIL_PASSWORD: Gmail app password"
    echo "   - EMAIL_TO: recipient email"
    echo ""
    echo "3. Test the workflow at:"
    echo "   https://github.com/danielxing/claude-daily-digest/actions"
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "💡 To fix this, you can:"
    echo "1. Use GitHub CLI: gh auth login"
    echo "2. Or manually push from terminal and enter your credentials when prompted"
    echo "3. Or use a Personal Access Token as password"
fi
