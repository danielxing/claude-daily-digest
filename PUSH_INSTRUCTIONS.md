# 推送代码到GitHub的说明

## 问题
仓库 `https://github.com/danielxing/claude-daily-digest` 可能还没有创建成功。

## 解决步骤

### 1. 创建GitHub仓库

访问: https://github.com/new

配置:
- Repository name: `claude-daily-digest`
- Description: `📰 Automated daily digest of Claude and Anthropic news`
- Public ✓
- **不要**勾选 "Add a README file"

点击 **Create repository**

### 2. 推送代码

创建仓库后,在终端执行:

```bash
cd /Users/xingdaniel/Claude/claude-daily-digest

# 确认remote配置正确
git remote -v

# 推送代码
git push -u origin main
```

### 3. 如果还是失败

尝试使用Personal Access Token:

```bash
# 生成Token: https://github.com/settings/tokens/new
# 勾选 "repo" 权限
# 复制生成的token

# 使用token推送
git remote set-url origin https://YOUR_TOKEN@github.com/danielxing/claude-daily-digest.git
git push -u origin main
```

### 4. 或者使用GitHub CLI

```bash
# 如果安装了gh命令
gh auth login
git push -u origin main
```

## 推送成功后

### 配置Secrets

访问: https://github.com/danielxing/claude-daily-digest/settings/secrets/actions

添加3个secrets(和ai-tutorial-newsletter相同的值):

| Secret名称 | 说明 |
|-----------|------|
| `EMAIL_USERNAME` | 你的Gmail地址 |
| `EMAIL_PASSWORD` | Gmail应用专用密码 |
| `EMAIL_TO` | 接收邮件的地址 |

### 测试运行

1. 访问: https://github.com/danielxing/claude-daily-digest/actions
2. 点击 **Claude Daily Digest** workflow
3. 点击 **Run workflow**

## 需要帮助?

如果遇到问题:
1. 检查GitHub仓库是否创建成功
2. 确认你有推送权限
3. 尝试使用Personal Access Token
