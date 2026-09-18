# AI Love Strategist Development Handover

更新时间：2026-09-18
当前阶段：TEST-136 — Authenticated Core Workspace — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-136-authenticated-core-workspace
TEST-135 VERIFIED 服务器代码 HEAD：`a2792c0207b1d43e6ad488c6deefec9e679f460f`
TEST-133 VERIFIED 服务器代码 HEAD：`74a9c5a976be094d9dd2d51e764ab457965f83ec`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-135：按既有交接记录 VERIFIED。
TEST-134 VERIFIED — platform-neutral release runbook / rollback safety contract。
TEST-135 VERIFIED — authenticated single-page product shell。
TEST-136 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — authenticated Person / Relationship / Conversation Workspace；GitHub full 747。

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

## TEST-134 — Release Runbook Contract — VERIFIED

目标：把 TEST-126~133 的既有能力组合成可验证的发布/回滚顺序，而不是新增第二套运行逻辑。

实现：
1. `backend/app/core/deployment.py` + 只读 CLI `python -m app.deployment --json`；CLI 只输出计划，不执行任何步骤；
2. 发布顺序固定为 `online_backup → release_preflight → stop_current_process → switch_release → start_candidate_process → verify_liveness → verify_readiness`；
3. online backup 必须在 release switch 前成功；preflight 必须在停止进程前成功；
4. release switch 是 external platform action，不自动操作 Git/systemd/Nginx/Docker；
5. stop/start/probe 复用 TEST-133/132；
6. code rollback 与 database rollback 严格分离；发布失败不会自动 restore 数据库；
7. DB restore 仅在明确需要 schema/data rollback、应用完全离线且 backup 已验证时人工执行；
8. 命令为 argv，不经 shell，不嵌入 secrets/database path；production-only、loopback-only、拒绝 8899；
9. 无 schema migration，不启动/停止真实进程。

GitHub Actions run `35355369005` success：TEST-134 12、TEST-133 11、TEST-132 11、TEST-131 9、TEST-130 10、restore 8、backup 8、production auth 8、scope 4；full 734 passed、1 warning。

服务器最终累计验收于 TEST-135 HEAD `a2792c0207b1d43e6ad488c6deefec9e679f460f` 完成：TEST-134/135 targeted 18 passed，full 740 passed，`git diff --check` 和 `git status --short` 均无输出。TEST-134 正式锁定 VERIFIED。

## TEST-135 — Authenticated Product Shell — VERIFIED

目标：解决旧 Auth UI 与 Provider UI 登录态无法安全跨页衔接的问题，让普通用户拥有统一产品入口，同时坚持 session token 只存在当前页面内存。

实现：
1. `backend/app/ui/product_shell.py` + `backend/app/ui/routes.py` 提供顶层 `/app`，隐藏于 OpenAPI；
2. `/app` 同页完成 register/login/logout/session management、LLM Provider 管理与 Structured Analysis；
3. opaque session token 只保存于 `let currentAccessToken` 页面内存，不写 `localStorage`、`sessionStorage`、URL、DOM token input 或 X-User-ID；
4. Provider 复用 `/api/v1/settings/llm` 与 `/test`，API key 不回显；
5. Structured Analysis 复用 `/api/v1/conversations/{id}/analysis/structured`；
6. 原 Auth/Provider UI 保留；无 schema migration。

GitHub Actions run `35356010017`：full 740 passed、1 warning。

服务器第一次累计验收暴露 `Path(".env.example")` cwd-dependent 测试缺陷；修复提交 `416dc6c3f5d1769161fb688eb4a8c7f12920e16b` 改为基于测试文件定位仓库根目录，不改 production code。GitHub server-parity run `35362679263`：bootstrap 6、TEST-134/135 18、full 740 passed。

服务器最终复跑于 `a2792c0207b1d43e6ad488c6deefec9e679f460f`：bootstrap 6 passed、TEST-134/135 18 passed、full 740 passed，`git diff --check`、`git status --short` 无输出。TEST-135 正式锁定 VERIFIED。

## TEST-136 — Authenticated Core Workspace — GITHUB SELF-TEST PASSED

目标：把真正的核心业务 Workspace 接入统一 `/app`，先覆盖 Person → Relationship → Conversation；只复用既有 canonical API 和 bearer session，不增加第二套业务逻辑，不提前实现 Recommendation / Action Plan / Execution / Outcome UI。

实现：
1. 在 `backend/app/ui/product_shell.py` 的 `/app` 中增加 Person Workspace：加载、创建、选择 Person；字段沿用既有 `name / nickname / notes` schema；
2. 增加 Relationship Workspace：始终基于当前选中 Person；加载既有 `/api/v1/relationships` 后仅展示当前 Person 的记录，创建直接提交 `person_id` 与既有 status/stage/goal/notes 字段；
3. 增加 Conversation Workspace：基于当前 Person，Relationship 可选；列表调用 `/api/v1/conversations?person_id=...`；创建提交现有 `person_id / relationship_id / title / status` contract；
4. Conversation status UI 只暴露既有 `active / archived`；
5. 选择 Conversation 后自动同步到既有 Structured Analysis 的 `conversation-id`，分析仍走 `/api/v1/conversations/{id}/analysis/structured`；
6. 前端不复制 Person/Relationship cross-consistency 规则；Relationship 是否属于 Person 等 canonical 校验仍由现有 backend service 决定；
7. 所有新操作继续通过现有 `api()` 注入 `Authorization: Bearer <in-memory token>`；没有 localStorage、sessionStorage、X-User-ID、DOM token input；
8. server data 通过 `textContent` / `createElement` / `replaceChildren` 渲染，不使用 `innerHTML`；
9. logout 清空 Person / Relationship / Conversation 选择以及 Structured Analysis conversation target；
10. 无新业务路由、无 schema migration、无 Recommendation/Action Plan 后续链路实现。

实现提交：
- `39a2dda6924a4a8c7bbbd793d84aadc30170ce87` — authenticated core workspace UI；
- `0bf54a6bc52e2cdfb7ecc8980ca6d142a7d43a47` — TEST-136 Workspace contract + real bearer user-isolation tests。

GitHub Actions run `35364179911`：success；从与服务器一致的 `backend/` 工作目录执行：
- TEST-136 `tests/test_authenticated_core_workspace.py`：7 passed；
- TEST-135 `tests/test_authenticated_product_shell.py`：6 passed；
- Person / Relationship / Conversation canonical regression：9 passed；
- bearer account scope regression：7 passed；
- full pytest：747 passed、1 warning in 36.59s；
- warning 仍为 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 workflow 已删除，清理提交 `8e2a50fe8f6641ebe17702ae746ff8db7f8ba752`。

当前等待服务器验收 TEST-136。服务器验收只运行 pytest / git diff / git status；不执行 deployment/backup/restore/preflight/server/probe CLI，不修改 `.env`，不触碰 8899。

## 下一阶段候选

TEST-136 服务器验收通过后，再审计并决定下一个最小产品化增量。优先候选是把 Conversation 的内容录入链路（existing Messages / Text Import API）接入 Workspace，使已创建 Conversation 可以录入真实证据；仍不一次性展开 Recommendation / Action Plan / Execution / Outcome 全链路 UI。

## 架构与持续禁止事项

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed 且等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 relationship 或伪造 Outcome。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle。
- 所有数据必须 user_id 隔离；Person / Relationship / Conversation 不得跨 scope 混用。
- 不修改历史 migration；新增 schema 必须使用新 migration。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~136 verification tag 已创建。
