# Android 正式发布准备

当前版本为 1.0.0-rc3 候选，versionCode 22801。正式签名候选与普通 CI 的 debug 包明确分开。当前没有已发布的 1.0.0 正式包。

## 悬浮小窗

最大宽度 304dp，同时不超过屏幕宽度 82%；内容区最大 320dp，不超过屏幕高度 48%。外围透明、无背景压暗，卡片保留半透明白色保证可读。拖动标题移动，点击标题收起，内容可滚动，外部区域可继续操作其他应用。

## 固定签名（只需一次）

由仓库所有者在受信任电脑生成和离线备份 keystore，不把私钥、密码或 base64 文本提交到 Git。

```sh
keytool -genkeypair -keystore junshi-release.jks -alias junshi -keyalg RSA -keysize 3072 -validity 10000
```

命令交互式询问密码和证书信息。密码不要写入脚本或聊天。将密钥文件转为 base64 后保存到仓库 Settings → Secrets and variables → Actions 的 ANDROID_KEYSTORE_BASE64；同时设置 ANDROID_KEYSTORE_PASSWORD、ANDROID_KEY_ALIAS（junshi）、ANDROID_KEY_PASSWORD。base64 不是加密，必须当作私钥保护。

运行 Actions → Android signed candidate → Run workflow，选择已验收分支。流程会核对签名并生成签名候选 APK 及校验清单；缺少配置时会失败，不回退使用测试签名。签名文件仅临时存在于 runner，最后删除。

首次从测试签名切换到正式签名通常需要卸载预览版，再安装固定签名版本。服务器业务数据不受影响；未提交草稿会丢失。以后必须用同一私钥和递增 versionCode 签名才能覆盖更新。

## 正式版验收

在真实手机验证登录、人物/平台/会话、文字/图片/视频导入、回复与发送确认、小窗拖动和收起、键盘、旋转、权限撤销、退出登录。验证目标机型后台限制；Android 8 与 Android 15 的行为可能不同。完成后单独将版本命名为 1.0.0，递增版本号，并发布固定签名附件。签名候选构建不会自动宣称正式发布，也不操作服务器。


当前 [TEST-228 下载](https://github.com/soyh/junshi/releases/tag/test-228-email-accounts) 中的 APK 为测试签名，支持邮箱注册和找回密码。后端 TEST-228 已通过生产上线验收；这不代表 APK 已完成长期正式签名配置。
