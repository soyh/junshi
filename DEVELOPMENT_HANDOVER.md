# AI Love Strategist Development Handover

更新时间：2026-08-29
当前阶段：TEST-078 — StructuredAnalysis → Action Plan 消费契约
当前 Branch：test-078-structured-analysis-action-plan-consumption
上一阶段：TEST-077 — Strategic Reply downstream boundary — VERIFIED
上一阶段服务器验收：全量 471 passed；Strategic Reply Context 实际 Qwen HTTP 200；未产生 action_decisions / action_executions / action_outcomes side effect。

---

## 信息检索优先级（新增，强制执行）

凡是需要检索、确认或定位的内容，必须首先从 GitHub 仓库 `soyh/junshi` 当前开发分支及其相关历史代码、测试、文档中查找。只有在 GitHub 仓库中找不到所需信息时，才能要求用户从服务器端查找，并明确说明需要执行的服务器端命令及原因。

不得在尚未完成 GitHub 仓库检索的情况下，直接要求用户通过服务器端 `grep`、`sed`、日志或数据库查询来提供本应可以从 GitHub 确认的信息。

---

## 架构冻结：Analysis → LLM → StructuredAnalysis → Strategy

正式架构契约：`docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`

冻结后的主链：

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Human Confirmation → Execution / Outcome`

核心边界：
- AnalysisContext 是 deterministic、source-backed、read-only 的 LLM 输入，不是 AI 分析结果。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- LLM 只在 AnalysisContext 边界之后出现。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- StructuredAnalysis 中的 inference / hypothesis / material signal 应保留 canonical evidence provenance。
- unknown 必须在证据不足时保持 unknown，不得被模型猜测自动提升为事实。
- Strategy、Strategic Reply、Action Plan 只能在既有生命周期内消费 derived analysis。
- 不允许 LLM 直接发送第三方消息、自动执行 action、修改 relationship state、写入 learning history 或伪造 outcome success。
- 现有 Persistence、Evidence、Relationship State、Learning Strategy、Strategy Decision、Strategic Reply、Action Plan、Execution 生命周期不因引入 LLM 而重写。
- 当前全局 no-LLM 约束解除；deterministic Context / Evidence / Learning / Persistence / Decision / Execution 层仍保持 no-LLM。

第一阶段不新增数据库表；StructuredAnalysis 初期视为 derived request-scoped output。未来如需持久化，必须另行设计并新增 migration。

Provider：Qwen，通过 DashScope OpenAI-compatible API；provider adapter 与上层 LLM contract 解耦。

---

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 Strategy Decision Lifecycle — VERIFIED
TEST-046 Strategy Decision Lifecycle Synthesis — VERIFIED
TEST-047 Strategy Decision Learning Input — VERIFIED
TEST-048 Strategy Decision Learning Synthesis — VERIFIED
TEST-049 Strategy Decision Learning Bridge — VERIFIED
TEST-050 Strategy Decision Learning Synthesis Bridge — VERIFIED
TEST-051 Learning Strategy Recommendation Bridge — VERIFIED
TEST-052 Learning Strategy Strategic Reply Bridge — VERIFIED
TEST-053 Learning Strategy Action Plan Bridge — VERIFIED
TEST-054 Learning Strategy Downstream Candidate Contract — VERIFIED
TEST-055 Learning Strategy Downstream Constraint Contract — VERIFIED
TEST-056 Learning Strategy Downstream Memory Update Semantics — VERIFIED
TEST-057 Learning Strategy Downstream Candidate Parity — VERIFIED
TEST-058 Learning Strategy Source Provenance — VERIFIED
TEST-059 Learning Strategy Provenance Immutability — VERIFIED
TEST-060 Learning Strategy Source Provenance Completeness — VERIFIED
TEST-061 Learning Strategy Provenance Parity — VERIFIED
TEST-062 Learning Strategy Decision Provenance Parity — VERIFIED
TEST-063 Learning Strategy Decision Constraint Parity — VERIFIED
TEST-064 Learning Strategy Decision Learning Evidence Completeness — VERIFIED
TEST-065 Analysis Context learning-strategy bridge — VERIFIED
TEST-066 Analysis Context relationship-state bridge — VERIFIED
TEST-067 Analysis Context canonical evidence bridge — VERIFIED
TEST-068 Analysis Context conversation evidence bridge — VERIFIED
TEST-069 Analysis Context evidence contract sync — VERIFIED
TEST-070 Analysis LLM Service — VERIFIED
TEST-071 Structured Analysis Strategy Bridge — VERIFIED
TEST-072 Analysis → Strategy Orchestration — VERIFIED
TEST-073 Qwen Provider Integration — VERIFIED
TEST-074 Analysis → Strategy formal entrypoint — VERIFIED
TEST-075 StructuredAnalysis → Strategy Decision 最小消费契约 — VERIFIED
TEST-076 StructuredAnalysis → Strategic Reply 消费契约 — VERIFIED
TEST-077 Strategic Reply downstream boundary — VERIFIED

---

## TEST-077 服务器验收

TEST-077 实际验证：
- Branch：`test-077-strategic-reply-downstream-boundary`
- HEAD：`994ebb4bcd83c29f892572f23bf199e9751bfdf3`
- 专项 bridge：3 passed
- Strategic Reply / Decision regression：49 passed
- 全量回归：471 passed
- FastAPI `127.0.0.1:18080`：HTTP 200
- `GET /api/v1/conversations/{conversation_id}/strategic-reply/context`：实际 Qwen HTTP 200
- 返回 `structured_analysis`、`reply_inputs`，且 `analysis_is_derived=true`
- `draft=null`
- `action_decisions` / `action_executions` / `action_outcomes` 均保持 0
- 未产生自动发送、relationship mutation、decision、execution、outcome side effect

TEST-077 正式标记为 VERIFIED。

---

## TEST-078 — StructuredAnalysis → Action Plan 消费契约

目标：在现有 Action Plan 生命周期中增加最小 derived-analysis consumption boundary，不建立第二套 Action Plan / Execution 生命周期。

目标链：
`AnalysisContext → LLM → StructuredAnalysis → Existing Action Plan Context → Explicit Confirmation / Execution Boundary`

本阶段采用与 TEST-076 / TEST-077 一致的最小投影原则：
- `StructuredAnalysis` 保留为 request-scoped derived output。
- 将可消费的 analysis buckets 投影到 `action_plan_inputs.signals`。
- 保留每个信号的 `evidence_source_ids` provenance。
- 保留 unknown，不把 unknown 转换为 action fact。
- `action_plan` 不因为 LLM 分析自动新增 proposal。
- `requires_user_confirmation` 必须继续为 true。
- `must_not_auto_execute` 必须继续为 true。
- 不自动确认、不执行、不发送消息、不修改 relationship。
- 不新增数据库表、不持久化 StructuredAnalysis。

### TEST-078 当前实现

新增：
- `backend/app/services/analysis_action_plan.py`
- `backend/app/schemas/analysis_action_plan.py`
- `backend/app/api/routes/analysis_action_plan.py`
- `backend/tests/test_analysis_action_plan.py`
- `backend/tests/test_analysis_action_plan_route.py`

正式入口：
`GET /api/v1/conversations/{conversation_id}/action-plan/context`

执行链：
`conversation_id → AnalysisContext → LLMAnalysisService/Qwen → StructuredAnalysis → existing ActionPlan context → action_plan_inputs`

`AnalysisActionPlanService`：
- 从现有 `AnalysisLLMService` 获取 conversation-scoped derived analysis。
- 从现有 `ActionPlanService` 获取 canonical action-plan context。
- 仅投影 observed_facts、inferences、hypotheses、emotional_signals、relationship_signals、risk_signals、intent_signals、unknowns。
- 明确 `action_plan_inputs.analysis_is_derived = true`。
- 保留 `evidence_source_ids` provenance。
- 强化 action constraints：evidence-backed、preserve unknowns、requires confirmation、no auto execution、no relationship change、derived output、provenance preservation。
- 不把 StructuredAnalysis 直接转换成 action-plan proposal。

### TEST-078 验收要求

1. 先执行新增专项测试：
   - `backend/tests/test_analysis_action_plan.py`
   - `backend/tests/test_analysis_action_plan_route.py`
2. 执行现有 Action Plan / Strategic Reply / Decision / Execution 回归。
3. 执行全量 `pytest -q`。
4. 服务器最终验收：
   - `GET /health` → 200
   - 新 Action Plan derived-context endpoint → 200
   - 实际 Qwen 调用成功
   - `action_plan` 不因 LLM 自动产生 proposal
   - `action_decisions` / `action_executions` / `action_outcomes` 无新增 side effect

在上述验收全部通过前，TEST-078 不得标记 VERIFIED。

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-078 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 下一阶段方向

TEST-078 验收通过后，再从 GitHub 读取 TEST-078 实际代码、测试、文档和相关 Action Plan / Decision / Execution contract，决定 TEST-079 的最小真实产品边界。不得预先假定继续增加字段或直接进入自动执行。

---

## 持续禁止事项

- 新增数据库表用于暂存或持久化 StructuredAnalysis，除非先完成独立 persistence 设计并新增 migration。
- 让 LLM 进入 canonical evidence、persistence、learning context、decision persistence 或 execution 层。
- 让模型自动生成或选择 action、自动确认 decision、自动执行 action、自动发送消息或伪造 outcome。
- 为了测试方便修改既有业务语义或绕过 user / person / conversation isolation。
- 建立第二套 Strategy / Decision / Strategic Reply / Action Plan 生命周期。
- 使用 8899。
- MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

架构冻结后：LLM 仅位于 AnalysisContext → StructuredAnalysis 边界之后；不得进入 canonical evidence、persistence、learning context、decision persistence 或 execution 层。
