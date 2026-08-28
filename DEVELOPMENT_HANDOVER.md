# AI Love Strategist Development Handover

更新时间：2026-08-29
当前阶段：TEST-060 + TEST-061 Learning Strategy provenance completeness/parity — IMPLEMENTED, AWAITING SERVER VERIFICATION
当前 Branch：test-061-learning-strategy-provenance-parity
最近一次服务器验收：TEST-057 专项 30 passed；全量 408 passed。

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
TEST-052 Learning Strategy Strategic Reply Bridge — IMPLEMENTED
TEST-053 Learning Strategy Action Plan Bridge — IMPLEMENTED
TEST-054 Learning Strategy Downstream Candidate Contract — IMPLEMENTED
TEST-055 Learning Strategy Downstream Constraint Contract — IMPLEMENTED
TEST-056 Learning Strategy Downstream Memory Update Semantics — IMPLEMENTED
TEST-057 Learning Strategy Downstream Candidate Parity — VERIFIED
TEST-058 Learning Strategy Source Provenance — IMPLEMENTED，待服务器验收
TEST-059 Learning Strategy Provenance Immutability — IMPLEMENTED，待服务器验收
TEST-060 Learning Strategy Source Provenance Completeness — IMPLEMENTED，待服务器验收
TEST-061 Learning Strategy Provenance Parity — IMPLEMENTED，待服务器验收

---

## TEST-060 Learning Strategy Source Provenance Completeness

目标：让 source provenance 不仅记录 observed/unknown outcome 数字，还完整保留其上游 decision cardinality，避免 downstream 只有 outcome 聚合而失去 source evidence 的决策规模信息。

本轮实现：
- ActionFeedbackLearningService 的 canonical `source` 增加 `decision_count` 与 `decision_counts`。
- LearningStrategySynthesisService 不再重新构造 provenance，而是原样保留上游 canonical source。
- 保持 observed / unknown outcome counts 与既有 candidate 字段一致。
- 不新增 migration，不改变 persistence，不排名，不调用 LLM。

---

## TEST-061 Learning Strategy Provenance Parity

目标：验证同一 source provenance 在 Action Feedback Learning Input → Learning Strategy Synthesis → Strategic Reply / Action Plan 三层之间保持完全一致。

本轮实现：
- 新增跨层 provenance parity tests。
- 验证 mixed observed/unknown feedback 的 source cardinality 在各层完全一致。
- 验证 Strategic Reply / Action Plan 只投影 canonical source，不产生新的事实推断。
- 继续验证 unknown preservation、read-only、no auto-execution、no auto-send、no LLM 等约束。

核心边界：read-only；source-backed；preserve unknowns；user/person isolation；不自动持久化；不自动发送；不自动执行；不调用 LLM。

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-061 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 服务器测试

TEST-057 最终服务器验收：专项 30 passed；全量 408 passed。

TEST-058 ~ TEST-061 本轮统一验收：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q \
  backend/tests/test_learning_strategy_synthesis.py \
  backend/tests/test_learning_strategy_provenance_parity.py \
  backend/tests/test_strategic_reply.py \
  backend/tests/test_strategic_reply_learning_strategy_bridge.py \
  backend/tests/test_action_plan.py \
  backend/tests/test_action_plan_learning_strategy_bridge.py

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
