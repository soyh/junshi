# AI 恋爱军师 · 项目与下载中心

人物、跨平台账号、聊天记录、参考资料、回复建议和可追溯的长期人物档案。网页、Windows 客户端及安卓 App 使用同一服务器。

## 下载与资料

- [安卓 1.0.0 正式版](https://github.com/soyh/junshi/releases/tag/android-v1.0.0)：固定签名 APK、源码、文档及签名验证报告。
- [PC 229 与项目附件](https://github.com/soyh/junshi/releases/tag/test-229-account-interface)
- [TEST-230 网页修复与部署](https://github.com/soyh/junshi/releases/tag/test-230-transfer-entry-style)
- [项目总览与版本](docs/PROJECT_OVERVIEW.md)
- [全部文档](docs/README.md)
- [本地部署](docs/LOCAL_DEPLOYMENT.md) · [服务器运维与恢复](docs/OPERATIONS.md)
- [PC 使用说明](desktop/CLIENT_README.txt) · [安卓使用说明](android/README.md)

## 当前组件版本

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| 后端与网页 | TEST-230 | 用户反馈服务器验收通过；数据库 001–023，统一底部迁移入口 |
| Windows 独立客户端 | 229 | 蓝白小窗、邮箱注册与找回密码、独立模型设置 |
| 安卓 App | 1.0.0 / versionCode 23100 | 已发布固定签名正式包，Android 8.0 及以上 |

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
