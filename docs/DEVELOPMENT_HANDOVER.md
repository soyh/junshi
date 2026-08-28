# Development Handover

更新时间：2026-08-29
当前阶段：TEST-062 Learning Strategy decision provenance parity — IMPLEMENTED，待服务器验证
当前 Branch：test-062-learning-strategy-decision-provenance-parity
最近一次服务器验收：TEST-061 专项 47 passed；全量 418 passed。

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
TEST-062 Learning Strategy Decision Provenance Parity — IMPLEMENTED，待服务器验证

---

## TEST-062 Learning Strategy Decision Provenance Parity

目标：验证 Learning Strategy 中的 strategy-decision learning evidence 在 Learning Strategy Synthesis、Strategic Reply、Action Plan 三层之间保持同一事实来源与完全一致的 decision provenance。

本轮实现：
- 新增 `backend/tests/test_learning_strategy_decision_provenance_parity.py`。
- 验证 observed decision 与 outcome-unknown decision 的 decision ID 分流保持一致。
- 验证 synthesis / Strategic Reply / Action Plan 三层的 `strategy_decision_learning` 完全一致。
- 验证 repeated read deterministic / read-only。
- 验证 person isolation 与 user isolation。
- 不新增 migration，不改变 persistence，不改变 decision/outcome lifecycle，不调用 LLM，不自动执行，不自动发送。

核心边界：source-backed；preserve unknowns；read-only；deterministic；person/user isolation；不把 learning 转成 fact；不排名推荐；不自动执行；不自动发送；不调用 LLM。

专项覆盖：
`backend/tests/test_learning_strategy_decision_provenance_parity.py`

状态：代码完成，待服务器验收。

---

## TEST-060 / TEST-061 验收结果

TEST-060：canonical learning `source` 保留 `decision_count` 与 `decision_counts`，并继续保留 observed / unknown outcome provenance。

TEST-061：验证 Action Feedback Learning Input → Learning Strategy Synthesis → Strategic Reply / Action Plan 三层之间 canonical source provenance 完全一致。

服务器最终验收：
- TEST-058~061 专项：47 passed
- 全量：418 passed

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-062 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 服务器测试

TEST-061 最终服务器验收：专项 47 passed；全量 418 passed。

TEST-062 建议验收：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q \
  backend/tests/test_learning_strategy_decision_provenance_parity.py

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
