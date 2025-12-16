# 手动推送代码到GitHub

由于是新的私有仓库,可能需要重新认证。

## 方法1: 直接在你的终端推送

**请在你自己的终端(Terminal.app)中运行**:

```bash
cd /Users/xingdaniel/Claude/claude-daily-digest
git push -u origin main
```

这样会触发macOS钥匙串弹窗,你可以输入GitHub凭证。

---

## 方法2: 如果方法1失败,使用Personal Access Token

1. **生成Token**:
   - 访问: https://github.com/settings/tokens/new
   - Note: `claude-daily-digest`
   - Expiration: `No expiration`
   - 勾选: ✓ **repo** (所有权限)
   - 点击 **Generate token**
   - **复制token** (ghp_xxxxx...)

2. **使用token推送**:
   ```bash
   cd /Users/xingdaniel/Claude/claude-daily-digest

   # 临时使用token作为密码
   git remote set-url origin https://YOUR_TOKEN@github.com/danielxing/claude-daily-digest.git
   git push -u origin main

   # 推送成功后,改回普通URL
   git remote set-url origin https://github.com/danielxing/claude-daily-digest.git
   ```

---

## 方法3: 检查钥匙串中的凭证

ai-tutorial-newsletter能工作,说明钥匙串里有GitHub凭证。可能只需要更新一下:

```bash
# 查看钥匙串里的GitHub凭证
security find-internet-password -s github.com

# 如果显示凭证,删除它重新创建
security delete-internet-password -s github.com

# 然后推送(会提示输入新凭证)
cd /Users/xingdaniel/Claude/claude-daily-digest
git push -u origin main
```

---

## 推送成功后

配置GitHub Secrets:
- https://github.com/danielxing/claude-daily-digest/settings/secrets/actions

添加3个secrets(和ai-tutorial-newsletter相同):
- `EMAIL_USERNAME`
- `EMAIL_PASSWORD`
- `EMAIL_TO`

然后测试workflow:
- https://github.com/danielxing/claude-daily-digest/actions
