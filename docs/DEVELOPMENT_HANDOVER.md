# Development Handover

更新时间：2026-08-24

当前阶段：TEST-019 + TEST-020 action feedback loop foundations

当前状态：IN PROGRESS

当前 Branch：test-020-action-outcome-foundation

---

## TEST-008

Person Timeline

状态：VERIFIED

Branch：test-008-person-timeline

---

## TEST-009

Text Import

状态：VERIFIED

Branch：test-009-text-import

最终验证 Commit：a2059a6 test: verify text import rollback atomicity

最终测试：Text Import 专项 44 passed；全量 103 passed

验收结论：TEST-009 Text Import VERIFIED。

---

## TEST-010

Conversation Analysis Foundation

状态：VERIFIED

Branch：test-010-conversation-analysis

目标：建立分析输入上下文，暂不接真实 LLM。

最终服务器验证：TEST-010 专项 9 passed；全量 112 passed。

验收结论：TEST-010 Conversation Analysis Foundation VERIFIED。

---

## TEST-011

Evidence

状态：VERIFIED

Branch：test-011-evidence

目标：建立分析事实的证据层，使后续 Fact / Inference 能够引用明确、可追溯的原始数据来源。

API：GET /api/v1/conversations/{conversation_id}/analysis/evidence

最终服务器验证：TEST-011 专项 11 passed；全量 123 passed。

验收结论：TEST-011 Evidence VERIFIED。

---

## TEST-012

Person profile

状态：VERIFIED

Branch：test-012-person-profile

目标：建立人物档案的只读聚合入口，为后续人物画像和关系分析提供稳定输入边界。

最终服务器验证：TEST-012 专项 8 passed；全量 131 passed。

验收结论：TEST-012 Person profile VERIFIED。

---

## TEST-013

Relationship state analysis

状态：VERIFIED

Branch：test-013-relationship-state-analysis

目标：建立关系状态分析的稳定输入与输出边界。

最终服务器验证：TEST-013 专项 10 passed；全量 141 passed。

验收结论：TEST-013 Relationship state analysis VERIFIED。

---

## TEST-014

Recommendation foundation

状态：VERIFIED

Branch：test-014-recommendation-foundation

目标：建立建议输出的稳定契约与证据边界。

API：GET /api/v1/persons/{person_id}/recommendation-analysis/context

最终服务器验证：TEST-014 专项 9 passed；全量 150 passed。

验收结论：TEST-014 Recommendation foundation VERIFIED。

---

## TEST-015

Strategic reply foundation

状态：VERIFIED

Branch：test-015-strategic-reply-foundation

目标：在 Recommendation Foundation 之上建立“策略回复”的稳定输入契约，同时严格保持分析、生成和执行分离。

API：GET /api/v1/persons/{person_id}/strategic-reply/context

reply_constraints：
- must_be_evidence_backed=true
- must_preserve_unknowns=true
- must_not_auto_send=true
- must_not_change_relationship=true

最终服务器验证：TEST-015 专项 9 passed；全量 159 passed。

验收结论：TEST-015 Strategic reply foundation VERIFIED。

---

## TEST-016

Action plan foundation

状态：VERIFIED

Branch：test-016-action-plan-foundation

目标：建立行动计划输入契约，但不自行创造行动、不执行行动。

API：GET /api/v1/persons/{person_id}/action-plan/context

最终服务器验证：TEST-016 专项 7 passed；全量 166 passed。

验收结论：TEST-016 Action plan foundation VERIFIED。

---

## TEST-017

Action plan synthesis

状态：VERIFIED

Branch：test-017-action-plan-synthesis

目标：把已经存在的 Recommendation 转换为结构化 Action Plan Proposal，但只允许“明确行动 + 明确证据引用”的 Recommendation 被提升为行动计划。

核心边界：不自行创造建议、不调用 LLM、不执行行动。

最终服务器验证：TEST-017 专项 11 passed；全量 170 passed。

验收结论：TEST-017 Action Plan Synthesis VERIFIED。

---

## TEST-018

Strategic reply synthesis

状态：VERIFIED（服务器已验收）

Branch：test-018-strategic-reply-synthesis

目标：只允许 Recommendation 明确提供 `reply` 且引用真实 Evidence 时生成确定性的 draft，不自行编造回复。

最终服务器验证：TEST-018 专项 10 passed；全量 180 passed。

验收结论：TEST-018 Strategic Reply Synthesis VERIFIED。

---

## TEST-019

Action confirmation foundation

状态：IN PROGRESS

Branch：test-019-action-confirmation-foundation

目标：把“requires_user_confirmation”从静态约束推进为可记录的用户决策层。用户可以确认或拒绝一个已有、证据支持的 Action Plan；系统只记录用户决策，不执行行动。

API：
- GET /api/v1/persons/{person_id}/action-plan/decisions/context
- POST /api/v1/persons/{person_id}/action-plan/decisions

第一阶段实现：
- 新增 action_decisions 持久化表
- 记录 confirmed / rejected
- confirmed 必须引用当前可用的 evidence-backed recommendation
- rejected 可以记录用户暂不执行的决定
- 决策历史 deterministic ordering
- user_id / person_id isolation
- 不自动执行
- 不自动发送消息
- 不修改 Relationship

新增 migration：004_action_feedback.sql

服务器验证待完成：TEST-019 专项测试 + TEST-020 专项测试一次性验证；随后执行全量测试。

---

## TEST-020

Action outcome foundation

状态：IN PROGRESS

Branch：test-020-action-outcome-foundation

目标：在用户确认行动之后记录执行结果，为后续反馈分析和长期记忆更新建立确定性输入层。

API：
- GET /api/v1/persons/{person_id}/action-plan/outcomes
- POST /api/v1/persons/{person_id}/action-plan/outcomes/{decision_id}

第一阶段实现：
- 新增 action_outcomes 持久化表
- 仅允许 confirmed action decision 产生 outcome
- outcome 固定为 completed / skipped / failed
- 保留用户 note
- deterministic history ordering
- user_id / person_id isolation
- 不把 outcome 自动写成 Interaction
- 不自动发送消息
- 不自动修改 Relationship
- 不接真实 LLM

新增 migration：005_action_outcomes.sql

服务器验证待完成：与 TEST-019 一起专项验证；随后执行全量测试。

---

## 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

当前生产数据库 schema migrations：001 / 002 / 003 / 004 / 005。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。

本次流程约定：TEST-019 与 TEST-020 作为相邻的反馈闭环阶段，合并为一次服务器专项测试，再执行一次全量测试。
