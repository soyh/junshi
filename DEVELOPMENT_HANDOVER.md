# AI Love Strategist Development Handover

更新时间：2026-09-19
当前阶段：TEST-140 — Action Plan Workspace — VERIFIED
当前 Branch：test-140-action-plan-workspace
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

- TEST-008 ~ TEST-140：按既有交接记录 VERIFIED。
- TEST-134 VERIFIED：platform-neutral release runbook / rollback safety contract。
- TEST-135 VERIFIED：authenticated single-page product shell。
- TEST-136 VERIFIED：authenticated Person / Relationship / Conversation Workspace。
- TEST-137 VERIFIED：Conversation Content Workspace，Messages + Text Import 产品化接入。
- TEST-138 VERIFIED：Relationship Evidence / Timeline Workspace。
- TEST-139 VERIFIED：Strategy & Recommendation Workspace。
- TEST-140 VERIFIED：Action Plan Workspace。

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

### Contract 审计

现有系统有两类 Action Plan context，必须区分：

1. `GET /api/v1/conversations/{conversation_id}/action-plan/context`
   - 运行现有 Analysis → Recommendation → Action Plan orchestration；
   - 当存在合格 Recommendation 时执行 `build_action_plan()`；
   - 并调用 `persist_action_plan()` 写入 `action_plan_snapshots`；
   - 因此虽为 GET，但不是纯 read-only，且可能调用 LLM/provider。

2. `GET /api/v1/persons/{person_id}/action-plan/context`
   - 读取已持久化 Action Plan context；
   - existing service 会基于当前 canonical evidence 过滤失效 snapshot；
   - 适合作为“Refresh saved plans”只读入口。

Action Plan item 继续保持：`status=proposed`、`requires_user_confirmation=true`、evidence-backed。Action Decision 与 Execution 是后续独立边界，TEST-140 不调用。

### 实现

1. 新增 `backend/app/ui/action_plan_workspace.py`；
2. `/app` 新增两个明确动作：
   - `Generate & save action plan`：仅在用户显式点击时调用 Conversation-level orchestration；
   - `Refresh saved plans`：读取 Person-level persisted Action Plan context；
3. 登录、Person/Conversation 切换、Strategy/Recommendation 加载均不会自动生成 Action Plan；切换只清空旧 UI；
4. 展示 action、recommendation_id、status、`requires_user_confirmation`、evidence IDs、priority、time horizon 与 action constraints；
5. 生成结果明确提示仍需用户确认，未创建 Action Decision、未执行；
6. TEST-140 fragment 不发 POST/PATCH/DELETE，不调用 `/decisions` 或 `/execution`；
7. 继续复用 page-memory bearer token 与 `textContent/createElement/replaceChildren` 安全 DOM；
8. foreign Person / Conversation 继续由 canonical authenticated scope 返回 404；
9. 无新业务 API、无 schema migration、未提前实现 Action Decision / Execution / Outcome。

### 实现与测试提交

- `ded5914596ea744fb82c51b056ccab114827630a` — Action Plan workspace fragment；
- `6df86e042adbe17fc60cdabaefc81363eb87b8bb` — 注入统一 product shell；
- `c044c13451a2be5f89eb7eb0bab35cc52f3354ba` — 8 项 authenticated Action Plan workspace tests；
- `6529104c5a670550ff8377e390e0b0f5befbeb70` — 保持 TEST-139 Strategy fragment 脚本隔离契约，未修改旧测试。

第一次临时 GitHub Actions run `35370431025`：TEST-140 自身 8 项通过，但旧 TEST-139 `test_strategy_recommendation_fragment_is_read_only` 失败。没有删除或弱化旧测试；通过调整扩展 script 注入顺序解决。

第二次 GitHub Actions run `35370519984`：success：
- TEST-140 focused：8 passed、1 warning；
- TEST-135~139 Product Workspace regression：34 passed、1 warning；
- Action Plan canonical/persistence/snapshot regression：32 passed、1 warning；
- Action Decision + Execution safety gates：18 passed、1 warning；
- account bearer scope：7 passed、1 warning；
- 合并 targeted 集：99 passed；
- full pytest：776 passed、1 warning in 40.10s；
- warning 仍为 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 workflow 已删除，清理提交 `de8e868a6ee517e688d97882ea7de7ca2b6056bf`。

服务器最终验收于 2026-09-19 完成：
- branch：`test-140-action-plan-workspace`；
- HEAD：`323eea1dab49c8e3cc96d95a936875781072a187`；
- targeted：99 passed in 17.04s；
- full pytest：776 passed in 134.61s；
- `git diff --check` 无输出；
- `git status --short` 无输出。

TEST-140 正式锁定 VERIFIED。

## 下一阶段

TEST-141 — Action Decision Workspace。

目标：只复用现有 Person-level Action Decision context/create API，让用户对当前 `proposed` 且 evidence-backed Action Plan 做明确 `confirmed / rejected` 决定。Confirm 只创建 canonical Action Decision，不得自动触发 Execution；Execution 继续保持后续独立阶段。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~140 verification tag 已创建。
