# AI Love Strategist Development Handover

更新时间：2026-08-23
当前阶段：TEST-011 Evidence
当前状态：IN PROGRESS
下一阶段：Person profile
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

已完成的基础能力包括：user_id isolation、person_id isolation、relationship / person 归属检查、conversations / messages CRUD、Person Timeline、Text Import、Conversation Analysis input context。

---

## 5. TEST-008

Person Timeline

状态：VERIFIED

Branch：test-008-person-timeline

已完成：Interaction timeline events、Conversation creation events、Message timeline events、Message → Conversation → Person 归属、user_id isolation、person_id isolation、pagination、deterministic ordering、deleted message reflection、SQLite UNION ALL ordering 修复、Conversation creation event ordering 修复。

无新增 migration。

---

## 6. TEST-009

Text Import

状态：VERIFIED

Branch：test-009-text-import

最终验证 Commit：a2059a6 test: verify text import rollback atomicity

最终测试：Text Import 专项 44 passed；全量 103 passed；git diff --check 通过。

数据库变化：无新增 migration。架构变化：无。

验收结论：TEST-009 Text Import VERIFIED。

---

## 7. TEST-010

Conversation Analysis Foundation

状态：VERIFIED

Branch：test-010-conversation-analysis

目标：建立分析输入上下文。

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

当前返回结构：conversation、person、messages、facts、inferences、unknowns、recommendations。

当前阶段边界：只读取和组装已有持久化数据；不进行推断、不生成未知事实、不生成推荐、不调用模型。四类分析字段均为空列表，作为后续分析层的明确契约边界。

最终服务器验证：TEST-010 专项 9 passed；全量 112 passed。

数据库变化：无新增 migration。

验收结论：TEST-010 Conversation Analysis Foundation VERIFIED。

---

## 8. TEST-011

Evidence

状态：IN PROGRESS

Branch：test-011-evidence

目标：建立分析事实的证据层，使后续 Fact / Inference 能够引用明确、可追溯的原始数据来源。

设计原则：Evidence 必须指向已有持久化事实，不自行创造事实。第一阶段只支持已有 Message / Interaction 作为证据来源。Evidence 必须进行 user_id isolation，并保持 person / conversation 归属边界。

暂不接真实 LLM。暂不生成推断。暂不生成推荐。暂不进入 Memory System。

数据库变化：优先无新增 migration；若实现证据持久化确有必要，再单独评估 migration，不提前扩大架构。

下一步：服务器同步 test-011-evidence 后执行专项测试和全量 pytest；通过后继续 TEST-011 契约与边界验收。

---

## 9. 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

领域错误由 Service / Domain 层定义。API 层负责将领域错误转换成 HTTP 状态码。所有用户数据必须进行 user_id 隔离。person、relationship、interaction、conversation、message 都不能发生跨用户访问。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。

---

## 10. 新对话启动时的第一任务

首先确认当前项目目录：/opt/ai-love-strategist

然后读取：DEVELOPMENT_HANDOVER.md、docs/DEVELOPMENT_HANDOVER.md

确认当前 Branch、HEAD、测试基线和当前 TEST 阶段后，再继续开发。

---

## 11. 当前项目状态总结

已完成：Persons、Relationships、Interactions、Conversations、Messages、Migration 001、Migration 002、Migration 003、TEST-026、TEST-027、TEST-008 / Person Timeline、TEST-009 / Text Import、TEST-010 / Conversation Analysis Foundation

当前：TEST-011 Evidence

Branch：test-011-evidence

数据库：SQLite
Migrations：001 / 002 / 003

下一验收目标：TEST-011 Evidence

后续：Person profile、Relationship state analysis、Strategic reply、Action plan、Feedback、Memory system、Model Router、AI provider integration、Long-term relationship tracking
