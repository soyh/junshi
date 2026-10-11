# AI 恋爱军师 · AI Love Strategist

管理人物、关系和聊天记录，结合个人参考资料生成回复建议，并维护可追溯的长期人物档案。

默认分支 `main` 用于可部署版本。此次整理的功能基线为 **TEST-214**（`125c918f759786cec56e61e07411d794fed210cf`），数据库迁移 **001–021**。TEST-216 在此基础上增加 PC 助手、多平台人物绑定和完整业务数据迁移。

## 在自己的电脑运行

需要 Git（下载 ZIP 可不安装 Git）和 **Python 3.11 或更新版本**。在准备存放项目的目录打开终端，执行：

```sh
git clone https://github.com/soyh/junshi.git
cd junshi
```

Windows PowerShell：

```powershell
python -m pip install -r backend/requirements.txt
.\Start-AI-Love-Strategist.cmd
```

Linux / macOS：

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python scripts/init_local.py
.venv/bin/python -m app.server
```

浏览器打开 **http://127.0.0.1:18080/app**，注册自己的账号，再到设置中填写自己的模型供应商、模型名、接口地址和 API Key。每个用户独立配置 API，不会共用其他用户的密钥。终端保持打开，按 `Ctrl+C` 停止服务。

**Windows 一键启动：** 安装应用依赖后，双击仓库根目录的 `Start-AI-Love-Strategist.cmd`。它会读取本机端口配置，等待服务健康后自动打开浏览器；重复双击会直接打开已运行的页面。保留首次启动的窗口，按 `Ctrl+C` 停止。优先使用 PATH 中的 Python，其次 Windows 的 py -3，最后兼容已有 .venv。首次空白安装自动初始化，已有配置和数据不覆盖。

初始化仅创建本机私有配置和存储目录；首次启动自动创建空数据库并应用迁移。已有配置或数据库时会拒绝重新初始化。不会导入原服务器的账号、人物、聊天、参考资料或模型配置。

端口占用时，首次初始化可用 `python scripts/init_local.py --port 18081`，随后访问对应端口。完整说明见 [本地安装](docs/LOCAL_DEPLOYMENT.md)。

## 功能

- 登录、注册、账号安全与用户独立模型设置。
- 人物卡选择、连续翻转放大过渡、人物工作区及人物删除。
- 中文日期、北京时间、24 小时制；批量聊天识别、预览与发送者映射。
- 聊天截图/媒体、参考文档和 Skills、目录检索、全局指南在线编辑。
- 最新消息校验、自动纠正、长历史预算和回复建议。
- 人物关系、状态及精简长期档案；分批分析、依据校验与可查询的更新原因。

## 项目资料

| 入口 | 内容 |
| --- | --- |
| [文档目录](docs/README.md) | 当前操作说明和历史设计资料 |
| [本地安装](docs/LOCAL_DEPLOYMENT.md) | Windows/Linux 启动、配置及常见问题 |
| [运维与恢复](docs/OPERATIONS.md) | 升级、备份、恢复、服务器部署边界 |
| [开发与仓库结构](docs/DEVELOPMENT.md) | 模块位置、验证和分支约定 |
| [当前交接](DEVELOPMENT_HANDOVER.md) | 已验收功能基线和后续维护入口 |
| [隐私与发布范围](docs/PRIVACY_AND_PUBLISHING.md) | 哪些文件可提交、哪些必须留在本机 |

## 目录

```text
backend/app/          后端与页面实现
backend/migrations/   按序执行的数据库迁移
backend/tests/        自动化测试和浏览器验收
app/                 从仓库根目录运行的兼容入口
scripts/             本地初始化和备份工具
deploy/systemd/      Linux 服务器服务模板
docs/                当前文档、设计说明和历史交接
.github/workflows/    主分支 CI 与历史阶段 CI
data/、logs/         本机运行数据（不提交）
```

代码仓库不携带私人数据。第三方参考文档/Skills 由用户自行上传，未纳入本仓库。历史 `test-*` 分支保留用于定位已验收提交；日常新安装使用 `main`，不要直接执行旧阶段的专用上线脚本。

## PC 快捷聊天助手（TEST-216）

部署新版服务器后，在 Windows 安装 `desktop/requirements.txt`，双击 **Start-PC-Assistant.cmd**。登录服务器，选择人物、平台和会话；Ctrl+Alt+J 唤起小窗并读取复制的文字、图片或本地视频文件。上方预览确认后再上传，下方显示可编辑建议，支持复制及“确认已发送”。

[完整使用说明与限制](docs/TEST-216-pc-assistant.md) 包括多平台账号绑定、加密完整导出/导入、依赖安装和媒体识别要求。首次部署新版服务会新增迁移 021，请先隔离验收和备份。
