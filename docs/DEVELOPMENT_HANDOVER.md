# Development Handover

更新时间：2026-08-27
当前阶段：TEST-047 + TEST-048 strategy decision learning bridge
当前状态：IMPLEMENTED，待服务器批次验收
当前 Branch：test-047-048-strategy-decision-learning

---

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 Strategy Decision Lifecycle — VERIFIED
TEST-046 Strategy Decision Lifecycle Synthesis — VERIFIED

最近服务器验收：TEST-045 + TEST-046 专项 12 passed；全量 375 passed。

---

## TEST-045 / TEST-046

Lifecycle 统一表达 decision → result → execution → outcome → feedback。

API：
GET /api/v1/persons/{person_id}/strategy-decision/lifecycle-context
GET /api/v1/persons/{person_id}/strategy-decision/lifecycle-synthesis

核心边界：read-only；execution 与 outcome 独立；feedback source-backed；unknown 保留；不推断 recommendation quality、success、relationship impact；不自动执行、不自动发送、不调用 LLM；user/person isolation。

---

## TEST-047 Strategy Decision Learning Input

API：
GET /api/v1/persons/{person_id}/strategy-decision/learning-input

目标：把 lifecycle context 转换为后续 learning layer 可消费的 deterministic、source-backed learning input。

每个 item 保留 decision_id、recommendation_id、decision_status、result_status、feedback_status、learning_status、learning_eligible、outcome、feedback、unknowns、source。

只有 observed feedback 才进入 learning candidates；pending execution、pending outcome、rejected/not_actionable 等 unknown 状态不得被视为学习结果。

专项测试：backend/tests/test_strategy_decision_learning.py

---

## TEST-048 Strategy Decision Learning Synthesis

API：
GET /api/v1/persons/{person_id}/strategy-decision/learning-synthesis

汇总 learning input，输出 learning_candidate_decision_ids、unknown_decision_ids、recommendation_observed_counts、learning_summary 和完整 learning_items。

核心边界：deterministic、read-only、source-backed only、preserve unknowns；不改变关系、不自动执行、不自动发送、不调用 LLM；user/person isolation。

专项测试：backend/tests/test_strategy_decision_learning_synthesis.py

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-048 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 服务器测试

当前批次：TEST-047 + TEST-048。

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q \
  backend/tests/test_strategy_decision_learning.py \
  backend/tests/test_strategy_decision_learning_synthesis.py

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
