# Development Handover

更新时间：2026-08-29
当前阶段：TEST-064 Learning Strategy decision learning evidence completeness — IMPLEMENTED，待服务器验证
当前 Branch：test-064-learning-strategy-decision-learning-evidence-completeness
最近一次服务器验收：TEST-063 专项 3 passed；TEST-063 后全量 424 passed。

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
TEST-064 Learning Strategy Decision Learning Evidence Completeness — IMPLEMENTED，待服务器验证

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

状态：代码完成，待服务器验收。

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
TEST-045 ~ TEST-064 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 服务器测试

TEST-064 建议验收：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q \
  backend/tests/test_learning_strategy_decision_learning_evidence_completeness.py

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
