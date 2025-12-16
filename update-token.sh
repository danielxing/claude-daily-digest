#!/bin/bash

echo "🔑 更新GitHub Token"
echo ""
echo "你的新token需要包含以下权限:"
echo "  ✓ repo"
echo "  ✓ workflow"
echo ""
echo "请访问: https://github.com/settings/tokens/new"
echo ""
echo -n "请粘贴你的新token: "
read -s TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ Token为空"
    exit 1
fi

echo ""
echo "🚀 设置remote URL并推送..."

git remote set-url origin "https://${TOKEN}@github.com/danielxing/claude-daily-digest.git"
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功!"
    echo ""
    echo "🔒 恢复安全的remote URL..."
    git remote set-url origin "https://github.com/danielxing/claude-daily-digest.git"
    echo "✅ 完成!"
    echo ""
    echo "📋 下一步:"
    echo "1. 配置Secrets: https://github.com/danielxing/claude-daily-digest/settings/secrets/actions"
    echo "2. 添加: EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO"
    echo "3. 测试workflow: https://github.com/danielxing/claude-daily-digest/actions"
else
    echo ""
    echo "❌ 推送失败"
    echo "请检查token权限是否包含 repo 和 workflow"
fi
