# AI Love Strategist Development Handover

更新时间：2026-08-24
当前阶段：TEST-021 Action Feedback Synthesis
当前状态：IN PROGRESS
当前 Branch：test-021-action-feedback-synthesis

---

## 项目定位

项目名称：AI Love Strategist

定位：AI 恋爱军师 / AI Relationship Management & Dating Companion System。

最终目标：用户添加一个关系对象后，可以持续导入聊天记录和互动数据，由系统建立人物画像、关系状态、历史记忆和行动计划，并根据后续反馈持续更新。

核心闭环：
添加对象 → 建立人物档案 → 导入聊天/互动 → 分析 → 建立画像 → 判断关系状态 → 生成策略回复 → 用户确认 → 用户执行 → 记录结果 → 反馈 → 更新记忆 → 长期关系跟踪

当前工程阶段仍以“稳定的数据、证据、分析、策略、用户决策和结果反馈契约”为主，尚未进入真实 LLM、自动执行或自动发送阶段。

系统不得自动联系第三方。每个人物必须保持独立档案和数据隔离。

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

TEST-019 Action Confirmation Foundation — 待服务器批次验收
TEST-020 Action Outcome Foundation — 待服务器批次验收

---

## TEST-021 Action Feedback Synthesis

Branch：test-021-action-feedback-synthesis
状态：IN PROGRESS

目标：把用户决策与行动结果汇总为确定性的反馈上下文，为后续长期记忆更新提供稳定输入，但不把反馈自动解释为新的事实或关系变化。

API：GET /api/v1/persons/{person_id}/action-plan/feedback/context

第一阶段实现：
- 聚合 action_decisions 与 action_outcomes
- deterministic ordering
- decision 可没有 outcome；缺失 outcome 不代表成功或失败
- 保留 completed / skipped / failed 原始结果
- 保留 decision / outcome note
- user_id / person_id isolation
- read-only
- 必须保持 unknowns
- 不自动修改 Relationship
- 不自动执行行动
- 不自动发送消息
- 不接真实 LLM

---

## TEST-022 Memory Update Foundation

Branch：test-022-memory-update-foundation
状态：PLANNED

目标：把已经存在的、明确来源于用户决策与行动结果的反馈转换为“记忆更新候选”输入；第一阶段只提供候选，不直接写入长期记忆。

第一阶段边界：
- 只允许真实 decision / outcome 作为 source
- 不从缺失 outcome 推导成功
- 不把 skipped / failed 自动改写成事实
- memory candidate 必须标记为 proposed
- 保留 source decision_id / outcome_id
- user_id / person_id isolation
- read-only
- 不自动修改 Relationship
- 不自动发送消息
- 不接真实 LLM
- 暂不新增长期 memory migration

---

## 服务器测试规则

从 TEST-019 开始，严格采用相邻两个 TEST-No 合并一次服务器测试批次：

TEST-019 + TEST-020：一次专项 + 一次全量
TEST-021 + TEST-022：一次专项 + 一次全量

每个 TEST 仍保持独立代码边界、测试文件和验收记录。

---

## 开发原则

不要随意改变现有架构。

优先采用：Route → Service → Repository → SQLite

所有用户数据必须进行 user_id 隔离。API Key 不得明文保存。系统不得自动向第三方发送消息。不得使用 8899。MVP 阶段不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

当前生产数据库 schema migrations：001 / 002 / 003 / 004 / 005。

每完成一个明确阶段：代码 → 测试 → Git status → Git commit → 更新交接文档。
