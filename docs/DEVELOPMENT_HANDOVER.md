# Development Handover

更新时间：2026-09-17
当前阶段：TEST-105 — Provider Runtime Routing — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-105-provider-runtime-routing

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

TEST-105 当前状态 — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING。

## TEST-104 — VERIFIED

目标：让用户能够按 user scope 保存自己的 OpenAI-compatible API Key、Base URL、Model、Timeout，并让现有 Analysis / Strategy / Recommendation / Strategic Reply / Action Plan analysis routes 使用该配置；没有用户配置时保持原有 Qwen 默认行为。

已建立：user-scoped provider config、Fernet API key encryption、GET/PUT/DELETE `/api/v1/settings/llm`、`openai_compatible` provider、`LLM_CONFIG_ENCRYPTION_KEY`、requirements 中 `cryptography==46.0.5`，以及对现有分析入口的配置读取。

## TEST-105 — Provider Runtime Routing

目标：验证 TEST-104 保存的 provider configuration 不只是“设置 API”，而是实际进入各 AI 分析入口；同时验证无配置时保持原有 Qwen fallback。

覆盖入口：
- Structured Analysis
- Strategy
- Recommendation
- Strategic Reply
- Action Plan Analysis

新增 `backend/tests/test_llm_provider_runtime_routing.py`，验证：
1. configured provider 由 `provider_config_service.build_provider()` 返回并被全部上述入口使用；
2. 未配置时各入口继续实例化 `QwenProvider()`。

GitHub Actions 自测 run `35202685438`：
- targeted：2 passed，1 warning；
- full pytest：532 passed，1 warning；
- workflow 已完成 success；
- 临时 TEST-105 validation workflow 已删除。

当前尚未进行服务器验收，因此 TEST-105 暂不标记 VERIFIED。

## 产品化后续审计方向

服务器验收 TEST-105 通过后，再继续审计真实第三方 provider HTTP 调用、provider connection test、provider/model capability、前端设置页，以及正式认证；不应仅凭单元测试假定第三方模型调用已经完成产品化闭环。

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
