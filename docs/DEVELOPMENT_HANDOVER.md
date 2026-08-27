# Development Handover

更新时间：2026-08-27
当前阶段：TEST-049 + TEST-050 strategy decision learning bridge
当前状态：IMPLEMENTED，待服务器批次验收
当前 Branch：test-049-050-strategy-decision-learning-bridge

---

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 Strategy Decision Lifecycle — VERIFIED
TEST-046 Strategy Decision Lifecycle Synthesis — VERIFIED
TEST-047 Strategy Decision Learning Input — VERIFIED
TEST-048 Strategy Decision Learning Synthesis — VERIFIED

最近服务器验收：TEST-047 + TEST-048 专项 14 passed；全量 389 passed。

---

## TEST-049 Strategy Decision Learning Bridge

目标：把 strategy decision learning input 接入既有 learning-strategy context，而不是创建第二套学习事实。

既有 API：
GET /api/v1/persons/{person_id}/learning-strategy/context

新增 learning_inputs.strategy_decision，直接复用 TEST-047 source-backed learning input。

核心边界：不改变 decision / execution / outcome 生命周期；不新增 migration；不把 unknown 转换成成功或失败；不推断 recommendation quality、success、relationship impact；read-only；user/person isolation。

专项测试：backend/tests/test_strategy_decision_learning_bridge.py

---

## TEST-050 Strategy Decision Learning Synthesis Bridge

目标：把 TEST-048 synthesis 接入既有 learning-strategy synthesis，使策略学习层同时看到 action feedback、memory updates 和 strategy decision learning。

既有 API：
GET /api/v1/persons/{person_id}/learning-strategy/synthesis

新增 strategy_decision_learning：
- learning_candidate_decision_ids
- unknown_decision_ids
- recommendation_observed_counts
- learning_candidate_count
- unknown_count
- constraints

核心边界：deterministic、read-only、source-backed only、preserve unknowns；不排名推荐、不把学习结果写成事实、不自动执行、不自动发送、不调用 LLM。

专项测试：backend/tests/test_strategy_decision_learning_bridge.py

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-050 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 服务器测试

当前批次：TEST-049 + TEST-050。

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q \
  backend/tests/test_strategy_decision_learning_bridge.py

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
