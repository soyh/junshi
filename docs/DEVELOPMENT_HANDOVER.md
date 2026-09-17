# Development Handover

更新时间：2026-09-17
当前阶段：TEST-110 — Provider Capability / Analysis Contract — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-110-provider-capability-contract

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

TEST-107 VERIFIED — Provider Connection Test；服务器 targeted connection 3 passed、HTTP contract 3 passed、full pytest 539 passed；工作树 clean；历史 migration diff blank。

TEST-108 当前状态 — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING。

TEST-109 当前状态 — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING。

TEST-110 当前状态 — CONTRACT LOCKED / GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING。

## TEST-104 — VERIFIED

目标：让用户能够按 user scope 保存自己的 OpenAI-compatible API Key、Base URL、Model、Timeout，并让现有 Analysis / Strategy / Recommendation / Strategic Reply / Action Plan analysis routes 使用该配置；没有用户配置时保持原有 Qwen 默认行为。

已建立：user-scoped provider config、Fernet API key encryption、GET/PUT/DELETE `/api/v1/settings/llm`、`openai_compatible` provider、`LLM_CONFIG_ENCRYPTION_KEY`、requirements 中 `cryptography==46.0.5`，以及对现有分析入口的配置读取。

## TEST-105 — Provider Runtime Routing — VERIFIED

目标：验证 TEST-104 保存的 provider configuration 不只是“设置 API”，而是实际进入各 AI 分析入口；同时验证无配置时保持原有 Qwen fallback。

覆盖入口：Structured Analysis、Strategy、Recommendation、Strategic Reply、Action Plan Analysis。服务器 targeted 2 passed、full pytest 532 passed。

## TEST-106 — Provider Runtime Materialization — VERIFIED

目标：锁定 user-scoped persisted provider configuration 在 runtime 中实际 materialize 为 Provider 实例参数，而不是只验证“拿到了某个 Provider 对象”。

验证 persisted API key 解密、base_url、model、timeout_seconds 均进入现有 QwenProvider adapter；不建立第二套 provider 实现。服务器 targeted 1 passed、full pytest 533 passed；历史 migration diff blank。

## TEST-107 — Provider Connection Test — VERIFIED

目标：建立独立于正式 Analysis 的 Provider 连接测试能力，使用户可以验证当前 user-scoped provider configuration 是否能够实际访问其 OpenAI-compatible `/chat/completions` endpoint。

新增：
- `LLMProvider.test_connection()` provider contract；
- `QwenProvider.test_connection()` 轻量连接请求，不要求返回完整 StructuredAnalysis；
- `LLMProviderConfigService.test_connection()`，通过当前 user scope materialize provider 后执行连接测试；
- `POST /api/v1/settings/llm/test`；
- configuration/materialization error → HTTP 503；upstream/provider connection failure → HTTP 502；成功返回 `{"status": "ok"}`。

新增测试覆盖：
1. connection request 使用 materialized API key、model、base URL，并发送受限 `max_tokens`；
2. upstream HTTP failure 映射为 `LLMAnalysisError`；
3. malformed/empty choices 被拒绝；
4. HTTP endpoint 成功、configuration error、upstream failure 的状态码契约；
5. 不修改数据库 schema / migration。

GitHub Actions run `35204314910`：targeted connection tests passed、full pytest passed；随后已删除临时 TEST-107 validation workflow。服务器 targeted connection 3 passed、HTTP contract 3 passed、full pytest 539 passed；工作树 clean；历史 migration diff blank。

## TEST-108 — Provider Error Contract — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：锁定 Provider 连接失败的稳定错误边界，避免 timeout、HTTP 429、malformed response 等上游异常直接泄漏实现细节、上游响应体或 API Key。

新增测试覆盖：
1. timeout → 统一 `LLMAnalysisError`；
2. HTTP 429 → 统一连接失败错误，不返回 upstream response body；
3. malformed JSON → 统一连接失败错误；
4. 错误信息不得包含测试 API Key 或敏感上游响应内容。

GitHub Actions run `35204873790`：targeted provider error contract tests passed、full pytest passed；随后已删除临时 TEST-108 validation workflow。服务器尚未验收，因此 TEST-108 暂不标记 VERIFIED。

## TEST-109 — Provider Base URL Contract — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：锁定 OpenAI-compatible provider 的 `base_url` 输入边界，避免将非法 URL、URL 内嵌凭据、query/fragment 等不应作为 API endpoint 配置的内容持久化并进入 runtime。

新增测试覆盖：
1. HTTP / HTTPS URL 必须包含 host；
2. URL 内嵌 username/password 被拒绝；
3. query / fragment 被拒绝；
4. 保存配置时规范化 trailing slash；
5. 合法 URL 可以进入现有 provider materialization；
6. 不修改数据库 schema / migration。

GitHub Actions run `35205313729`：targeted provider URL contract tests 8 passed、full pytest 550 passed、1 warning；随后已删除临时 TEST-109 validation workflow。服务器尚未验收，因此 TEST-109 暂不标记 VERIFIED。

## TEST-110 — Provider Capability / Analysis Contract — CONTRACT LOCKED / GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：明确“Provider connection test 成功”只证明当前 API endpoint / credential / model 能完成轻量 chat-completions 请求，不等于该模型已经满足正式业务 Analysis capability；正式 Analysis 必须继续通过现有 JSON object 与 `StructuredAnalysis` schema validation。

本阶段采用 contract-lock 而不是新增公共 capabilities API，避免在没有产品需求时引入第二套 capability registry 或静态宣称模型能力。

新增测试覆盖：
1. connection test 成功后，合法 StructuredAnalysis 仍按现有 Analysis pipeline 成功；
2. connection test 返回普通文本 `OK` 不得被正式 Analysis 当成成功；
3. JSON array 等非 object structured result 必须被拒绝；
4. 保持现有 selected model / `response_format={"type":"json_object"}` provider 行为由既有 Qwen Provider 测试覆盖；
5. 不修改生产 Provider 实现，不新增 endpoint，不修改数据库 schema / migration。

首次 GitHub run `35205937727` 因测试对内部错误文案绑定过严失败；修正为只锁定 `LLMAnalysisError` 业务边界，没有修改生产代码。GitHub Actions run `35209692341`：TEST-110 targeted 3 passed、既有 Qwen Provider 5 passed、full pytest 553 passed、1 warning；随后删除临时 TEST-110 validation workflow。相对 TEST-109 基线的最终功能差异仅为 TEST-110 contract test；无 migration 变化。服务器尚未验收，因此 TEST-110 暂不标记 VERIFIED。

## 产品化后续审计方向

完成 TEST-108 ~ TEST-110 服务器验收后，继续审计：
1. provider rate-limit / timeout / retry 契约；
2. API Key、请求头及敏感错误信息的日志泄漏边界；
3. 前端设置页与分析工作流；
4. 正式认证替换当前 `X-User-ID` 信任边界；
5. 发布与运行时安全。

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
