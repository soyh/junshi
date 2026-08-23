# Development Handover

更新时间：2026-08-24

当前阶段：TEST-012 Person profile

当前状态：VERIFIED

当前 Branch：test-012-person-profile

最终验证 Commit：fe0c58d test: align person profile ordering with relationship invariant

最终服务器验证：TEST-012 专项 8 passed；全量 131 passed。

验收结论：TEST-012 Person profile VERIFIED。

下一阶段：TEST-013 Relationship state analysis

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

状态：VERIFIED

Branch：test-012-person-profile

目标：建立人物档案的只读聚合入口，为后续人物画像和关系分析提供稳定输入边界。

第一阶段实现：
- Person profile response schema
- Person 基础档案
- Person 关联 Relationship 列表
- Relationship / Conversation / Interaction / Message 统计
- 最新 Interaction
- user_id isolation
- person_id isolation
- read-only behavior
- deterministic relationship ordering
- deterministic latest interaction selection by occurred_at
- missing person 404 boundary

API：GET /api/v1/persons/{person_id}/profile

边界：当前只读取已有持久化数据，不进行人物推断、不生成画像结论、不调用 LLM、不写入 profile analysis 结果、不新增 migration。

最终服务器验证：TEST-012 专项 8 passed；全量 131 passed。

验收结论：TEST-012 Person profile VERIFIED。

---

## TEST-013

Relationship state analysis

状态：PLANNED

目标：在已有 Person profile、Timeline、Conversation Analysis Context、Evidence 基础上，建立关系状态分析的稳定输入与输出边界。

第一阶段原则：只基于已有持久化事实和 Evidence 进行状态分析契约建设；不接真实 LLM，不自动生成未经证据支持的事实，不自动发送消息，不直接修改 Relationship 状态。

下一步：建立 Relationship state analysis schema / service / repository 或最小必要读取层，并补齐 user_id、person_id、relationship 归属、deterministic ordering、read-only 与 Fact / Inference / Unknown / Recommendation 边界测试。

---

## 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
