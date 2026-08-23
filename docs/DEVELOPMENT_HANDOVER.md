# Development Handover

更新时间：2026-08-23

当前阶段：TEST-011 Evidence

当前状态：IN PROGRESS

当前 Branch：test-011-evidence

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

验收结果：
- Conversation Analysis 输入模型
- 分析上下文组装
- Message / Conversation / Person 关系映射
- user_id / person_id 隔离
- Fact / Inference / Unknown / Recommendation 四类信息边界
- Route → Service → Repository 层边界
- 稳定顶层响应契约
- 空会话处理
- 消息确定性排序
- 删除消息反映
- 分析上下文不写入分析结果

API：GET /api/v1/conversations/{conversation_id}/analysis/context

当前上下文结构：conversation、person、messages、facts、inferences、unknowns、recommendations。

边界规则：当前阶段只组装已有持久化事实，不进行推断，不生成未知事实，不生成推荐，不调用模型；facts / inferences / unknowns / recommendations 均为空列表。

最终服务器验证：TEST-010 专项 9 passed；全量 112 passed。

数据库变化：无新增 migration。

验收结论：TEST-010 Conversation Analysis Foundation VERIFIED。

---

## TEST-011

Evidence

状态：IN PROGRESS

Branch：test-011-evidence

目标：建立分析事实的证据层，使后续 Fact / Inference 能够引用明确、可追溯的原始数据来源。

当前第一阶段实现：
- Evidence response schema
- Message evidence
- Person-scoped Interaction evidence
- source_id / source_type / occurred_at / content / metadata
- user_id isolation
- conversation → person 归属边界
- deterministic ordering
- deleted source reflection
- read-only behavior，无分析结果持久化

API：GET /api/v1/conversations/{conversation_id}/analysis/evidence

Evidence 仅引用已有 Message / Interaction，不自行创造事实。

暂不接真实 LLM、Model Router、AI Provider；不生成推断、不生成推荐、不进入 Memory System。

服务器验证结果：TEST-011 专项 9 passed；全量 121 passed。

已追加边界测试：
- 排除同一 user 下其他 person 的 Interaction
- 同时覆盖 user / person 两种 Message sender_type

数据库变化：无新增 migration。

下一步：服务器同步最新 test-011-evidence 后执行新增专项测试；通过后 TEST-011 可进入最终验收收尾。

---

## 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
