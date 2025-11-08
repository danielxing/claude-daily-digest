# 📰 Claude Daily Digest

自动化收集Claude和Anthropic相关的最新资讯,每天通过邮件发送精美的摘要报告。

## ✨ 功能特性

- 🤖 **全自动化**: 通过GitHub Actions每天定时运行,无需人工干预
- 📊 **多源收集**: 聚合来自官方文档、GitHub、技术博客等多个来源的内容
- 🎯 **智能过滤**: 自动去重和质量评分,只推送高质量内容
- 📧 **精美邮件**: 响应式HTML邮件模板,支持移动端查看
- 💾 **持久化存储**: 使用TinyDB跟踪已发送内容,避免重复推送

## 📦 数据来源

### 官方更新
- Anthropic官方博客
- API文档和Release Notes
- 官方公告

### GitHub项目
- Claude相关trending项目
- 新发布的工具和插件
- SDK更新和重要releases

### 技术博客
- Simon Willison
- MIT Technology Review
- TechCrunch
- The Verge
- 其他AI/LLM相关博客

## 🚀 快速开始

### 1. Fork这个仓库

点击右上角的Fork按钮,将项目复制到你的GitHub账户。

### 2. 配置GitHub Secrets

在你的仓库中,进入 `Settings` > `Secrets and variables` > `Actions`,添加以下secrets:

#### 必需的Secrets:

| Secret名称 | 说明 | 获取方式 |
|-----------|------|---------|
| `EMAIL_USERNAME` | 你的Gmail地址 | 例: your-email@gmail.com |
| `EMAIL_PASSWORD` | Gmail应用专用密码 | [获取方式](#如何获取gmail应用密码) |
| `EMAIL_TO` | 接收邮件的地址 | 可以与EMAIL_USERNAME相同 |

#### 可选的Secrets:

| Secret名称 | 说明 | 获取方式 |
|-----------|------|---------|
| `GITHUB_TOKEN` | GitHub API访问令牌 | Actions自动提供,无需配置 |

### 3. 启用GitHub Actions

1. 进入仓库的 `Actions` 标签页
2. 如果提示启用workflows,点击启用
3. 手动触发第一次运行测试

### 4. 测试运行

在Actions页面,点击 `Claude Daily Digest` workflow,然后点击 `Run workflow` 手动触发测试。

## 🔐 如何获取Gmail应用密码

1. **启用两步验证**
   - 访问 [Google账户安全设置](https://myaccount.google.com/security)
   - 启用"两步验证"

2. **创建应用密码**
   - 访问 [应用密码页面](https://myaccount.google.com/apppasswords)
   - 选择"邮件"和"其他(自定义名称)"
   - 输入名称如"Claude Digest"
   - 点击生成
   - 复制生成的16位密码

3. **添加到GitHub Secrets**
   - 将16位密码添加为 `EMAIL_PASSWORD`
   - 不要添加空格

## ⏰ 运行时间

- **默认时间**: 每天UTC时间04:00 (北京时间中午12:00)
- **修改时间**: 编辑 `.github/workflows/daily-digest.yml` 中的cron表达式

```yaml
on:
  schedule:
    # 修改这一行来改变运行时间
    - cron: '0 4 * * *'
```

Cron表达式格式: `分 时 日 月 周`
- `0 4 * * *` = 每天04:00 UTC
- `0 0 * * *` = 每天00:00 UTC (北京时间08:00)
- `0 8 * * *` = 每天08:00 UTC (北京时间16:00)

## 🛠 本地测试

### 安装依赖

```bash
cd claude-daily-digest
pip install -r requirements.txt
```

### 设置环境变量

```bash
export EMAIL_USERNAME="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export EMAIL_TO="recipient@example.com"
export GITHUB_TOKEN="your-github-token"  # 可选
```

### 运行数据收集

```bash
python scripts/collect_data.py
```

### 发送测试邮件

```bash
python scripts/send_email.py
```

### 查看HTML预览

运行发送脚本后,会在 `data/email_preview.html` 生成预览文件,可以在浏览器中打开查看。

## 📁 项目结构

```
claude-daily-digest/
├── .github/
│   └── workflows/
│       └── daily-digest.yml    # GitHub Actions配置
├── scripts/
│   ├── collectors/             # 数据收集器
│   │   ├── anthropic_docs.py  # Anthropic官方文档
│   │   ├── github_trends.py   # GitHub项目
│   │   └── rss_aggregator.py  # RSS订阅
│   ├── collect_data.py        # 主收集脚本
│   └── send_email.py          # 邮件发送脚本
├── templates/
│   └── email_template.html    # 邮件HTML模板
├── data/
│   ├── content_db.json        # 内容数据库(自动生成)
│   └── daily_digest.json      # 每日摘要(自动生成)
├── requirements.txt           # Python依赖
└── README.md                  # 本文档
```

## 🎨 自定义

### 修改邮件模板

编辑 `templates/email_template.html` 来自定义邮件样式。

### 添加新的数据源

1. 在 `scripts/collectors/` 创建新的收集器
2. 在 `scripts/collect_data.py` 中导入并调用
3. 更新邮件模板以显示新内容

### 调整内容过滤

修改 `scripts/collect_data.py` 中的 `calculate_quality_score()` 函数来调整质量评分逻辑。

## 📊 监控和调试

### 查看运行日志

1. 进入仓库的 `Actions` 标签页
2. 点击最近的workflow运行
3. 查看每个步骤的详细日志

### 常见问题

#### 邮件未收到

1. 检查垃圾邮件文件夹
2. 验证GitHub Secrets配置正确
3. 查看Actions日志中的错误信息
4. 确认Gmail应用密码正确

#### 认证失败

- 确保使用的是应用专用密码,而非Google账户密码
- 检查两步验证已启用
- 重新生成应用密码并更新Secret

#### 没有新内容

- 这是正常的,某些天可能确实没有新的Claude相关内容
- 系统会跳过发送邮件,不会浪费配额

## 💡 进阶功能

### 添加通知

修改 `.github/workflows/daily-digest.yml`,在失败时发送通知:

```yaml
- name: Send failure notification
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.GMAIL_USER }}
    password: ${{ secrets.GMAIL_APP_PASSWORD }}
    subject: ⚠️ Claude Digest Failed
    to: ${{ secrets.RECIPIENT_EMAIL }}
    from: ${{ secrets.GMAIL_USER }}
    body: The daily digest workflow failed. Check logs.
```

### 多收件人

在GitHub Secrets中将 `EMAIL_TO` 设置为逗号分隔的邮件地址:

```
email1@example.com,email2@example.com,email3@example.com
```

### 添加Reddit监控

1. 创建Reddit应用获取API密钥
2. 添加Secrets: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
3. 在requirements.txt添加: `praw>=7.7.1`
4. 创建 `scripts/collectors/reddit_monitor.py`

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request!

## 📮 联系方式

如有问题,请在GitHub创建Issue。

---

**Powered by GitHub Actions** | Made with ❤️ for Claude enthusiasts
