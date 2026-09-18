# AI Love Strategist Development Handover

更新时间：2026-09-19
唯一交接文档：`/DEVELOPMENT_HANDOVER.md`
当前阶段：TEST-142 — Action Execution Workspace — SERVER TESTS PASSED / CLEAN WORKTREE PENDING
当前 Branch：`test-142-action-execution-workspace`
TEST-142 服务器已测试代码 HEAD：`06b2fd49aedc6a5d31bfd9d56025db755cd6b10b`
TEST-141 VERIFIED 服务器代码 HEAD：`49275dab6f83620159fc2fba6ef4fda30a0088ad`

> 本文件是项目唯一 canonical handover。后续不再维护 `docs/DEVELOPMENT_HANDOVER.md` 或其他镜像副本；所有阶段状态、验证结果、约束和下一阶段计划只更新本文件。

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

Canonical lifecycle：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

最终产品必须让用户在统一认证入口中管理 Person / Relationship / Conversation、持续录入真实互动证据，并让分析、策略、建议、行动、结果、反馈和学习沿唯一 canonical lifecycle 闭环运行。

## 固定运行环境与硬约束

- Server：Alibaba Cloud Linux 3.2104 LTS 64-bit。
- Project：`/opt/ai-love-strategist`。
- Venv：`/opt/ai-love-strategist/.venv`。
- FastAPI historical bind：`127.0.0.1:18080`。
- SQLite：`/opt/ai-love-strategist/data/app.sqlite3`。
- GitHub：`soyh/junshi`。
- 禁止使用、修改或停止端口 `8899`。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB。
- 不修改历史 migration；需要 schema 变更时只能新增 migration。
- 不删除测试、不修改测试来掩盖真实错误。
- 所有数据必须严格 user_id 隔离，Person / Relationship / Conversation 不得跨 scope 串档。
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- 每阶段必须完成 targeted + full regression；临时 CI 用完即删；服务器最终验收后才能标记 VERIFIED。
- verification tag 只有实际创建并验证存在后才能写为完成；当前未声称 TEST-113~142 verification tag 已创建。

## 架构边界

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed、保留 unknowns、等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 Relationship 或伪造 Outcome。
- Action Execution 必须来自独立显式动作；confirmed decision 本身不得触发执行。
- Outcome 必须保持为 Execution 之后的独立显式阶段。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle。

## 已 VERIFIED 基线

### Runtime / Operations

- TEST-122：彻底退役 `X-User-ID` 身份来源。
- TEST-123：基础 HTTP 安全响应头、auth/settings no-store、旧 `/health` cache contract 兼容、无 permissive CORS。
- TEST-124：production 强制 `debug=False`，关闭 docs/redoc/openapi。
- TEST-125：统一 `python -m app.server`；production loopback-only、single-worker、no reload、no proxy trust、no Server header。
- TEST-126：WAL-safe SQLite online backup + integrity verification + atomic publish。
- TEST-127：offline-confirmed restore + pre/post integrity verification + atomic replace + stale WAL/SHM cleanup。
- TEST-128：managed backup manifest + SHA-256 + strict verification + safe retention。
- TEST-129：read-only database/migration/backup readiness report + machine-readable exit status。
- TEST-130：release preflight。
- TEST-131：HTTP liveness 与 runtime readiness 分离。
- TEST-132：loopback-only runtime probe CLI。
- TEST-133：platform-neutral supervisor lifecycle contract。
- TEST-134：platform-neutral release runbook，明确 backup/preflight/stop/switch/start/probe/rollback 顺序，数据库 restore 仅在 offline + verified backup 下手工执行。

### Product Workspace

- TEST-135 VERIFIED：authenticated single-page `/app`，account/session、LLM Provider、Structured Analysis；token 仅在页面内存。服务器代码 HEAD `a2792c0207b1d43e6ad488c6deefec9e679f460f`。
- TEST-136 VERIFIED：Person / Relationship / Conversation Workspace；服务器代码 HEAD `07d2cf6fe47f1f2ec7a0672dfb9a9120385d1066`。
- TEST-137 VERIFIED：Conversation Content Workspace，Messages + Text Import；服务器代码 HEAD `da5a3b355dbdb6345809cfe0e2c28cd880e9e849`；full 754 passed。
- TEST-138 VERIFIED：Relationship Evidence / Timeline Workspace；服务器代码 HEAD `483d1f01d24de5c3ec53e96c62b26c46fac44713`；full 761 passed。
- TEST-139 VERIFIED：Strategy & Recommendation Workspace；显式加载，不在 Conversation 切换时自动调用 LLM；服务器代码 HEAD `6a9eb85104d5fd7dc35bd09bb89d35f2efba52c6`；targeted 72 / full 768 passed。
- TEST-140 VERIFIED：Action Plan Workspace；显式 generation + persisted read，proposal 保持 `status=proposed`、`requires_user_confirmation=true`；服务器代码 HEAD `323eea1dab49c8e3cc96d95a936875781072a187`；targeted 99 / full 776 passed。
- TEST-141 VERIFIED：Action Decision Workspace；显式 Confirm/Reject，只记录 decision，不启动 execution；服务器代码 HEAD `49275dab6f83620159fc2fba6ef4fda30a0088ad`；targeted 80 / full 784 passed。

## TEST-142 — Action Execution Workspace

### Contract

Canonical API：
- `GET /api/v1/persons/{person_id}/action-plan/execution-context`
- `POST /api/v1/persons/{person_id}/action-plan/executions/{decision_id}`

Create payload 仅包含可选 `executed_at` 与 `note`。

Context 状态：
- `execution_ready`
- `executed`
- `outcome_recorded`
- `not_executable`

只有 `decision=confirmed` 且未 Execution、未 Outcome 的 decision 才能进入 `execution_ready`。服务端 POST 时重新强制 confirmed、user/person/decision scope、no existing Outcome、no duplicate Execution。rejected 不可执行；重复 Execution 和已有 Outcome 后再次执行均为 conflict。

Execution 只写 `action_executions`，不会发送消息、创建 Outcome 或修改 Relationship。约束包括：
- `must_require_confirmed_decision=true`
- `must_require_explicit_execution=true`
- `must_not_execute_rejected_decision=true`
- `must_not_execute_from_confirmation_automatically=true`
- `must_not_send=true`
- `must_not_create_outcome_automatically=true`

### UI 实现

- 新增 `backend/app/ui/action_execution_workspace.py`。
- `/app` 顺序保持 Action Plan → Action Decision → Action Execution。
- 用户必须显式点击 `Load execution context`。
- 登录、Person 切换、Action Decision Confirm 都不会自动加载或执行。
- UI 只把 `decision=confirmed && execution_status=execution_ready` 作为候选；服务端仍是 authority。
- 可填写可选 `executed_at`、`note`，再单独点击 `Record selected execution`。
- POST 成功后只刷新 execution context；不会自动发送或创建 Outcome。
- Person 切换/logout 只 reset Execution workspace。
- page-memory bearer + safe DOM；不使用 localStorage/sessionStorage/innerHTML/X-User-ID。
- 无新业务 API、无 schema migration、未实现 Outcome UI。

### TEST-142 主要提交

- `94e519ca01ef3d38d0464b86045c8d7f2eeaf023` — Action Execution workspace fragment。
- `40d857c906ab049fa885a865562be977eb9d3401` — product shell injection / fragment isolation。
- `be3d16efd0b787a083e888ba07f5eaf5cbaf02b0` — 8 项 authenticated Action Execution workspace tests。
- `c34e76babd2bc549bb1885520d49804d6beedae9` — 临时 TEST-142 validation workflow。
- `b0ca633507939f36d9f910ecd7387045eee60bc7` — 删除临时 workflow。
- `06b2fd49aedc6a5d31bfd9d56025db755cd6b10b` — TEST-142 GitHub self-test 文档基线，也是本次服务器实际测试的代码 HEAD。

### GitHub Actions 验证

Run `35375105715`，job `105697834658`，整体 success：
- focused：8 passed。
- TEST-135~141 Product Workspace：50 passed。
- Execution canonical/synthesis/bridge/gate/scope：26 passed。
- Action Decision regression：13 passed。
- Outcome separation：12 passed。
- auth：7 passed。
- combined targeted：116 passed。
- full：792 passed。

唯一 pytest warning 为 Starlette TestClient / anyio BlockingPortal deprecation；GitHub runner 另有 Node20→Node24 action compatibility warning，均非测试失败。

### 2026-09-19 服务器返回值

服务器实际验证：
- Branch：`test-142-action-execution-workspace` — 正确。
- HEAD：`06b2fd49aedc6a5d31bfd9d56025db755cd6b10b` — 与预期测试代码 HEAD 完全匹配。
- Targeted：`116 passed in 24.13s` — 通过。
- Full regression：`792 passed in 137.37s` — 通过。
- `git diff --check` — 无输出，通过。
- `git status --short` — **非空**：
  - `?? ui-preview.log`
  - `?? uvicorn.log`

结论：TEST-142 的代码与测试验证均通过，但按项目既有“最终工作区必须 clean”的验收标准，当前仍有两个未跟踪运行日志，因此 **TEST-142 暂不标记 VERIFIED**。这些文件不是 tracked source diff，也未影响 pytest 结果，但需要先确认/清理或纳入明确的运行日志忽略策略，再做最后一次 clean-state 检查。

## 下一阶段

TEST-143 — Outcome Workspace。

只有 TEST-142 完成 clean-state 最终确认并正式标记 VERIFIED 后才创建 TEST-143 分支。TEST-143 预期只把现有 canonical Outcome create/read contract 接入 `/app`：只能基于已执行 Action Decision，由用户显式记录 Outcome；不得由 Execution 自动生成，不得跳过 Execution，不得自动创建 Feedback/Learning/Re-analysis。开始前必须先审计 Outcome schema、route、service、repository 和现有测试。
