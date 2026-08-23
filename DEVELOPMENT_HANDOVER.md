# AI Love Strategist Development Handover

更新时间：2026-08-24
当前阶段：TEST-018 Strategic reply synthesis
当前状态：IN PROGRESS
当前 Branch：test-018-strategic-reply-synthesis

---

## 1. 项目定位

项目名称：AI Love Strategist

定位：AI 恋爱军师 / AI Relationship Management & Dating Companion System。

最终目标：用户添加一个关系对象后，可以持续导入聊天记录和互动数据，由系统建立人物画像、关系状态、历史记忆和行动计划，并根据后续反馈持续更新。

核心闭环：
添加对象 → 建立人物档案 → 导入聊天/互动 → 分析 → 建立画像 → 判断关系状态 → 生成策略回复 → 用户执行 → 反馈 → 更新记忆 → 长期关系跟踪

当前工程阶段仍以“稳定的数据、证据、分析和策略契约”为主，尚未进入真实 LLM、自动执行或自动发送阶段。

系统不得自动联系第三方。每个人物必须保持独立档案和数据隔离。

---

## 2. 服务器环境

服务器：Alibaba Cloud Linux 3.2104 LTS 64-bit
Python：3.11.13
Node.js：20.20.2
项目目录：/opt/ai-love-strategist
虚拟环境：/opt/ai-love-strategist/.venv
数据库：SQLite
数据库文件：/opt/ai-love-strategist/data/app.sqlite3
FastAPI：127.0.0.1:18080

禁止使用、修改、停止：8899
当前没有 Docker。当前没有 Nginx。

---

## 3. 当前技术架构

Backend：Python 3.11 / FastAPI / SQLite / Pydantic / pydantic-settings
Frontend：React / TypeScript / Vite

主要结构：backend/app/api、backend/app/config、backend/app/core、backend/app/domain、backend/app/repositories、backend/app/schemas、backend/app/services、backend/migrations、backend/tests

当前生产数据库 schema migrations：001 / 002 / 003

---

## 4. 已完成阶段

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

---

## 5. TEST-008 至 TEST-013

TEST-008 Person Timeline
Branch：test-008-person-timeline
状态：VERIFIED

TEST-009 Text Import
Branch：test-009-text-import
最终验证 Commit：a2059a6 test: verify text import rollback atomicity
最终测试：专项 44 passed；全量 103 passed；git diff --check 通过。

TEST-010 Conversation Analysis Foundation
Branch：test-010-conversation-analysis
API：GET /api/v1/conversations/{conversation_id}/analysis/context
最终服务器验证：专项 9 passed；全量 112 passed。

TEST-011 Evidence
Branch：test-011-evidence
API：GET /api/v1/conversations/{conversation_id}/analysis/evidence
目标：为 Fact / Inference 提供可追溯 Evidence；只引用已有 Message / Interaction，不自行创造事实。
最终服务器验证：专项 11 passed；全量 123 passed。

TEST-012 Person Profile
Branch：test-012-person-profile
API：GET /api/v1/persons/{person_id}/profile
目标：建立人物档案的只读聚合入口。
最终服务器验证：专项 8 passed；全量 131 passed。

TEST-013 Relationship State Analysis
Branch：test-013-relationship-state-analysis
API：GET /api/v1/persons/{person_id}/relationship-analysis/state
目标：建立关系状态分析的稳定输入与输出边界。
最终服务器验证：专项 10 passed；全量 141 passed。

---

## 6. TEST-014 Recommendation Foundation

Branch：test-014-recommendation-foundation
状态：VERIFIED
API：GET /api/v1/persons/{person_id}/recommendation-analysis/context

目标：建立建议输出的稳定契约与证据边界。

核心边界：
- Person / Relationship / current_state 聚合
- Evidence / facts / inferences / unknowns / recommendations
- user_id isolation
- person_id isolation
- relationship ownership boundary
- deterministic ordering
- read-only behavior
- locked response shape
- 不接真实 LLM
- 不自动发送消息
- 不直接修改 Relationship

最终服务器验证：专项 9 passed；全量 150 passed。

---

## 7. TEST-015 Strategic Reply Foundation

Branch：test-015-strategic-reply-foundation
状态：VERIFIED
API：GET /api/v1/persons/{person_id}/strategic-reply/context

目标：建立策略回复输入契约，同时严格保持分析、生成和执行分离。

reply_constraints：
- must_be_evidence_backed=true
- must_preserve_unknowns=true
- must_not_auto_send=true
- must_not_change_relationship=true

最终服务器验证：专项 9 passed；全量 159 passed。

---

## 8. TEST-016 Action Plan Foundation

Branch：test-016-action-plan-foundation
状态：VERIFIED
API：GET /api/v1/persons/{person_id}/action-plan/context

目标：建立行动计划输入契约，但不自行创造行动、不执行行动。

最终服务器验证：专项 7 passed；全量 166 passed。

---

## 9. TEST-017 Action Plan Synthesis

Branch：test-017-action-plan-synthesis
状态：VERIFIED

目标：把已经存在的 Recommendation 转换为结构化 Action Plan Proposal，但只允许“明确行动 + 明确证据引用”的 Recommendation 被提升为行动计划。

核心实现：
- deterministic ActionPlanService.build_action_plan()
- 非空 action
- 非空 evidence_source_ids
- Evidence source 必须真实存在
- 保持 Recommendation 原始顺序
- status=proposed
- requires_user_confirmation=true
- 保留 priority / time_horizon
- 不自动执行

最终服务器验证：TEST-017 专项 11 passed；全量 170 passed。

验收结论：TEST-017 Action Plan Synthesis VERIFIED。

---

## 10. TEST-018 Strategic Reply Synthesis

Branch：test-018-strategic-reply-synthesis
状态：IN PROGRESS

目标：在 Strategic Reply Foundation 之上，把“已经明确存在的、证据支持的回复候选”提升为确定性的 draft；只允许 Recommendation 明确提供 reply 且引用真实 Evidence 时生成 draft，不自行编造回复。

第一阶段实现：
- deterministic StrategicReplyService.build_draft()
- 仅接受非空 reply
- 必须包含非空 evidence_source_ids
- 每个 evidence source id 必须真实存在于当前上下文 evidence
- 按 Recommendation 原始顺序选择第一个合法 draft
- 只做外层空白清理，不重写回复内容
- 没有合法、证据支持的 reply 时保持 draft=null
- 保留既有 reply_constraints
- 保持 user_id / person_id isolation
- 保持 read-only

第一阶段边界：不接真实 LLM，不生成无证据回复，不自动发送消息，不修改 Relationship，不新增 migration，不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

服务器验证待完成：TEST-018 专项 10 项测试；全量测试。

---

## 11. 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
