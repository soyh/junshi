# AI 恋爱军师 · 项目与下载中心

人物、跨平台账号、聊天记录、参考资料、回复建议和可追溯的长期人物档案。网页、Windows 客户端及安卓 App 使用同一服务器。

## 下载与资料

- [项目附件发布页](https://github.com/soyh/junshi/releases/tag/project-snapshot-223)：PC 安装包、安卓 APK、源码、文档、检查报告、页面预览及校验清单。
- [项目总览与版本](docs/PROJECT_OVERVIEW.md)
- [全部文档](docs/README.md)
- [本地部署](docs/LOCAL_DEPLOYMENT.md) · [服务器运维与恢复](docs/OPERATIONS.md)
- [PC 使用说明](desktop/CLIENT_README.txt) · [安卓使用说明](android/README.md)

## 当前版本

| 组件 | 阶段 | 说明 |
| --- | --- | --- |
| 后端与网页 | TEST-219 | 数据库迁移 001–022，含浏览器登录交接 |
| Windows 独立客户端 | TEST-221 / 221.1 | 蓝白紧凑小窗，独立模型设置、人物与平台管理 |
| 安卓 App | TEST-223 / 223.1-preview | 跨应用悬浮窗、蓝白卡片界面，测试签名预览版 |

版本表表示仓库内容，不代表生产服务器自动升级。

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
