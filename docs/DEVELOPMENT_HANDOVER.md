# Development Handover

更新时间：2026-09-19
当前阶段：TEST-142 — Action Execution Workspace — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-142-action-execution-workspace
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
- TEST-142：GitHub self-test passed，等待服务器最终验收，尚未标记 VERIFIED。

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

现有 canonical Action Decision API 为 `GET /api/v1/persons/{person_id}/action-plan/decisions/context` 与 `POST /api/v1/persons/{person_id}/action-plan/decisions`。decision 只允许 `confirmed | rejected`；confirmed 必须引用当前仍为 `proposed` 且 `requires_user_confirmation=true` 的 recommendation。Action Decision create 只写 decision，不会调用 Execution service。

TEST-141 UI 只在显式 `Load decision context` 后展示 proposal，并由用户显式 Confirm/Reject；Confirm 只记录用户决定，明确不会启动 execution。继续使用 page-memory bearer、安全 DOM，并保持 Person/logout reset，不自动加载或提交。

GitHub Actions 修复后 run `35371684170`：combined targeted 80 passed，full 784 passed。服务器最终验收于 2026-09-19 完成：branch `test-141-action-decision-workspace`，HEAD `49275dab6f83620159fc2fba6ef4fda30a0088ad`，targeted 80 passed in 15.74s，full 784 passed in 138.02s，`git diff --check` 与 `git status --short` 无输出。TEST-141 VERIFIED。

## TEST-142 — Action Execution Workspace — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

### Contract 审计

现有 canonical Action Execution API：
- `GET /api/v1/persons/{person_id}/action-plan/execution-context`：读取当前 Person 的 Action Decision execution status 与 execution constraints；
- `POST /api/v1/persons/{person_id}/action-plan/executions/{decision_id}`：记录单独、显式的 Action Execution；payload 仅包含可选 `executed_at` 与 `note`；
- context 对 decision 状态分类为 `execution_ready | executed | outcome_recorded | not_executable`；
- 只有 `decision=confirmed` 且未 execution、未 Outcome 的 decision 才是 `execution_ready`；
- 服务端 POST 时再次强制 confirmed、user/person/decision scope、no existing Outcome、no duplicate Execution；客户端筛选不是 authority；
- rejected decision 不可执行，重复 execution 返回 conflict，Outcome 已存在时不可再次执行；
- execution repository 只写 `action_executions`，不会发送消息、创建 Outcome 或修改 Relationship；
- constraints 明确包含 `must_require_confirmed_decision=true`、`must_require_explicit_execution=true`、`must_not_execute_rejected_decision=true`、`must_not_execute_from_confirmation_automatically=true`、`must_not_send=true`、`must_not_create_outcome_automatically=true`。

### 实现

1. 新增 `backend/app/ui/action_execution_workspace.py`；
2. `/app` 在 Action Decision 后新增 Action Execution 区域；
3. 只有用户显式点击 `Load execution context` 才 GET canonical execution context；登录、Person 切换、Action Decision Confirm 都不会自动加载或执行；
4. UI 仅把 `decision=confirmed && execution_status=execution_ready` 的记录作为可选择候选；
5. 用户可填写可选 `executed_at` 与 `note`，然后单独点击 `Record selected execution`；
6. POST 成功后只重新加载 execution context，并明确提示 `No message was sent and no Outcome was created`；
7. Person 切换/logout 只 reset Execution workspace；
8. 继续复用 page-memory bearer token 和安全 DOM `textContent/createElement/replaceChildren`，不使用 localStorage/sessionStorage/innerHTML/X-User-ID；
9. TEST-142 script 放在 TEST-141 Action Decision script 之前，HTML 仍按 Action Plan → Action Decision → Action Execution 排列，从而保持 TEST-139/140/141 fragment isolation；
10. 无新业务 API、无 schema migration、未实现 Outcome UI。

### 实现提交

- `94e519ca01ef3d38d0464b86045c8d7f2eeaf023` — 新增 Action Execution workspace fragment；
- `40d857c906ab049fa885a865562be977eb9d3401` — 注入统一 product shell 并保持旧 fragment isolation；
- `be3d16efd0b787a083e888ba07f5eaf5cbaf02b0` — 新增 8 项 authenticated Action Execution workspace tests；
- `c34e76babd2bc549bb1885520d49804d6beedae9` — 临时 TEST-142 validation workflow；
- `b0ca633507939f36d9f910ecd7387045eee60bc7` — CI 成功后删除临时 workflow。

### GitHub Actions 验证

临时 GitHub Actions run `35375105715`，job `105697834658`，测试 HEAD `c34e76babd2bc549bb1885520d49804d6beedae9`，整体 success：
- TEST-142 focused：8 passed、1 warning in 0.80s；
- TEST-135~141 Product Workspace regression：50 passed、1 warning in 5.63s；
- Execution canonical + synthesis + bridge + gate + scope：26 passed、1 warning in 1.82s；
- Action Decision regression：13 passed、1 warning in 5.02s；
- Outcome separation regression：12 passed、1 warning in 0.44s；
- account bearer scope：7 passed、1 warning in 1.10s；
- combined targeted：116 passed、1 warning in 8.97s；
- full pytest：792 passed、1 warning in 50.21s。

唯一 pytest warning 仍为 Starlette TestClient 对 `anyio.abc.BlockingPortal` alias 的 deprecation；GitHub runner 另提示 actions/checkout@v4 与 setup-python@v5 的 Node20 target 被强制 Node24，均非测试失败。临时 workflow 已删除。

服务器最终验收尚未执行，因此 TEST-142 当前不能标记 VERIFIED。

## 下一阶段候选

TEST-143 — Outcome Workspace。

只能在 TEST-142 服务器最终验收通过并标记 VERIFIED 后开始。预期只把现有 canonical Outcome create/read contract 接入统一 `/app`：只能基于已执行的 Action Decision 由用户显式记录 Outcome；不得由 Execution 自动生成，不得跳过 Execution，不得自动生成 Feedback/Learning/Re-analysis。具体范围必须先审计现有 Outcome schema、route、service、repository 与测试后再锁定。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~142 verification tag 已创建。
