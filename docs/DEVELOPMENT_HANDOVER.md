# Development Handover

更新时间：2026-09-17
当前阶段：TEST-107 — Provider Connection Test — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-107-provider-connection-test

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-090：按既有交接记录 VERIFIED；TEST-091 CONTRACT LOCKED；TEST-092 VERIFIED；TEST-093 VERIFIED；TEST-094 CONTRACT LOCKED。

TEST-095 VERIFIED — 真实 Recommendation / Action Plan 跨请求 persistence bridge；新增 migration 008 `action_plan_snapshots`，保持 evidence freshness validation，不放宽 Action Decision validation。

TEST-096 VERIFIED — confirmed Decision → explicit Execution → Outcome safety；scope / duplicate / conflict gates 完成。

TEST-097 VERIFIED — evidence-backed proposal freshness；stale snapshots 排除但不删除。

TEST-098 VERIFIED — Action Plan snapshot user/person isolation。

TEST-099 VERIFIED — Action Plan persistence gate；只有真实 Recommendation 对应 item 可持久化。

TEST-100 VERIFIED — proposal gate + execution gate；Decision 必须引用 proposed、requires-user-confirmation 的真实 Action Plan item；Execution 必须来自 confirmed Decision。

TEST-101 VERIFIED — Execution 精确 user/person/decision scope isolation；服务器 full pytest 526 passed；历史 migration diff blank。

TEST-102 VERIFIED — DB-level Outcome idempotency；新增 migration 009 `uq_action_outcomes_decision`，未修改历史 migration 005；服务器 full pytest 528 passed；migration diff blank。

TEST-103 VERIFIED — `sqlite3.IntegrityError → HTTP 409 Conflict`；服务器 targeted 1 passed、full 529 passed；migration diff blank。

TEST-104 VERIFIED — user-selectable LLM Provider / API configuration；服务器 targeted 1 passed、full 530 passed；工作树 clean；HEAD `0ebe095`；历史 migration 001~009 未修改。

TEST-105 VERIFIED — Provider Runtime Routing；服务器 targeted 2 passed、full 532 passed；工作树 clean；历史 migration diff blank。

TEST-106 VERIFIED — Provider Runtime Materialization；服务器 targeted 1 passed、full 533 passed；工作树 clean；历史 migration diff blank。

TEST-107 当前状态 — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING。

## TEST-104 — VERIFIED

目标：让用户能够按 user scope 保存自己的 OpenAI-compatible API Key、Base URL、Model、Timeout，并让现有 Analysis / Strategy / Recommendation / Strategic Reply / Action Plan analysis routes 使用该配置；没有用户配置时保持原有 Qwen 默认行为。

已建立：user-scoped provider config、Fernet API key encryption、GET/PUT/DELETE `/api/v1/settings/llm`、`openai_compatible` provider、`LLM_CONFIG_ENCRYPTION_KEY`、requirements 中 `cryptography==46.0.5`，以及对现有分析入口的配置读取。

## TEST-105 — Provider Runtime Routing — VERIFIED

目标：验证 TEST-104 保存的 provider configuration 不只是“设置 API”，而是实际进入各 AI 分析入口；同时验证无配置时保持原有 Qwen fallback。

覆盖入口：Structured Analysis、Strategy、Recommendation、Strategic Reply、Action Plan Analysis。服务器 targeted 2 passed、full pytest 532 passed。

## TEST-106 — Provider Runtime Materialization — VERIFIED

目标：锁定 user-scoped persisted provider configuration 在 runtime 中实际 materialize 为 Provider 实例参数，而不是只验证“拿到了某个 Provider 对象”。

验证 persisted API key 解密、base_url、model、timeout_seconds 均进入现有 QwenProvider adapter；不建立第二套 provider 实现。服务器 targeted 1 passed、full pytest 533 passed；历史 migration diff blank。

## TEST-107 — Provider Connection Test

目标：建立独立于正式 Analysis 的 Provider 连接测试能力，使用户可以验证当前 user-scoped provider configuration 是否能够实际访问其 OpenAI-compatible `/chat/completions` endpoint。

新增：
- `LLMProvider.test_connection()` provider contract；
- `QwenProvider.test_connection()` 轻量连接请求，不要求返回完整 StructuredAnalysis；
- `LLMProviderConfigService.test_connection()`，通过当前 user scope materialize provider 后执行连接测试；
- `POST /api/v1/settings/llm/test`；
- configuration/materialization error → HTTP 503；upstream/provider connection failure → HTTP 502；成功返回 `{\"status\": \"ok\"}`。

新增测试覆盖：
1. connection request 使用 materialized API key、model、base URL，并发送受限 `max_tokens`；
2. upstream HTTP failure 映射为 `LLMAnalysisError`；
3. malformed/empty choices 被拒绝；
4. HTTP endpoint 成功、configuration error、upstream failure 的状态码契约；
5. 不修改数据库 schema / migration。

GitHub Actions run `35204314910`：targeted connection tests passed、full pytest passed；随后已删除临时 TEST-107 validation workflow。服务器尚未验收，因此 TEST-107 暂不标记 VERIFIED。

## 产品化后续审计方向

TEST-107 服务器验收通过后，继续审计：
1. provider/model capability；
2. API Key 与敏感错误信息的日志泄漏边界；
3. provider rate-limit / timeout / retry 契约；
4. 前端设置页与分析工作流；
5. 正式认证替换当前 `X-User-ID` 信任边界；
6. 发布与运行时安全。

连接测试成功不等于模型业务分析成功，也不等于所有 provider capability 均可用；正式 Analysis 仍必须经过 StructuredAnalysis schema validation。

## 架构与持续禁止事项

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed 且等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 relationship 或伪造 Outcome。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle。
- 所有数据必须 user_id 隔离；Person / Relationship / Conversation 不得跨 scope 混用。
- 不修改历史 migration；不建立第二套 lifecycle。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
