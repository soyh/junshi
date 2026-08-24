# Development Handover

更新时间：2026-08-24
当前阶段：TEST-023 + TEST-024 memory update loop
当前状态：IN PROGRESS
当前 Branch：test-024-memory-update-synthesis

---

## 已完成阶段

TEST-008 Person Timeline — VERIFIED
TEST-009 Text Import — VERIFIED
TEST-010 Conversation Analysis Foundation — VERIFIED
TEST-011 Evidence — VERIFIED
TEST-012 Person Profile — VERIFIED
TEST-013 Relationship State Analysis — VERIFIED
TEST-014 Recommendation Foundation — VERIFIED
TEST-015 Strategic Reply Foundation — VERIFIED
TEST-016 Action Plan Foundation — VERIFIED
TEST-017 Action Plan Synthesis — VERIFIED
TEST-018 Strategic Reply Synthesis — VERIFIED
TEST-019 Action Confirmation Foundation — VERIFIED
TEST-020 Action Outcome Foundation — VERIFIED
TEST-021 Action Feedback Synthesis — VERIFIED
TEST-022 Memory Update Foundation — VERIFIED

TEST-019 + TEST-020 最终服务器验证：专项 15 passed；全量 195 passed。
TEST-021 + TEST-022 最终服务器验证：专项 18 passed；全量 213 passed。

---

## TEST-023 Memory Update Synthesis

Branch：test-023-memory-update-synthesis
状态：IMPLEMENTED，待服务器批次验收

目标：把 TEST-022 的 source-backed memory candidate 转换为稳定的记忆更新提案，仍然只提供 proposal，不写入长期 memory。

API：GET /api/v1/persons/{person_id}/memory-updates/synthesis

核心边界：
- 仅允许 source-backed candidate
- deterministic proposal id
- status=proposed
- 保留 source_candidate_id / source_decision_id / source_outcome_id
- 保留 action outcome 与 note
- 明确 relationship impact 与未来行为为 unknown
- user_id / person_id isolation
- read-only
- 不接真实 LLM

---

## TEST-024 Memory Update Persistence Foundation

Branch：test-024-memory-update-synthesis
状态：IMPLEMENTED，待服务器批次验收

目标：建立显式持久化边界。只有通过 TEST-023 synthesis 得到的 source-backed candidate，并由用户显式调用 persist endpoint，才允许写入长期 memory。

API：POST /api/v1/persons/{person_id}/memory-updates/{candidate_id}/persist

新增 migration：006_memory_updates.sql

核心边界：
- 只允许当前 person / user 下真实存在的 synthesis candidate 持久化
- 完整保留 source_candidate_id / source_decision_id / source_outcome_id
- 保留 action outcome 与 note
- deterministic persisted memory id
- 同一 candidate 重复 persist 不产生重复记录
- user_id / person_id isolation
- 不修改 Relationship
- 不执行行动
- 不发送消息
- 不接真实 LLM

安全约束：
- GET synthesis/context 不自动持久化
- persist 必须由明确 POST 调用触发
- 缺失或跨 person/user candidate 返回 404
- 不从 outcome 推断关系变化或对方心理

---

## 服务器测试规则

相邻两个 TEST-No 合并为一次服务器测试批次：

TEST-019 + TEST-020：专项 15 passed + 全量 195 passed
TEST-021 + TEST-022：专项 18 passed + 全量 213 passed
TEST-023 + TEST-024：一次专项 + 一次全量

每个 TEST 仍保持独立代码边界、测试文件和验收记录。

---

## 开发原则

不要随意改变现有架构。
优先采用：Route → Service → Repository → SQLite
所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

当前生产数据库 schema migrations：001 / 002 / 003 / 004 / 005 / 006。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
