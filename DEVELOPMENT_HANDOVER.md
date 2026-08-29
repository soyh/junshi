# AI Love Strategist Development Handover

更新时间：2026-08-29
当前阶段：QWEN PROVIDER INTEGRATION — AnalysisContext → Qwen → StructuredAnalysis 已接入 API 边界，待服务器专项/全量验收
当前 Branch：test-073-qwen-provider
最近一次服务器验收：TEST-073 Provider 层前置全量 452 passed；API route 集成后的服务器验收待执行。

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
TEST-073 Qwen Provider Integration — CODE COMPLETE, SERVER ROUTE ACCEPTANCE PENDING

---

## TEST-070 ~ TEST-073

TEST-070 established the provider-neutral `LLMAnalysisService` boundary and provider failure translation.

TEST-071 connected validated `StructuredAnalysis` to the existing strategy decision context without changing decision/execution semantics.

TEST-072 established `AnalysisStrategyService` orchestration:
`AnalysisContext → LLMAnalysisService → StructuredAnalysis → StrategyDecisionContext`.

TEST-073 adds the first concrete provider, Qwen, while preserving the provider-neutral boundary. Qwen configuration uses DashScope credentials and the OpenAI-compatible endpoint. A request-scoped API endpoint now exposes:
`GET /api/v1/conversations/{conversation_id}/analysis/structured`
which obtains canonical AnalysisContext, invokes Qwen, validates the response as StructuredAnalysis, and returns only the derived structured result.

The route translates LLMAnalysisError to HTTP 502 and does not persist StructuredAnalysis.

No database migration was added.

---

## 数据库

当前 schema migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-073 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

---

## 下一阶段

1. 服务器拉取 `test-073-qwen-provider`。
2. 运行新增 structured-analysis route 专项测试与全量测试。
3. 若专项/全量通过，再配置真实 DashScope API key，仅进行受控单次 Qwen smoke test。
4. 验证真实 Qwen 输出能稳定通过 StructuredAnalysis contract，尤其是 evidence_source_ids、unknowns、analysis_constraints 与 provenance 约束。
5. 再将同一 provider composition 接入 Analysis → Strategy orchestration 的正式调用入口；不得让 Strategy 绕过 StructuredAnalysis。
6. 最后才进入真实产品层的回复生成、human confirmation、action plan / execution UI/API 编排。

---

## 开发原则

Route → Service → Repository → SQLite。
所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

架构冻结后：LLM 仅位于 AnalysisContext → StructuredAnalysis 边界之后；不得进入 canonical evidence、persistence、learning context、decision 或 execution 层。
