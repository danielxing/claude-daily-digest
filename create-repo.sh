#!/bin/bash

# Script to create GitHub repository and push code
# Requires: gh CLI (GitHub CLI)

echo "📦 Creating GitHub repository: claude-daily-digest"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo ""
    echo "Please either:"
    echo "1. Install gh: brew install gh"
    echo "2. Or manually create the repo at: https://github.com/new"
    echo ""
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "🔐 Please authenticate with GitHub first"
    gh auth login
fi

# Create repository
echo "Creating repository..."
gh repo create danielxing/claude-daily-digest \
    --public \
    --description "📰 Automated daily digest of Claude and Anthropic news" \
    --source=. \
    --remote=origin

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Repository created successfully!"
    echo ""
    echo "🚀 Pushing code to GitHub..."
    git push -u origin main

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Code pushed successfully!"
        echo ""
        echo "🔗 Repository: https://github.com/danielxing/claude-daily-digest"
        echo ""
        echo "📋 Next steps:"
        echo "1. Configure Secrets at:"
        echo "   https://github.com/danielxing/claude-daily-digest/settings/secrets/actions"
        echo ""
        echo "2. Add these 3 secrets:"
        echo "   - EMAIL_USERNAME"
        echo "   - EMAIL_PASSWORD"
        echo "   - EMAIL_TO"
        echo ""
        echo "3. Test at:"
        echo "   https://github.com/danielxing/claude-daily-digest/actions"
    else
        echo ""
        echo "❌ Failed to push code"
    fi
else
    echo ""
    echo "❌ Failed to create repository"
    echo ""
    echo "Please manually create it at: https://github.com/new"
fi
