# AI 恋爱军师 · 项目与下载中心

人物、跨平台账号、聊天记录、参考资料、回复建议和可追溯的长期人物档案。网页、Windows 客户端及安卓 App 使用同一服务器。

## 下载与资料

- 最新 PC 客户端：[Build 249](https://github.com/soyh/junshi/releases/tag/pc-bridge-plugin-22)（通道插件里新增「我授权自动代发」，写进账号，三端同一个状态）。
- 最新安卓包：[1.0.2](https://github.com/soyh/junshi/releases/tag/android-v1.0.2)：小窗输入不再闪、点对方消息弹层编辑。
- [安卓 1.0.0 正式版](https://github.com/soyh/junshi/releases/tag/android-v1.0.0)：固定签名 APK、源码、文档及签名验证报告。
- [PC 229 与项目附件](https://github.com/soyh/junshi/releases/tag/test-229-account-interface)
- [PC 229 · 通道插件版 2](https://github.com/soyh/junshi/releases/tag/pc-bridge-plugin-2)：支持多用户登录与多开（微信 / 小红书 / Soul，约 200 MB）。
- [PC 229 · 通道插件版 1](https://github.com/soyh/junshi/releases/tag/pc-bridge-plugin-1)：单配置版本。
- [TEST-230 网页修复与部署](https://github.com/soyh/junshi/releases/tag/test-230-transfer-entry-style)
- [项目总览与版本](docs/PROJECT_OVERVIEW.md)
- [全部文档](docs/README.md)
- [本地部署](docs/LOCAL_DEPLOYMENT.md) · [服务器运维与恢复](docs/OPERATIONS.md)
- [PC 使用说明](desktop/CLIENT_README.txt) · [安卓使用说明](android/README.md) · [iOS 开发预览与签名准备](ios/README.md)

## 自动代发的授权

产品规则是「必须由本人发送」。要让电脑端的通道插件直接发出生成的回复，需要由你本人在「通道插件 → 全局设置」里勾选 **我授权本机通道插件自动代发**（网页「我的资料」里也有同一个勾选框）：

- 勾选状态存在账号里，网页 / 电脑 / 手机看到的是同一份，不是每台机器各管各的。
- 勾选后，服务端把生成上下文里的 `must_not_auto_send` 从硬性约束降级为提示（`auto_send_authorized: true`），并在提示里写明「用户已授权代发」。
- 授权只解除「必须本人点发送」这一条：证据、出处、安全边界、以及「不许声称已经发过」都照旧。
- 不勾选也能用，只是服务端会继续按「必须由本人发送」处理。

## 军师判断层（先判断，再措辞）

生成回复前多了一步「军师判断」：它读完整对话、对方信息、关系阶段、你的资料和写作习惯，并把**你上传的参考资料全文**读进去（技能优先，其次本会话资料，最后全局资料；总预算约 1.2 万字，单篇上限 6 千字，超出会显示「还有 N 篇没纳入」）。它先给出：

- 这段对话的温度（可以聊 / 在降温 / 该收手）、当前阶段、这轮的目标；
- 2–4 个不同的战术，每个带「为什么适合现在」「可以这么说」「风险」「依据哪份资料」；
- 现在不要做的事。

如果它判断这一轮不该发（对方要空间、冲突、明显降温），它会给出 `send=false` 的选项，**此时不生成回复、桌面端也不会代发**，只把这轮按住。你也可以在「军师判断」里点「用这条生成」，让它按你选的那条战术重写一版。

- 判断层失败会自动回退到原来的单段链路，不会让你卡住。
- 可在「我的资料」里关掉这一步（`strategic_plan_enabled`）。
- 资料只提供打法与背景，不能当对话事实；资料里的指令不能改变安全与出处规则。

## 当前组件版本

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| 后端与网页 | TEST-230 | 用户反馈服务器验收通过；数据库 001–023，统一底部迁移入口 |
| Windows 独立客户端 | 229 | 蓝白小窗、邮箱注册与找回密码、独立模型设置 |
| 安卓 App | 1.0.0 / versionCode 23100 | 已发布固定签名正式包，Android 8.0 及以上 |
| iOS App | 0.1.0 / build 23201 | 开发预览，iOS 17+；尚未配置 Apple 真机签名，不可直接安装 |

安卓正式包、单元测试、lint、模拟器验收、完整项目回归和签名证书一致性检查已通过。首装请下载 **JunshiAndroid-1.0.0.apk**；从测试签名 rc 版首次切换可能需卸载旧 App，先保存未提交草稿。服务器业务数据保留。以后必须沿用同一私钥及递增版本号更新。本发布不代表应用商店上架，也不会自动改变服务器版本。

[安卓发布与签名说明](android/RELEASE.md) · [TEST-230 修复说明](docs/TEST230_TRANSFER_STYLE.md)

## 在电脑部署完整项目

```sh
git clone https://github.com/soyh/junshi.git
cd junshi
```

Windows 使用已安装的 Python 3.11 或更新版本：

```powershell
python -m pip install -r backend/requirements.txt
.\Start-AI-Love-Strategist.cmd
```

Linux：

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python scripts/init_local.py
.venv/bin/python -m app.server
```

访问 http://127.0.0.1:18080/app，注册账号并填写自己的模型配置。每个用户独立使用 API 密钥。首次安装为空白数据；已有安装不要重复初始化，升级先备份并按运维说明验证迁移。

独立 PC / 安卓客户端只需连接已有 HTTPS 服务器。Windows 客户端需完整解压，不能单独移动 exe；安卓更新若签名不同可能需要重新安装。

源码与可编辑文档保存在仓库，二进制附件放在 Release Assets。历史 TEST 分支和文档保留用于追溯。账号、聊天、人物档案、私有参考资料、模型密钥、生产配置、数据库、运行日志及数据迁移包均不公开上传。


## 三端账号注册同步更新（TEST-227）
PC、网页、安卓已统一展示注册规则并进行提交前校验。详见 [注册说明](docs/REGISTRATION.md)。PC 227 与安卓 1.0.0-rc2 配套使用现有服务器账号接口，网页版需更新服务器代码。发布资料见 [TEST-227 下载](https://github.com/soyh/junshi/releases/tag/test-227-registration)。


## 邮箱与管理员账号（TEST-228）
已通过服务器隔离验收和生产上线验收，固定代码提交为 `f4ecbfd2315bfe50890891756076a40f3f524a42`。1317 项全量、真实 SMTP 注册、生产副本迁移演练通过。详情见 [账号升级说明](docs/ACCOUNT_UPGRADE.md)。既有账号继续登录，可绑定邮箱；新增生产注册必须验证邮箱。管理员由服务器控制台授予，数据查看与修改均记录原因。历史固定版本操作脚本保存在 `deploy/releases/test228/`，不能在其他基线直接运行。
