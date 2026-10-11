# 升级、备份与恢复

本机运行见 [本地安装](LOCAL_DEPLOYMENT.md)。代码安装和私人数据迁移是两件独立的事。GitHub 包含应用与工具，不保存用户数据。

## 本地升级

1. 记录 `git rev-parse HEAD`，确认没有待保留的代码修改。
2. 停止本机应用；完整保留 `.env`、可选 `backend/.env`、`data/`。这些备份需保存在仓库外的私有位置。
3. 数据库备份使用项目工具，避免直接复制运行中的 SQLite 主文件而遗漏 WAL：

   ```sh
   python -m app.backup --destination data/backups/before-upgrade.sqlite3
   python -m app.backup --verify-manifest data/backups/before-upgrade.sqlite3
   ```

   `python` 指项目虚拟环境；备份文件与生成的 manifest 必须一同保留。每次换用新文件名。
4. `git pull --ff-only`，重新安装 `backend/requirements.txt`，阅读目标版本是否新增迁移。
5. 启动 `python -m app.server`，检查 `/health/ready` 和 `/app`，登录后验证数据与模型配置。

新版本首次启动会执行新增迁移。发生问题时先停服，核对代码与数据库兼容性；不能一律覆盖数据库回退，否则可能丢失新数据。

## 私人数据恢复到新机器

使用与备份兼容的代码，停止目标应用后操作。按 [可移植恢复](PORTABLE_RECOVERY.md) 使用加密包，或通过安全渠道迁移数据库备份及 manifest、媒体目录、私有配置。

```sh
python -m app.backup --verify-manifest /private/path/backup.sqlite3
python -m app.restore --backup /private/path/backup.sqlite3 --destination /private/path/app.sqlite3 --offline-confirmed
```

以上路径是占位示例，必须替换。两份 `.env` 若存在均需保留；恢复时保留原加密密钥并调整绝对数据路径。不得把配置、恢复包或截图作为公开 issue 附件。

首次迁移采用停服最终备份；目标登录、数据和模型验证通过前保留源端备份。避免新旧实例同时写入各自数据库造成分叉。

## Linux 服务器

`deploy/systemd/` 模板采用固定目录 `/opt/ai-love-strategist`、虚拟环境 `.venv` 和 loopback 监听；请先阅读六个 unit 与 `install.sh`。它们是已有 Linux 部署方案，不适用于 Windows。

先完成独立 Python 环境、代码版本核对、私有配置、数据库初始化或恢复和有效备份，然后执行 `python -m app.preflight --backup-dir data/backups --json`。只有检查通过再安装/启动项目服务与备份、看门狗定时任务。安装脚本会启用 unit，但不会启动它们。

公网访问使用 Nginx 等反向代理与 HTTPS；域名/IP、证书路径、续期策略和防火墙属于各自环境配置，不在仓库内携带旧服务器的配置。数据库与媒体不可放入静态站点目录。升级前停用项目定时任务，备份、切换、验收后恢复原状态。

主分支 CI 验证代码，不会自动连接任何生产服务器或执行部署。历史阶段的单次上线脚本具有固定基线与环境假设，不是通用安装器。
