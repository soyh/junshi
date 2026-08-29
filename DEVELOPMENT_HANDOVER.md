# AI Love Strategist Development Handover

更新时间：2026-08-29
当前阶段：TEST-074 — Analysis → Strategy 正式入口实现，服务器验收待执行
当前 Branch：test-074-analysis-strategy-entrypoint
最近一次服务器验收：TEST-073 Qwen Provider Integration 全链路验收通过；专项测试 15 passed；全量 454 passed；Structured Analysis API 实际调用 Qwen 返回 200 OK。

---

## 架构冻结：Analysis → LLM → StructuredAnalysis → Strategy

正式架构契约见：`docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`

冻结后的主链：

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Human Confirmation → Execution / Outcome`

核心边界：
- AnalysisContext 是 deterministic、source-backed、read-only 的 LLM 输入，不是 AI 分析结果。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- LLM 只在 AnalysisContext 边界之后出现。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- StructuredAnalysis 中的 inference / hypothesis / material signal 应保留 canonical evidence provenance。
- unknown 必须在证据不足时保持 unknown，不得被模型猜测自动提升为事实。
- Strategy 消费 StructuredAnalysis，但不得绕过现有 decision / confirmation / execution 生命周期。
- 不允许 LLM 直接发送第三方消息、自动执行 action、修改 relationship state、写入 learning history 或伪造 outcome success。
- 现有 Persistence、Evidence、Relationship State、Learning Strategy、Strategy Decision、Strategic Reply、Action Plan、Execution 生命周期不因引入 LLM 而重写。
- 当前全局 no-LLM 约束解除；改为仅对 deterministic Context / Evidence / Learning / Persistence / Decision / Execution 层保持 no-LLM。

第一阶段不新增数据库表；StructuredAnalysis 初期视为 derived request-scoped output。未来如需持久化，必须另行设计并新增 migration。

Provider 当前选择：Qwen，通过 DashScope OpenAI-compatible API；provider adapter 与上层 LLM contract 解耦。

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
TEST-074 Analysis → Strategy formal entrypoint — IMPLEMENTED, SERVER ACCEPTANCE PENDING

---

## TEST-070 ~ TEST-073

TEST-070 established the provider-neutral `LLMAnalysisService` boundary and provider failure translation.

TEST-071 connected validated `StructuredAnalysis` to the existing strategy decision context without changing decision/execution semantics.

TEST-072 established `AnalysisStrategyService` orchestration:
`AnalysisContext → LLMAnalysisService → StructuredAnalysis → StrategyDecisionContext`.

TEST-073 adds the first concrete provider, Qwen, while preserving the provider-neutral boundary. Qwen configuration uses DashScope credentials and the OpenAI-compatible endpoint. A request-scoped API endpoint exposes:
`GET /api/v1/conversations/{conversation_id}/analysis/structured`
which obtains canonical AnalysisContext, invokes Qwen, validates the response as StructuredAnalysis, and returns only the derived structured result.

TEST-073 服务器最终验收：
- `backend/tests/test_qwen_provider.py`：5 passed
- `backend/tests/test_analysis_llm_service.py`：4 passed
- `backend/tests/test_structured_analysis.py`：4 passed
- `backend/tests/test_analysis_structured_route.py`：2 passed
- TEST-073 直接专项合计：15 passed
- 全量回归：454 passed
- FastAPI server：127.0.0.1:18080 正常运行
- `/health`：HTTP 200
- `/api/v1/conversations/{conversation_id}/analysis/structured`：实际调用 Qwen 成功并返回 HTTP 200

TEST-073 同时修复 Qwen API key 的 omitted / explicit semantics：未提供 key 与显式提供 key 的配置语义被区分处理。

The route translates LLMAnalysisError to HTTP 502 and does not persist StructuredAnalysis.

No database migration was added.

---

## TEST-074 Analysis → Strategy 正式入口

TEST-074 在既有 `AnalysisStrategyService` 上增加正式 API entrypoint，而不是建立第二套 Strategy 体系。

新增：
- `backend/app/api/routes/analysis_strategy.py`
- `backend/app/schemas/analysis_strategy.py`
- `backend/tests/test_analysis_strategy_route.py`

正式入口：
`GET /api/v1/conversations/{conversation_id}/strategy/context`

执行链：
`conversation_id → AnalysisContext → Qwen → StructuredAnalysis → StrategyDecisionContext`

该入口：
- 使用当前用户身份获取 conversation-scoped AnalysisContext。
- 使用 QwenProvider 产生 StructuredAnalysis。
- 将 StructuredAnalysis 注入现有 StrategyDecisionContextService。
- 返回 candidates / decision_inputs / current_state 等既有 Strategy context，同时附带 derived StructuredAnalysis。
- 保持 `requires_explicit_decision` 与 `must_not_auto_select`。
- 保持 LLM derived / provenance / unknown 约束。
- 将 LLM provider failure 映射为 HTTP 502。
- 不新增数据库表，不持久化 StructuredAnalysis，不创建新的 decision / execution 生命周期。

TEST-074 当前状态为 CODE IMPLEMENTED，尚未执行服务器专项验收，因此不得标记 VERIFIED。

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-074 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 下一阶段：TEST-074 验收 → Strategy 消费深化

首先完成 TEST-074 的服务器验收：
1. 拉取 `test-074-analysis-strategy-entrypoint` 最新提交。
2. 运行 `backend/tests/test_analysis_strategy_route.py`。
3. 运行 TEST-070 ~ TEST-074 相关专项测试。
4. 运行全量 pytest。
5. 验证 `/health`、现有 Structured Analysis endpoint，以及新的 `/api/v1/conversations/{conversation_id}/strategy/context`。
6. 对新的 Strategy entrypoint 执行真实 Qwen smoke test。
7. 验证调用前后数据库无新增 StructuredAnalysis persistence / 无 decision / execution side effect。

TEST-074 验收通过后，下一实现阶段继续推进 StructuredAnalysis 对现有 Strategy Decision / Strategic Reply / Action Plan 的最小消费契约，但不得新增平行 decision 体系。

下一阶段仍禁止：
- 新增数据库表用于暂存或持久化 StructuredAnalysis，除非先完成独立 persistence 设计并新增 migration。
- 让 LLM 进入 canonical evidence、persistence、learning、decision persistence 或 execution 层。
- 让模型自动选择 candidate、自动确认 decision、自动执行 action 或伪造 outcome。
- 为了测试方便修改既有业务语义或绕过 user / person isolation。
- 使用 8899。

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

架构冻结后：LLM 仅位于 AnalysisContext → StructuredAnalysis 边界之后；不得进入 canonical evidence、persistence、learning context、decision 或 execution 层。
