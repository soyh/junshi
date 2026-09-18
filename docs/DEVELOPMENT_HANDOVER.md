# Development Handover

更新时间：2026-09-18
当前阶段：TEST-136 — Authenticated Core Workspace — VERIFIED
当前 Branch：test-136-authenticated-core-workspace
TEST-136 VERIFIED 服务器代码 HEAD：`07d2cf6fe47f1f2ec7a0672dfb9a9120385d1066`
TEST-135 VERIFIED 服务器代码 HEAD：`a2792c0207b1d43e6ad488c6deefec9e679f460f`
TEST-133 VERIFIED 服务器代码 HEAD：`74a9c5a976be094d9dd2d51e764ab457965f83ec`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

最终产品必须让用户在统一认证入口中管理 Person / Relationship / Conversation、持续录入真实互动证据，并让分析、策略、建议、行动、结果、反馈和学习沿唯一 canonical lifecycle 闭环运行。

## 阶段状态

- TEST-008 ~ TEST-136：按既有交接记录 VERIFIED。
- TEST-134 VERIFIED：platform-neutral release runbook / rollback safety contract。
- TEST-135 VERIFIED：authenticated single-page product shell。
- TEST-136 VERIFIED：authenticated Person / Relationship / Conversation Workspace。

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

发布顺序固定为：
`online_backup → release_preflight → stop_current_process → switch_release → start_candidate_process → verify_liveness → verify_readiness`

关键约束：online backup 与 preflight fail closed；release switch 是 external platform action；code rollback 与 database rollback 分离；数据库 restore 仅能在明确需要、应用完全离线且 backup 已验证时人工执行；不自动操作 Git/systemd/Nginx/Docker；不触碰 8899。

GitHub Actions run `35355369005`：full 734 passed、1 warning。服务器最终累计验收在 TEST-135 基线通过，TEST-134 正式 VERIFIED。

## TEST-135 — Authenticated Product Shell — VERIFIED

统一 `/app` 产品入口已经完成：
1. register/login/logout/session management；
2. LLM Provider 管理；
3. Structured Analysis；
4. opaque session token 只存在当前页面 `currentAccessToken` 内存；
5. 不使用 localStorage/sessionStorage/URL/DOM token input/X-User-ID；
6. Provider API key 不回显；
7. Structured Analysis 继续复用 `/api/v1/conversations/{id}/analysis/structured`；
8. 原 Auth/Provider UI 保留；无 schema migration。

GitHub Actions run `35356010017`：full 740 passed。cwd-dependent `.env.example` 测试缺陷由 `416dc6c3f5d1769161fb688eb4a8c7f12920e16b` 修正；server-parity run `35362679263` full 740 passed。服务器最终复跑 HEAD `a2792c0207b1d43e6ad488c6deefec9e679f460f`：full 740 passed，仓库干净，TEST-135 VERIFIED。

## TEST-136 — Authenticated Core Workspace — VERIFIED

目标：把真正核心业务 Workspace 接入统一 `/app`，覆盖 `Person → Relationship → Conversation`；只复用既有 canonical API 和 bearer session，不增加第二套业务逻辑，不提前实现 Recommendation / Action Plan / Execution / Outcome UI。

实现：
1. Person Workspace：加载、创建、选择 Person，沿用 `name / nickname / notes` schema；
2. Relationship Workspace：基于当前 Person，复用 `/api/v1/relationships`，创建沿用既有 status/stage/goal/notes contract；
3. Conversation Workspace：基于当前 Person、Relationship 可选，复用 `/api/v1/conversations?person_id=...` 与现有 create contract；
4. Conversation status 只暴露既有 `active / archived`；
5. 选择 Conversation 后自动同步到 Structured Analysis conversation target；
6. Person/Relationship cross-consistency 等规则仍由 backend canonical service 校验，前端不复制；
7. 所有操作继续通过统一 `api()` 注入 `Authorization: Bearer <in-memory token>`；
8. server data 用 `textContent/createElement/replaceChildren` 渲染，不使用 `innerHTML`；
9. logout 清空 Person / Relationship / Conversation 选择与分析 target；
10. 无新业务路由、无 schema migration、无后续 Action lifecycle UI 提前实现。

实现提交：
- `39a2dda6924a4a8c7bbbd793d84aadc30170ce87` — authenticated core workspace UI；
- `0bf54a6bc52e2cdfb7ecc8980ca6d142a7d43a47` — Workspace contract + real bearer user-isolation tests。

GitHub Actions run `35364179911` success：
- TEST-136 Workspace：7 passed；
- TEST-135 Product Shell：6 passed；
- Person / Relationship / Conversation canonical regression：9 passed；
- bearer account scope regression：7 passed；
- full pytest：747 passed、1 warning in 36.59s；
- 临时 workflow 已删除。

服务器最终验收由用户于 2026-09-18 确认结果符合预期：
- branch：`test-136-authenticated-core-workspace`；
- HEAD：`07d2cf6fe47f1f2ec7a0672dfb9a9120385d1066`；
- targeted：29 passed；
- full pytest：747 passed；
- `git diff --check` 无输出；
- `git status --short` 无输出。

TEST-136 正式锁定 VERIFIED。

## 下一阶段

TEST-137 — Conversation Content Workspace。

目标：把已创建 Conversation 从“容器”推进为“可录入真实互动证据的工作区”。优先复用 existing Messages / Text Import API，使用户在选中 Conversation 后可以读取、手工录入或导入真实聊天内容，再进入现有 Structured Analysis；不新增第二套消息模型，不绕过 canonical scope，不提前展开 Recommendation / Action Plan / Execution / Outcome UI。

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
