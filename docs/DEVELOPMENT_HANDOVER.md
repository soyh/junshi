# Development Handover

更新时间：2026-08-29
当前阶段：TEST-054 + TEST-055 Learning Strategy downstream contract hardening — IMPLEMENTED, AWAITING SERVER VERIFICATION
当前状态：已修复 Strategic Reply learning candidate contract，并统一 Action Plan / Strategic Reply downstream learning candidate projection；最近一次已验证基线仍为 398 passed（TEST-051）
当前 Branch：test-055-learning-strategy-downstream-constraints
当前开发基线提交：0a760354a413baefe5b5de02a10e33577e669d53
最近一次已验证基线提交：b1a9f93e71c221d2020d94912f2309ec918d8d3e

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
TEST-052 Learning Strategy Strategic Reply Bridge — IMPLEMENTED，待服务器验收
TEST-053 Learning Strategy Action Plan Bridge — IMPLEMENTED，待服务器验收
TEST-054 Learning Strategy Downstream Candidate Contract — IMPLEMENTED，待服务器验收
TEST-055 Learning Strategy Downstream Constraint Contract — IMPLEMENTED，待服务器验收

TEST-049 + TEST-050 最终服务器验收：专项 10 passed；全量 392 passed；失败 0。
TEST-051 最终服务器验收：Recommendation 专项 15 passed；全量 398 passed；失败 0。

---

## TEST-054 Learning Strategy Downstream Candidate Contract

目标：修复 Strategic Reply downstream learning candidate 的输出契约，使其只暴露 canonical learning candidate 字段，不把 synthesis 内部字段泄漏到 downstream response。

既有 API：
GET /api/v1/persons/{person_id}/strategic-reply/context
GET /api/v1/persons/{person_id}/action-plan/context

本轮实现：
- StrategicReplyLearningStrategyBridgeService 增加 canonical candidate projection。
- 保留 recommendation_id、observed_outcome_count、outcome_counts、unknown_outcome_count、memory_update_count、synthesis_status、unknowns。
- 继续只暴露 observed outcome candidates；unobserved decisions 保持 unknown。

核心边界：不重新计算 learning facts；不改变 action decision / outcome 生命周期；read-only；source-backed；preserve unknowns；不自动发送；不自动执行；不调用 LLM。

专项覆盖：
backend/tests/test_strategic_reply_learning_strategy_bridge.py
backend/tests/test_action_plan_learning_strategy_bridge.py

状态：代码完成，尚未进行本轮服务器验收。

---

## TEST-055 Learning Strategy Downstream Constraint Contract

目标：确保 Action Plan 与 Strategic Reply 两个 downstream bridge 对 learning candidate 使用同一 canonical 字段契约，同时保留各自独有的执行/发送约束。

本轮实现：
- ActionPlanLearningStrategyBridgeService 增加相同 canonical candidate projection。
- Strategic Reply 继续暴露 must_not_auto_send。
- Action Plan 继续暴露 must_not_auto_execute。
- 两者均继承 learning-strategy synthesis 的 must_preserve_unknowns、must_not_turn_learning_into_fact 等约束。

核心边界：两个 downstream context 只消费既有 LearningStrategySynthesisService；不创建第二套学习事实；不排名推荐；不改变 relationship；read-only；user/person isolation；不调用 LLM。

专项覆盖：
backend/tests/test_strategic_reply.py
backend/tests/test_strategic_reply_learning_strategy_bridge.py
backend/tests/test_action_plan.py
backend/tests/test_action_plan_learning_strategy_bridge.py

状态：代码完成，尚未进行本轮服务器验收。

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-055 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 服务器测试

最近一次完成基线：TEST-051，398 passed。

TEST-052 ~ TEST-055 代码已完成，本轮等待一次统一服务器验收。

建议验收命令：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q backend/tests/test_strategic_reply.py backend/tests/test_strategic_reply_learning_strategy_bridge.py backend/tests/test_action_plan.py backend/tests/test_action_plan_learning_strategy_bridge.py

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
