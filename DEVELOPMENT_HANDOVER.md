# AI Love Strategist Development Handover

更新时间：2026-09-08
当前阶段：TEST-089 — Real LLM → Strategy Recommendation Candidate → Recommendation — CONTRACT DEFINITION
当前 Branch：test-088-real-llm-user-workflow

## 项目目标

本项目是长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人或回复生成器。

核心链路：

`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## TEST-088 — VERIFIED

TEST-088 已 VERIFIED。

已完成真实用户工作流的最小验收：

- 真实 canonical user / person / relationship / conversation / messages 可进入 AnalysisContext。
- Real Qwen / DashScope StructuredAnalysis 成功返回并完成 schema validation。
- StructuredAnalysis 保留 Fact / Inference / Unknown、hypothesis / signal 与 evidence provenance。
- Action Plan Context 能读取真实 relationship state 与 evidence。
- 无 Recommendation 时 `recommendations=[]`、`action_plan=[]` 为当前架构预期，不得为了验收强行生成 action。
- user isolation、read-only、source-backed、unknown preservation、no-auto-execution 等约束均保持。
- 此次 `/persons` FK 500 已确认是使用未注册 `X-User-ID=test-088-real-user` 导致 SQLite 正常拒绝，不属于 FK、migration、数据库损坏或 Person 业务逻辑缺陷。
- StructuredAnalysis 历史间歇性 502 不再作为 TEST-088 未完成项；当前真实 StructuredAnalysis 已成功通过。
- 未修改 production code、tests、migration 或数据库 schema。

## TEST-089 — 最小必要契约

目标：只验证现有 `AnalysisRecommendationService` 已定义的最小桥接边界：

`Real AnalysisContext → Real StructuredAnalysis → StrategyDecisionContext → explicit StrategyRecommendationCandidate → RecommendationProducer → Recommendation`

TEST-089 不重新实现 TEST-075/Strategy Decision、TEST-086 Action Decision/Execution 或 TEST-087 Outcome/Feedback/Learning 生命周期。

### 契约

- StructuredAnalysis 仍是 derived input，不成为 canonical truth。
- Strategy 只消费并保留 StructuredAnalysis 的语义、unknowns 与 evidence provenance。
- StrategyRecommendationCandidate 必须是显式、deterministic 的候选边界；不得让 RecommendationProducer 直接消费 StructuredAnalysis。
- candidate 必须有稳定 identity、非空 recommendation、非空 evidence_source_ids 和 provenance。
- candidate 的 evidence_source_ids 必须存在于 canonical evidence；无证据候选不得进入 Recommendation。
- Recommendation 必须只由 RecommendationProducer 产生。
- Recommendation 必须保留 candidate identity、evidence_source_ids 与 provenance。
- unknowns 可以作为 derived constraint/provenance 被保留，但不得被转换成 fact、success evidence 或 recommendation quality。
- 不自动选择、不自动确认、不自动执行、不自动发送消息、不修改 relationship。
- 不新增 StructuredAnalysis persistence，不新增第二套 Strategy / Recommendation 生命周期。
- user/person/conversation isolation 必须保持。
- 该阶段只证明 Recommendation 形成边界，不要求 Action Plan 非空；Action Plan 仍由后续已有 contract 消费显式 Recommendation。

### 最小验收

1. 对 TEST-088 已存在的真实 conversation 调用 analysis recommendation context。
2. Real Qwen 返回 StructuredAnalysis。
3. hypotheses 中满足 candidate contract 且具有真实 evidence provenance 的内容，经 StrategyRecommendationCandidateService 转换为显式 candidate。
4. RecommendationProducer 成功产生 Recommendation。
5. 返回结果中的 recommendation、evidence_source_ids、provenance 可追踪到真实 evidence。
6. 无证据 candidate 被拒绝。
7. 重复读取结果 deterministic，且无 decision / execution / outcome side effect。
8. 全量 pytest 保持通过；不得修改测试掩盖失败。

## 架构与安全边界

- AnalysisContext 必须 deterministic、source-backed、read-only。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Fact / Inference / Unknown 必须严格区分；inference、hypothesis、material signal 必须保留 provenance。
- Recommendation 必须经过显式 candidate contract 与 RecommendationProducer。
- 不得自动选择、确认、执行 action，不得自动发送消息、修改 relationship 或伪造 outcome。
- 所有数据必须 user_id 隔离。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- 不得修改历史 migration、重写 migrations.py、修改 conversations/messages 业务逻辑或通过修改测试掩盖错误。

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 ~ TEST-064：VERIFIED
TEST-065 ~ TEST-087：VERIFIED
TEST-088：VERIFIED

TEST-087 已锁定 Outcome → Feedback → Learning → Re-analysis → Recommendation 闭环，未新增第二套生命周期、migration 或数据库结构。

## TEST-089 边界

TEST-089 只负责验证 Recommendation 形成的最小桥接，不负责重新验证已经锁定的 Action Decision、Execution、Outcome、Feedback、Learning 生命周期。

当前 GitHub 已存在相关实现：

- `AnalysisRecommendationService` 负责 Analysis → Strategy context → candidate → RecommendationProducer 编排。
- `StrategyRecommendationCandidateService` 负责显式 candidate 形成。
- `RecommendationProducer` 负责 candidate → typed Recommendation，并验证 evidence provenance。

因此 TEST-089 的第一原则是先验证现有实现是否满足上述契约；不得为了制造更长的 demo pipeline 而扩大范围。

## 持续禁止事项

- 不得让 RecommendationProducer 直接消费 StructuredAnalysis。
- 不得把 inference 自动写入 canonical evidence 或 memory。
- 不得把 unknown 自动转换为 fact、success 或 recommendation quality。
- 不得自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 不得绕过 user / person / conversation isolation。
- 不得建立第二套 Strategy / Decision / Action Plan / Execution / Learning 生命周期。
- GitHub 能确认的信息不得先要求服务器端查询。
