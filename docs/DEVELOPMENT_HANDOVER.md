# Development Handover

更新时间：2026-09-17
当前阶段：TEST-106 — Provider Runtime Materialization — VERIFIED
当前 Branch：test-106-provider-http-contract

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

## TEST-104 — VERIFIED

目标：让用户能够按 user scope 保存自己的 OpenAI-compatible API Key、Base URL、Model、Timeout，并让现有 Analysis / Strategy / Recommendation / Strategic Reply / Action Plan analysis routes 使用该配置；没有用户配置时保持原有 Qwen 默认行为。

已建立：user-scoped provider config、Fernet API key encryption、GET/PUT/DELETE `/api/v1/settings/llm`、`openai_compatible` provider、`LLM_CONFIG_ENCRYPTION_KEY`、requirements 中 `cryptography==46.0.5`，以及对现有分析入口的配置读取。

## TEST-105 — Provider Runtime Routing — VERIFIED

目标：验证 TEST-104 保存的 provider configuration 不只是“设置 API”，而是实际进入各 AI 分析入口；同时验证无配置时保持原有 Qwen fallback。

覆盖入口：
- Structured Analysis
- Strategy
- Recommendation
- Strategic Reply
- Action Plan Analysis

新增 `backend/tests/test_llm_provider_runtime_routing.py`，验证 configured provider 与 Qwen fallback 均覆盖全部上述入口。

GitHub Actions run `35202685438`：targeted 2 passed、full pytest 532 passed；临时 validation workflow 已删除。服务器随后完成同等 targeted/full 验收，结果一致，migration diff blank。

## TEST-106 — Provider Runtime Materialization — VERIFIED

目标：锁定 user-scoped persisted provider configuration 在 runtime 中实际 materialize 为 Provider 实例参数，而不是只验证“拿到了某个 Provider 对象”。

新增 `backend/tests/test_llm_provider_runtime_materialization.py`，验证：
1. persisted `api_key_encrypted` 经解密后传入 provider；
2. persisted `base_url`、`model`、`timeout_seconds` 均传入 provider；
3. provider 类型仍为现有 `QwenProvider` adapter，不建立第二套 provider 实现。

GitHub Actions run `35203595737`：targeted materialization + existing Qwen provider tests、full pytest 均 success；临时 validation workflow 已删除。服务器验收：targeted 1 passed、full pytest 533 passed、工作树 clean、历史 migration diff blank。

## 产品化后续审计方向

TEST-106 服务器验收通过后，继续审计：
1. provider connection test / 实际第三方 HTTP 调用的产品化边界；
2. provider/model capability；
3. 前端设置页与分析工作流；
4. 正式认证替换当前 `X-User-ID` 信任边界；
5. 发布与运行时安全。

不应仅凭 MockTransport 单元测试假定第三方模型调用已经完成产品化闭环。

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
