# Development Handover

更新时间：2026-08-24

当前阶段：TEST-021 Action Feedback Synthesis

当前状态：IN PROGRESS

当前 Branch：test-021-action-feedback-synthesis

---

## 已完成阶段

TEST-008 Person Timeline — VERIFIED
TEST-009 Text Import — VERIFIED
TEST-010 Conversation Analysis Foundation — VERIFIED
TEST-011 Evidence — VERIFIED
TEST-012 Person Profile — VERIFIED
TEST-013 Relationship State Analysis — VERIFIED
TEST-014 Recommendation Foundation — VERIFIED
TEST-015 Strategic Reply Foundation — VERIFIED
TEST-016 Action Plan Foundation — VERIFIED
TEST-017 Action Plan Synthesis — VERIFIED
TEST-018 Strategic Reply Synthesis — VERIFIED

TEST-019 Action Confirmation Foundation — 服务器待验收
TEST-020 Action Outcome Foundation — 服务器待验收

TEST-019 + TEST-020 服务器验证规则：两个 TEST-No 合并一次专项测试，再执行一次全量测试。

---

## TEST-021 Action Feedback Synthesis

Branch：test-021-action-feedback-synthesis

目标：把用户决策与行动结果汇总为确定性的反馈上下文，为后续长期记忆更新提供稳定输入，但不把反馈自动解释为新的事实或关系变化。

API：GET /api/v1/persons/{person_id}/action-plan/feedback/context

第一阶段实现：
- 聚合 action_decisions 与 action_outcomes
- deterministic ordering
- decision 可没有 outcome；缺失 outcome 不代表成功或失败
- 保留 completed / skipped / failed 原始结果
- 保留 decision / outcome note
- user_id / person_id isolation
- read-only
- 必须保持 unknowns
- 不自动修改 Relationship
- 不自动执行行动
- 不自动发送消息
- 不接真实 LLM

反馈约束：
- must_be_decision_backed=true
- must_be_outcome_backed=false
- must_preserve_unknowns=true
- must_not_infer_success_from_missing_outcome=true
- must_not_change_relationship=true
- must_not_auto_execute=true

服务器验证待完成：与 TEST-022 一起专项验证；随后执行全量测试。

---

## TEST-022 Memory Update Foundation

Branch：test-022-memory-update-foundation

目标：把已经存在的、明确来源于用户决策与行动结果的反馈转换为“记忆更新候选”输入；第一阶段只提供候选，不直接写入长期记忆。

第一阶段边界：
- 只允许真实 decision / outcome 作为 source
- 不从缺失 outcome 推导成功
- 不把 skipped / failed 自动改写成事实
- memory candidate 必须标记为 proposed
- 保留 source decision_id / outcome_id
- user_id / person_id isolation
- read-only
- 不自动修改 Relationship
- 不自动发送消息
- 不接真实 LLM
- 暂不新增长期 memory migration

服务器验证规则：TEST-021 + TEST-022 合并一次专项测试，再执行一次全量测试。

---

## 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

当前生产数据库 schema migrations：001 / 002 / 003 / 004 / 005。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
