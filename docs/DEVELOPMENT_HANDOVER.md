# Development Handover

更新时间：2026-08-24

当前阶段：TEST-012 Person profile

当前状态：IN PROGRESS

当前 Branch：test-012-person-profile

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

状态：IN PROGRESS

Branch：test-012-person-profile

目标：建立人物档案的只读聚合入口，为后续人物画像和关系分析提供稳定输入边界。

当前第一阶段实现：
- Person profile response schema
- Person 基础档案
- Person 关联 Relationship 列表
- Relationship / Conversation / Interaction / Message 统计
- 最新 Interaction
- user_id isolation
- person_id isolation
- read-only behavior
- deterministic relationship ordering

API：GET /api/v1/persons/{person_id}/profile

边界：当前只读取已有持久化数据，不进行人物推断、不生成画像结论、不调用 LLM、不写入 profile analysis 结果、不新增 migration。

当前专项测试：服务器待执行。

下一步：服务器同步 test-012-person-profile 后执行 TEST-012 专项测试和全量 pytest；通过后继续收紧 Person profile 契约并最终验收。

---

## 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
