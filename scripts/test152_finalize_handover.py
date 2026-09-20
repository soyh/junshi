from pathlib import Path
import re

path = Path("DEVELOPMENT_HANDOVER.md")
text = path.read_text(encoding="utf-8")
text = re.sub(r"^当前阶段：.*$", "当前阶段：TEST-152 — Product Management Completeness — VERIFIED", text, count=1, flags=re.M)
text = re.sub(r"^当前 Branch：.*$", "当前 Branch：`test-152-product-management-completeness`", text, count=1, flags=re.M)
marker = "## TEST-152 — Product Management Completeness — VERIFIED"
if marker not in text:
    block = """

## TEST-152 — Product Management Completeness — VERIFIED

用户明确要求“优先实现项目功能，最后再考虑环境数据迁移”。因此 TEST-152 从 TEST-150 VERIFIED 产品/生产基线继续，只补真实用户功能完整性；TEST-151 replacement-server bootstrap / environment-data migration 继续延期，不进入本阶段产品基线。

### 产品功能补齐

- 统一 `/app` 新增 `Core Record Management`：Person / Relationship / Conversation / Interaction 显式 Load / Update / Delete；Conversation 支持 archive / reactivate；Message 保持 evidence 不提供 PATCH，但支持显式删除后重录。
- Person / Relationship PATCH 统一 `UNSET` 语义：未提供字段与显式 `null` 分离，可空 nickname / notes / goals 可以真正清空。
- Person Profile 接入管理页面，继续读取 source-backed aggregate。
- 新增 `Account Security`：显式修改密码并接续新 session；Logout 清空密码输入；可加载并单独撤销某个其它 active session。
- 新增 Persisted Learning Memory history：按当前 user + Person 显式读取已保存 `memory_updates`；读取不调用 LLM、不触发 Re-analysis、不发送消息、不修改 Relationship。
- 修复 Interaction 管理状态同步：刷新列表后若选中记录仍存在，会从服务端重新加载完整编辑字段，避免 Relationship 等字段被局部 reset 后误保存。
- 没有为内部 synthesis / bridge API 机械复制第二套用户入口。

### GitHub verification

最终产品候选代码 HEAD：`bfab1ee55f91b0574c392d1fe08d5b16af458386`。

GitHub Actions run `35496707431`：focused `17 passed`；authenticated product / CRUD regression `134 passed`；full regression `876 passed`；`git diff --check` passed。

相对 TEST-150 post-verification handover baseline `9e9cfc81805e131a308c78f4ea981a9985373468`，有效 diff 仅为产品 API/service/repository/UI 与对应 tests；没有 historical migration、systemd、backup/restore、runtime environment 配置变化。

### 2026-09-20 production server acceptance

固定验收结果：branch `ops-server-acceptance-results`，file `ops/server_acceptance/latest.json`，result commit `35b419a725b6a4069fc3a22f325c633b7c61933c`。

- source HEAD `bfab1ee55f91b0574c392d1fe08d5b16af458386`；status=`passed`。
- server isolated tests：focused `17`、product regression `134`、full `876`；pytest 使用 detached worktree + tmp SQLite，不读取/改写 production database。
- production switch 前 live / ready / preflight 均通过，并创建 managed safety backup。
- 第一次 restart 失败来自 acceptance harness：手工默认 `app.backup` 后立刻触发 systemd `ExecStartPre app.backup`，秒级默认文件名发生同名 manifest collision；固定结果明确 `product_code_failure=false`。
- retry 使用唯一文件名 safety backup 后现有 systemd service 正常重启；最终 runtime PID `578548`；live / ready / preflight 与 live `/app` markers 均通过。
- backup timer 与 watchdog timer active；reserved port 8899 仍由独立 PID `52822` 持有。
- database restore：`NOT_EXECUTED`；environment/data migration：`NOT_EXECUTED`；historical migration 未修改。

### 结论

TEST-152 VERIFIED。当前产品功能基线已补齐认证与账号安全、Person / Relationship / Conversation / Interaction / Message 管理、Text Import、Evidence / Timeline、Structured Analysis、Strategy / Recommendation、Action Plan、Decision、Execution、Outcome、Feedback、Learning、Persisted Learning history 与 Re-analysis，并保持唯一 canonical lifecycle 与 scope 边界。

后续继续坚持“产品功能优先”：只有审计出新的真实用户功能 gap 才继续产品阶段；replacement-server / environment-data migration / automatic migration / additional disaster-recovery work 全部延后。
"""
    text = text.rstrip() + block.rstrip() + "\n"
path.write_text(text, encoding="utf-8")
