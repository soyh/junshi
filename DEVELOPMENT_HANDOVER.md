# AI Love Strategist Development Handover

更新时间：2026-08-23
当前阶段：TEST-009 Text Import
当前状态：VERIFIED
下一阶段：TEST-010 Conversation Analysis Foundation
项目目录：/opt/ai-love-strategist

---

## 1. 项目定位

项目名称：

AI Love Strategist

定位：

AI 恋爱军师 / AI Relationship Management & Dating Companion System。

最终目标：

用户添加一个关系对象后，可以持续导入聊天记录和互动数据，由系统建立人物画像、关系状态、历史记忆和行动计划，并根据后续反馈持续更新。

核心闭环：

添加对象
→ 建立人物档案
→ 导入聊天/互动
→ 分析
→ 建立画像
→ 判断关系状态
→ 生成策略回复
→ 用户执行
→ 反馈
→ 更新记忆
→ 长期关系跟踪

系统不得自动联系第三方。
每个人物必须保持独立档案和数据隔离。

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

当前没有 Docker。
当前没有 Nginx。

---

## 3. 当前技术架构

Backend：Python 3.11 / FastAPI / SQLite / Pydantic / pydantic-settings
Frontend：React / TypeScript / Vite

主要结构：

backend/app/api
backend/app/config
backend/app/core
backend/app/domain
backend/app/repositories
backend/app/schemas
backend/app/services
backend/migrations
backend/tests

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

已完成的基础能力包括：

- user_id isolation
- person_id isolation
- relationship / person 归属检查
- conversations / messages CRUD
- Person Timeline
- Text Import

---

## 5. TEST-008

Person Timeline

状态：VERIFIED

Branch：

test-008-person-timeline

已完成：

- Interaction timeline events
- Conversation creation events
- Message timeline events
- Message → Conversation → Person 归属
- user_id isolation
- person_id isolation
- pagination
- deterministic ordering
- deleted message reflection
- SQLite UNION ALL ordering 修复
- Conversation creation event ordering 修复

无新增 migration。

---

## 6. TEST-009

Text Import

状态：VERIFIED

Branch：

test-009-text-import

基础实现 Commit：

f7b2455 feat: add TEST-009 text import foundation

最终验证 Commit：

a2059a6 test: verify text import rollback atomicity

目标：

文本聊天记录导入。

流程：

Text
→ Parse
→ Message Candidates
→ Validation
→ Conversation
→ Message

已完成：

- 固定文本导入格式：timestamp | sender_type | content
- 空行跳过
- Message Candidate 生成
- line_number 保留
- sender_type validation
- content validation
- ISO-8601 timestamp validation
- Zulu timestamp 支持
- 时间顺序 validation
- 相同 timestamp 允许
- 等价 timezone instant validation
- 相同 instant 保持原始输入顺序
- Person existence validation
- user_id isolation
- Conversation 自动创建
- Message 自动创建
- imported_count 返回
- message_ids 返回
- candidates 返回
- message_ids 与 persisted messages 顺序一致
- message_ids 与 candidates 顺序一致
- 导入失败时不创建 Conversation
- Message 创建过程中发生异常时整个导入事务 rollback
- rollback 后不残留已创建 Message

API：

POST /api/v1/text-imports

最终测试：

Text Import 专项：44 passed
全量：103 passed

git diff --check：通过

数据库变化：无新增 migration。
架构变化：无。

明确边界：

- 不接 OCR
- 不接 screenshot import
- 不接外部聊天平台 integration
- 不接 LLM
- 不做自动发送
- 不进入 Conversation Analysis

验收结论：

TEST-009 Text Import VERIFIED。

---

## 7. 当前 Git 状态

代码分支：

test-009-text-import

最新代码 Commit：

a2059a6 test: verify text import rollback atomicity

随后 handover 文档已通过 GitHub 更新，作为文档同步提交。

本地开发环境在 TEST-009 验收时：

Working tree：clean

---

## 8. 当前稳定测试基线

TEST-009 专项：

44 passed

全量：

103 passed

验证命令：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q backend/tests/test_text_import.py backend/tests/test_text_import_contract.py

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

---

## 9. 下一阶段：TEST-010

Conversation Analysis Foundation

Branch：

test-010-conversation-analysis

状态：NOT STARTED

目标：

建立分析输入上下文。

暂不接真实 LLM。

第一阶段目标：

1. 定义 Conversation Analysis 输入模型
2. 设计分析上下文组装
3. 建立 Message / Conversation / Person 关系映射
4. 保证 user_id / person_id 隔离
5. 明确 Fact / Inference / Unknown / Recommendation 四类信息边界
6. 设计 Route → Service → Repository 层边界
7. 编写测试契约
8. 执行全量 pytest
9. Git status / commit
10. 更新 handover

明确禁止：

- 不接真实 LLM
- 不接 Model Router
- 不接 AI Provider
- 不生成真实策略回复
- 不自动发送消息
- 不提前进入 Memory System

TEST-010 的第一步必须是设计契约，而不是直接接入模型。

---

## 10. 开发原则

不要随意改变现有架构。

优先采用：

Route
→ Service
→ Repository
→ SQLite

领域错误由 Service / Domain 层定义。
API 层负责将领域错误转换成 HTTP 状态码。
所有用户数据必须进行 user_id 隔离。
person、relationship、interaction、conversation、message 都不能发生跨用户访问。
API Key 不得明文保存。
系统不得自动向第三方发送消息。
不得使用 8899。
MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

每完成一个明确阶段：

代码
→ 测试
→ Git status
→ Git commit
→ 更新交接文档

---

## 11. 新对话启动时的第一任务

新对话不要重新从项目零开始。

首先确认：

当前项目目录：
/opt/ai-love-strategist

然后读取：

DEVELOPMENT_HANDOVER.md
docs/DEVELOPMENT_HANDOVER.md

确认当前 Branch、HEAD、测试基线和当前 TEST 阶段后，再继续开发。

---

## 12. 当前项目状态总结

已完成：

Persons
Relationships
Interactions
Conversations
Messages
Migration 001
Migration 002
Migration 003
TEST-026
TEST-027
TEST-008 / Person Timeline
TEST-009 / Text Import

当前：

TEST-009 VERIFIED

Branch：

test-009-text-import

Latest code commit：

a2059a6

Tests：

103 passed

Text Import tests：

44 passed

Working tree（本次 TEST-009 验收时）：

clean

未完成：

Conversation Analysis
Evidence
Person profile
Relationship state analysis
Strategic reply
Action plan
Feedback
Memory system
Model Router
AI provider integration
Long-term relationship tracking

下一阶段：

TEST-010 Conversation Analysis Foundation

下一 Branch：

test-010-conversation-analysis
