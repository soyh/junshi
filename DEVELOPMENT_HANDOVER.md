# AI Love Strategist Development Handover

更新时间：2026-09-18
当前阶段：TEST-138 — Relationship Evidence / Timeline Workspace — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-138-relationship-evidence-timeline-workspace
TEST-137 VERIFIED 服务器代码 HEAD：`da5a3b355dbdb6345809cfe0e2c28cd880e9e849`
TEST-136 VERIFIED 服务器代码 HEAD：`07d2cf6fe47f1f2ec7a0672dfb9a9120385d1066`
TEST-135 VERIFIED 服务器代码 HEAD：`a2792c0207b1d43e6ad488c6deefec9e679f460f`
TEST-133 VERIFIED 服务器代码 HEAD：`74a9c5a976be094d9dd2d51e764ab457965f83ec`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

最终产品必须让用户在统一认证入口中管理 Person / Relationship / Conversation、持续录入真实互动证据，并让分析、策略、建议、行动、结果、反馈和学习沿唯一 canonical lifecycle 闭环运行。

## 阶段状态

- TEST-008 ~ TEST-137：按既有交接记录 VERIFIED。
- TEST-134 VERIFIED：platform-neutral release runbook / rollback safety contract。
- TEST-135 VERIFIED：authenticated single-page product shell。
- TEST-136 VERIFIED：authenticated Person / Relationship / Conversation Workspace。
- TEST-137 VERIFIED：Conversation Content Workspace，Messages + Text Import 产品化接入。
- TEST-138 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING：Relationship Evidence / Timeline Workspace。

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

统一 `/app` 产品入口已经完成：register/login/logout/session、LLM Provider、Structured Analysis；opaque session token 仅存在页面内存；无 localStorage/sessionStorage/X-User-ID/DOM token input；Provider key 不回显；无 migration。

服务器最终复跑 HEAD `a2792c0207b1d43e6ad488c6deefec9e679f460f`：full 740 passed，仓库干净，TEST-135 VERIFIED。

## TEST-136 — Authenticated Core Workspace — VERIFIED

统一 `/app` 已接入 Person → Relationship → Conversation；cross-consistency 继续由 backend canonical service 校验；选择 Conversation 同步 Structured Analysis；所有操作复用 bearer `api()`；无新业务路由、无 migration。

GitHub Actions run `35364179911`：full 747 passed。服务器最终验收 HEAD `07d2cf6fe47f1f2ec7a0672dfb9a9120385d1066`：targeted 29、full 747，仓库干净。TEST-136 VERIFIED。

## TEST-137 — Conversation Content Workspace — VERIFIED

目标：把 Conversation 从容器推进为真实聊天证据工作区，只复用 Messages / Text Import canonical API。

实现：
1. Messages 读取与单条写入当前 Conversation；sender_type 沿用 `user / person / system / assistant`；
2. Text Import 保持既有“创建新 Conversation + 批量写消息”语义，不伪装成 append；
3. import 后自动选择新 Conversation；
4. 安全 DOM 渲染；复用同一 in-memory bearer token；
5. 无 migration、无新业务 API。

GitHub Actions run `35365645959`：full 754 passed。服务器最终验收 HEAD `da5a3b355dbdb6345809cfe0e2c28cd880e9e849`：targeted 81、full 754，`git diff --check` 与 `git status --short` 无输出。TEST-137 VERIFIED。

## TEST-138 — Relationship Evidence / Timeline Workspace — GITHUB SELF-TEST PASSED

目标：把 Conversation 之外的真实关系事件与 Person 级统一 evidence timeline 接入 `/app`，只复用现有 Interaction / Timeline canonical API。

关键 contract 审计：
- Interaction create/list 已由 `InteractionService` 校验 user scope、Person ownership、Relationship↔Person consistency；合法 type 固定为 `message / call / meeting / date / gift / other`。
- Person Timeline 是 read-only 聚合视图，现有 `TimelineService` 聚合 `conversation + message + interaction`，按 canonical occurred_at 顺序提供 pagination/source metadata；不创建第二套事件数据。

实现：
1. 新增 `backend/app/ui/relationship_evidence_workspace.py` fragment；
2. `backend/app/ui/routes.py` 将 TEST-137 Conversation Content 与 TEST-138 Relationship Evidence fragment 共同注入统一 `/app`，继续运行在原单页 bearer/session IIFE 内；
3. Interaction UI 支持为当前 Person 创建事件，当前 Relationship 可选；前端不复制 relationship-person consistency；
4. 支持读取当前 Person 的 Interaction 列表；
5. Person Timeline UI 读取 `/api/v1/persons/{person_id}/timeline?limit=50&offset=0`，只读展示 Conversation / Message / Interaction 聚合结果；
6. Interaction 创建成功后刷新 Interaction + Timeline；
7. 所有 server data 使用 `textContent/createElement/replaceChildren` 安全渲染；
8. logout/person change 通过既有 resetWorkspace wrapper 清理 evidence 状态；
9. 无 schema migration、无新业务 API、无 Strategy/Recommendation/Action Plan 提前实现。

实现提交：
- `4887875423ba3fef0c46ec4ab089302a95bbccb3` — Relationship Evidence / Timeline fragment；
- `791d2f4d6bce5fe613de50a025fbb058437de75e` — 注入统一 product shell；
- `8517b8891b7b41679b4505833a8b2d95e8e795ba` — TEST-138 UI contract + real bearer scope/timeline tests。

GitHub Actions run `35367816536`：success；从 `backend/` 工作目录执行：
- TEST-138：7 passed、1 warning in 9.48s；
- TEST-135~137 Product Workspace regression：20 passed、1 warning；
- Interaction + Timeline canonical regression：14 passed、1 warning；
- account bearer scope：7 passed、1 warning；
- full pytest：761 passed、1 warning in 159.18s；
- warning 仍为 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 workflow 已删除，清理提交 `9feae612d568c6b81eaaa8eb59b8192c7fca7684`。

当前等待服务器最终验收 TEST-138。未声称 TEST-138 VERIFIED。

## 下一阶段候选

TEST-138 服务器通过后，优先审计现有 StructuredAnalysis → Strategy → Recommendation 的 API/service contract，确定 TEST-139 最小产品化增量。目标是从“证据输入完整化”进入“AI 决策输出产品化”，但 Recommendation 必须继续经过 StrategyRecommendationCandidate → RecommendationProducer，不允许 UI 绕过 canonical lifecycle。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~138 verification tag 已创建。
