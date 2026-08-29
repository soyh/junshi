# Development Handover

更新时间：2026-08-29
当前阶段：TEST-078 — StructuredAnalysis → Action Plan 消费契约
当前 Branch：test-078-structured-analysis-action-plan-consumption
上一阶段：TEST-077 — Strategic Reply downstream boundary — VERIFIED
最近一次服务器验收：TEST-077 全量 471 passed；18080 Strategic Reply Context 实际 Qwen HTTP 200；无 decision / execution / outcome side effect。

## 架构冻结

主链：`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Human Confirmation → Execution / Outcome`

AnalysisContext 保持 deterministic、source-backed、read-only。LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。StructuredAnalysis 始终是 derived interpretation，不是 canonical truth；inference / hypothesis / material signal 必须保留 evidence provenance；unknown 不得被猜测提升为事实。Strategy / Strategic Reply / Action Plan 必须保持既有 decision / confirmation / execution 生命周期。

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 ~ TEST-064：VERIFIED
TEST-065 ~ TEST-069：Analysis Context bridges / evidence contract — VERIFIED
TEST-070 Analysis LLM Service — VERIFIED
TEST-071 Structured Analysis Strategy Bridge — VERIFIED
TEST-072 Analysis → Strategy Orchestration — VERIFIED
TEST-073 Qwen Provider Integration — VERIFIED
TEST-074 Analysis → Strategy formal entrypoint — VERIFIED
TEST-075 StructuredAnalysis → Strategy Decision 最小消费契约 — VERIFIED
TEST-076 StructuredAnalysis → Strategic Reply 消费契约 — VERIFIED
TEST-077 Strategic Reply downstream boundary — VERIFIED

## TEST-077 验收摘要

- Strategic Reply derived-input bridge：3 passed
- Strategic Reply / Decision regression：49 passed
- 全量：471 passed
- `/health`：200
- `/api/v1/conversations/{conversation_id}/strategic-reply/context`：实际 Qwen 200
- `structured_analysis` / `reply_inputs` 保持 derived semantics，`draft=null`
- `action_decisions` / `action_executions` / `action_outcomes` 均保持 0

## TEST-078 — StructuredAnalysis → Action Plan 消费契约

目标链：`AnalysisContext → LLM → StructuredAnalysis → Existing Action Plan Context → Explicit Confirmation / Execution Boundary`

本阶段只建立最小 derived-analysis consumption boundary，不建立第二套 Action Plan / Execution 生命周期。

新增：
- `backend/app/services/analysis_action_plan.py`
- `backend/app/schemas/analysis_action_plan.py`
- `backend/app/api/routes/analysis_action_plan.py`
- `backend/tests/test_analysis_action_plan.py`
- `backend/tests/test_analysis_action_plan_route.py`

正式入口：`GET /api/v1/conversations/{conversation_id}/action-plan/context`

核心语义：
- 从既有 AnalysisContext 获取 StructuredAnalysis。
- 从既有 ActionPlanService 获取 canonical action-plan context。
- 将 observed_facts、inferences、hypotheses、emotional_signals、relationship_signals、risk_signals、intent_signals、unknowns 投影到 `action_plan_inputs.signals`。
- 保留 `evidence_source_ids` provenance，设置 `action_plan_inputs.analysis_is_derived=true`。
- LLM 分析不得自动生成 action-plan proposal。
- `requires_user_confirmation=true`、`must_not_auto_execute=true`、`must_not_change_relationship=true` 必须保持。
- unknown 不得被提升为 action fact。
- 不新增数据库表，不持久化 StructuredAnalysis。

### 当前代码边界

`AnalysisActionPlanService` 只做：`AnalysisContext → StructuredAnalysis → existing Action Plan context → action_plan_inputs`。它不调用 Repository，不执行 action。

`AnalysisActionPlanContextResponse` 扩展既有 Action Plan response，仅增加 derived `structured_analysis`、`action_plan_inputs` 以及 derived/provenance constraints。

### 验收要求

1. `backend/tests/test_analysis_action_plan.py`
2. `backend/tests/test_analysis_action_plan_route.py`
3. Action Plan / Strategic Reply / Strategy Decision / Execution 回归
4. 全量 `pytest -q`
5. `/health` → 200
6. 新 Action Plan Context 实际 Qwen smoke test
7. 检查 `action_decisions` / `action_executions` / `action_outcomes` 无新增

全部通过后才能将 TEST-078 标记 VERIFIED。

## 数据库

当前 migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。TEST-045 ~ TEST-078 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

## 下一阶段

TEST-078 验收通过后，必须再次从 GitHub 读取 TEST-078 实际代码、测试、文档及相关 Action Plan / Decision / Execution contract，再决定 TEST-079 的真实最小边界。

## 持续禁止

LLM 不得进入 canonical evidence、persistence、learning context、decision persistence 或 execution；不得自动确认 decision、自动执行 action、自动发送消息或伪造 outcome；不得绕过 user/person/conversation isolation；不得建立第二套生命周期；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。
