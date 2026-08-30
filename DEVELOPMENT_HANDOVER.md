# AI Love Strategist Development Handover

更新时间：2026-08-30
当前阶段：TEST-080 — StructuredAnalysis → Action Plan Candidate Boundary — VERIFIED
当前 Branch：test-080-structured-analysis-action-plan-candidate-contract
当前 HEAD：e7b431bf7364b9f5c2aa4861f90c9c1b66456090
上一阶段：TEST-079 — Learning Strategy → Action Plan HTTP Response Contract — VERIFIED
最近一次服务器验收：全量 480 passed；TEST-080 专项回归 23 passed；Action Plan candidate boundary 已锁定；StructuredAnalysis 不得直接晋升为 action candidate；无 action_decisions / action_executions / action_outcomes side effect。

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
TEST-078 StructuredAnalysis → Action Plan 消费契约 — VERIFIED
TEST-079 Learning Strategy → Action Plan HTTP Response Contract — VERIFIED
TEST-080 StructuredAnalysis → Action Plan Candidate Boundary — VERIFIED

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

TEST-078 已由后续 TEST-079 / TEST-080 继续强化并保持 VERIFIED。

---

## TEST-079 — Learning Strategy → Action Plan HTTP Response Contract

TEST-079 在 TEST-078 已建立的 Action Plan derived-analysis consumption boundary 上，锁定 `learning_strategy` 的 HTTP response contract。

目标链：

`AnalysisContext → LLM → StructuredAnalysis → Existing Action Plan Context → learning_strategy HTTP projection`

本阶段不新增业务生命周期，不新增数据库表，不改变 Action Plan / Decision / Execution / Outcome 生命周期。

### TEST-079 实际变更

Git commit：

`bdedc820c99590b642a419f8b5bff1e05a72d5ab` — `test: lock learning strategy HTTP response contract`

TEST-079 相对于 TEST-078 仅强化 `backend/tests/test_analysis_action_plan_route.py` 的 HTTP response contract，确保 Action Plan Context response 中的 `learning_strategy` 与 service 输出保持一致，并继续验证：

- `action_plan_inputs.analysis_is_derived = true`
- `action_plan = []`
- `action_constraints.must_not_auto_execute = true`
- `learning_strategy` 完整保留
- `learning_strategy` 的 source-backed / read-only / provenance / unknown / no-auto-execution / no-auto-send / no-LLM 约束保持不变
- LLM provider failure 继续转换为 HTTP 502 `LLM analysis failed`
- 不因 learning strategy projection 自动生成 action proposal
- 不自动确认 decision、不执行 action、不发送消息、不修改 relationship、不伪造 outcome

### TEST-079 服务器验收

- Branch：`test-079-learning-strategy-action-plan-contract`
- HEAD：`bdedc820c99590b642a419f8b5bff1e05a72d5ab`
- 全量 pytest：`478 passed`
- `127.0.0.1:18080`：正常监听
- `GET /health`：HTTP 200
- `GET /api/v1/conversations/{conversation_id}/action-plan/context`：HTTP 200
- Action Plan Context 实际 Qwen 调用：HTTP 200
- `learning_strategy`：正常出现在 HTTP response 中
- `action_plan`：保持空数组，不自动产生 proposal
- 缺失 conversation：HTTP 404 `Conversation not found`
- `action_decisions` / `action_executions` / `action_outcomes`：无新增 side effect
- 未产生自动发送、relationship mutation、decision、execution、outcome side effect

TEST-079 正式标记为 VERIFIED。

---

## TEST-080 — StructuredAnalysis → Action Plan Candidate Boundary

TEST-080 的目标不是增加新的 Action Plan 生命周期，而是锁定一个关键安全边界：`StructuredAnalysis` 是 derived interpretation，不能直接晋升为 action candidate / recommendation / proposal。

### TEST-080 实际变更

Git commit：

`e7b431bf7364b9f5c2aa4861f90c9c1b66456090` — `test: enforce analysis action candidate boundary`

仅修改：
- `backend/tests/test_analysis_action_plan.py`

主要强化：
- 使用 `StructuredAnalysisItem` 构造 hypothesis / intent signal，避免测试通过不严格的 `model_copy(update=...)` 绕过真实 Pydantic 类型边界。
- 增加 `test_service_does_not_promote_structured_analysis_into_action_candidate`，明确验证高置信度 hypothesis / intent signal 即使表达出“应该立即发送消息”“对方明确希望继续推进”等 action-like 内容，也不能自动进入 `recommendations` 或 `action_plan`。
- 增加/保留既有 candidate boundary contract：只有 existing explicit recommendations 才能进入 Action Plan promotion；derived analysis 本身不是 recommendation。
- 保留 existing action candidate 与 derived analysis 的边界隔离：existing evidence-backed recommendation 可以继续生成 proposal，但不能因为 StructuredAnalysis 的存在而被改写或自动新增。

### TEST-080 验收

- Branch：`test-080-structured-analysis-action-plan-candidate-contract`
- HEAD：`e7b431bf7364b9f5c2aa4861f90c9c1b66456090`
- focused regression：23 passed
- 全量 regression：480 passed in 74.16s
- `git diff --check`：通过
- commit 已 push 至 `origin/test-080-structured-analysis-action-plan-candidate-contract`
- working tree 在提交前已清理；误生成的临时文件已删除
- 未新增 migration
- 未修改 Action Plan / Decision / Execution 生命周期
- 未产生自动 confirmation / decision / execution / outcome side effect

TEST-080 正式标记为 VERIFIED。

---

## TEST-080 后的关键产品边界

当前 Action Plan promotion 的 deterministic 边界仍由现有 `ActionPlanService.build_action_plan()` 控制：
- recommendation 必须是显式 dict。
- `action` 必须是非空字符串。
- `evidence_source_ids` 必须为非空 list。
- 所有 `evidence_source_ids` 必须命中 canonical evidence 的 `source_id` 集合。
- 合法 recommendation 才能生成 `status="proposed"` 的 action-plan item。
- proposal 必须继续 `requires_user_confirmation=true`。
- StructuredAnalysis 可以作为 derived interpretation / signal input，但不得冒充 canonical evidence，也不得自行创建 recommendation。

因此，下一阶段不得继续扩大 StructuredAnalysis → candidate 的直接映射。应首先检查 recommendation 的真实生产边界，以及 recommendation → action-plan promotion 的 provenance / candidate contract。

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-080 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 下一阶段方向

TEST-080 已完成并 VERIFIED。下一阶段暂定围绕 **Action Recommendation Provenance / Candidate Promotion Contract** 进行仓库级审查，正式 TEST 编号与范围必须在读取当前分支实际 recommendation producer、schema、Action Plan promotion tests、Decision / Confirmation lifecycle 后确定。

必须优先从 GitHub 当前开发分支读取实际代码、测试、文档，再决定下一个 TEST 的最小真实产品边界。

不得预先假定继续增加字段、扩大 LLM 消费范围或直接进入自动执行。

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
