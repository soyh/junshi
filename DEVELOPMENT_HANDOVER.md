# AI Love Strategist Development Handover

更新时间：2026-08-27
当前阶段：TEST-047 + TEST-048 strategy decision learning bridge
当前状态：IMPLEMENTED，待服务器批次验收
当前 Branch：test-047-048-strategy-decision-learning

---

## 项目定位

项目名称：AI Love Strategist
定位：AI 恋爱军师 / AI Relationship Management & Dating Companion System。

最终目标：用户添加关系对象后，持续导入聊天记录和互动数据，由系统建立人物画像、关系状态、历史记忆和行动计划，并根据后续反馈持续更新。

核心闭环：
添加对象 → 建立人物档案 → 导入聊天/互动 → 分析 → 建立画像 → 判断关系状态 → 生成策略回复 → 用户确认 → 用户执行 → 记录结果 → 反馈 → 更新记忆 → 长期关系跟踪

当前阶段仍以稳定的数据、证据、分析、策略、用户决策、结果反馈和学习输入契约为主，尚未进入真实 LLM、自动执行或自动发送阶段。

系统不得自动联系第三方。每个人物必须保持独立档案和数据隔离。

---

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 Strategy Decision Lifecycle — VERIFIED
TEST-046 Strategy Decision Lifecycle Synthesis — VERIFIED

最近服务器验收：
TEST-045 + TEST-046 专项：12 passed
全量：375 passed

---

## TEST-045 / TEST-046 Strategy Decision Lifecycle

Lifecycle 统一表达：decision → result → execution → outcome → feedback。

TEST-045 API：
GET /api/v1/persons/{person_id}/strategy-decision/lifecycle-context

TEST-046 API：
GET /api/v1/persons/{person_id}/strategy-decision/lifecycle-synthesis

核心边界：
- read-only
- execution 与 outcome 保持独立
- outcome 不等于自动 execution
- feedback 必须 source-backed
- unknown 必须保留
- 不推断 recommendation quality
- 不推断 success
- 不推断 relationship impact
- 不自动执行
- 不自动发送
- 不调用 LLM
- user/person isolation

---

## TEST-047 Strategy Decision Learning Input

API：
GET /api/v1/persons/{person_id}/strategy-decision/learning-input

目标：把 TEST-045 lifecycle context 转换为可供后续 learning layer 消费的 deterministic、source-backed learning input。

每个 item 对应一个 strategy decision，并保留：
decision_id、recommendation_id、decision_status、result_status、feedback_status、learning_status、learning_eligible、outcome、feedback、unknowns、source。

只有 feedback_status=outcome_observed 时 learning_eligible=true。
confirmed_pending_execution、executed_pending_outcome、rejected/not_actionable 等没有已观察 outcome 的状态必须保持 outcome_unknown，不得进入学习候选。

不新增 migration，不改变 decision / execution / outcome 生命周期。

专项测试：backend/tests/test_strategy_decision_learning.py

---

## TEST-048 Strategy Decision Learning Synthesis

API：
GET /api/v1/persons/{person_id}/strategy-decision/learning-synthesis

目标：汇总 TEST-047 learning input，输出：
- learning_candidate_decision_ids
- unknown_decision_ids
- recommendation_observed_counts
- learning_summary
- 完整 learning_items

学习候选只来自 source-backed observed feedback。
unknown 不得被压缩成成功、失败、推荐质量或关系影响判断。

核心边界：
- deterministic
- read-only
- source-backed only
- preserve unknowns
- 不改变关系
- 不自动执行
- 不自动发送
- 不调用 LLM
- user/person isolation

专项测试：backend/tests/test_strategy_decision_learning_synthesis.py

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。

TEST-045 ~ TEST-048 均不新增 migration，不改变既有 action_decisions、action_executions、action_outcomes 生命周期。

---

## 服务器测试规则

相邻两个 TEST-No 合并为一次服务器测试批次。

当前批次：TEST-047 + TEST-048。

推荐命令：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q \
  backend/tests/test_strategy_decision_learning.py \
  backend/tests/test_strategy_decision_learning_synthesis.py

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

每个 TEST 保持独立代码边界、测试文件和验收记录。

---

## 开发原则

不要随意改变现有架构。
优先采用 Route → Service → Repository → SQLite。
所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
