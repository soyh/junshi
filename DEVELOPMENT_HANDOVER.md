# AI Love Strategist Development Handover

更新时间：2026-08-24
当前阶段：TEST-014 Recommendation foundation
当前状态：VERIFIED
下一阶段：Strategic reply foundation
项目目录：/opt/ai-love-strategist

---

## 1. 项目定位

项目名称：AI Love Strategist

定位：AI 恋爱军师 / AI Relationship Management & Dating Companion System。

最终目标：用户添加一个关系对象后，可以持续导入聊天记录和互动数据，由系统建立人物画像、关系状态、历史记忆和行动计划，并根据后续反馈持续更新。

核心闭环：
添加对象 → 建立人物档案 → 导入聊天/互动 → 分析 → 建立画像 → 判断关系状态 → 生成策略回复 → 用户执行 → 反馈 → 更新记忆 → 长期关系跟踪

系统不得自动联系第三方。每个人物必须保持独立档案和数据隔离。

---

## 2. 服务器环境

服务器：Alibaba Cloud Linux 3.2104 LTS 64-bit
Python：3.11.13
Node.js：20.20.2
NPM：10.8.2
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

## 4. 已完成核心功能

Persons
Relationships
Interactions
Conversations
Messages
Person Timeline
Text Import
Conversation Analysis Foundation
Evidence
Person Profile
Relationship State Analysis
Recommendation Foundation

---

## 5. TEST-008

Person Timeline — VERIFIED

Branch：test-008-person-timeline

---

## 6. TEST-009

Text Import — VERIFIED

Branch：test-009-text-import

最终验证 Commit：a2059a6 test: verify text import rollback atomicity
最终测试：Text Import 专项 44 passed；全量 103 passed；git diff --check 通过。
数据库变化：无新增 migration。架构变化：无。

---

## 7. TEST-010

Conversation Analysis Foundation — VERIFIED

Branch：test-010-conversation-analysis

API：GET /api/v1/conversations/{conversation_id}/analysis/context
最终服务器验证：TEST-010 专项 9 passed；全量 112 passed。
数据库变化：无新增 migration。

---

## 8. TEST-011

Evidence — VERIFIED

Branch：test-011-evidence

API：GET /api/v1/conversations/{conversation_id}/analysis/evidence
第一阶段仅引用已有 Message / Interaction，不自行创造事实；完成 user_id isolation、person / conversation 归属边界、deterministic ordering、deleted source reflection、read-only behavior。
最终服务器验证：TEST-011 专项 11 passed；全量 123 passed。
数据库变化：无新增 migration。

---

## 9. TEST-012

Person Profile — VERIFIED

Branch：test-012-person-profile

API：GET /api/v1/persons/{person_id}/profile
目标：建立人物档案的只读聚合入口，为后续人物画像和关系分析提供稳定输入边界。
最终服务器验证：TEST-012 专项 8 passed；全量 131 passed。
数据库变化：无新增 migration。

---

## 10. TEST-013

Relationship State Analysis — VERIFIED

Branch：test-013-relationship-state-analysis

API：GET /api/v1/persons/{person_id}/relationship-analysis/state
目标：在 Person profile、Timeline、Conversation Analysis Context、Evidence 基础上建立关系状态分析的稳定输入与输出边界。
最终服务器验证：TEST-013 专项 10 passed；全量 141 passed。
数据库变化：无新增 migration。

---

## 11. TEST-014

Recommendation Foundation — VERIFIED

Branch：test-014-recommendation-foundation

API：GET /api/v1/persons/{person_id}/recommendation

目标：在现有 Person profile、Timeline、Conversation Analysis Context、Evidence、Relationship state analysis 之上，建立建议输出的稳定契约与证据边界。

第一阶段实现：
- Recommendation foundation response schema
- Person / Relationship / Relationship state context aggregation
- Evidence-backed analysis context boundary
- facts / inferences / unknowns / recommendations analysis buckets
- user_id isolation
- person_id isolation
- relationship ownership boundary
- deterministic ordering
- read-only behavior
- locked response shape

第一阶段边界：只允许基于已有事实、Evidence 和已确认关系状态形成结构化建议输入；当前不生成未经证据支持的分析内容，不接真实 LLM，不自动发送消息，不直接修改 Relationship，不新增 migration，不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

最终服务器验证：TEST-014 专项 9 passed；全量 150 passed。

验收结论：TEST-014 Recommendation Foundation VERIFIED。

---

## 12. 下一阶段

Strategic reply foundation。

目标：在 Recommendation Foundation 之上建立“策略回复”输入与输出边界，但仍保持分析与执行分离。

原则：
- 先建立稳定的策略回复契约
- 必须能够追溯到已有事实 / Evidence / Recommendation context
- 不直接发送消息
- 不接真实 LLM，除非后续阶段明确进入 Model Router / AI provider integration
- 不修改既有 Relationship 状态
- 不新增 migration，除非数据持久化确有必要并单独评估

---

## 13. 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
