# AI Love Strategist Development Handover

更新时间：2026-09-19
当前阶段：TEST-147 — Full Product Lifecycle E2E / Release Acceptance — VERIFIED
当前 Branch：`test-147-full-lifecycle-release-acceptance`
TEST-146 post-verification 基线：`dcb4bef6f4d07fddfba80b9448408a1e436a736f`
TEST-146 VERIFIED 服务器代码/文档 HEAD：`8a58d056897a2cfbb09ba284c386fe01cb9cbcf7`
TEST-145 post-verification 基线：`ff33b34fa9896259cacd4dc4543486a8afc39df1`
TEST-145 VERIFIED 服务器代码/文档 HEAD：`a6b98548d70eec000066f94c49531e462412d5bb`
TEST-144 VERIFIED 服务器代码/文档 HEAD：`0108a2b5b46878d67514f174ba98b72e73736664`
TEST-144 post-verification 基线：`aa34e958b4e1a95865870ce55e7bc36c663ef50b`
TEST-143 VERIFIED 服务器代码/文档 HEAD：`02cc3c4805f199e9ce9c521f82b0c93672a95ef2`
TEST-143 post-verification 基线：`97d82d30e85e412bdadc11698ff601736227ad5a`
TEST-142 VERIFIED 服务器代码 HEAD：`06b2fd49aedc6a5d31bfd9d56025db755cd6b10b`
TEST-142 post-verification 基线：`1532c569f4607e2256e5a72e104b4c1827cf0849`
TEST-141 VERIFIED 服务器代码 HEAD：`49275dab6f83620159fc2fba6ef4fda30a0088ad`
TEST-140 VERIFIED 服务器代码 HEAD：`323eea1dab49c8e3cc96d95a936875781072a187`
TEST-139 VERIFIED 服务器代码 HEAD：`6a9eb85104d5fd7dc35bd09bb89d35f2efba52c6`
TEST-138 VERIFIED 服务器代码 HEAD：`483d1f01d24de5c3ec53e96c62b26c46fac44713`
TEST-137 VERIFIED 服务器代码 HEAD：`da5a3b355db6345809cfe0e2c28cd880e9e849`
TEST-136 VERIFIED 服务器代码 HEAD：`07d2cf6fe47f1f2ec7a0672dfb9a9120385d1066`
TEST-135 VERIFIED 服务器代码 HEAD：`a2792c0207b1d43e6ad488c6deefec9e679f460f`

本文件是唯一 canonical handover。`docs/DEVELOPMENT_HANDOVER.md` 已删除，不再维护镜像副本。

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

最终产品必须让用户在统一认证入口中管理 Person / Relationship / Conversation、持续录入真实互动证据，并让分析、策略、建议、行动、结果、反馈和学习沿唯一 canonical lifecycle 闭环运行。

## 阶段状态

- TEST-008 ~ TEST-147：按既有交接记录 VERIFIED。
- TEST-147：GitHub self-test、服务器完整回归、真实 managed backup、production release preflight、liveness/readiness 均已通过；正式 VERIFIED。
- TEST-134 VERIFIED：platform-neutral release runbook / rollback safety contract。
- TEST-135 VERIFIED：authenticated single-page product shell。
- TEST-136 VERIFIED：authenticated Person / Relationship / Conversation Workspace。
- TEST-137 VERIFIED：Conversation Content Workspace。
- TEST-138 VERIFIED：Relationship Evidence / Timeline Workspace。
- TEST-139 VERIFIED：Strategy & Recommendation Workspace。
- TEST-140 VERIFIED：Action Plan Workspace。
- TEST-141 VERIFIED：Action Decision Workspace。
- TEST-142 VERIFIED：Action Execution Workspace。
- TEST-143 VERIFIED：Outcome Workspace。
- TEST-144 VERIFIED：Feedback Workspace。
- TEST-145 VERIFIED：Learning Workspace。
- TEST-146 VERIFIED：Re-analysis Workspace。

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
- TEST-131：HTTP liveness 与 runtime readiness 分离。
- TEST-132：本机 loopback-only runtime probe CLI。
- TEST-133：平台无关 supervisor lifecycle contract。
- TEST-134：平台无关 release runbook，明确 backup/preflight/stop/switch/start/probe/rollback 顺序和数据库回滚安全门槛。

## TEST-135 ~ TEST-138 — VERIFIED 产品化基线

- TEST-135：统一 `/app`，完成 account/session、LLM Provider 与 Structured Analysis；token 仅在页面内存。
- TEST-136：Person → Relationship → Conversation Workspace；后端负责 canonical scope/cross-consistency。
- TEST-137：Messages + Text Import；Text Import 保持创建新 Conversation 语义；server verified targeted 81 / full 754。
- TEST-138：Interaction + Person Timeline；Timeline 只读聚合 Conversation + Message + Interaction；server verified targeted 48 / full 761。

## TEST-139 — Strategy & Recommendation Workspace — VERIFIED

Strategy / Recommendation canonical context 已接入统一 `/app`。Conversation 切换不自动调用 LLM；用户显式加载；Recommendation 保留 evidence provenance、`must_not_auto_select` 与 `must_not_auto_execute`。

GitHub Actions run `35369269897`：full 768。服务器 HEAD `6a9eb85104d5fd7dc35bd09bb89d35f2efba52c6`：targeted 72、full 768，repository clean。TEST-139 VERIFIED。

## TEST-140 — Action Plan Workspace — VERIFIED

Conversation-level Action Plan generation/persistence 与 Person-level persisted read 保持分离。只有显式 `Generate & save action plan` 才会触发可能调用 LLM/provider 的 orchestration；Action Plan 保持 `status=proposed`、`requires_user_confirmation=true`，不自动创建 Decision 或执行。

GitHub Actions run `35370519984`：targeted 99 / full 776。服务器 HEAD `323eea1dab49c8e3cc96d95a936875781072a187`：targeted 99、full 776，repository clean。TEST-140 VERIFIED。

## TEST-141 — Action Decision Workspace — VERIFIED

Canonical API：
- `GET /api/v1/persons/{person_id}/action-plan/decisions/context`
- `POST /api/v1/persons/{person_id}/action-plan/decisions`

Decision 只允许 `confirmed | rejected`；confirmed 必须引用当前 `proposed` 且 `requires_user_confirmation=true` 的 recommendation。Action Decision 只记录显式用户决定，不启动 Execution。

GitHub Actions run `35371684170`：combined targeted 80 / full 784。服务器 HEAD `49275dab6f83620159fc2fba6ef4fda30a0088ad`：targeted 80、full 784，repository clean。TEST-141 VERIFIED。

## TEST-142 — Action Execution Workspace — VERIFIED

Canonical API：
- `GET /api/v1/persons/{person_id}/action-plan/execution-context`
- `POST /api/v1/persons/{person_id}/action-plan/executions/{decision_id}`

只有 confirmed、未 execution、未 Outcome 的 decision 才是 `execution_ready`。Execution 必须来自独立显式动作；服务端校验 confirmed、scope、no existing Outcome 与 no duplicate Execution。Execution 不发送消息、不创建 Outcome、不修改 Relationship。

GitHub Actions run `35375105715`：combined targeted 116 / full 792。服务器实际测试代码 HEAD `06b2fd49aedc6a5d31bfd9d56025db755cd6b10b`：targeted 116、full 792。最终 repository clean。正式验证记录提交为 `1532c569f4607e2256e5a72e104b4c1827cf0849`。TEST-142 VERIFIED。

## TEST-143 — Outcome Workspace — VERIFIED

Canonical API：
- `GET /api/v1/persons/{person_id}/action-plan/outcomes`
- `POST /api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}`

Outcome 只允许 `completed | skipped | failed`；decision 必须属于当前 user/person、为 confirmed、且已有 Action Execution。同一 decision 只能一个 Outcome。Outcome repository 只写 `action_outcomes`，不会自动创建 Feedback、Learning、Re-analysis，不发送消息，不修改 Relationship。

UI 只有显式 `Load outcome context` 与 `Record selected outcome`；仅 `decision=confirmed && execution_status=executed` 作为候选；无自动 Outcome。

GitHub Actions run `35376407255` / job `105702003793`：focused 8、Product regression 58、Outcome + Execution gates 22、Feedback/Learning/Re-analysis separation 17、auth 7、combined targeted 112、full 800。

2026-09-19 服务器最终验收：branch `test-143-outcome-workspace`，HEAD `02cc3c4805f199e9ce9c521f82b0c93672a95ef2`；targeted 112 passed in 25.49s；full 800 passed in 140.96s；`git diff --check`、`git status --short` 无输出；唯一 handover 存在且 duplicate handover 不存在。正式验证记录提交为 `97d82d30e85e412bdadc11698ff601736227ad5a`。TEST-143 VERIFIED。

## TEST-144 — Feedback Workspace — VERIFIED

### Canonical contract 审计

现有 Feedback 不是独立可写业务实体，而是 Action Decision + optional Outcome 的确定性、source-backed read model。TEST-144 没有新增 Feedback POST、数据库表或第二套业务逻辑。

现有 canonical read endpoints：
- `GET /api/v1/persons/{person_id}/action-plan/feedback`
- `GET /api/v1/persons/{person_id}/action-plan/feedback/context`
- `GET /api/v1/persons/{person_id}/action-plan/feedback/summary`
- `GET /api/v1/persons/{person_id}/action-plan/feedback/trend`
- `GET /api/v1/persons/{person_id}/action-plan/feedback/signals`
- 现有 `/learning-context` 明确属于后续 Learning bridge；TEST-144 UI 不调用它。

Repository 只 LEFT JOIN `action_decisions` 与 `action_outcomes` 并按当前 `user_id/person_id` 读取，不写数据。Feedback synthesis：
- 有 Outcome：`feedback_status=outcome_observed`，保留原始 `completed | skipped | failed`；
- 无 Outcome：`feedback_status=outcome_unknown`、`outcome_signal=unknown`；
- unknowns 保留 `action_effect`、`relationship_impact`；
- 不把 missing Outcome 推断成成功/失败；
- Summary 只计数 confirmed/rejected、observed/unknown 及 outcome categories；
- Trend 使用确定性排序，保留 Decision/Outcome source identity；
- Signals 只按 `recommendation_id` 聚合，不推断 recommendation quality；
- 所有 views 均保持 read-only、Person/user scope isolation、no Relationship change、no auto execution。

### 产品实现

1. 新增 `backend/app/ui/action_feedback_workspace.py`；
2. `/app` HTML 顺序扩展为 Action Plan → Action Decision → Action Execution → Outcome → Feedback；
3. TEST-144 script 放在 TEST-143 Outcome script 之前，保持 TEST-139~143 fragment isolation；
4. 用户必须显式点击 `Load feedback`；Person 切换只 reset，不自动加载；
5. 一次显式加载并行读取 canonical `/context`、`/summary`、`/trend`、`/signals`；
6. Decision/Outcome Feedback 显示 decision、recommendation identity、Outcome、feedback_status、unknowns；
7. Summary 显示 decisions、observed/unknown Outcome 与 completed/skipped/failed counts；
8. Trend 显示 deterministic event/source-backed observations；
9. Signals 显示按 recommendation identity 聚合的计数，不展示 quality/success 推断；
10. UI 不调用 `/learning-context`，不调用 Learning synthesis 或 Re-analysis；
11. 无 POST/PATCH/DELETE；Feedback Workspace 完全只读；
12. 继续复用 page-memory bearer token、安全 DOM `textContent/createElement/replaceChildren`；无 localStorage/sessionStorage/innerHTML/X-User-ID；
13. Outcome 完成不会自动加载 Feedback；Feedback 不发送消息、不修改 Relationship、不启动 Execution、Learning 或 Re-analysis；
14. 无新业务 API、无 schema migration。

### TEST-144 tests

新增 `backend/tests/test_authenticated_action_feedback_workspace.py`，8 项覆盖：
- `/app` controls；
- canonical read-only endpoint 使用；
- `/learning-context` 与 write methods 不进入 Feedback fragment；
- 显式 load / Person reset / Outcome separation；
- unknown/source/non-inference 与 safe DOM/page-memory token；
- bearer identity 对四个 read views 的真实传递；
- canonical Decision + Execution + Outcome 后的 Feedback/summary/trend/signals 一致性；
- missing Outcome 保持 unknown；
- authenticated user scope isolation。

首轮 CI run `35377443578`：业务逻辑 7/8 已通过，唯一失败是测试使用 `assert "re-analysis" not in script.lower()`，把 UI 的说明文本 `no Learning or Re-analysis was started` 误判为调用。只修正测试为检查 `/re-analysis` endpoint 与 `load/runReanalysis` function 不存在；没有修改业务代码、没有删除或弱化架构边界。

修正后 GitHub Actions run `35377552725`，job `105705740367`，测试 HEAD `222e8a1d704e5934e90b1c58a2bf4714571e8e29`，全部 success：
- TEST-144 focused：8 passed、1 warning in 5.79s；
- TEST-135~143 Product Workspace regression：66 passed、1 warning in 21.79s；
- Feedback canonical read model：33 passed、1 warning in 10.44s；
- Learning / Re-analysis separation：15 passed、1 warning in 4.02s；
- Outcome / auth regression：19 passed、1 warning in 4.88s；
- combined targeted：141 passed、1 warning in 45.34s；
- full pytest：808 passed、1 warning in 126.56s。

唯一 pytest warning 为 Starlette TestClient 对 `anyio.abc.BlockingPortal` alias 的 deprecation；GitHub runner 的 Node20→Node24 action warning 非测试失败。临时 TEST-144 workflow 已在成功后删除，cleanup commit `3baf1d72582666b72060ff59df8de72f7f8f2680`。

### TEST-144 实现提交

- `e3421971e2d42cc56fabc0493cf672b0c628a47b` — Feedback workspace fragment；
- `730850c8e74996609349aa5973885715394bcb42` — 注入统一 `/app`；
- `97aa3516f0d75f5a317e84dab198d159fc5bfaf8` — 8 项 authenticated Feedback workspace tests；
- `49820534f25301b39647c611f9fd314f130def5a` — 临时 TEST-144 validation workflow；
- `222e8a1d704e5934e90b1c58a2bf4714571e8e29` — 收窄 Re-analysis isolation 测试断言；
- `3baf1d72582666b72060ff59df8de72f7f8f2680` — 删除临时 workflow。

### 服务器最终验收

2026-09-19 最终验收通过：
- branch：`test-144-feedback-workspace`；
- HEAD：`0108a2b5b46878d67514f174ba98b72e73736664`；
- 初始 `git status --short` 无输出；
- targeted：141 passed in 33.23s；
- full：808 passed in 140.97s；
- `git diff --check` 无输出；
- 最终 `git status --short` 无输出；
- `DEVELOPMENT_HANDOVER.md` 存在；
- `docs/DEVELOPMENT_HANDOVER.md` 不存在；
- `.github/workflows/test-144-validation.yml` 不存在。

TEST-144 VERIFIED。正式 post-verification 文档提交：`aa34e958b4e1a95865870ce55e7bc36c663ef50b`。

## TEST-145 — Learning Workspace — VERIFIED

### Canonical contract 审计

Learning 不是从 Feedback 自动写入数据库。现有 canonical lifecycle 已明确分层：

`Observed Outcome → Feedback learning context → Learning input → Learning candidate → Memory candidate → Memory synthesis / learning provenance → explicit persist → persisted memory`

本阶段直接复用现有服务与 API，没有新增第二套 Learning 业务逻辑：

- `GET /api/v1/persons/{person_id}/action-plan/feedback/learning-inputs`：只把 `feedback_status=outcome_observed` 的 Feedback 转成 deterministic、source-backed learning input；
- `GET /api/v1/persons/{person_id}/action-plan/feedback/learning-synthesis`：生成 `status=proposed` 的 learning candidates；
- `GET /api/v1/persons/{person_id}/memory-updates/context`：生成 proposed memory candidates；
- `GET /api/v1/persons/{person_id}/memory-updates/synthesis`：生成 proposed memory updates；
- `GET /api/v1/persons/{person_id}/memory-updates/learning-synthesis`：为 memory proposal 增加 source-backed learning provenance；
- `POST /api/v1/persons/{person_id}/memory-updates/{candidate_id}/persist`：唯一显式 memory persistence gate。

核心边界：
- 没有 observed Outcome 时不会产生 Learning proposal；
- learning/memory proposal 都是 deterministic、source-backed、`status=proposed`；
- unknowns 保留 long-term relationship impact / future behavior 等未知项；
- 不推断 recommendation quality、success 或 Relationship impact；
- proposal 生成不调用 LLM、不写 memory、不改变 Relationship、不执行 action；
- memory persist 必须来自用户单独显式 POST；
- persist 按 `source_candidate_id` 幂等，同 candidate 重复 POST 返回同一 persisted record，不重复插入；
- foreign user/person 无权 persist；
- persist 只写既有 `memory_updates`，不会自动调用 Re-analysis、Learning Strategy、Structured Analysis、发送消息或修改 Relationship。

当前 canonical API 没有 persisted-memory history GET。TEST-145 没有为方便 UI 擅自新增读取 API；persist 后只展示该次服务端返回，重新载入仍读取 canonical proposals。重复 persist 由服务端幂等性兜底。

### 产品实现

1. 新增 `backend/app/ui/action_learning_workspace.py`；
2. `/app` HTML 顺序扩展为 Action Plan → Action Decision → Action Execution → Outcome → Feedback → Learning；
3. TEST-145 script 放在 TEST-144 Feedback script 之前，因此 TEST-139~144 既有 fragment isolation 保持不变；
4. 用户必须显式点击 `Load learning` 才读取 `/memory-updates/learning-synthesis`；
5. Person 切换只 reset Learning Workspace，不自动 load、不自动 persist；
6. Learning proposal 展示 `source_candidate_id`、Decision/Outcome provenance、recommendation identity、observed outcome counts 与 unknowns；
7. 用户必须选择一个 proposal，再单独点击 `Persist selected learning memory`；
8. persist 只 POST canonical `/memory-updates/{candidate_id}/persist`，没有自定义 payload；
9. persist 后只显示服务器返回的 persisted memory record；不自动刷新/调用 Re-analysis、Learning Strategy 或 Structured Analysis；
10. 页面明确提示没有启动 Re-analysis、strategy application、LLM、message send 或 Relationship change；
11. 继续复用 page-memory bearer token 与安全 DOM `textContent/createElement/replaceChildren`；无 localStorage/sessionStorage/innerHTML/X-User-ID；
12. 无新业务 API、无 schema migration、未提前实现 Re-analysis Workspace。

### TEST-145 focused tests

新增 `backend/tests/test_authenticated_action_learning_workspace.py`，8 项覆盖：
- `/app` Learning controls；
- 只使用 canonical learning-synthesis GET 与 explicit persist POST；
- 不调用 learning-strategy / analysis / structured-analysis；
- 显式 load + 显式 persist，Person change 只 reset；
- Feedback Workspace 不会自动 load/persist Learning；
- provenance、unknowns、page-memory bearer 与 safe DOM；
- bearer identity 对 Learning GET 与 persist POST 的真实传递；
- canonical observed-Outcome gate、candidate-level idempotency、数据库单行写入；
- authenticated user scope isolation 与 Relationship non-mutation。

### GitHub Actions 验证

临时 workflow：`.github/workflows/test-145-validation.yml`；验证成功后已删除。

GitHub Actions run `35420818483`，job `105838048027`，测试 HEAD `0ab990889e96232cf757bb0e89b7640c008c256d`，整体 success：
- TEST-145 focused：8 passed、1 warning in 0.67s；
- TEST-135~144 Product Workspace regression：74 passed、1 warning in 6.72s；
- canonical Learning / Memory lifecycle：61 passed、1 warning in 4.32s；
- Re-analysis / Strategy separation regression：13 passed、1 warning in 0.99s；
- Feedback / Outcome / auth regression：52 passed、1 warning in 3.36s；
- combined targeted：208 passed、1 warning in 14.06s；
- full pytest：816 passed、1 warning in 40.53s。

唯一 pytest warning 仍为 Starlette TestClient 对 `anyio.abc.BlockingPortal` alias 的 deprecation；GitHub runner Node20→Node24 action warning 非测试失败。

### TEST-145 实现提交

- `0228ac59672c1f6fe1f11aba827fb6f52a747d7e` — Learning workspace fragment；
- `a25217c97f4a4f80d8a044c720f18c68cac3c2a9` — 注入统一 `/app` 并保持旧 fragment isolation；
- `47bdca379311ec01686a9a7b6fa8ed4fb4b3a8bd` — 8 项 authenticated Learning workspace tests；
- `0ab990889e96232cf757bb0e89b7640c008c256d` — 临时 TEST-145 validation workflow / GitHub tested HEAD；
- `9fe55417d44a96a03f5ec95f47a44fc9b29c3ef3` — GitHub success 后删除临时 workflow。

### 服务器最终验收

2026-09-19 最终验收通过：
- branch：`test-145-learning-workspace`；
- HEAD：`a6b98548d70eec000066f94c49531e462412d5bb`；
- 初始 `git status --short` 无输出；
- targeted：208 passed in 50.45s；
- full：816 passed in 145.24s；
- `git diff --check` 无输出；
- 最终 `git status --short` 无输出；
- `DEVELOPMENT_HANDOVER.md` 存在；
- `docs/DEVELOPMENT_HANDOVER.md` 不存在；
- `.github/workflows/test-145-validation.yml` 不存在。

TEST-145 VERIFIED。正式 post-verification 文档提交：`ff33b34fa9896259cacd4dc4543486a8afc39df1`。

## TEST-146 — Re-analysis Workspace — VERIFIED

### Canonical contract 审计

TEST-146 没有新增 `/re-analysis` backend API，也没有修改 Learning / Memory contract。现有 canonical Re-analysis 链路已经存在：

`AnalysisContext(with Learning Strategy) → AnalysisLLMService → StructuredAnalysis → StrategyRecommendationCandidate → RecommendationProducer → Recommendation`

关键边界：
- `GET /api/v1/conversations/{conversation_id}/analysis/context` 是 deterministic、source-backed、read-only preflight；它聚合当前 Conversation / Person 的 canonical evidence 与 Learning Strategy，不调用 LLM；
- Learning Strategy 继续消费 Action Feedback learning、Memory Learning synthesis 与 Strategy Decision learning，并明确 `must_not_call_llm=true`、`must_preserve_unknowns=true`、`must_not_infer_success=true`；
- `GET /api/v1/conversations/{conversation_id}/recommendation/context` 是现有显式 fresh-analysis + fresh-recommendation HTTP 入口；它在用户显式调用时通过当前用户配置的 provider 运行 Analysis LLM，再走 StrategyRecommendationCandidate → RecommendationProducer；
- Re-analysis 结果是 derived decision support，不是 canonical truth；
- Recommendation constraints 继续保留 evidence provenance、`must_not_auto_select`、`must_not_auto_execute`；
- Outcome / Feedback / Learning load / memory persist 均不会自动调用 Re-analysis；
- 当前 canonical closure 直接从 source-backed Learning Strategy 进入 AnalysisContext，因此 persisted memory 不是 Re-analysis 的前置 gate。TEST-146 没有擅自新增“必须先 persist 才能 re-analyze”的前端伪规则；
- missing Outcome 在 Learning Strategy 中继续保持 `outcome_unknown`，不会伪装成 observed success；
- Re-analysis 不自动创建 Action Plan / Decision / Execution / Outcome，不发送消息、不修改 Relationship。

### 产品实现

1. 新增 `backend/app/ui/action_reanalysis_workspace.py`；
2. `/app` HTML 顺序扩展为 Outcome → Feedback → Learning → Re-analysis → Provider；
3. TEST-146 script 放在 TEST-145 Learning script 之前，保持 TEST-139~145 fragment isolation；
4. `Load re-analysis inputs` 显式读取 `/analysis/context`，只展示 deterministic AnalysisContext/Learning Strategy preflight，不调用 provider/LLM；
5. preflight 展示 Conversation/Person identity、feedback learning count、memory learning update count、strategy-decision learning count、learning_status、observed/unknown Outcome counts、unknowns 与 source counts；
6. Person / Conversation 切换只 reset，不自动 preflight、不自动 Re-analysis；
7. `Run re-analysis` 是独立显式动作，只调用现有 `/recommendation/context`；该调用才允许通过 configured provider/LLM 生成 fresh StructuredAnalysis；
8. fresh result 展示 summary、fact/inference/unknown/hypothesis counts，以及经过 StrategyRecommendationCandidate → RecommendationProducer 的 Recommendation、evidence_source_ids 与 provenance；
9. UI 明确 fresh result 不自动 select、plan、execute、send 或 apply Relationship；
10. Learning fragment 不调用 Re-analysis；memory persist 完成也不会自动 Re-analysis；
11. 继续复用 page-memory bearer token、安全 DOM `textContent/createElement/replaceChildren`；无 localStorage/sessionStorage/innerHTML/X-User-ID；
12. 无新业务 API、无 migration、无第二套 Re-analysis service。

### TEST-146 focused tests

新增 `backend/tests/test_authenticated_action_reanalysis_workspace.py`，8 项覆盖：
- `/app` Re-analysis controls 与 Learning→Re-analysis visual order；
- fragment 只使用 canonical `/analysis/context` 与 `/recommendation/context`；不新增 `/re-analysis` endpoint、不使用 write methods；
- preflight 与 provider/LLM run 是两个独立显式动作；Conversation/Person 切换只 reset；
- Learning Workspace 不触发 Re-analysis；
- unknown Outcome、source counts、derived result、safe DOM、page-memory bearer；
- real bearer identity 流入 deterministic AnalysisContext preflight；
- real bearer identity 流入 explicit recommendation/re-analysis run；
- canonical Decision + Execution + Outcome + Message → Learning Strategy → provider → fresh StructuredAnalysis → evidence-backed Recommendation 闭环，并验证 Relationship 不变；
- confirmed Decision 缺少 Outcome 时保持 `outcome_unknown` / observed=0 / unknown=1，且 foreign user scope 返回 404。

### GitHub Actions 验证

临时 workflow：`.github/workflows/test-146-validation.yml`；run 成功后已删除。

GitHub Actions run `35421606290`，job `105840236242`，测试 HEAD `c15100158dd7c4668804126c8997da6fd66a8ed7`，整体 success：
- TEST-146 focused：8 passed、1 warning in 0.51s；
- TEST-135~145 Product Workspace regression：82 passed、1 warning in 6.12s；
- canonical Outcome → Learning → Re-analysis closure：25 passed、1 warning in 0.97s；
- Learning / unknown-preservation regression：46 passed、1 warning in 3.15s；
- Provider / route boundary regression：22 passed、1 warning in 0.95s；
- combined targeted：183 passed、1 warning in 10.90s；
- full pytest：824 passed、1 warning in 40.60s。

唯一 pytest warning 仍为 Starlette TestClient 对 `anyio.abc.BlockingPortal` alias 的 deprecation；GitHub runner Node20→Node24 action warning 非测试失败。

### TEST-146 实现提交

- `224096719536777a364c8cd22c7ad8f6846ef2d7` — Re-analysis workspace fragment；
- `afcd4164c236061153ef192a2a5a612b925c23bf` — 注入统一 `/app` 并保持旧 fragment isolation；
- `cfea693ffc0b7e83aab1f48839375918538cd902` — 修正 UI 对 unknown Outcome 的展示语义；
- `f8a98ba15ab79d4bb10452a267653878d64f1a13` — 8 项 authenticated Re-analysis workspace tests；
- `c15100158dd7c4668804126c8997da6fd66a8ed7` — 临时 TEST-146 validation workflow / GitHub tested HEAD；
- `3db4638e078a4aa083f0cff0537e9e6977357bc9` — GitHub success 后删除临时 workflow。

### 服务器最终验收

2026-09-19 最终验收通过：
- branch：`test-146-reanalysis-workspace`；
- HEAD：`8a58d056897a2cfbb09ba284c386fe01cb9cbcf7`；
- 初始 `git status --short` 无输出；
- combined targeted：183 passed in 39.14s；
- full：824 passed in 146.48s；
- `git diff --check` 无输出；
- 最终 `git status --short` 无输出；
- `DEVELOPMENT_HANDOVER.md` 存在；
- `docs/DEVELOPMENT_HANDOVER.md` 不存在；
- `.github/workflows/test-146-validation.yml` 不存在。

TEST-146 VERIFIED。

## TEST-147 — Full Product Lifecycle E2E / Release Acceptance — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

### Acceptance contract 审计

TEST-147 不新增业务生命周期阶段，也不修改生产 API / service / repository / schema / migration / UI。现有 release 层已经具备完整安全契约：
- release preflight 汇总 production config、secure launcher 与 operations readiness，并 fail closed；
- managed SQLite backup 具备 integrity / manifest / SHA-256 verification；
- release runbook 固定 `online_backup → release_preflight → stop_current_process → switch_release → start_candidate_process → verify_liveness → verify_readiness`；
- release switch 是 external platform action；
- code rollback 不等于 database rollback；database restore 永不自动执行，只允许 application fully offline + verified backup 下的显式人工 restore；
- runtime probe 只允许 loopback，8899 保持 forbidden。

现有业务闭环与 release safety tests 之前是分散验证。TEST-147 的唯一新增内容是顶层 acceptance tests，把“真实认证产品闭环”和“完整迁移数据库 release readiness”放进同一阶段验收；没有为了验收复制第二套业务逻辑。

### TEST-147 acceptance tests

新增 `backend/tests/test_full_product_lifecycle_release_acceptance.py`，2 项：

1. authenticated full lifecycle E2E：
   - 真实 `/auth/register` 取得 opaque Bearer session；
   - 真实 HTTP 创建 Person → Relationship → Conversation → Message；
   - 使用 deterministic test provider 隔离外部 LLM 网络依赖，但实际经过现有 Analysis → StrategyRecommendationCandidate → RecommendationProducer → Action Plan service/repository 路径；
   - Action Plan 必须含 explicit action、evidence provenance、`status=proposed`、`requires_user_confirmation=true`；
   - 用户单独显式创建 confirmed Action Decision；
   - Execution 前记录 Outcome 必须返回 409；
   - 用户单独显式创建 Execution，再单独显式记录 `completed` Outcome；
   - canonical Feedback 读取为 `outcome_observed` / `completed`；
   - Learning synthesis 产生 `learning_provenance.status=observed_outcome` 的 memory proposal；
   - memory persist 必须是独立显式 POST，并确认数据库 `memory_updates` 只有一条对应记录；
   - persist 完成后 provider 调用次数仍保持 1，证明 persist 没有自动触发 Re-analysis；
   - 用户随后显式调用 canonical `/recommendation/context`，第二次 provider invocation 消费 observed Feedback + memory learning，产生 fresh derived StructuredAnalysis 与 evidence-backed Recommendation；
   - Recommendation 仍保持 `must_not_auto_select=true`、`must_not_auto_execute=true`；
   - 整个闭环前后 Relationship profile 不变。

2. release acceptance on fully migrated SQLite：
   - 在真实完整 migration fixture DB 上注册用户并写入业务数据；
   - 实际创建 managed online backup + manifest；
   - `check_release_preflight()` 必须同时通过 configuration / secure launcher / database / migrations / verified backup readiness；
   - `build_release_runbook()` 必须保持 backup→preflight→stop→switch→start→live→ready 的固定顺序；
   - candidate start 必须使用 `python -m app.server` 且 loopback-only；
   - live/ready verification 必须使用 `python -m app.probe ... --json`；
   - database restore 必须 `automatic_database_restore=false`、`manual_only=true`、requires application fully offline、requires verified backup。

### 首轮 CI 发现与修正

首轮 GitHub Actions run `35422338837` / job `105842190418`：release acceptance 测试 1/2 通过，full lifecycle case 在 Action Plan gate 停止，因为 test provider 的 hypothesis 只有 recommendation 文本，没有 explicit `action`。现有 `ActionPlanService` 正确拒绝把没有 explicit action 的 Recommendation 提升为 Action Plan；这是 acceptance fixture 不完整，不是生产缺陷。

只修正 test provider，使 hypothesis 显式携带 `action`；没有修改生产代码、没有弱化 gate。修正提交：`4b691aa416cbdaf3ef90448b80b077d1bc4d6a95`。

### GitHub Actions 最终验证

成功 run `35422430074`，job `105842430832`，测试 HEAD `4b691aa416cbdaf3ef90448b80b077d1bc4d6a95`：
- TEST-147 focused：2 passed、1 warning in 0.42s；
- Product Workspace regression through TEST-146：90 passed、1 warning in 6.45s；
- canonical lifecycle / safety closure：17 passed、1 warning in 1.27s；
- release operations acceptance regression：100 passed、1 warning in 1.10s；
- combined targeted：209 passed、1 warning in 8.52s；
- full pytest：826 passed、1 warning in 40.40s。

唯一 pytest warning 仍为 Starlette TestClient 对 `anyio.abc.BlockingPortal` alias 的 deprecation；GitHub runner Node20→Node24 action warning 非测试失败。

### TEST-147 提交

- `014607599e1a6187818ad8f4e0c7acc3faf4f0e8` — 新增 2 项 Full Product Lifecycle / Release Acceptance tests；
- `2f0977a184c46705b6af89a13d1e566b1dc8c0b2` — 临时 TEST-147 validation workflow；
- `4b691aa416cbdaf3ef90448b80b077d1bc4d6a95` — 仅修正 acceptance fixture 的 explicit action；
- `16060d6b953d2e3b529a5d9fce3615d7125e27f4` — GitHub success 后删除临时 validation workflow。

### 服务器最终验收

2026-09-19 已完成并通过。以下为当时的服务器验收清单，现均已满足：
- branch `test-147-full-lifecycle-release-acceptance` 与最终 handover HEAD；
- combined targeted 209；
- full 826；
- 对当前实际数据库先创建 fresh managed online backup，再运行 `python -m app.preflight --json`，必须返回 `ready=true`；
- 在当前 service 正常运行时，loopback `python -m app.probe live --json` 与 `ready --json` 必须成功；
- 不停止/切换当前进程，不执行 restore；
- `git diff --check` 与 `git status --short` 无输出；
- root `DEVELOPMENT_HANDOVER.md` 存在、duplicate handover 不存在；
- TEST-147 临时 workflows 不存在。

上述服务器验收已经全部通过，TEST-147 已正式标记 VERIFIED；详细实测证据见本文末尾正式 VERIFIED 记录。

## 下一阶段

当前不创建 TEST-148。TEST-147 已 VERIFIED，产品业务闭环与 release acceptance 基线已经完整闭合。若进入实际发布，必须在用户明确要求后执行已 VERIFIED 的 TEST-134 release runbook；若继续新增阶段，必须先审计新的真实产品/运维缺口，不得为了延长 TEST 编号重复实现既有能力。

## 架构与持续禁止事项

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed 且等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 Relationship 或伪造 Outcome。
- Action Execution 必须来自独立显式 execution 动作；confirmed decision 本身不得触发执行。
- Outcome 必须基于已存在的 Action Execution，并由用户显式记录；Execution 本身不得自动生成 Outcome。
- Feedback 是 source-backed read model；missing Outcome 必须保持 unknown，不得推断成功、relationship impact 或 recommendation quality。
- Learning proposal 必须由 observed Outcome/source-backed Feedback 派生；不得把 unknown Outcome 当成学习事实。
- Learning memory persistence 必须来自独立显式 persist；proposal/load 本身不得写 memory。
- Persisted Learning 不得自动触发 Re-analysis、Strategy application、LLM、message send 或 Relationship mutation。
- Re-analysis preflight 必须保持 deterministic/read-only/no-LLM；只有用户显式 Run re-analysis 才能进入 provider/LLM derived-analysis 路径。
- Re-analysis 不得自动选择 Recommendation、创建 Action Plan、执行、发送消息或修改 Relationship。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle，各阶段边界必须保持显式、可审计。
- 所有数据必须 user_id 隔离；Person / Relationship / Conversation 不得跨 scope 混用。
- 不修改历史 migration；新增 schema 必须使用新 migration。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~146 verification tag 已创建。

## TEST-147 — Full Product Lifecycle E2E / Release Acceptance — VERIFIED

TEST-147 是 TEST-008 ~ TEST-146 canonical lifecycle 与 TEST-122 ~ TEST-134 runtime/release contract 的最终产品验收阶段；没有新增第二套业务链路，也没有为通过验收修改 production API/service/repository/UI/schema/migration。

### GitHub acceptance

- TEST-146 post-verification 基线：`dcb4bef6f4d07fddfba80b9448408a1e436a736f`。
- TEST-147 server-validation 前代码/文档 HEAD：`4646a32260da0a9deb38ccd57810137a71f80c60`。
- 新增 acceptance test：`backend/tests/test_full_product_lifecycle_release_acceptance.py`。
- GitHub successful validation run `35422430074` / job `105842430832`：focused 2、Product Workspace regression 90、canonical lifecycle/safety closure 17、release operations acceptance 100、combined targeted 209、full 826。
- 最终从 TEST-146 baseline 到 server-validation HEAD 的有效 diff 仅为根 `DEVELOPMENT_HANDOVER.md` 与上述 acceptance test；temporary workflow/helper/trigger 已清理。

### 2026-09-19 server final acceptance

服务器目录：`/opt/ai-love-strategist`；branch `test-147-full-lifecycle-release-acceptance`；实际验证代码/文档 HEAD `4646a32260da0a9deb38ccd57810137a71f80c60`；验证前后 repository clean。

- combined targeted：`209 passed in 30.19s`。
- full regression：`826 passed in 145.31s`。
- 真实当前数据库 managed online backup 成功：`/opt/ai-love-strategist-backups/app-test147-20260919T051320Z.sqlite3`；manifest：`/opt/ai-love-strategist-backups/app-test147-20260919T051320Z.sqlite3.manifest.json`。
- operations readiness：database OK；13/13 migrations (`001` ~ `013`) 一致；managed backup OK。
- 初次 release preflight 正确 fail closed，暴露 root `.env` 仍为 development、debug=true、无 LLM encryption key；没有修改代码绕过。
- 安全配置准备确认 `user_llm_provider_configs` 中加密配置记录数为 0，`.env` 与当前 18080 进程均无旧 encryption key，因此在不存在既有密文兼容风险的前提下生成新的 Fernet key，并只写入被 gitignore 的本机 `.env`；旧 `.env` 保存为 `/opt/ai-love-strategist/.env.pre-test147-20260919T143411Z.bak`；密钥值未写入 handover / Git / 日志摘要。
- candidate production config：`APP_ENV=production`、`APP_DEBUG=false`、`HOST=127.0.0.1`、`PORT=18080`、`AUTH_BOOTSTRAP_ENABLED=false`、`LLM_CONFIG_ENCRYPTION_KEY` configured、`LOG_LEVEL=INFO`。
- 最终 release preflight：configuration OK、secure launcher OK（loopback、1 worker、no reload、no proxy trust、no Server header）、operations ready；overall `ready=true`；exit code 0。
- runtime liveness probe：HTTP 200、`ok=true`、exit code 0。
- runtime readiness probe：HTTP 200、`ok=true`、exit code 0。
- `git diff --check` 与 `git status --short` 无输出；root handover 存在；`docs/DEVELOPMENT_HANDOVER.md` 不存在；TEST-147 temporary validation/handover workflow/helper/trigger 均不存在。
- 此验收没有 stop/restart 当前服务、没有 switch release、没有 restore database、没有触碰端口 8899。production `.env` 是 release candidate 配置；实际 release execution 仍必须按 TEST-134 VERIFIED runbook 显式执行。

结论：TEST-147 VERIFIED。至此 canonical product lifecycle + runtime/release acceptance baseline 已闭合。没有自动创建 TEST-148；后续只有在发现真实新 gap 时才定义新 TEST 阶段，或在用户明确要求发布时按 TEST-134 release runbook 执行实际 release。

## 2026-09-19 Actual Release Execution — COMPLETED

在 TEST-147 VERIFIED 后，按 TEST-134 VERIFIED release runbook 实际执行生产重启发布；未创建 TEST-148。

- release baseline / HEAD：`0a0f4a931d7e82da877b4a55f933b13de5ab449a`；branch `test-147-full-lifecycle-release-acceptance`；发布前后 working tree clean。
- production candidate config 检查通过：`APP_ENV=production`、`APP_DEBUG=false`、loopback `127.0.0.1`、port `18080`、bootstrap disabled、LLM encryption key configured。
- VERIFIED runbook 顺序保持：online backup → release preflight → stop current process → switch release → start candidate process → verify liveness → verify readiness；数据库 restore 仍为 manual/offline-only。
- fresh managed online backup：`/opt/ai-love-strategist/data/backups/app-20260919T144654Z.sqlite3`；manifest：`/opt/ai-love-strategist/data/backups/app-20260919T144654Z.sqlite3.manifest.json`。
- release preflight（停止旧进程前）：overall `ready=true`、exit code 0；database OK；13/13 migrations (`001`~`013`)；fresh backup OK；secure launcher OK。
- 旧 18080 runtime：PID `534089`，cwd `/opt/ai-love-strategist`，command `python -m app.server`；确认未占用/修改 8899 后以 SIGTERM 正常停止，无需数据库 restore。
- switch release：代码已处于 VERIFIED baseline，无额外代码切换；保持 database / backups / runtime config。
- 新 production runtime：PID `551359`；cwd `/opt/ai-love-strategist`；command `/opt/ai-love-strategist/.venv/bin/python -m app.server`；监听 `127.0.0.1:18080`。
- release log：`/opt/ai-love-strategist/logs/release-20260919T144656Z.log`；PID file：`/opt/ai-love-strategist/logs/app.pid`。
- liveness：HTTP 200、`ok=true`、exit code 0。
- readiness：HTTP 200、`ok=true`、exit code 0。
- post-start preflight：overall `ready=true`、exit code 0；再次确认 production configuration、secure launcher、database、13/13 migrations 与 fresh managed backup readiness。
- `/proc/551359/environ` 未显示 APP_ENV/APP_DEBUG/HOST/PORT/LLM key 是预期现象：这些值由项目根 `.env` 通过 Settings 加载，不要求导出为父 shell 环境变量；启动后的 post-start preflight 已验证实际配置仍为 production-ready。
- 8899 observation：`0.0.0.0:8899` 由独立 Python PID `52822` 监听；本次 release 未停止、修改、复用或接管该端口/进程。
- `git diff --check` 与 `git status --short` 无输出。
- database restore：`NOT_EXECUTED`。没有自动 restore，也没有 schema/data rollback。

结论：TEST-147 VERIFIED baseline 已按 TEST-134 runbook 完成一次实际 production release execution。当前生产 runtime 为 PID `551359`、loopback `127.0.0.1:18080`，live/readiness/preflight 均通过。TEST-008 ~ TEST-147 的 canonical product lifecycle、release acceptance 与首次实际 release execution 至此闭合。后续不机械创建 TEST-148；只有发现新的真实产品/运维 gap 时才定义新阶段。
