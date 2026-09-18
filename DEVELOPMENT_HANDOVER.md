# AI Love Strategist Development Handover

更新时间：2026-09-19
当前阶段：TEST-141 — Action Decision Workspace — VERIFIED
当前 Branch：test-141-action-decision-workspace
TEST-141 VERIFIED 服务器代码 HEAD：`49275dab6f83620159fc2fba6ef4fda30a0088ad`
TEST-140 VERIFIED 服务器代码 HEAD：`323eea1dab49c8e3cc96d95a936875781072a187`
TEST-139 VERIFIED 服务器代码 HEAD：`6a9eb85104d5fd7dc35bd09bb89d35f2efba52c6`
TEST-138 VERIFIED 服务器代码 HEAD：`483d1f01d24de5c3ec53e96c62b26c46fac44713`
TEST-137 VERIFIED 服务器代码 HEAD：`da5a3b355dbdb6345809cfe0e2c28cd880e9e849`
TEST-136 VERIFIED 服务器代码 HEAD：`07d2cf6fe47f1f2ec7a0672dfb9a9120385d1066`
TEST-135 VERIFIED 服务器代码 HEAD：`a2792c0207b1d43e6ad488c6deefec9e679f460f`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

最终产品必须让用户在统一认证入口中管理 Person / Relationship / Conversation、持续录入真实互动证据，并让分析、策略、建议、行动、结果、反馈和学习沿唯一 canonical lifecycle 闭环运行。

## 阶段状态

- TEST-008 ~ TEST-141：按既有交接记录 VERIFIED。
- TEST-134 VERIFIED：platform-neutral release runbook / rollback safety contract。
- TEST-135 VERIFIED：authenticated single-page product shell。
- TEST-136 VERIFIED：authenticated Person / Relationship / Conversation Workspace。
- TEST-137 VERIFIED：Conversation Content Workspace，Messages + Text Import 产品化接入。
- TEST-138 VERIFIED：Relationship Evidence / Timeline Workspace。
- TEST-139 VERIFIED：Strategy & Recommendation Workspace。
- TEST-140 VERIFIED：Action Plan Workspace。
- TEST-141 VERIFIED：Action Decision Workspace。

## Runtime / Operations 产品化基线

- TEST-122：彻底退役 `X-User-ID` 身份来源。
- TEST-123：基础 HTTP 安全响应头、auth/settings no-store、旧 `/health` cache contract 保持兼容、无 permissive CORS。
- TEST-124：production 强制 `debug=False`，关闭 docs/redoc/openapi。
- TEST-125：统一 `python -m app.server`；production loopback-only、single-worker、no reload、no proxy trust、no Server header。
- TEST-126：WAL-safe SQLite online backup + integrity verification + atomic publish。
- TEST-127：offline-confirmed restore + pre/post integrity verification + atomic replace + stale WAL/SHM cleanup。
- TEST-128：managed backup manifest + SHA-256 + strict verification + safe retention。
- TEST-129：read-only database/migration/backup readiness report + machine-readable exit status。
- TEST-130：release preflight 汇总 production config、secure launcher、operations readiness；部署前 fail closed。
- TEST-131：HTTP liveness 与 runtime readiness 分离；高频 probe 不执行 backup checksum/integrity。
- TEST-132：本机 loopback-only runtime probe CLI。
- TEST-133：平台无关 supervisor lifecycle contract。
- TEST-134：平台无关 release runbook，明确 backup/preflight/stop/switch/start/probe/rollback 顺序和数据库回滚安全门槛。

## TEST-135 ~ TEST-138 — VERIFIED 产品化基线

- TEST-135：统一 `/app`，完成 account/session、LLM Provider 与 Structured Analysis；token 仅在页面内存。
- TEST-136：Person → Relationship → Conversation Workspace；后端继续负责 canonical scope/cross-consistency。
- TEST-137：Messages + Text Import；Text Import 保持“创建新 Conversation”既有语义；server verified targeted 81 / full 754。
- TEST-138：Interaction + Person Timeline；Timeline 只读聚合 Conversation + Message + Interaction；server verified targeted 48 / full 761。

## TEST-139 — Strategy & Recommendation Workspace — VERIFIED

目标：把 Strategy / Recommendation canonical context 接入统一 `/app`，不新建第二套策略或建议逻辑。

关键约束：Conversation 切换不自动调用 LLM；用户显式点击加载；Recommendation 保留 evidence provenance、`must_not_auto_select` 与 `must_not_auto_execute`；无 Action Plan / Decision / Execution。

GitHub Actions run `35369269897`：full 768 passed。服务器最终验收 branch `test-139-strategy-recommendation-workspace`、HEAD `6a9eb85104d5fd7dc35bd09bb89d35f2efba52c6`：targeted 72 passed、full 768 passed，`git diff --check` 与 `git status --short` 无输出。TEST-139 VERIFIED。

## TEST-140 — Action Plan Workspace — VERIFIED

现有系统区分 Conversation-level Action Plan generation/persistence 与 Person-level persisted Action Plan read。TEST-140 只在用户显式点击 `Generate & save action plan` 时调用可能触发 LLM/provider 并写入 `action_plan_snapshots` 的 Conversation-level orchestration；`Refresh saved plans` 只读 Person-level persisted context。Action Plan item 保持 `status=proposed`、`requires_user_confirmation=true`，不创建 Action Decision、不执行。

GitHub Actions run `35370519984` success：targeted 99 passed，full 776 passed。服务器最终验收于 2026-09-19 完成：branch `test-140-action-plan-workspace`，HEAD `323eea1dab49c8e3cc96d95a936875781072a187`，targeted 99 passed in 17.04s，full 776 passed in 134.61s，`git diff --check` 与 `git status --short` 无输出。TEST-140 VERIFIED。

## TEST-141 — Action Decision Workspace — VERIFIED

### Contract 审计

现有 canonical Action Decision API：
- `GET /api/v1/persons/{person_id}/action-plan/decisions/context`：读取当前 Person Action Plan proposals、decision constraints 与 decision history；
- `POST /api/v1/persons/{person_id}/action-plan/decisions`：记录显式用户决定；payload 为 `recommendation_id`、`decision`、可选 `note`；
- `decision` 只允许 `confirmed | rejected`；
- `confirmed` 必须提供 `recommendation_id`；
- 任何带 `recommendation_id` 的 decision 只能引用当前 Action Plan 中仍满足 `status=proposed` 且 `requires_user_confirmation=true` 的 proposal；服务端在 POST 时再次校验，客户端不是 authority；
- decision history 由 repository 按 `created_at DESC, id DESC` 返回；
- Action Decision create 只写 `action_decisions`，不会调用 Execution service。

Execution 是独立后续边界：`POST /api/v1/persons/{person_id}/action-plan/executions/{decision_id}` 才能创建 execution，并且只接受 confirmed decision。现有 execution constraints 明确包含 `must_require_explicit_execution=true`、`must_not_execute_from_confirmation_automatically=true`、`must_not_send=true`、`must_not_create_outcome_automatically=true`。

### 实现

1. 新增 `backend/app/ui/action_decision_workspace.py`；
2. `/app` 新增显式 `Load decision context`，不会在登录或 Person 切换时自动加载/提交；
3. UI 只展示/允许选择当前 `proposed + requires_user_confirmation=true` 的 Action Plan proposal；
4. 用户可填写可选 note，并显式点击 `Confirm selected proposal` 或 `Reject selected proposal`；
5. Confirm/Reject 都只 POST 到 canonical Action Decision API，成功后重新读取 context/history；
6. UI 明确提示 Confirm 只记录用户决定，`No execution was started`；
7. TEST-141 fragment 不调用 `/execution-context`、`/executions/{decision_id}`、Outcome、send 或 Relationship mutation；
8. 继续复用 page-memory bearer token 与安全 DOM `textContent/createElement/replaceChildren`；
9. Person 切换/logout 清理旧 candidate/history，不自动产生 Decision；
10. 无 schema migration、无新业务 API、未提前实现 Action Execution / Outcome。

### 实现与修复提交

- `ece63d191897ec2e257e4a593ca92a3c434b8e72` — Action Decision workspace fragment；
- `75c45c0bbcd590d374595e7d06eedab6ed1d55a1` — 注入统一 product shell，并保持 TEST-139/140 fragment isolation；
- `4fd489cf61cf3ecc098d142ee366ea13765c6bc8` — 8 项 authenticated Action Decision workspace tests；
- `9ea1e71baad0b0820f93858bc97df94a12e838ff` — 修正 Action Decision POST Person/Relationship scope 错误状态映射。

首轮临时 GitHub Actions run `35371603903` 发现真实后端问题：focused tests 为 7 passed / 1 failed。foreign Person 的 GET 正确返回 404，但 POST 返回 409。原因是 route 用大小写敏感的 `"person" in detail` / `"relationship" in detail` 判断 scope error，而实际服务错误为 `"Person not found"`。没有修改或弱化测试；route 改为对 `detail.lower()` 分类，使 Person/Relationship scope error 正确返回 404，同时 unavailable proposal / invalid confirmation 等 domain conflict 继续返回 409。

修复后 GitHub Actions run `35371684170` success：
- TEST-141 focused：8 passed、1 warning in 0.78s；
- TEST-135~140 Product Workspace regression：42 passed、1 warning in 3.57s；
- Action Decision canonical + proposal gate：13 passed、1 warning in 1.15s；
- Execution separation gates：5 passed、1 warning；
- Action Plan persistence/snapshot regression：5 passed、1 warning；
- account bearer scope：7 passed、1 warning；
- 合并 targeted 集：80 passed；
- full pytest：784 passed、1 warning in 40.05s；
- warning 仍为 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 workflow 已删除，清理提交 `3e162e4019a06cbd67d6fee60f9329d2c65edcb1`。

服务器最终验收于 2026-09-19 完成：branch `test-141-action-decision-workspace`，HEAD `49275dab6f83620159fc2fba6ef4fda30a0088ad`，targeted 80 passed in 15.74s，full 784 passed in 138.02s，`git diff --check` 与 `git status --short` 无输出。TEST-141 VERIFIED。

## 下一阶段候选

TEST-142 — Action Execution Workspace。

TEST-141 已服务器 VERIFIED，可进入 TEST-142。预期只复用现有 execution context/create API：显式加载 execution context，只允许选择 `execution_ready` 的 confirmed Action Decision，并通过单独显式动作记录 execution。不得自动发送消息、自动创建 Outcome 或修改 Relationship；Outcome 继续保持后续独立阶段。

## 架构与持续禁止事项

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed 且等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 relationship 或伪造 Outcome。
- Action Execution 必须来自独立显式 execution 动作；confirmed decision 本身不得触发执行。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle。
- 所有数据必须 user_id 隔离；Person / Relationship / Conversation 不得跨 scope 混用。
- 不修改历史 migration；新增 schema 必须使用新 migration。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~141 verification tag 已创建。
