# Development Handover

更新时间：2026-08-29
当前阶段：ARCHITECTURE FREEZE — Analysis → LLM → StructuredAnalysis → Strategy contract 已固化
当前 Branch：test-065-analysis-context-learning-strategy-bridge
最近一次服务器验收：TEST-069 后全量 444 passed。

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
- 不允许 LLM 直接发送第三方消息、自动执行 action、修改 relationship state、写入 learning history 或伪造 outcome success。
- 现有 Persistence、Evidence、Relationship State、Learning Strategy、Strategy Decision、Strategic Reply、Action Plan、Execution 生命周期不因引入 LLM 而重写。
- 当前全局 no-LLM 约束解除；改为仅对 deterministic Context / Evidence / Learning / Persistence / Decision / Execution 层保持 no-LLM。

第一阶段不新增数据库表；StructuredAnalysis 初期视为 derived request-scoped output。未来如需持久化，必须另行设计并新增 migration。

后续实现顺序：
1. 保持现有 AnalysisContext contract 不变。
2. 新增 provider-neutral LLM adapter boundary。
3. 定义严格校验的最小 StructuredAnalysis schema。
4. 实现 AnalysisContext → StructuredAnalysis。
5. 覆盖 provenance、unknowns、isolation、malformed output、provider failure、no-side-effect。
6. 将 StructuredAnalysis 接入现有 Strategy，同时不改变 decision/execution 语义。
7. 专项回归后执行全量测试。

冻结后禁止继续通过 TEST 单纯逐字段扩张 AnalysisContext；只有真实架构需求才新增字段或 bridge。

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

---

## TEST-069 Analysis Context evidence contract sync

目标：同步 Analysis Context 与 canonical conversation evidence contract，并保持 evidence 在 conversation analysis 边界上的 canonical reuse。

服务器最终验收：
`backend/tests/test_analysis_conversation_evidence_bridge.py`
`backend/tests/test_evidence.py`
`backend/tests/test_analysis_canonical_evidence_bridge.py`
`backend/tests/test_analysis_relationship_state_bridge.py`
`backend/tests/test_analysis_learning_strategy_bridge.py`
`backend/tests/test_analysis.py`
以上专项 37 passed；全量 444 passed。

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-069 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

架构冻结后：LLM 仅位于 AnalysisContext → StructuredAnalysis 边界之后；不得进入 canonical evidence、persistence、learning context、decision 或 execution 层。
