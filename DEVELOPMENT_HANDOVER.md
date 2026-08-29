# AI Love Strategist Development Handover

更新时间：2026-08-29
当前阶段：TEST-065 Analysis Context learning-strategy bridge — IMPLEMENTED，路由注册已修复，待服务器专项/全量验收
当前 Branch：test-065-analysis-context-learning-strategy-bridge
最近一次服务器验收：TEST-064 专项 3 passed；TEST-063 后全量 424 passed；TEST-064 后全量 427 passed。

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
TEST-064 Learning Strategy Decision Learning Evidence Completeness — IMPLEMENTED，已通过服务器验收
TEST-065 Analysis Context learning-strategy bridge — IMPLEMENTED，路由注册已修复，待服务器专项/全量验收

---

## TEST-065 Analysis Context learning-strategy bridge

目标：把已经建立并验证的 person-level Learning Strategy Context 安全接入 conversation-level Analysis Context，使后续分析入口可以直接获得 source-backed learning inputs 与 canonical strategy constraints，同时不把 learning 结果提升为事实或推荐。

本轮实现：
- AnalysisService 注入 `LearningStrategyContextService`。
- Analysis Context 新增 `learning_strategy` 字段。
- 仅暴露 `learning_inputs` 与 `strategy_constraints`，避免重复复制 person/relationship 主上下文。
- learning inputs 直接复用 canonical Learning Strategy Context，不重新推导 decision、feedback、memory 或 provenance。
- Analysis Context schema 更新为显式声明 `learning_strategy`。
- 更新原有 Analysis Context contract 测试。
- 新增 `backend/tests/test_analysis_learning_strategy_bridge.py`。
- 验证 Analysis Context 与 Person Learning Strategy Context 的 learning inputs / strategy constraints 完全一致。
- 验证 strategy-decision source provenance 与 unknowns 在 Analysis Context 中保持不变。
- 验证 user isolation、determinism、read-only、no-auto-execution、no-auto-send、no-LLM 边界。
- 修复 `backend/app/api/router.py` 未注册 `analysis_router` 的路由接线问题，确保 `/api/v1/conversations/{conversation_id}/analysis/context` 实际进入 Analysis route。
- 服务器直接 TestClient smoke test 已确认 Analysis Context 路由返回预期的 conversation-not-found 404，而不是路由不存在的 404；同时 `/api/v1/persons` 正常返回 200。
- 不新增 migration，不改变 persistence，不改变 decision/outcome lifecycle。

核心边界：conversation-scoped entry；source-backed learning；canonical reuse；preserve source provenance；preserve unknowns；read-only；deterministic；person/user isolation；不把 learning 转成 fact；不排名推荐；不自动执行；不自动发送；不调用 LLM。

专项覆盖：
`backend/tests/test_analysis_learning_strategy_bridge.py`
`backend/tests/test_analysis.py`

状态：代码完成，路由接线已修复，服务器 smoke test 已通过，待专项测试与全量回归。

---

## TEST-064 Learning Strategy Decision Learning Evidence Completeness

目标：确保 strategy-decision learning synthesis 不仅保留 observed/unknown decision IDs 与计数，还完整暴露每个 learning candidate 和 unknown decision 对应的 canonical source provenance，并在 Strategic Reply / Action Plan 下游保持完全一致。

本轮实现：
- StrategyDecisionLearningBridgeService 新增 `learning_candidate_provenance`。
- StrategyDecisionLearningBridgeService 新增 `unknown_decision_provenance`。
- 两组 provenance 直接来自 strategy-decision learning item 的 canonical `source`，不重新推导事实。
- 新增 `backend/tests/test_learning_strategy_decision_learning_evidence_completeness.py`。
- 验证 observed / unknown 两类 evidence 的 provenance 完整性。
- 验证 provenance 与 decision IDs、counts 的一致性。
- 验证 Learning Strategy Synthesis / Strategic Reply / Action Plan 三层保持完全一致。
- 不新增 migration，不改变 persistence，不改变 decision/outcome lifecycle，不调用 LLM，不自动执行，不自动发送。

核心边界：source-backed；canonical source provenance；preserve unknowns；read-only；deterministic；person/user isolation；不把 learning 转成 fact；不排名推荐；不自动执行；不自动发送；不调用 LLM。

专项覆盖：
`backend/tests/test_learning_strategy_decision_learning_evidence_completeness.py`

状态：代码完成，已通过服务器验收。

---

## TEST-063 Learning Strategy Decision Constraint Parity

目标：确保 strategy-decision learning 的 provenance preservation constraint 在 Learning Strategy Context、Learning Strategy Synthesis、Strategic Reply、Action Plan 四层保持一致，并继续保留 source-backed、read-only、unknown-preserving 边界。

本轮实现：
- StrategyDecisionLearningBridgeService 的 synthesis constraints 增加 `must_preserve_source_provenance`。
- LearningStrategyContextService 将 `must_preserve_source_provenance` 作为 canonical strategy constraint 向上游/下游传播。
- 新增 `backend/tests/test_learning_strategy_decision_constraint_parity.py`。
- 验证 Learning Strategy Synthesis / Strategic Reply / Action Plan 三层 constraint parity。
- 验证 Learning Strategy Context 中 strategy-decision learning constraints 的 source provenance / unknown preservation 声明。
- 验证 read-only 与 person/user isolation 边界。
- 不新增 migration，不改变 persistence，不改变 decision/outcome lifecycle，不调用 LLM，不自动执行，不自动发送。

核心边界：source-backed；preserve source provenance；preserve unknowns；read-only；deterministic；person/user isolation；不把 learning 转成 fact；不排名推荐；不自动执行；不自动发送；不调用 LLM。

专项覆盖：
`backend/tests/test_learning_strategy_decision_constraint_parity.py`

状态：代码完成，已通过服务器验收。

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-065 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 服务器测试

TEST-065 建议验收：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q \
  backend/tests/test_analysis_learning_strategy_bridge.py \
  backend/tests/test_analysis.py

然后执行一次全量：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

后续开发节奏：不再为每个 TEST 单独执行一次专项测试；开发阶段以相关测试文件/模块的合并专项测试为主，阶段性完成后再执行一次全量回归。只有出现失败时才缩小范围定位。

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
