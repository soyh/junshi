# Android 1.0.0 正式发布

正式版 **1.0.0** 已发布，versionCode **23100**。下载 [固定签名正式 APK](https://github.com/soyh/junshi/releases/download/android-v1.0.0/JunshiAndroid-1.0.0.apk)，完整附件见 [正式发布页](https://github.com/soyh/junshi/releases/tag/android-v1.0.0)。普通 CI 的 debug 包仅用于测试，不能作为正式包分发。

APK SHA-256：`a72102b8cdbc19e0b3e1d6f169cc7c6173aaa94fe7db5956ce279a5fb1fd79c6`。

公开签名证书 SHA-256：`2dced13cb16401fc6ec015c7c8ebd9f5e0f4aa91cd501e8b33c31e3367b36c69`。

正式构建提交：`66a769a4ed0f2527aae2f09f59cb87a08747756e`。已验证固定签名、证书一致性、APK 非调试标志、安装版本、单元测试、lint、模拟器交互与项目回归。服务器与 PC 无需因本发布更新。

## 悬浮小窗

最大宽度 304dp，同时不超过屏幕宽度 82%；内容区最大 320dp，不超过屏幕高度 48%。外围透明、无背景压暗，卡片保留半透明白色保证可读。拖动标题移动，点击标题收起，内容可滚动，外部区域可继续操作其他应用。

## 固定签名（只需一次）

由仓库所有者在受信任电脑生成和离线备份 keystore，不把私钥、密码或 base64 文本提交到 Git。

```sh
keytool -genkeypair -keystore junshi-release.jks -alias junshi -keyalg RSA -keysize 3072 -validity 10000
```

命令交互式询问密码和证书信息。密码不要写入脚本或聊天。将密钥文件转为 base64 后保存到仓库 Settings → Secrets and variables → Actions 的 ANDROID_KEYSTORE_BASE64；同时设置 ANDROID_KEYSTORE_PASSWORD、ANDROID_KEY_ALIAS（junshi）、ANDROID_KEY_PASSWORD。base64 不是加密，必须当作私钥保护。

运行 Actions → Android signed release → Run workflow，选择已验收分支。流程会核对签名并生成固定签名 APK 及校验清单；缺少配置时会失败，不回退使用测试签名。签名文件仅临时存在于 runner，最后删除。

首次从测试签名切换到正式签名通常需要卸载预览版，再安装固定签名版本。服务器业务数据不受影响；未提交草稿会丢失。以后必须用同一私钥和递增 versionCode 签名才能覆盖更新。

## 正式版验收

在真实手机验证登录、人物/平台/会话、文字/图片/视频导入、回复与发送确认、小窗拖动和收起、键盘、旋转、权限撤销、退出登录。验证目标机型后台限制；Android 8 与 Android 15 的行为可能不同。1.0.0 已完成当前发布门禁。后续每个版本仍需重复验证，递增 versionCode 并沿用固定私钥；已公开的正式 APK 不覆盖替换。构建流程不操作服务器。

