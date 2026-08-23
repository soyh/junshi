# AI Love Strategist Development Handover

更新时间：2026-08-23
当前阶段：TEST-027 完成
下一阶段：TEST-028 Person Timeline
项目目录：/opt/ai-love-strategist

---

## 1. 项目定位

项目名称：

AI Love Strategist

定位：

AI 恋爱军师 / AI Relationship Management & Dating Companion System。

项目不是简单聊天机器人，也不是单纯的回复话术生成器。

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

服务器：

Alibaba Cloud Linux 3.2104 LTS 64-bit

Python：

3.11.13

Node.js：

20.20.2

NPM：

10.8.2

项目目录：

/opt/ai-love-strategist

虚拟环境：

/opt/ai-love-strategist/.venv

激活方式：

source /opt/ai-love-strategist/.venv/bin/activate

数据库：

SQLite

数据库文件：

/opt/ai-love-strategist/data/app.sqlite3

FastAPI：

127.0.0.1:18080

禁止使用、修改、停止：

8899

原因：

服务器上已有其他服务占用 8899。

当前没有 Docker。

当前没有 Nginx。

当前没有域名。

第一阶段通过公网 IP 访问。

---

## 3. 当前技术架构

Backend：

Python 3.11
FastAPI
SQLite
Pydantic / pydantic-settings

Frontend：

React
TypeScript
Vite

当前重点开发区域：

backend/app

主要结构：

backend/app/api
backend/app/config
backend/app/core
backend/app/domain
backend/app/repositories
backend/app/schemas
backend/app/services

数据库迁移：

backend/migrations

测试：

backend/tests

---

## 4. 当前数据库迁移

目前存在：

001_initial.sql
002_interactions.sql
003_conversations_messages.sql

当前生产数据库：

/opt/ai-love-strategist/data/app.sqlite3

当前 schema_migrations：

001
002
003

当前数据库表：

users
persons
relationships
interactions
conversations
messages
schema_migrations

---

## 5. 已完成的核心功能

### Persons

已经实现人物对象 CRUD 和用户隔离。

### Relationships

已经实现关系记录 CRUD、人物归属检查以及相关边界处理。

### Interactions

已经实现：

创建互动
查询互动列表
按 person_id 筛选
查询单条互动
更新互动
删除互动
用户隔离
人物归属检查
关系归属检查
interaction type 校验
PATCH omitted / explicit null 语义

### Conversations

已经实现 conversations 基础 CRUD/API。

### Messages

已经实现 messages 基础 CRUD/API。

同时支持：

/messages

以及：

/conversations/{conversation_id}/messages

---

## 6. Migration 问题诊断结果

TEST-026 专门调查了此前 app.log 中大量出现：

Applying migration: 001
Applying migration: 002
Applying migration: 003

的问题。

最终结论：

不是 migration runner 的幂等性 Bug。

验证结果：

同一个数据库连续执行两次 run_migrations()：

第一次：
正常。

第二次：
不会重复应用。

schema_migrations 保持：

001
002
003

生产数据库也已经正确保存：

001
002
003

进一步测试 TestClient 使用不同临时数据库时：

test1.sqlite3
test2.sqlite3

两个数据库都会分别初始化：

001
002
003

因此之前日志中大量 migration 日志主要来自测试期间反复创建独立 SQLite 测试数据库。

TEST-026：

PASS

不需要修改 migration runner。

---

## 7. TEST-027

执行：

PYTHONPATH=backend pytest -q

结果：

51 passed in 6.44s

当前测试：

51 tests

通过：

51

失败：

0

当前 Git 工作区：

clean

---

## 8. 当前 Git 状态

当前分支：

test-008-person-timeline

当前 HEAD：

411ae05 feat: add conversations and messages

当前：

git status --short

无输出。

工作区干净。

注意：

虽然分支名称已经包含 person-timeline，但 Person Timeline 功能尚未正式开始开发。

---

## 9. 当前稳定基线

当前代码可以视为一个稳定开发基线。

基线：

Branch:
test-008-person-timeline

HEAD:
411ae05 feat: add conversations and messages

Tests:
51 passed

Working tree:
clean

Database:
SQLite

Migrations:
001 / 002 / 003

Backend:
FastAPI

Python:
3.11.13

Port:
18080

Forbidden:
8899

---

## 10. 下一阶段：TEST-028

下一阶段目标：

Person Timeline / Relationship Timeline

当前尚未开始正式实现。

TEST-028 需要首先设计，而不是直接写代码。

目标步骤：

1. 明确 Timeline 的领域模型
2. 明确 Interaction 如何进入 Timeline
3. 明确 Conversation 如何进入 Timeline
4. 明确 Message 如何进入 Timeline
5. 明确事件类型
6. 明确统一时间字段
7. 明确排序规则
8. 明确分页规则
9. 明确 user_id 隔离
10. 明确 person_id 隔离
11. 设计 repository
12. 设计 service
13. 设计 API
14. 编写测试
15. 执行全量 pytest
16. 检查 Git
17. commit

不要在 TEST-028 阶段提前进入 AI 分析、模型 Router、人物画像、记忆系统等高级模块。

---

## 11. 开发原则

不要随意改变现有架构。

优先采用：

Route
→ Service
→ Repository
→ SQLite

领域错误由 Service/Domain 层定义。

API 层负责将领域错误转换成 HTTP 状态码。

所有用户数据必须进行 user_id 隔离。

person、relationship、interaction、conversation、message 都不能发生跨用户访问。

API Key 不得明文保存。

系统不得自动向第三方发送消息。

不得使用 8899。

不要因为测试日志问题修改正常的 migration 幂等机制。

每完成一个明确阶段：

代码
→ 测试
→ Git status
→ Git commit
→ 更新交接文档

---


## 12. 新对话启动时的第一任务

新对话不要重新从项目零开始。

首先确认：

当前项目目录：

/opt/ai-love-strategist

当前分支：

test-008-person-timeline

当前 HEAD：

a671cfb

当前测试基线：

59 passed

然后读取：

docs/DEVELOPMENT_HANDOVER.md

再根据当前 TEST 阶段继续开发。

---

## 13. 当前项目状态总结

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
TEST-028 / Person Timeline
TEST-008 / Person Timeline

当前：

Branch：

test-008-person-timeline

HEAD：

a671cfb

Tests：

59 passed

Timeline tests：

8 passed

Git：

clean

TEST-008：

VERIFIED

已完成：

Person Timeline

包含：

Interaction
Conversation
Message
Pagination
Ordering
Person isolation
User isolation
Message → Conversation → Person mapping
Deleted message reflection

未完成：

Text Import
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

当前下一阶段：

TEST-009 Text Import

下一 Branch：

test-009-text-import
