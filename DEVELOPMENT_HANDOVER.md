# AI Love Strategist Development Handover

更新时间：2026-09-19
当前阶段：TEST-139 — Strategy & Recommendation Workspace — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-139-strategy-recommendation-workspace
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

- TEST-008 ~ TEST-138：按既有交接记录 VERIFIED。
- TEST-134 VERIFIED：platform-neutral release runbook / rollback safety contract。
- TEST-135 VERIFIED：authenticated single-page product shell。
- TEST-136 VERIFIED：authenticated Person / Relationship / Conversation Workspace。
- TEST-137 VERIFIED：Conversation Content Workspace，Messages + Text Import 产品化接入。
- TEST-138 VERIFIED：Relationship Evidence / Timeline Workspace。
- TEST-139 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING：Strategy & Recommendation Workspace。

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

TEST-138 服务器最终验收：branch `test-138-relationship-evidence-timeline-workspace`，HEAD `483d1f01d24de5c3ec53e96c62b26c46fac44713`，targeted 48 passed，full 761 passed，`git diff --check` 与 `git status --short` 无输出。

## TEST-139 — Strategy & Recommendation Workspace — GITHUB SELF-TEST PASSED

目标：从 canonical evidence 输入工作区进入 AI 决策输出产品化，只复用已经存在的 Strategy / Recommendation context，不新建第二套策略或建议逻辑。

既有 contract：
- `GET /api/v1/conversations/{conversation_id}/strategy/context`：AnalysisContext → StructuredAnalysis → StrategyDecisionContext；保留 `must_not_auto_select`、`requires_explicit_decision` 等约束。
- `GET /api/v1/conversations/{conversation_id}/recommendation/context`：StructuredAnalysis → StrategyRecommendationCandidate → RecommendationProducer → Recommendation；Recommendation 必须携带 evidence source/provenance，并保留 `must_not_auto_select / must_not_auto_execute`。
- 两条 route 均先通过 canonical AnalysisContext 解析当前 authenticated user + Conversation；foreign Conversation 在进入 LLM 之前返回 404。

实现：
1. 新增 `backend/app/ui/strategy_recommendation_workspace.py`；
2. `backend/app/ui/routes.py` 将该 fragment 注入统一 `/app`，继续复用原页面内存 bearer token 与 selected Conversation；
3. Strategy UI 显示 structured-analysis summary、current state、selection status、strategy candidates 及 strategy constraints；
4. Recommendation UI 显示 recommendation、`evidence_source_ids`、action/reply/priority/time_horizon/provenance 与 recommendation constraints；
5. Conversation 选择变化只清空旧结果，不自动请求 Strategy/Recommendation；用户必须显式点击 `Load strategy` / `Load recommendations`，避免无意触发 LLM/provider/API 消耗；
6. TEST-139 fragment 只发 GET，不提供 POST/PATCH/DELETE，不提供 auto-select、execute、send 或 Action Plan 按钮；
7. server data 继续使用 `textContent/createElement/replaceChildren` 安全渲染；
8. logout/person/conversation change 清理旧 Strategy/Recommendation 结果；
9. 无 schema migration、无新业务 API、无 Action Plan / Decision / Execution / Outcome 提前实现。

实现/测试提交：
- `807dc42e739f287665fb1ddda46043a62b79def0` — Strategy & Recommendation workspace fragment；
- `a2e3616cf61f0151254d5149382e967e9ed0e09d` — 注入统一 product shell；
- `e04e6d2dc176da0ebe25867a8e34d8b942c31964` — 初始 TEST-139 contract/bearer tests；
- `497ca1473664d586154eb32fb765751c187c4841` — 修正测试 bearer user_id 来源，改为从 authenticated Person response 获取 canonical `user_id`。

GitHub Actions run `35369269897` success：
- TEST-139：7 passed、1 warning in 0.62s；
- TEST-135~138 Product Workspace regression：27 passed、1 warning；
- Strategy / Recommendation canonical regression：31 passed、1 warning；
- account bearer scope regression：7 passed、1 warning；
- full pytest：768 passed、1 warning in 38.57s；
- warning 仍为 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 workflow 已删除，清理提交 `5b4756afe28460b37d1bb44e2cd0488478360963`。

当前等待服务器最终验收 TEST-139；未声称 TEST-139 VERIFIED。

## 下一阶段候选

TEST-139 服务器通过后，下一最小产品化增量应审计并接入现有 Recommendation → Action Plan orchestration，形成 TEST-140 — Action Plan Workspace。必须继续保持 evidence-backed、显式 user confirmation、不得自动选择 Recommendation、不得自动确认或执行 Action Plan。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~139 verification tag 已创建。
