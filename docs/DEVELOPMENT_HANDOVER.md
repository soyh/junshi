# Development Handover

更新时间：2026-08-24

当前阶段：TEST-021 + TEST-022 feedback-to-memory foundations

当前状态：IN PROGRESS

当前 Branch：test-022-memory-update-foundation

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

TEST-019 Action Confirmation Foundation — 待服务器批次验收
TEST-020 Action Outcome Foundation — 待服务器批次验收

---

## TEST-021 Action Feedback Synthesis

Branch：test-021-action-feedback-synthesis

状态：IMPLEMENTED，待服务器验收

目标：把用户决策与行动结果汇总为确定性的反馈上下文，为后续长期记忆更新提供稳定输入，但不把反馈自动解释为新的事实或关系变化。

API：GET /api/v1/persons/{person_id}/action-plan/feedback/context

核心边界：
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

---

## TEST-022 Memory Update Foundation

Branch：test-022-memory-update-foundation

状态：IN PROGRESS

目标：把已经存在的、明确来源于用户决策与行动结果的反馈转换为“记忆更新候选”输入；第一阶段只提供候选，不直接写入长期记忆。

API：GET /api/v1/persons/{person_id}/memory-updates/context

核心实现：
- 只从真实 decision + outcome 生成 candidate
- deterministic candidate id
- status=proposed
- 保留 source_decision_id / source_outcome_id
- 保留原始 decision / outcome / note
- 缺失 outcome 不产生 memory candidate
- user_id / person_id isolation
- read-only

memory_constraints：
- must_be_source_backed=true
- must_be_proposed=true
- must_preserve_unknowns=true
- must_not_infer_from_missing_outcome=true
- must_not_auto_persist=true
- must_not_change_relationship=true

第一阶段边界：不直接写长期 memory，不自动改变 Relationship，不自动发送消息，不接真实 LLM，不新增 migration。

服务器验证规则：TEST-021 + TEST-022 合并一次专项测试，再执行一次全量测试。

---

## 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

当前生产数据库 schema migrations：001 / 002 / 003 / 004 / 005。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
