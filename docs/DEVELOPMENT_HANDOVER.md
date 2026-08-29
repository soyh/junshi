# Development Handover

更新时间：2026-08-29
当前阶段：TEST-077 — Strategic Reply downstream boundary
当前 Branch：test-076-structured-analysis-strategic-reply-consumption
最近一次服务器验收：TEST-076 全量回归 468 passed；18080 实际 HTTP smoke test 已验证 StructuredAnalysis → Strategic Reply derived-input 链路成功；LLM failure 映射为 HTTP 502；未产生 reply draft / auto-send / relationship mutation side effect。

---

## 架构冻结：Analysis → LLM → StructuredAnalysis → Strategy

正式架构契约见：`docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`

冻结后的主链：

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Human Confirmation → Execution / Outcome`

核心边界：
- AnalysisContext 是 deterministic、source-backed、read-only 的 LLM 输入，不是 AI 分析结果。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- LLM 只在 AnalysisContext 边界之后出现。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- StructuredAnalysis 中的 inference / hypothesis / material signal 应保留 canonical evidence provenance。
- unknown 必须在证据不足时保持 unknown，不得被模型猜测自动提升为事实。
- Strategy 消费 StructuredAnalysis，但不得绕过现有 decision / confirmation / execution 生命周期。
- Strategic Reply 只能在既有 Strategy / Decision 边界内消费 derived analysis，不得因为 LLM 输出而自动生成、确认或发送消息。
- 现有 Persistence、Evidence、Relationship State、Learning Strategy、Strategy Decision、Strategic Reply、Action Plan、Execution 生命周期不因引入 LLM 而重写。
- 当前全局 no-LLM 约束解除；改为仅对 deterministic Context / Evidence / Learning / Persistence / Decision / Execution 层保持 no-LLM。

第一阶段不新增数据库表；StructuredAnalysis 初期视为 derived request-scoped output。未来如需持久化，必须另行设计并新增 migration。

---

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 Strategy Decision Lifecycle — VERIFIED
TEST-046 Strategy Decision Lifecycle Synthesis — VERIFIED
TEST-047 Strategy Decision Learning Input — VERIFIED
TEST-048 Strategy Decision Learning Synthesis — VERIFIED
TEST-049 Strategy Decision Learning Bridge — VERIFIED
TEST-050 Strategy Decision Learning Synthesis Bridge — VERIFIED
TEST-051 Learning Strategy Recommendation Bridge — VERIFIED
TEST-052 Learning Strategy Strategic Reply Bridge — VERIFIED
TEST-053 Learning Strategy Action Plan Bridge — VERIFIED
TEST-054 Learning Strategy Downstream Candidate Contract — VERIFIED
TEST-055 Learning Strategy Downstream Constraint Contract — VERIFIED
TEST-056 Learning Strategy Downstream Memory Update Semantics — VERIFIED
TEST-057 Learning Strategy Downstream Candidate Parity — VERIFIED
TEST-058 Learning Strategy Source Provenance — VERIFIED
TEST-059 Learning Strategy Provenance Immutability — VERIFIED
TEST-060 Learning Strategy Source Provenance Completeness — VERIFIED
TEST-061 Learning Strategy Provenance Parity — VERIFIED
TEST-062 Learning Strategy Decision Provenance Parity — VERIFIED
TEST-063 Learning Strategy Decision Constraint Parity — VERIFIED
TEST-064 Learning Strategy Decision Learning Evidence Completeness — VERIFIED
TEST-065 Analysis Context learning-strategy bridge — VERIFIED
TEST-066 Analysis Context relationship-state bridge — VERIFIED
TEST-067 Analysis Context canonical evidence bridge — VERIFIED
TEST-068 Analysis Context conversation evidence bridge — VERIFIED
TEST-069 Analysis Context evidence contract sync — VERIFIED
TEST-070 Analysis LLM Service — VERIFIED
TEST-071 Structured Analysis Strategy Bridge — VERIFIED
TEST-072 Analysis → Strategy Orchestration — VERIFIED
TEST-073 Qwen Provider Integration — VERIFIED
TEST-074 Analysis → Strategy formal entrypoint — VERIFIED
TEST-075 StructuredAnalysis → Strategy Decision 最小消费契约 — VERIFIED
TEST-076 StructuredAnalysis → Strategic Reply 消费契约 — VERIFIED

---

## TEST-076 StructuredAnalysis → Strategic Reply 消费契约

TEST-076 在既有 Strategic Reply 体系中增加最小 derived-analysis consumption boundary，不建立第二套回复体系。

核心边界：
- `backend/app/services/analysis_strategic_reply.py`
- `backend/app/services/strategic_reply_analysis_bridge.py`
- `backend/app/api/routes/analysis_strategic_reply.py`
- `backend/tests/test_strategic_reply_analysis_bridge.py`
- `backend/tests/test_analysis_strategic_reply_route.py`

正式入口：
`GET /api/v1/conversations/{conversation_id}/strategic-reply/context`

执行链：
`conversation_id → AnalysisContext → LLMAnalysisService/Qwen → StructuredAnalysis → existing Strategic Reply context → derived reply_inputs`

`StrategicReplyAnalysisBridgeService`：
- 保留 `StructuredAnalysis` 为 derived output。
- 将 summary、observed_facts、inferences、hypotheses、emotional_signals、relationship_signals、risk_signals、intent_signals、unknowns 投影到 `reply_inputs.signals`。
- 保留 `evidence_source_ids` provenance。
- 设置 `analysis_is_derived = true`。
- 保留/强化 evidence-backed、unknown、provenance、derived、no-auto-send、no-relationship-change 约束。
- 不把 LLM 分析直接转换为 reply draft 或 recommendation。

Route：
- 当前用户身份通过 `get_current_user_id` 获取。
- conversation scope 继续由既有 AnalysisContext contract 约束。
- Qwen/LLM failure 映射为 HTTP 502。
- 不发送消息，不执行 action，不修改 relationship，不持久化 StructuredAnalysis。

TEST-076 契约测试覆盖：
- derived input 返回。
- provenance 与 unknown 保留。
- 不生成 reply draft / recommendation。
- reply constraints 语义保持。
- 非 dict reply context 输入校验。
- route 的 LLM failure → 502。

服务器最终验收（本轮提供）：
- FastAPI：127.0.0.1:18080
- `/health`：HTTP 200
- `/api/v1/conversations/{conversation_id}/strategic-reply/context`：实际 Qwen HTTP 200
- `structured_analysis` 返回为 derived output。
- `reply_inputs.analysis_is_derived=true`。
- `draft=null`。
- 全量回归：468 passed。
- 未产生自动发送或 relationship / decision / execution side effect。

TEST-076 正式标记为 VERIFIED。

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-076 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## TEST-077 — Strategic Reply downstream boundary

TEST-077 从 TEST-076 的 Strategic Reply derived-input 边界继续向下推进，但不把 LLM 直接变成发送器，也不建立第二套 Strategic Reply / Decision 生命周期。

开始实现前必须从 GitHub 读取：
1. `docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`
2. TEST-075 StructuredAnalysis → Strategy Decision 相关 service / schema / tests
3. TEST-076 Strategic Reply analysis bridge / route / schema / tests
4. 现有 Strategic Reply、Strategy Decision、Action Plan、Execution 相关 service / schema / tests

实现原则：
- 不改变 canonical evidence / AnalysisContext contract。
- 不让 LLM 进入 persistence / decision persistence / execution。
- 不自动生成并发送第三方消息。
- 不自动确认 decision。
- `reply_inputs` 仍是 derived input，不是 canonical fact。
- 保持 evidence provenance 与 unknown semantics。
- 保持 user/person/conversation isolation。
- 优先建立最小、可测试的 downstream contract，再决定是否需要新增 route/service/schema。
- 不新增数据库表。

实现顺序：
1. GitHub 读取 TEST-075 / TEST-076 及相关 Strategic Reply / Decision / Action Plan / Execution 代码、测试和文档。
2. 明确 TEST-077 的最小真实产品边界。
3. 先补契约测试。
4. 实现最小代码。
5. 执行 TEST-077 专项测试。
6. 执行 Strategic Reply / Decision 相关回归。
7. 执行全量 pytest。
8. 最后服务器专项验收；真实 Qwen smoke test 只验证 derived downstream input，不允许发送、执行或写入 outcome。

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

架构冻结后：LLM 仅位于 AnalysisContext → StructuredAnalysis 边界之后；不得进入 canonical evidence、persistence、learning context、decision persistence 或 execution 层。
