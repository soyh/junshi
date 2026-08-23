# Development Handover

更新时间：2026-08-24

当前阶段：TEST-015 Strategic reply foundation

当前状态：IMPLEMENTED — awaiting server verification

当前 Branch：test-015-strategic-reply-foundation

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

第一阶段仅引用已有 Message / Interaction，不自行创造事实；完成 user_id isolation、person / conversation 归属边界、deterministic ordering、deleted source reflection、read-only behavior。

最终服务器验证：TEST-011 专项 11 passed；全量 123 passed。

数据库变化：无新增 migration。

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

状态：IMPLEMENTED — awaiting server verification

Branch：test-015-strategic-reply-foundation

目标：在 Recommendation Foundation 之上建立“策略回复”的稳定输入契约，同时严格保持分析、生成和执行分离。

API：GET /api/v1/persons/{person_id}/strategic-reply/context

第一阶段实现：
- 复用 Recommendation Foundation 的 person / relationship / current_state
- 复用 evidence、facts、inferences、unknowns、recommendations
- 固化 reply_constraints
- 固化 draft=null，明确当前阶段不生成真实回复
- user_id isolation
- person_id isolation
- deterministic evidence ordering
- read-only behavior
- deleted evidence reflection
- missing person / missing relationship 404 boundary
- locked response shape

reply_constraints 当前固定为：
- must_be_evidence_backed=true
- must_preserve_unknowns=true
- must_not_auto_send=true
- must_not_change_relationship=true

第一阶段边界：不接真实 LLM，不生成真实回复，不自动发送消息，不修改 Relationship，不新增 migration，不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

验收前需要服务器执行：TEST-015 专项测试与全量 pytest。

---

## 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
