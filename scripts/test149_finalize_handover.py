from pathlib import Path

HANDOVER = Path("DEVELOPMENT_HANDOVER.md")
text = HANDOVER.read_text(encoding="utf-8")

text = text.replace("更新时间：2026-09-19", "更新时间：2026-09-20", 1)
text = text.replace(
    "当前阶段：TEST-148 — Platform Supervision / Backup Scheduling / Runtime File Hardening — VERIFIED",
    "当前阶段：TEST-149 — Runtime Health Watchdog / Degraded-State Recovery — VERIFIED",
    1,
)
text = text.replace(
    "当前 Branch：`test-148-platform-supervision-backup-scheduling`",
    "当前 Branch：`test-149-runtime-health-watchdog`",
    1,
)
text = text.replace(
    "- TEST-008 ~ TEST-148：按既有交接记录 VERIFIED。",
    "- TEST-008 ~ TEST-149：按既有交接记录 VERIFIED。",
    1,
)

marker = "## TEST-149 — Runtime Health Watchdog / Degraded-State Recovery — VERIFIED"
if marker not in text:
    section = r'''

## TEST-149 — Runtime Health Watchdog / Degraded-State Recovery — VERIFIED

TEST-148 完成 OS-level systemd process supervision 后继续审计 TEST-133 supervision contract，确认真实缺口：已有 contract 明确要求 readiness 每 10 秒、liveness 每 30 秒、连续失败阈值 3，但 platform deployment 尚未把“进程仍存活但 runtime degraded”映射为持续 health supervision。TEST-149 只补 runtime watchdog / degraded-state recovery，不修改业务 API、canonical lifecycle、database schema、历史 migration，也不触碰 reserved port 8899。

### 实现与安全边界

- 新增 `backend/app/core/runtime_watchdog.py`：readiness 每 tick 检查，liveness 每 3 tick 检查；默认 tick cadence 10 秒，对应 readiness 10 秒、liveness 30 秒；连续失败阈值 3；成功立即清零对应 failure counter。
- 新增 `backend/app/watchdog.py`：复用既有 loopback-only `app.probe`，状态仅写 `/run/ai-love-strategist/watchdog.json`，目录 `0700`、文件 `0600`。
- watchdog 只有真实达到 failure threshold 时才创建 `/run/ai-love-strategist/recovery-required`；monitoring/state-file 自身故障不会创建 recovery marker，避免 monitor failure 被误解释为 application failure。
- 新增 `ai-love-strategist-watchdog.timer/service`：timer 每 10 秒运行一次 watchdog；`OnFailure` 仅进入独立 recovery unit。
- 新增 `ai-love-strategist-recovery.service`：以 `ExecCondition` 要求 recovery marker 存在；没有 marker 不允许 restart；recovery 只执行 `systemctl restart ai-love-strategist.service`，不自动 restore database。
- recovery service 有独立 rate limit；runtime restart 仍沿 TEST-148 启动门执行 managed backup → retention keep=7 → preflight → `app.server`。
- runtime service 启动/重启后清除旧 watchdog state/recovery marker，避免 stale degraded state 穿越 restart。
- 首次服务器验收发现真实 startup race：`Type=simple` service 在 Python process 刚创建约 20ms 即返回 started，18080 尚未 listen，紧接 probe 会得到 `probe connection failed`。未用 sleep 绕过，而是新增 `app.wait_ready` + systemd `ExecStartPost` readiness gate；`systemctl start/restart` 只有在 readiness 真正成功后才返回成功，默认最多等待 30 秒。
- `app.wait_ready` 继续复用既有 runtime probe contract：loopback-only、拒绝 8899、machine-readable exit status；没有新增第二套 health endpoint。

### GitHub verification

最终 startup-readiness 修复 CI run `35453484593`，测试 HEAD `8d9e1b1c93f2d025092a4ff990d197cde6ab3f6a`：
- focused watchdog + startup readiness：`14 passed`；
- operations regression：`90 passed`；
- full regression：`847 passed`；
- `git diff --check` success。

临时 validation workflow 随后删除；server candidate effective HEAD / server-acceptance source HEAD：`39652fdad525703c03e1506f7ed8be3b5404ddc1`。

### Server full runtime acceptance

固定 machine-readable acceptance channel：branch `ops-server-acceptance-results`，file `ops/server_acceptance/latest.json`；full acceptance result commit `eeba8830d0707148f69a22923cd36fa526f02cd1`。

实机最终结果：
- source branch `test-149-runtime-health-watchdog`；source HEAD `39652fdad525703c03e1506f7ed8be3b5404ddc1`；status `passed`。
- startup readiness race fix 后：restart/live/ready/preflight 全部 exit code 0。
- no-marker gate 实测：没有 `/run/ai-love-strategist/recovery-required` 时 recovery unit 不会重启 runtime。
- 连续 failure threshold 实测 exit codes：`0, 0, 1`；第三次才进入 recovery-required；trigger=`readiness`。
- watchdog state 与 recovery marker 权限均为 private runtime state；controlled recovery verified。
- controlled recovery 将 systemd runtime PID `558463` 重启为 `559990`；恢复后 stale watchdog state/marker 被清理。
- recovery 后 liveness/readiness/preflight 全部 exit code 0；最终 runtime PID `559990`，仍由 `ai-love-strategist.service` systemd cgroup 管理。
- healthy watchdog unit：Result=`success`、ExecMainStatus=`0`。
- backup timer active；watchdog timer active 且 enabled。
- `.env` mode `0600`；`data/app.sqlite3` mode `0600`。
- reserved port 8899 owner before/after 均为独立 PID `52822`；TEST-149 未停止、修改、复用或接管 8899。
- database restore：`NOT_EXECUTED`。

结论：TEST-149 VERIFIED。TEST-133 supervision contract 的 process failure 与 degraded-health recovery 均已完成 platform-level systemd 落地；startup readiness race 也已用显式 readiness gate 修复。后续不机械创建下一 TEST 编号，必须继续审计新的真实产品/运维缺口后再定义阶段。
'''
    text = text.rstrip() + section.rstrip() + "\n"

HANDOVER.write_text(text, encoding="utf-8")
