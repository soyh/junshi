from pathlib import Path

path = Path("DEVELOPMENT_HANDOVER.md")
text = path.read_text(encoding="utf-8")

text = text.replace(
    "当前阶段：TEST-147 — Full Product Lifecycle E2E / Release Acceptance — VERIFIED\n当前 Branch：`test-147-full-lifecycle-release-acceptance`",
    "当前阶段：TEST-148 — Platform Supervision / Backup Scheduling / Runtime File Hardening — VERIFIED\n当前 Branch：`test-148-platform-supervision-backup-scheduling`",
    1,
)
text = text.replace(
    "- TEST-008 ~ TEST-147：按既有交接记录 VERIFIED。",
    "- TEST-008 ~ TEST-148：按既有交接记录 VERIFIED。",
    1,
)
needle = "- TEST-147：GitHub self-test、服务器完整回归、真实 managed backup、production release preflight、liveness/readiness 均已通过；正式 VERIFIED。"
replacement = needle + "\n- TEST-148：systemd supervisor、daily persistent managed-backup timer、safe retention、runtime file permission hardening 已完成 GitHub + server 实机验证；正式 VERIFIED。"
text = text.replace(needle, replacement, 1)

section = r'''

## TEST-148 — Platform Supervision / Backup Scheduling / Runtime File Hardening — VERIFIED

TEST-147 实际 production release 后进行只读 gap audit，确认真实运维缺口：18080 runtime 仍属于 SSH/nohup session、无 systemd service / boot supervision；无 managed-backup timer/cron；`.env` 与主 SQLite database 权限均为 `0644`。TEST-148 只做 platform operations hardening，不修改业务 API、schema、历史 migrations、LLM lifecycle，也不触碰 reserved port 8899。

### 实现

- `deploy/systemd/ai-love-strategist.service`：映射既有 TEST-133 supervision contract；`WorkingDirectory=/opt/ai-love-strategist`；启动前严格执行 managed backup → retention `keep=7` → production preflight；正式进程仍为 `.venv/bin/python -m app.server`；`Restart=on-failure`、`RestartSec=5`、SIGTERM、30 秒 stop grace、`UMask=0077`。
- `deploy/systemd/ai-love-strategist-backup.service`：oneshot managed backup + verified retention，完全复用既有 `app.backup` / manifest / SHA-256 / retention 实现。
- `deploy/systemd/ai-love-strategist-backup.timer`：`OnCalendar=daily`、`Persistent=true`、15 分钟 randomized delay，错过日程后可在后续 boot 补跑。
- `deploy/systemd/install.sh`：安装并 enable units，但验证阶段不自动 start/restart/stop；把 `.env`、`data/app.sqlite3` 和 managed backup / manifest 收紧为 `0600`。
- 新增 `backend/tests/test_systemd_operational_hardening.py`，验证 unit/timer/install script 与 VERIFIED runtime/backup contracts 一致且不引用 8899。

### GitHub self-test

GitHub Actions run `35450677053` / job `105917164725`，测试 HEAD `ab81b9dafa7d79f8f4cdf5a736be71a06d5af7dd`：
- TEST-148 focused：7 passed；
- operations regression：76 passed；
- full regression：833 passed in 152.26s；
- `git diff --check` passed。

临时 validation workflow 随后删除。最终服务器验证代码 HEAD：`0f8f839ee49fa2990d4b340ca3fa93420aa5a851`。

### 服务器验证与真实 takeover（2026-09-19）

- installer syntax 与 `systemd-analyze verify` 均通过；server targeted operations regression `76 passed in 1.23s`；full regression `833 passed in 149.85s`；repository clean。
- takeover 前 production runtime PID `551359`；live / ready / preflight 均成功；8899 为独立 PID `52822`。
- safety backup：`app-20260919T151926Z.sqlite3` + manifest；preflight overall ready=true。
- `install.sh` 安装并 enable runtime service 与 backup timer，安装后 `.env`、`data/app.sqlite3`、managed backups/manifests 均为 `0600`。
- 旧 SSH/nohup PID `551359` 通过 SIGTERM 正常停止；无需 database restore。
- systemd 首次启动 PID `553206`；cgroup 明确属于 `/system.slice/ai-love-strategist.service`；监听保持 `127.0.0.1:18080`；启动前实际执行 backup → retention → preflight，全部 success。
- backup timer 已 `enabled + active`，下一次调度已由 systemd 注册；手工触发 `ai-love-strategist-backup.service` 返回 `Result=success` / `ExecMainStatus=0`；当时 managed backup count=4，符合 `keep=7`。
- 故障恢复实测：对 systemd MainPID `553206` 发送 SIGKILL；systemd 按 `RestartSec=5` 自动重启为 PID `553280`；journal 显示 failed-by-signal → scheduled restart → backup → retention → preflight → app.server 完整恢复链。
- 故障恢复后 live / ready / preflight 再次全部 exit 0；最终 runtime PID `553280`，service enabled+active，timer enabled+active。
- 8899 PID takeover 前后均为 `52822`，本阶段没有停止、修改、复用或接管 8899。
- database restore：`NOT_EXECUTED`。

结论：TEST-148 VERIFIED。生产 runtime 已从 SSH/nohup 进程升级为 OS-level systemd supervision，具备 boot enable、failure auto-restart、startup fail-closed preflight、启动前 fresh managed backup、daily persistent backup scheduling、safe retention 与敏感运行文件权限 hardening。后续不机械创建 TEST-149；先继续审计 TEST-148 之后仍存在的真实产品/运维 gap，再决定下一阶段。
'''

if "## TEST-148 — Platform Supervision / Backup Scheduling / Runtime File Hardening — VERIFIED" not in text:
    text = text.rstrip("\n") + section + "\n"

path.write_text(text.rstrip("\n") + "\n", encoding="utf-8")
