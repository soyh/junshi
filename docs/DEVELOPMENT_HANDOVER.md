# Development Handover

更新时间：2026-09-16
当前阶段：TEST-093 — Outcome → Feedback → Learning → Re-analysis → Recommendation — CONTRACT LOCKED
当前 Branch：test-093-outcome-learning-reanalysis-closure

## 项目目标

本项目是长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人或回复生成器。

核心链路：

`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 ~ TEST-064：VERIFIED
TEST-065 ~ TEST-087：VERIFIED
TEST-088：VERIFIED
TEST-089：VERIFIED
TEST-090：VERIFIED
TEST-091：CONTRACT LOCKED
TEST-092：VERIFIED
TEST-093：CONTRACT LOCKED

TEST-087 已锁定 Outcome → Feedback → Learning → Re-analysis → Recommendation 闭环，未新增第二套生命周期、migration 或数据库结构。

## TEST-088 — VERIFIED

目标：真实用户工作流最小验收。

- 真实 canonical user / person / relationship / conversation / messages 进入 AnalysisContext。
- Real Qwen / DashScope StructuredAnalysis 成功返回并完成 schema validation。
- StructuredAnalysis 保留 Fact / Inference / Unknown、hypothesis / signal 与 evidence provenance。
- Action Plan Context 正确读取真实 relationship state 与 evidence。
- 无 Recommendation 时 `recommendations=[]`、`action_plan=[]` 为当前架构预期，不得为了验收强行生成 action。
- user isolation、read-only、source-backed、unknown preservation、no-auto-execution 等约束保持。
- `/persons` FK 500 已定性为未注册 `X-User-ID=test-088-real-user` 导致 SQLite 正常拒绝，不属于 FK、migration、数据库损坏或 Person 业务逻辑缺陷。
- StructuredAnalysis 历史间歇性 502 不再阻塞 TEST-088；当前真实 StructuredAnalysis 已成功通过。
- 未修改 production code、tests、migration 或数据库 schema。

## TEST-089 — VERIFIED

目标：验证现有桥接边界：

`Real AnalysisContext → Real StructuredAnalysis → StrategyDecisionContext → explicit StrategyRecommendationCandidate → RecommendationProducer → Recommendation`

验收结论：

- Real Qwen StructuredAnalysis 成功进入现有 AnalysisRecommendationService。
- StrategyRecommendationCandidate 保持显式、deterministic、evidence-backed 边界。
- candidate 具有稳定 identity、recommendation、evidence_source_ids、provenance。
- evidence_source_ids 必须存在于 canonical evidence；无证据 candidate 被拒绝。
- Recommendation 只由 RecommendationProducer 产生，并保留 candidate identity、evidence provenance。
- unknowns 保持 derived constraint/provenance，不被转换为 fact、success evidence 或 recommendation quality。
- 不自动选择、不自动确认、不自动执行、不自动发送消息、不修改 relationship。
- 重复读取保持 deterministic，无 decision / execution / outcome side effect。
- 未新增 StructuredAnalysis persistence 或第二套 Strategy / Recommendation 生命周期。

## TEST-090 — VERIFIED

目标：验证最小必要桥接：

`Real Recommendation → Evidence Validation → Action Plan Proposal`

### 锁定契约

- Action Plan 只消费显式 Recommendation，不直接消费 StructuredAnalysis / hypothesis。
- Recommendation 必须有稳定 id、非空 action、非空 evidence_source_ids。
- 所有 evidence_source_ids 必须存在于当前 canonical evidence。
- 缺少 action、缺少 evidence、invalid evidence、blank action 的 Recommendation 均不得进入 Action Plan。
- Action Plan 输出只能是 `status="proposed"`。
- `requires_user_confirmation=true` 必须保持。
- 不自动确认、不自动执行、不自动发送消息。
- 不修改 relationship。
- 不创建 Outcome，不触发 Feedback / Learning。
- 保持 user/person/conversation isolation。
- TEST-090 不负责重新验证 Action Decision / Execution / Outcome 生命周期。

### 已完成验收

- Real evidence-backed Recommendation 成功进入 Action Plan。
- Action Plan 正确保留 recommendation identity、action、evidence_source_ids、priority、time_horizon。
- negative gates 已验证：missing action / missing evidence / invalid evidence / blank action 全部 BLOCKED。
- DB side-effect check 通过；测试 probe 前后不存在 Recommendation / Action Plan 等新的 canonical persistence side effect。
- 全量 pytest 已通过 509 tests（TEST-088 后服务器验收基线）。
- working tree 保持 clean。
- 未修改 production code、tests、migration 或数据库 schema。

## TEST-091 — CONTRACT LOCKED

目标：验证现有 `Action Plan → Action Decision` 人工决策边界，不扩大到 Execution。

### Canonical Boundary

`Action Plan (proposed + requires_user_confirmation)`

`→ Explicit User Decision`

`→ Action Decision`

`→ [Execution 为下一阶段边界]`

### 锁定契约

1. 只有 `status="proposed"` 的 Action Plan 才能进入 Decision。
2. `requires_user_confirmation=True` 必须保持，不能被系统隐式移除。
3. 系统不得自动把 proposed 转换成 confirmed。
4. 必须存在显式 user decision input。
5. Decision 必须绑定原始 Recommendation / Action Plan identity。
6. Decision 必须保持 evidence provenance，不得丢失来源约束。
7. rejected / cancelled Decision 不得进入 Execution。
8. 未 confirmed 的 Decision 不得进入 Execution。
9. 系统不得伪造 user confirmation。
10. Decision 不得自行创建 Outcome。
11. Decision 不得自行触发 Feedback / Learning。
12. 不得建立第二套 Action Decision lifecycle。
13. user/person/relationship/conversation isolation 必须保持。
14. 不得自动发送消息。
15. 不得通过 Decision 自动修改 relationship。

### TEST-091 非目标

- 不重新实现 TEST-086 已锁定的 Action Decision → Execution 边界。
- 不重新实现 TEST-087 Outcome → Feedback → Learning → Re-analysis 闭环。
- 不增加第二套 Action Plan / Decision / Execution 生命周期。
- 不新增 migration / database schema。
- 不要求真实第三方消息发送。
- 不允许为了制造 demo 而绕过用户确认。

### 当前 GitHub 实现基线

- `ActionPlanService`：只提升显式、evidence-backed、带 action 的 Recommendation 为 `status="proposed"` Action Plan，并要求用户确认。
- `ActionDecisionService`：只允许 Decision 引用当前可用的 evidence-backed action plan recommendation；confirmed 必须带 recommendation_id。
- Action Decision API 提供显式 POST Decision 入口；不存在由 Action Plan 自动确认 Decision 的路径。
- TEST-091 审计发现 `strategy-decision/confirmations` 曾作为独立 ActionDecision 写入入口，且其 decisionable 语义依赖 Outcome / Learning；因此 TEST-091 未直接标记 VERIFIED，而转入 TEST-092 做 lifecycle convergence。

## TEST-092 — VERIFIED

目标：收敛 Strategy Decision 与 Action Decision，消除第二个 canonical Decision 写入生命周期，同时保留 Strategy / Learning / Re-analysis 的只读派生智能职责。

### Canonical Boundary

`Strategy / Learning / Re-analysis`

`→ read-only derived intelligence`

`→ Action Plan`

`→ Explicit User Decision`

`→ ActionDecisionService`

`→ Action Decision`

`→ Execution`

`→ Outcome`

`→ Feedback / Learning`

`→ Re-analysis`

### 已完成验收

- `StrategyDecisionConfirmationService` 已收敛为 read-only context/synthesis service，不再持有 `ActionDecisionRepository`，不再提供 `create_confirmation()`。
- 已移除 `POST /persons/{person_id}/strategy-decision/confirmations`，因此 Strategy Decision 不再拥有独立 canonical ActionDecision 写入入口。
- 新的 Action Decision 写入仍统一经过 `ActionDecisionService`，并校验当前 Action Plan 中的 evidence-backed recommendation identity。
- Strategy Decision / Learning / Re-analysis 继续保留为 read-only derived intelligence，不负责确认、执行或发送。
- `StrategyDecisionExecutionService` 继续要求 confirmed ActionDecision，并拒绝 rejected / 未确认 / 已执行 / 已产生 Outcome 的 Decision。
- Outcome / Feedback / Learning / Re-analysis 下游闭环保持不变。
- 不新增第二套 lifecycle。
- 不自动确认、不自动执行、不自动发送消息、不修改 relationship、不伪造 Outcome。
- 未修改 migration / database schema。
- TEST-092 targeted tests：36 passed。
- TEST-092 full pytest：507 passed。
- 历史 confirmation synthesis 对“已产生 Outcome 的 Decision 不再计入 explicit confirmation”语义保持不变；相关测试仅按既有语义调整 fixture，不构成 production regression。

## TEST-093 — CONTRACT LOCKED

目标：证明上一轮 canonical Action 的 Outcome / Feedback / Learning 会进入下一轮 AnalysisContext，并且下一轮 Analysis 真正消费该 Learning，再沿既有 Strategy → Recommendation canonical lifecycle 产生新的 Recommendation。

### 审计结论

TEST-092 基线的 production architecture 已存在完整可达链：

`Outcome → Feedback → Learning → AnalysisContext.learning_strategy → StructuredAnalysis → StrategyRecommendationCandidate → RecommendationProducer → Recommendation`

当前 GAP 是集成测试只能证明 Learning 出现在 AnalysisContext，不能证明下一轮 Analysis 真正消费 Learning 并使新的 StructuredAnalysis / Recommendation 对该 Learning 产生依赖。

因此 TEST-093 先锁定集成验收契约，不修改 production architecture。

### Canonical Acceptance Chain

`ActionExecution`

`→ Outcome`

`→ Feedback`

`→ Learning`

`→ Fresh AnalysisContext`

`→ Learning-aware StructuredAnalysis`

`→ Strategy`

`→ StrategyRecommendationCandidate`

`→ RecommendationProducer`

`→ Fresh Recommendation`

### 锁定契约

1. Outcome 必须对应实际 ActionExecution / confirmed ActionDecision；不得伪造 Outcome。
2. Feedback 必须消费 canonical Outcome，并保留 decision / recommendation provenance。
3. Learning 必须消费 canonical Feedback，不得绕过 Feedback 自行产生 action decision。
4. 下一次 AnalysisContext 必须重新读取当前 canonical relationship/evidence 与 Learning inputs；不得复用旧 AnalysisContext snapshot。
5. Analysis provider 必须实际读取并消费 `learning_strategy.learning_inputs.action_feedback`，不能只因为该字段存在就判定闭环成立。
6. Learning-aware StructuredAnalysis 必须能够体现本轮 Learning 被消费；测试不得使用与 Learning 无关的固定返回值作为唯一证明。
7. 新 StructuredAnalysis 必须继续保持 Fact / Inference / Unknown 分离与 evidence provenance。
8. Strategy 必须继续通过现有 Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation 链生成 Recommendation。
9. Learning 不得直接创建 ActionDecision、ActionExecution 或 Outcome。
10. 新 Recommendation 必须具有当前 evidence provenance；不得静默复用旧 Recommendation / ActionDecision。
11. 必须保持 user / person / relationship / conversation isolation。
12. 不自动选择 Recommendation、不自动确认 ActionDecision、不自动执行 Action、不自动发送消息。
13. TEST-093 不新增 migration / database schema，不修改历史 migration，不建立第二套 lifecycle。

### 当前 TEST-093 验收测试

`backend/tests/test_outcome_reanalysis_closure.py`

测试已强化为 Learning-aware contract：Provider 在返回 StructuredAnalysis 前必须读取并校验上一轮 `recommendation-previous` 的 completed feedback learning，并将该 Learning identity 实际写入新的 analysis summary / hypothesis；随后验证 Recommendation 仍由 `strategy_candidate` provenance 产生，并引用当前 message evidence。

### 非目标

- 不修改 TEST-092 已锁定的 Strategy Decision lifecycle。
- 不建立 Learning → ActionDecision / Learning → Execution bypass。
- 不新增 StructuredAnalysis canonical persistence。
- 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
- 不做真实第三方消息发送。
- 不为了测试通过修改 production lifecycle。

## 架构与安全边界

- AnalysisContext 必须 deterministic、source-backed、read-only。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Fact / Inference / Unknown 必须严格区分；inference、hypothesis、material signal 必须保留 provenance。
- Recommendation 必须经过显式 candidate contract 与 RecommendationProducer。
- Action Plan 必须 evidence-backed 且必须等待用户确认。
- Action Decision 必须来自显式 user decision；不得伪造 confirmation。
- Strategy Decision / Learning / Re-analysis 为 read-only derived intelligence，不得形成第二套 canonical ActionDecision lifecycle。
- 不得自动选择、确认、执行 action，不得自动发送消息、修改 relationship 或伪造 outcome。
- 所有数据必须 user_id 隔离。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- 不得修改历史 migration、重写 migrations.py、修改 conversations/messages 业务逻辑或通过修改测试掩盖错误。

## 持续禁止事项

- 不得让 RecommendationProducer 直接消费 StructuredAnalysis。
- 不得把 inference 自动写入 canonical evidence 或 memory。
- 不得把 unknown 自动转换为 fact、success 或 recommendation quality。
- 不得自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 不得绕过 user / person / conversation isolation。
- 不得建立第二套 Strategy / Decision / Action Plan / Execution / Learning 生命周期。
- GitHub 能确认的信息不得先要求服务器端查询。
