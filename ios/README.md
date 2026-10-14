# iOS 客户端首版 · TEST-232

状态：0.1.0 开发预览。最低 iOS 17，支持 iPhone/iPad。源码复用既有 HTTPS 服务器接口，不改变生产数据库、网页、PC 或安卓功能。

## 功能

- 邮箱验证注册、登录、找回密码，展示账号和密码规则。
- 人物卡、会话与平台来源；新建人物时同时命名首个会话。
- 当前用户的模型配置列表、新增、启用和连接测试；不回显模型密钥。
- 文字、明确触发的系统粘贴、照片/视频及文件导入；每次 4 个媒体附件，每个 50 MB。HEIC 等未直接支持的图片会转换为 JPEG 并缩放最长边至 2048，已支持格式保留文件字节。
- 先保存对方内容，分析媒体，生成回复；一键复制，实际发送后确认入库。重试复用本次操作标识，避免请求不确定时重复记录。
- 登录交接到内嵌主网页，访问完整档案、参考资料、账号安全与注销、管理员功能。每位用户用独立模型 API。
- 分享扩展先将待处理文字/文件保存在本机 App Group，不直接上传；用户打开 App，选择人物会话后明确导入。分享缓存绑定当前登录凭证的不可逆标识，退出/换账号清除，10 分钟过期。

## iOS 的操作边界

没有安卓式跨应用悬浮窗，不使用私有 API 强行唤起主 App。系统分享扩展保存完成后，手动打开 App 继续。第三方 App 是否提供分享菜单、分享的是文件还是链接，取决于该 App；链接不等于视频文件。保持 App 前台完成长请求，切后台可能中断。仅在用户明确粘贴/选择/分享时读取内容，不扫描其他应用的聊天。

登录令牌保存于本机 Keychain（WhenUnlockedThisDeviceOnly），不会放到分享扩展、UserDefaults 或公开日志。服务器地址是普通偏好设置。密码和模型密钥仅存在提交表单的短期内存中；媒体草稿在受保护的本机缓存，清空与退出时删除。临时共享资料不是长期服务器档案。

## 无 Mac、无开发者会员时

GitHub Actions 的 macOS 环境能编译和运行模拟器测试。输出的 SIMULATOR.zip 仅供 Mac 上的模拟器，UNSIGNED.zip 是无签名设备 archive；**均不能直接在 iPhone 上安装，不是正式 IPA**。网页可以继续在 iPhone Safari 使用。

真实设备及分享扩展需要有效 Apple 签名和 App Groups 配置。TestFlight/App Store 分发需要 Apple Developer Program；此阶段未配置，也不宣称已提交或通过 Apple 审核。

## 在 Mac 上开发

安装 Xcode 与命令行工具，使用支持 iOS 17 或更新 SDK 的 Xcode。

```sh
brew install xcodegen
cd ios
swift scripts/make_icon.swift
xcodegen generate
open Junshi.xcodeproj
```

选择 Junshi scheme 和模拟器运行。项目配置源为 project.yml，生成的工程/Info.plist/entitlements 不手动作为源提交。代码内的 -ui-testing 仅在 DEBUG 构建启用模拟网络，Release 不包含模拟接口行为。

## 后续真机 / TestFlight 准备

1. 注册自己的 Apple Developer Program，创建属于自己团队的主 App、分享扩展 Bundle ID 与 App Group。
2. 更新 project.yml 中两个 PRODUCT_BUNDLE_IDENTIFIER 与 JUNSHI_APP_GROUP，两个 target 使用同一团队和 App Group。
3. 在 Apple Developer 网站启用 App Groups，配置主 App/分享扩展各自的签名及 provisioning profile；不要把证书私钥、密码或 App Store Connect 私钥上传 Git。
4. 真机验证注册、登录、人物/会话、平台来源、模型、图片/视频、分享、注销、后台中断重试及不同账号隔离。
5. 准备图标、截图、支持与隐私政策 URL、App Store 隐私表、审核测试账号。PrivacyInfo.xcprivacy 是技术声明初稿，需按实际部署的数据处理范围复核。
6. 用同一团队签名并递增 build，上传 App Store Connect，先通过 TestFlight 测试，再提交 App Review。无 Mac 可另行配置 GitHub 的受保护签名流程，不能绕过会员、证书或审核要求。

参考：[Apple 分享扩展](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/Share.html)、[App Groups](https://developer.apple.com/documentation/xcode/configuring-app-groups)、[Apple 分发](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases)。
