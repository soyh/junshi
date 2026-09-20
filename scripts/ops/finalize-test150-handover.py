from pathlib import Path

path = Path('DEVELOPMENT_HANDOVER.md')
text = path.read_text(encoding='utf-8')

old = '''更新时间：2026-09-20
当前阶段：TEST-149 — Runtime Health Watchdog / Degraded-State Recovery — VERIFIED
当前 Branch：`test-149-runtime-health-watchdog`
'''
new = '''更新时间：2026-09-20
当前阶段：TEST-150 — Portable Backup & Local Disaster Recovery — VERIFIED
当前 Branch：`test-150-offsite-disaster-recovery`
TEST-150 post-verification 基线：`773101052fa98345e6a85b8c5b2e2c4f1d9f7d7e`
'''
if old not in text:
    raise SystemExit('top-of-handover TEST-149 header not found')
text = text.replace(old, new, 1)

old_status = '- TEST-008 ~ TEST-149：按既有交接记录 VERIFIED。'
new_status = '- TEST-008 ~ TEST-150：按既有交接记录 VERIFIED。\n- TEST-150：portable encrypted recovery bundle + Windows pull/restore workflow 已完成 GitHub、服务器和真实 Windows off-server pull 验证；正式 VERIFIED。'
if old_status not in text:
    raise SystemExit('stage status marker not found')
text = text.replace(old_status, new_status, 1)

section = r'''

## TEST-150 — Portable Backup & Local Disaster Recovery — VERIFIED

TEST-149 后的生产耐久性审计确认：主 SQLite database 与 managed backups 位于同一服务器/同一存储设备。最初 TEST-150 曾验证 provider-neutral offsite mount 方案，但结合实际使用方式（自用、服务器更换频繁、固定 Windows 电脑）重新收敛为 portable local disaster recovery：GitHub 保留完整源代码；服务器视为可替换运行节点；可信 Windows 电脑保留独立的数据与私密配置恢复材料。

### 最终实现

- 新增 portable recovery core/CLI：对 verified managed SQLite backup + manifest 生成 AES-256-GCM authenticated encrypted recovery bundle；支持 SHA-256、manifest/integrity re-verification、tamper rejection、idempotent reuse 与 retention。
- 服务器 export 目录：`/opt/ai-love-strategist/data/recovery_exports`；production `.env` 中只保存实际 `PORTABLE_BACKUP_ENCRYPTION_KEY`，文件继续保持 `0600`；真实 key 不进入 GitHub/handover/log summary。
- 新增 `scripts/server/prepare-portable-recovery.sh`：生成/配置 portable key、创建 fresh managed backup、验证 bundle、通过 systemd readiness gate 部署 TEST-150 runtime；不执行 database restore、不修改 reserved port 8899。
- 新增 `scripts/windows/backup-pull.ps1`：Windows 主动 SSH/SCP 请求 fresh portable bundle、下载、重新计算 SHA-256、临时下载 production `.env`、使用 Windows DPAPI 当前用户/当前电脑保护 `.env`、删除明文临时文件并写 `recovery.json`。
- 新增 `scripts/windows/restore-push.ps1`：默认 stage-only，只传 encrypted bundle；未显式 `-ApplyRestore` 时不解密/上传 `.env`、不 stop service、不 restore database。只有显式 apply 才恢复 `.env`、离线验证/恢复 SQLite、重启服务并重新检查 live/ready/preflight。
- 新增 `docs/PORTABLE_RECOVERY.md`；GitHub 继续作为完整 source/deploy/test/handover code backup，不保存 production `.env`、database 或真实 encryption key。
- 已移除早期 TEST-150 的 OSS/NFS/offsite-mount systemd service/timer/installer 和 CLI 入口，避免同时维护两套灾备模型；底层已验证加密能力被 portable recovery 复用。

### GitHub verification

最终候选代码 HEAD：`773101052fa98345e6a85b8c5b2e2c4f1d9f7d7e`。

最终补跑 GitHub Actions：
- TEST-150 focused：`12 passed`；
- operations regression：`73 passed`；
- full regression：`859 passed`；
- Windows PowerShell scripts parser：passed；
- server preparation shell syntax：passed；
- retired offsite deployment files absence：passed；
- `git diff --check`：passed。

TEST-149 baseline `5e3669142b7c97061d370d5566bab61e3d83d9f4` → TEST-150 candidate 的最终有效 diff 仅保留 11 个长期文件；temporary validation workflows 已清理。

### 2026-09-20 服务器真实准备验收

服务器 branch `test-150-offsite-disaster-recovery`，source HEAD `773101052fa98345e6a85b8c5b2e2c4f1d9f7d7e`。

- `scripts/server/prepare-portable-recovery.sh`：`TEST150_SERVER_PREP=PASSED`。
- production runtime 通过 systemd 正常重启：PID `559990 -> 563415`。
- first verified portable bundle 已生成；server-prep bundle SHA-256：`78ec2c439f6c5def26e5cd8055b3ba6b9a957dd9f31f309655010ffce1ab8784`。
- reserved port 8899 owner 始终为独立 PID `52822`，没有停止、修改、复用或接管。
- database restore：`NOT_EXECUTED`。

### 2026-09-20 Windows 真实 off-server pull 验收

可信 Windows 电脑完成真实 SSH/SCP pull：

- `BACKUP_PULL=PASSED`。
- local snapshot：`C:\\Users\\12274\\AI-Love-Strategist-Backup\\snapshots\\20260920T033936Z`。
- source HEAD：`773101052fa98345e6a85b8c5b2e2c4f1d9f7d7e`。
- 实际下载 bundle SHA-256：`839b18947750f4356b1b0dd721d66e4a2feb8432c5696bda0192fb1d79e4839d`；Windows 端重新计算后与服务器本次 fresh prepare 结果一致，否则脚本会 fail closed。
- snapshot 由 encrypted recovery bundle + DPAPI-protected `production.env.dpapi` + `recovery.json` 组成；脚本不会在成功快照中保留明文 `.env` 临时文件。
- source code 已完整 clone 到 Windows，并固定到 TEST-150 candidate HEAD；因此服务器可被视为可替换运行节点。
- 这次 Windows pull 只创建 fresh backup/export 并读取 `.env`；没有执行 database restore，也没有修改 8899。

### 结论与边界

TEST-150 VERIFIED。当前灾备模型为：GitHub = 完整代码灾备；Windows PC = 数据 + production secrets 的独立恢复材料；服务器 = 可替换运行节点。服务器仍保留 TEST-148/149 的本机 managed backup、systemd supervision 与 watchdog 作为短期保护层。

已知边界：`production.env.dpapi` 使用 Windows DPAPI current user/current computer，因此若该 Windows 电脑也永久丢失，不能假定能在另一台电脑直接解密。需要更高耐久性时，应另做离线加密副本/第二本地介质；这不是 TEST-150 当前自用恢复模型的 blocker。

后续不机械创建 TEST-151。先基于 TEST-150 VERIFIED baseline 重新审计真实产品/运维 gap，再决定是否需要下一阶段。
'''

if '## TEST-150 — Portable Backup & Local Disaster Recovery — VERIFIED' in text:
    raise SystemExit('TEST-150 section already present')
text = text.rstrip() + section + '\n'
path.write_text(text, encoding='utf-8')
