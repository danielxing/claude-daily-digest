#!/bin/bash

echo "🔐 GitHub认证设置"
echo ""
echo "请按照以下步骤操作:"
echo ""
echo "1. 访问: https://github.com/settings/tokens/new"
echo "2. Note: 输入 'claude-daily-digest'"
echo "3. Expiration: 选择 'No expiration'"
echo "4. 勾选权限: ✓ repo (所有repo权限)"
echo "5. 点击 'Generate token'"
echo "6. 复制生成的token (ghp_xxxxxxxxxxxx)"
echo ""
echo -n "请粘贴你的Personal Access Token: "
read -s TOKEN
echo ""
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ Token为空,退出"
    exit 1
fi

# 使用token更新remote URL
git remote set-url origin "https://${TOKEN}@github.com/danielxing/claude-daily-digest.git"

echo "✅ 认证配置完成!"
echo ""
echo "现在尝试推送..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功!"
    echo ""
    echo "🔒 为了安全,将remote URL改回普通格式..."
    git remote set-url origin "https://github.com/danielxing/claude-daily-digest.git"

    # 保存token到钥匙串
    echo "protocol=https
host=github.com
username=danielxing
password=${TOKEN}" | git credential-osxkeychain store

    echo "✅ Token已保存到macOS钥匙串"
else
    echo ""
    echo "❌ 推送失败"
fi
