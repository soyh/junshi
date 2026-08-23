# AI Love Strategist — Development Handover & Roadmap

## 1. 文档目的

本文件是 AI Love Strategist 项目的长期开发交接文档。

它不是普通 README，也不是产品需求文档。

它的主要用途是：

1. 记录当前真实开发阶段。
2. 固定后续开发阶段。
3. 固定 Git branch 命名规则。
4. 固定 commit / verification tag 规则。
5. 固定每个阶段的开发流程。
6. 固定测试与验收标准。
7. 为新的 ChatGPT 对话提供完整接管入口。
8. 防止更换对话后重复分析项目或错误修改已经验证的代码。

任何新的开发对话，都必须优先阅读本文件。

---

# 2. 项目基本信息

项目名称：

AI Love Strategist

项目目录：

/opt/ai-love-strategist

Backend：

Python 3.11
FastAPI
SQLite
Pydantic 2.x

Frontend：

React
TypeScript
Vite
React Router
TanStack Query
Zustand
Tailwind CSS

当前第一阶段部署方式：

FastAPI：

127.0.0.1:18080

公网访问阶段：

http://公网IP:18080

重要：

服务器现有服务：

0.0.0.0:8899

绝对禁止：

- 占用 8899
- 停止 8899
- 修改 8899 服务
- 修改已有服务配置

第一阶段：

- 不使用 Docker
- 不使用 PostgreSQL
- 不使用 Redis
- 不使用 Elasticsearch
- 不使用独立 Vector DB
- 不安装 Nginx，除非后续阶段明确进入生产反向代理阶段

---

# 3. 产品核心原则

## 3.1 用户拥有最终决定权

AI 提供：

- 判断
- 依据
- 风险
- 反对理由
- 不确定性
- 建议

但最终行动由用户决定。

---

## 3.2 Fact / Inference / Unknown / Recommendation 必须分离

AI 不允许把推测伪装成事实。

必须区分：

Fact：

事实。

Inference：

推测。

Unknown：

未知。

Recommendation：

建议。

---

## 3.3 AI 不直接执行社交行为

绝对禁止：

- 自动发送微信消息
- 自动联系异性
- 自动执行外部社交行为

允许：

- 分析聊天
- 提取记忆
- 更新建议状态
- 生成回复
- 生成行动计划
- 通知用户

最终联系行为必须由用户执行。

---

## 3.4 多对象数据必须严格隔离

任何相关 AI Task / Service / Repository 操作都必须明确处理：

user_id
person_id
relationship_id

禁止不同 Person 之间串档。

数据隔离优先级高于功能数量。

---

## 3.5 AI 不直接修改核心关系状态

正确流程：

AI Analysis
→ Proposed State Change
→ Validation
→ Persist

AI 的分析结果不能绕过验证直接修改核心关系状态。

---

## 3.6 Memory 不是 Prompt 历史总结

Memory 必须是独立工程模块。

长期目标：

Conversation
→ Evidence
→ Candidate Memory
→ Validation
→ Confidence
→ Memory
→ Memory History
→ Retrieval

冲突信息不能简单覆盖旧信息。

---

# 4. Git 开发规则

## 4.1 每个开发阶段使用独立 branch

格式：

test-NNN-short-description

例如：

test-007-conversations-messages

---

## 4.2 每个阶段必须从已验证基线开始

开始阶段前：

git status --short

必须确认工作区干净。

然后：

git log -1 --oneline --decorate

记录基线 commit。

然后：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

必须确认基线测试通过。

---

## 4.3 不在主分支直接开发

开发阶段使用：

test-NNN-...

main 只作为稳定基线。

---

## 4.4 Commit 规则

Commit 应说明实际完成的事情。

推荐：

TEST-007: add conversation and message API

或者：

fix: preserve omitted interaction patch fields

不要使用：

update
test
fix stuff
changes

这种无法表达实际内容的 commit。

---

## 4.5 Verification Tag

一个阶段只有在测试和验收完成后才能建立：

TEST-NNN-VERIFIED

例如：

TEST-006-VERIFIED

Tag message：

TEST-006 verified: Interaction PATCH omitted/null semantics

Tag 表示：

该阶段已经验证完成，可以作为后续阶段稳定基线。

---

# 5. 每个阶段固定工作流程

每个 TEST 阶段必须遵循：

## Phase A — Baseline

1. 查看当前 branch。
2. 查看当前 commit。
3. 查看 worktree。
4. 运行完整测试。
5. 确认基线稳定。

---

## Phase B — Inspection

修改前先读取：

- 相关 migration
- schema
- repository
- service
- route
- tests
- 相关数据库结构

禁止在没有查看真实代码的情况下直接修改。

---

## Phase C — Design

明确：

- 数据结构
- 数据所有权
- user isolation
- person isolation
- relationship isolation
- API contract
- validation
- error handling
- migration strategy
- test strategy

---

## Phase D — Backup

修改关键文件前：

cp 原文件 /tmp/文件名.阶段.before

不要覆盖历史备份。

---

## Phase E — Implementation

按照：

Migration
→ Schema
→ Repository
→ Service
→ Route
→ Tests

逐层实现。

不能为了让测试通过而破坏数据库约束。

---

## Phase F — Verification

至少执行：

1. 新阶段测试。
2. 相关旧测试。
3. 全量 pytest。
4. 必要的数据库结构检查。
5. API smoke test。

---

## Phase G — Commit

测试全部通过后：

git status

git diff

确认修改范围。

然后 commit。

---

## Phase H — Verification Tag

确认 commit 后：

git tag -a TEST-NNN-VERIFIED ...

---

## Phase I — Handover

更新本文件：

- 当前完成阶段
- commit
- tag
- 测试结果
- 修改文件
- 下一阶段
- 下一分支
- 下一阶段启动命令

---

# 6. 当前阶段状态

## TEST-001

Person CRUD

状态：

VERIFIED

---

## TEST-002

Backend regression / foundation verification

Tag：

TEST-002-VERIFIED

状态：

VERIFIED

---

## TEST-003

Relationship boundary / isolation

Tag：

TEST-003-VERIFIED

状态：

VERIFIED

---

## TEST-004

Service foundation

状态：

已完成并作为后续 Interaction 开发基础。

---

## TEST-005

Interaction API

Branch：

test-005-interactions

Commit：

07ccf93

状态：

VERIFIED / 已作为 TEST-006 基线。

---

## TEST-006

Interaction PATCH omitted/null semantics

Branch：

test-005-interactions

Commit：

5155c54

Tag：

TEST-006-VERIFIED

状态：

VERIFIED

验证结果：

15 passed

核心内容：

JSON omitted field
→ Pydantic model_fields_set
→ UNSET
→ Service
→ Repository
→ 保留旧值

明确 null：

→ None
→ 按 schema / DB 约束处理

禁止回退 Repository 的 UNSET 设计。

---

# 7. 当前 TEST-007

## Branch

test-007-conversations-messages

## Baseline

5155c54

## Tag

TEST-006-VERIFIED

## 当前测试

15 passed

## 状态

NOT STARTED

---

# 8. TEST-007 — Conversations + Messages

目标：

建立真正的聊天数据模型。

不是简单增加一个 message 字段。

目标结构：

User
|
Person
|
Relationship
|
Conversation
|
Message

---

## 8.1 Conversation

Conversation 表示一段具有上下文边界的聊天。

必须考虑：

id
user_id
person_id
relationship_id
title / name
started_at
ended_at
created_at
updated_at

最终实际字段必须根据当前数据库设计确认，不允许未经检查直接复制。

---

## 8.2 Message

Message 表示 Conversation 中的一条消息。

必须考虑：

id
conversation_id
sender
content
occurred_at
created_at
updated_at

还必须为未来的：

- screenshot import
- text import
- OCR
- message source
- evidence
- analysis

预留合理的数据边界。

---

## 8.3 数据隔离

任何 Conversation 查询必须验证：

user_id

任何 Message 查询必须通过 Conversation 验证：

user_id

禁止仅凭 message_id 查询而绕过用户边界。

---

## 8.4 TEST-007 禁止事项

本阶段不要同时实现：

- AI Analysis
- Memory
- Knowledge
- Model Provider
- Model Router
- Strategy
- Reply Generation
- Action Plan
- Screenshot OCR

TEST-007 只建立：

Conversation
+
Message

以及必要的基础测试。

---

# 9. 后续开发路线

## TEST-007

Conversations + Messages

Branch：

test-007-conversations-messages

---

## TEST-008

Person Timeline

状态：

VERIFIED

Branch：

test-008-person-timeline

Commit：

a671cfb fix: keep conversation creation events after activity

目标：

建立 Person Timeline，将：

- Interaction
- Conversation
- Message

统一聚合为 Person 级时间线。

完成内容：

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

修改文件：

- backend/app/repositories/timeline.py
- backend/app/services/timeline.py
- backend/app/api/routes/timeline.py
- backend/app/schemas/timeline.py
- backend/app/api/router.py
- backend/tests/test_timeline.py

数据库变化：

无新增 migration。

API变化：

新增：

GET /api/v1/persons/{person_id}/timeline

测试：

Timeline：

8 passed

全量：

59 passed

验证：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

结果：

59 passed

已知问题：

无。

下一阶段：

TEST-009

Branch：

test-009-text-import

## TEST-009

Text Import

Branch：

test-009-text-import

目标：

文本聊天记录导入。

流程：

Text
→ Parse
→ Message Candidates
→ Validation
→ Conversation
→ Message

---

## TEST-010

Conversation Analysis Foundation

Branch：

test-010-conversation-analysis

目标：

建立分析输入上下文。

暂不接真实 LLM。

---

## TEST-011

Evidence

Branch：

test-011-evidence

目标：

建立：

Evidence
Analysis
Message

之间的可追溯关系。

---

## TEST-012

Basic Analysis

Branch：

test-012-basic-analysis

目标：

建立：

Fact
Inference
Unknown
Recommendation

分析结果结构。

AI 不直接修改 Relationship。

---

## TEST-013

Model Provider

Branch：

test-013-model-provider

目标：

建立：

Provider
Model
Credential

基础结构。

API Key 不允许明文存 SQLite。

---

## TEST-014

Model Router

Branch：

test-014-model-router

目标：

实现：

Task-specific model
→ Provider Adapter
→ Model

优先级：

1. 单次任务指定
2. Task 类型配置
3. System default
4. Auto route

---

## TEST-015

Basic Reply

Branch：

test-015-basic-reply

目标：

根据：

Relationship State
+
Analysis
+
Conversation
+
Strategy Context

生成战略性回复。

---

## TEST-016

Task Orchestrator

Branch：

test-016-task-orchestrator

目标：

统一：

API
→ Service
→ Task
→ Context
→ Knowledge
→ Model
→ Validator
→ Result

---

## TEST-017

Memory Foundation

Branch：

test-017-memory-foundation

目标：

Candidate Memory
→ Evidence
→ Validation
→ Confidence
→ Memory

---

## TEST-018

Memory History / Conflict

Branch：

test-018-memory-history

目标：

支持：

valid_from
valid_until

以及：

旧信息
+
新信息
→ 历史保留
→ 当前状态更新

---

## TEST-019

Knowledge / FTS5

Branch：

test-019-knowledge-fts

目标：

SQLite + FTS5。

暂不引入独立 Vector DB。

---

## TEST-020

Strategy

Branch：

test-020-strategy

目标：

主动策略 + 条件分支。

例如：

主动延长话题
→ 推进

正常回复
→ 保持

明显回避
→ 暂停

明确拒绝
→ 停止推进

---

## TEST-021

Action Plan

Branch：

test-021-action-plan

目标：

长期目标
+
当前目标
+
Actions

---

## TEST-022

Feedback

Branch：

test-022-feedback

目标：

Action
→ User Feedback
→ Relationship Update Proposal
→ Validation
→ Persist

---

## TEST-023

Screenshot Import

Branch：

test-023-screenshot-import

目标：

Image
→ Vision
→ OCR / Structure
→ Message Candidates
→ Verification
→ Persist

---

## TEST-024

Vision / OCR Verification

Branch：

test-024-vision-verification

目标：

UNVERIFIED
→ Human Verification
→ VERIFIED

---

## TEST-025

Frontend Foundation

Branch：

test-025-frontend-foundation

目标：

React
+
TypeScript
+
Vite
+
Router
+
Query
+
Zustand
+
Tailwind

---

## TEST-026

Frontend Person / Relationship

Branch：

test-026-frontend-person-relationship

---

## TEST-027

Conversation UI

Branch：

test-027-frontend-conversation

---

## TEST-028

Analysis UI

Branch：

test-028-frontend-analysis

---

## TEST-029

Reply UI

Branch：

test-029-frontend-reply

---

## TEST-030

Memory UI

Branch：

test-030-frontend-memory

---

## TEST-031

Model Settings

Branch：

test-031-frontend-model-settings

---

## TEST-032

Dashboard

Branch：

test-032-dashboard

---

## TEST-033

Notification

Branch：

test-033-notification

---

## TEST-034

End-to-End MVP

Branch：

test-034-mvp-e2e

目标：

完整闭环：

Person
→ Relationship
→ Conversation
→ Message
→ Analysis
→ Strategy
→ Reply
→ User Feedback
→ Memory

---

# 10. 阶段边界规则

每个 TEST 阶段必须：

1. 只解决自己的目标。
2. 不顺手重构无关模块。
3. 不删除已有功能。
4. 不修改已经 VERIFIED 阶段的行为，除非新阶段明确需要。
5. 不修改测试来掩盖实现错误。
6. 不降低数据库约束。
7. 不删除 user isolation。
8. 不允许跨 Person 串档。
9. 不把复杂业务塞进 main.py。
10. 不提前实现后续阶段功能。

如果发现架构问题：

先记录。

再判断是否属于当前阶段。

不是当前阶段的问题，不擅自扩大修改范围。

---

# 11. 测试规则

任何阶段完成前必须：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

必须全量通过。

测试数量增加是正常的。

完成阶段时必须记录：

Before：

X passed

After：

Y passed

并说明：

新增测试：

N

---

# 12. API 验证规则

API 阶段至少验证：

正常请求

非法请求

不存在资源

跨用户访问

资源隔离

PATCH omitted/null 语义（如果相关）

数据库约束

---

# 13. 数据库 Migration 规则

Migration 必须：

- 顺序编号
- 一次 migration 解决一个明确阶段
- 不修改历史 migration
- 不删除历史 migration
- 不为了测试方便修改已经存在的 schema
- 新 schema 必须考虑 foreign key
- 必须考虑 ON DELETE 行为
- 必须建立必要 index

历史 migration：

001_initial.sql
002_interactions.sql

后续：

003_...
004_...

禁止重新编号。

---

# 14. 新对话接管规则

任何新 ChatGPT 对话接手项目时：

第一步：

阅读：

docs/DEVELOPMENT_HANDOVER.md

第二步：

执行：

cd /opt/ai-love-strategist
source .venv/bin/activate

git branch --show-current
git log -1 --oneline --decorate
git status --short

第三步：

执行：

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

第四步：

根据本文件确定当前 TEST 阶段。

第五步：

检查当前阶段相关代码。

第六步：

再进行修改。

禁止：

- 从产品需求重新开始
- 猜测项目状态
- 猜测数据库结构
- 根据旧聊天内容直接覆盖当前代码
- 未查看真实代码就修改
- 跳过 baseline test

---

# 15. 每次阶段结束必须更新的内容

完成 TEST-NNN 后，本文件必须增加：

## TEST-NNN

状态：

VERIFIED

Branch：

...

Commit：

...

Tag：

...

完成内容：

...

修改文件：

...

数据库变化：

...

API变化：

...

测试：

...

新增测试：

...

已知问题：

...

下一阶段：

TEST-NNN+1

下一 Branch：

...

---

# 16. 当前接管模板

新的 ChatGPT 对话可以直接使用：

---

继续 AI Love Strategist 项目。

请先读取：

docs/DEVELOPMENT_HANDOVER.md

当前不要从产品需求重新开始。

然后执行：

cd /opt/ai-love-strategist
source .venv/bin/activate

git branch --show-current
git log -1 --oneline --decorate
git status --short

PYTHONPATH=/opt/ai-love-strategist/backend python -m pytest -q

然后根据 DEVELOPMENT_HANDOVER.md 中的当前 TEST 阶段继续。

必须遵守：

1. 不修改 8899。
2. 不破坏已 VERIFIED 功能。
3. 不修改历史 migration。
4. 不删除测试。
5. 不修改测试来掩盖错误。
6. 不允许跨用户 / Person / Relationship 串档。
7. 不提前实现后续阶段。
8. 修改前先检查真实代码。
9. 每个阶段必须完整测试。
10. 完成后 commit + verification tag + 更新交接文档。

---

# 17. 当前项目接管状态

当前阶段：

TEST-007

当前 branch：

test-007-conversations-messages

当前基线：

5155c54

最近 VERIFIED：

TEST-006-VERIFIED

当前测试：

15 passed

当前工作区：

应保持 clean

下一步：

先检查 Conversation / Message 所需的实际架构。

不要直接修改代码。



================================================================================
CURRENT STAGE ADDENDUM — TEST-023 ~ TEST-025
Date: 2026-08-17
================================================================================

【阶段说明】

本阶段继续接手 conversations / messages 功能开发后的数据库、
migration、测试初始化及 Git 状态验证。

本阶段暂不修改业务逻辑。
当前重点转向 Migration 生命周期、测试 fixture、FastAPI lifespan
以及 SQLite 数据库路径/状态的一致性验证。


--------------------------------------------------------------------------------
TEST-023 — GIT / MIGRATION FILE STATUS
--------------------------------------------------------------------------------

执行目录：

/opt/ai-love-strategist

Git root 已确认：

/opt/ai-love-strategist


当前 Git 状态：

 M backend/app/api/router.py
 M backend/app/domain/errors.py
 M backend/tests/test_relationship_boundaries.py
?? backend/app/api/routes/conversations.py
?? backend/app/api/routes/messages.py
?? backend/app/repositories/conversation.py
?? backend/app/repositories/message.py
?? backend/app/schemas/conversation.py
?? backend/app/schemas/message.py
?? backend/app/services/conversation.py
?? backend/app/services/message.py
?? backend/migrations/003_conversations_messages.sql
?? backend/tests/test_conversation_service.py
?? backend/tests/test_conversations.py
?? backend/tests/test_database_integrity.py
?? backend/tests/test_message_service.py
?? backend/tests/test_messages.py


当前 Git 已跟踪的 migration 文件：

backend/app/core/migrations.py
backend/migrations/001_initial.sql
backend/migrations/002_interactions.sql


重要结论：

backend/migrations/003_conversations_messages.sql 已经存在于服务器，
并且已经实际被 migration runner 执行过。

但是目前尚未加入 Git tracking。

当前状态：

?? backend/migrations/003_conversations_messages.sql

后续确认问题并完成测试之前，不要急于 commit。


--------------------------------------------------------------------------------
TEST-023 — MIGRATION LOG OBSERVATION
--------------------------------------------------------------------------------

app.log 中发现异常高频的 migration 日志。

短时间内反复出现：

Applying migration: 001_initial.sql
Migration applied: 001_initial.sql
Applying migration: 002_interactions.sql
Migration applied: 002_interactions.sql
Applying migration: 003_conversations_messages.sql
Migration applied: 003_conversations_messages.sql

随后又重复执行 001 / 002 / 003。

日志时间集中在：

2026-08-17 22:48:56
2026-08-17 22:48:57
2026-08-17 22:48:58
2026-08-17 22:48:59
2026-08-17 22:49:00
2026-08-17 22:49:01

该现象需要进一步诊断。


--------------------------------------------------------------------------------
TEST-024 — MIGRATION IMPLEMENTATION
--------------------------------------------------------------------------------

当前 migration runner：

backend/app/core/migrations.py


当前实现核心逻辑：

1. 根据 backend/migrations 目录读取所有 .sql 文件。
2. 按文件名排序。
3. 使用文件名前缀作为 migration version。
4. 创建 schema_migrations 表。
5. 检查 version 是否已经存在。
6. 不存在时执行 SQL。
7. 执行成功后写入 schema_migrations。


migration version 规则：

001_initial.sql
    -> 001

002_interactions.sql
    -> 002

003_conversations_messages.sql
    -> 003


当前 schema_migrations：

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)


当前 migration runner 的设计理论上具备幂等性。

因此：

同一个数据库在第二次执行 run_migrations() 时，
如果 schema_migrations 正常持久化，
不应该再次执行已经存在的 migration。


--------------------------------------------------------------------------------
TEST-024 — MIGRATION REFERENCES
--------------------------------------------------------------------------------

当前 run_migrations() 的调用位置已确认：

backend/app/main.py
backend/tests/conftest.py


main.py：

FastAPI lifespan 启动时执行：

initialize_database()
run_migrations()
ensure_local_user()


tests/conftest.py：

测试 fixture 中执行：

initialize_database()
run_migrations()
ensure_local_user()

随后：

with TestClient(app)


因此当前存在明确的重复初始化路径：

测试 fixture
    ->
initialize_database()
    ->
run_migrations()
    ->
ensure_local_user()
    ->
TestClient(app)
    ->
FastAPI lifespan
    ->
initialize_database()
    ->
run_migrations()
    ->
ensure_local_user()


这说明测试过程中 run_migrations() 至少可能被调用两次。


--------------------------------------------------------------------------------
TEST-024 — APPLICATION INITIALIZATION
--------------------------------------------------------------------------------

当前 backend/app/main.py：

FastAPI 使用 lifespan。

启动流程：

initialize_database()
run_migrations()
ensure_local_user()

然后：

Application startup complete


关闭时：

Application shutdown complete


当前 main.py 存在模块级：

settings = get_settings()


该 settings 缓存行为在测试环境动态切换 DATABASE_PATH 时需要特别关注。


--------------------------------------------------------------------------------
TEST-025 — TEST FIXTURE
--------------------------------------------------------------------------------

当前 backend/tests/conftest.py：

测试使用 pytest tmp_path 创建独立 SQLite：

tmp_path / "test.sqlite3"


然后：

monkeypatch.setenv("DATABASE_PATH", str(database_path))

get_settings.cache_clear()

initialize_database()
run_migrations()
ensure_local_user()

with TestClient(app)


测试结束：

get_settings.cache_clear()


当前测试 fixture 的目的：

每个测试使用独立 SQLite 数据库，避免污染生产数据库。


需要注意：

app 在 conftest.py 中提前：

from app.main import app

而 app.main.py 中存在模块级：

settings = get_settings()


因此：

DATABASE_PATH
+
get_settings.cache
+
app.main 模块级 settings

之间的初始化时序需要进一步验证。


--------------------------------------------------------------------------------
TEST-025 — DATABASE LAYER
--------------------------------------------------------------------------------

当前 backend/app/core/database.py 已确认。

initialize_database()：

1. 获取 settings
2. 创建 database directory
3. 开启 SQLite foreign_keys
4. 开启 WAL
5. 设置 busy_timeout = 5000


get_connection()：

sqlite3.connect(
    settings.database_path,
    timeout=5.0,
)

row_factory = sqlite3.Row

并设置：

PRAGMA foreign_keys = ON
PRAGMA busy_timeout = 5000


异常时 rollback。
正常时 commit。
最终关闭 connection。


当前 database.py 暂未发现需要立即修改的问题。


--------------------------------------------------------------------------------
TEST-025 — BOOTSTRAP
--------------------------------------------------------------------------------

当前 backend/app/core/bootstrap.py：

ensure_local_user()


使用：

INSERT OR IGNORE INTO users (id)
VALUES (?)


该操作具有幂等性。


当前启动顺序：

initialize_database()
    ->
run_migrations()
    ->
ensure_local_user()


该顺序目前合理。


--------------------------------------------------------------------------------
TEST-025 — TEST FILE INVENTORY
--------------------------------------------------------------------------------

当前 backend/tests：

conftest.py
__init__.py
test_conversation_service.py
test_conversations.py
test_database_integrity.py
test_health.py
test_interactions.py
test_message_service.py
test_messages.py
test_persons.py
test_relationship_boundaries.py
test_relationships.py
test_services.py


本阶段新增/涉及：

test_conversation_service.py
test_conversations.py
test_database_integrity.py
test_message_service.py
test_messages.py


--------------------------------------------------------------------------------
CURRENT BLOCKER
--------------------------------------------------------------------------------

当前最重要的问题：

app.log 中存在大量短时间重复 migration application。


目前已经确认：

A. migration runner 本身具备 version 检查逻辑。

B. 测试 fixture 会主动调用 run_migrations()。

C. TestClient(app) 会触发 FastAPI lifespan。

D. FastAPI lifespan 又会调用 run_migrations()。

因此存在重复调用。

但是：

仅仅“调用两次”无法完全解释为什么日志显示：

Applying migration: 001
Applying migration: 002
Applying migration: 003

不断重复。

因为如果两次使用的是同一个 SQLite 数据库，
第一次执行成功后 schema_migrations 应该包含：

001
002
003

第二次调用应该全部跳过。


因此当前尚不能直接认定 migrations.py 存在 bug。


--------------------------------------------------------------------------------
CURRENT DIAGNOSTIC HYPOTHESES
--------------------------------------------------------------------------------

需要重点区分：

A.
同一个数据库被重复调用，
但是 schema_migrations 没有正常持久化。

B.
不同 DATABASE_PATH 之间发生切换。

C.
TestClient / lifespan 导致重复调用，
但 migration 本身实际上是正常幂等的。

D.
get_settings() cache / 初始化时序导致：
fixture 使用测试数据库，
而 app/lifespan 使用了另外的 database_path。

E.
SQLite transaction / connection 行为导致 schema_migrations 状态异常。

F.
其他尚未发现的数据库初始化路径。


--------------------------------------------------------------------------------
IMPORTANT CURRENT CONSTRAINTS
--------------------------------------------------------------------------------

当前阶段：

不要删除数据库。

不要删除 schema_migrations。

不要删除或修改 001_initial.sql。

不要删除或修改 002_interactions.sql。

不要修改 003_conversations_messages.sql，
除非后续诊断证明 SQL 本身存在问题。

不要重写 migrations.py。

不要修改 conversations / messages 业务逻辑。

不要为了让 pytest 通过而修改测试预期。

不要进行大规模架构重构。

不要提交 Git。


--------------------------------------------------------------------------------
NEXT ACTION — TEST-026
--------------------------------------------------------------------------------

下一步执行 TEST-026。

目标：

确认每一次 run_migrations()：

1. 使用哪个 database_path。
2. migration files 是什么。
3. schema_migrations 中当前有哪些 version。
4. 每个 migration version 的 exists 状态。
5. fixture 和 FastAPI lifespan 是否使用相同数据库。
6. get_settings() cache 是否导致 database_path 不一致。


建议临时增加诊断日志：

Migration database path

Migration files

Migration check:
version
exists
database_path


目标是最终区分：

A. 同一数据库状态未持久化
B. database_path 切换
C. 正常重复调用
D. settings cache / 初始化时序问题
E. SQLite transaction 问题
F. 其他问题


--------------------------------------------------------------------------------
TEST-026 AFTER DIAGNOSIS
--------------------------------------------------------------------------------

确定根因后：

1. 采用最小修改方案。
2. 不改变已有业务功能。
3. 修复测试初始化 / migration 生命周期。
4. 重新执行完整 pytest。
5. 检查 SQLite schema_migrations。
6. 检查 app.log。
7. 再检查 Git status。
8. 确认 003 migration 纳入 Git。
9. 更新本交接文档。
10. 最后再考虑 commit。


--------------------------------------------------------------------------------
HANDOVER RULE FOR NEXT CONVERSATION
--------------------------------------------------------------------------------

下一次对话必须首先读取：

/opt/ai-love-strategist/docs/DEVELOPMENT_HANDOVER.md


然后：

1. 不从零重新设计项目。
2. 不重复修改已经完成的 conversations / messages 功能。
3. 先确认当前服务器实际代码。
4. 先执行 TEST-026。
5. 不在根因确认前进行大规模修改。
6. 所有修改都以实际服务器代码为准。
7. 每次修改后运行对应测试。
8. 涉及数据库必须检查实际 SQLite 状态。
9. 涉及 migration 必须检查 schema_migrations。
10. 涉及 Git 必须检查 git diff / git status。


================================================================================
END OF CURRENT STAGE ADDENDUM
================================================================================
