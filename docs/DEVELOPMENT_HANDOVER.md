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

---

## TEST-009

Text Import

状态：

IN PROGRESS

Branch：

test-009-text-import

基础实现 Commit：

f7b2455 feat: add TEST-009 text import foundation

最近验证增强 Commit：

20d0a6e test: strengthen TEST-009 text import validation

目标：

文本聊天记录导入。

流程：

Text
→ Parse
→ Message Candidates
→ Validation
→ Conversation
→ Message

当前完成内容：

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
- Person existence validation
- user_id isolation
- Conversation 自动创建
- Message 自动创建
- imported_count 返回
- message_ids 返回
- candidates 返回
- 导入失败时不创建 Conversation

API：

POST /api/v1/text-imports

请求示例：

{
  "person_id": "<person_id>",
  "title": "导入聊天",
  "text": "2026-08-23T10:00:00+00:00 | user | 你好\n2026-08-23T10:01:00+00:00 | person | 你好呀"
}

当前测试：

8 个 API/集成测试 + 4 个 parser/validation 测试

服务器验证：

待执行。

数据库变化：

无新增 migration。

架构变化：

无。

明确边界：

- 不接 OCR
- 不接 screenshot import
- 不接外部聊天平台 integration
- 不接 LLM
- 不做自动发送
- 不进入 Conversation Analysis

下一步：

继续完善 TEST-009 Text Import 的导入契约与边界测试；验证通过后再标记 TEST-009 VERIFIED。

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
