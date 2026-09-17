# Development Handover

更新时间：2026-09-17
当前阶段：TEST-114 — Production Authentication Boundary — VERIFIED / PAUSED
当前 Branch：test-114-production-auth-boundary
服务器验收代码 HEAD：`693946882ca780eafc0367dfa26a3b7f0ea06f84`

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

TEST-104 VERIFIED — user-selectable LLM Provider / API configuration；服务器 targeted 1 passed、full 530 passed；工作树 clean；历史 migration 001~009 未修改。

TEST-105 VERIFIED — Provider Runtime Routing；服务器 targeted 2 passed、full 532 passed；工作树 clean；历史 migration diff blank。

TEST-106 VERIFIED — Provider Runtime Materialization；服务器 targeted 1 passed、full 533 passed；工作树 clean；历史 migration diff blank。

TEST-107 VERIFIED — Provider Connection Test；服务器 targeted connection 3 passed、HTTP contract 3 passed、full pytest 539 passed；工作树 clean；历史 migration diff blank。

TEST-108 VERIFIED — Provider Error Contract；服务器 targeted 3 passed；最终 full pytest 553 passed；工作树 clean；migration diff blank。

TEST-109 VERIFIED — Provider Base URL Contract；服务器 targeted 8 passed；最终 full pytest 553 passed；工作树 clean；migration diff blank。

TEST-110 VERIFIED — Provider Capability / Analysis Contract；服务器 targeted 3 passed、既有 Qwen Provider 5 passed、full pytest 553 passed；工作树 clean；migration diff blank；服务器 HEAD `2de393a29dc7419654321e558ad3dd4f69928405`。

TEST-111 VERIFIED — Provider Timeout / Rate-Limit / No-Retry Contract；服务器 targeted 9 passed、Provider Error Contract 3 passed、Provider Connection 3 passed、full pytest 562 passed；工作树 clean；migration diff blank；服务器 HEAD `4d750c571f64f14ece97b19f84e000c3c4950275`。

TEST-112 VERIFIED — Provider Log Redaction / Exception Boundary；服务器 targeted 6 passed、provider config/materialization 2 passed、provider error/connection 6 passed、full pytest 568 passed；工作树 clean；migration diff blank；服务器 HEAD `3bb10a300cf7d09614c4e271c3415328ce7a939a`。

TEST-113 VERIFIED — Provider Settings UI / Analysis Entry；服务器 targeted UI contract 3 passed、provider config/redaction 7 passed、full pytest 571 passed in 89.15s；工作树 clean；相对 TEST-112 migration diff blank；服务器 HEAD `b59b7625ffd8a391835545852ce981871da32580`。

TEST-114 VERIFIED — Production Authentication Boundary；服务器 auth boundary 7 passed、Provider UI auth regression 3 passed、Provider security regression 7 passed、full pytest 578 passed in 89.48s；工作树 clean；相对 TEST-113 migration diff blank；服务器验收代码 HEAD `693946882ca780eafc0367dfa26a3b7f0ea06f84`。

## TEST-104 ~ TEST-112 — Provider 产品化与安全边界

TEST-104 建立 user-scoped OpenAI-compatible Provider 配置：API Key、Base URL、Model、Timeout；API Key 通过 Fernet 加密持久化，GET 响应只返回 `api_key_configured`，无用户配置时保持 Qwen fallback。

TEST-105/106 锁定 persisted configuration 会真实进入所有 Analysis 路由及 Provider constructor 参数，包括解密后的 API key、base_url、model、timeout_seconds。

TEST-107 增加独立 `POST /api/v1/settings/llm/test` connection test；connection success 仅证明 endpoint / credential / model 可完成轻量请求，不代表正式 Analysis capability。

TEST-108/109/110 锁定错误归一化、合法 Provider URL、connection 与 StructuredAnalysis capability 的边界；正式 Analysis 仍必须通过 JSON object 与 `StructuredAnalysis` schema validation。

TEST-111 明确当前 Provider 不执行隐式自动 retry：timeout / 429 第一次失败即归一化为 `LLMAnalysisError`，避免隐藏重复计费和不可控延迟。

TEST-112 建立 secret/log boundary：Provider API Key 使用 `SecretStr`；root logging handler 统一脱敏 Authorization、Bearer token、API key、encryption key；Provider/service 归一化上游异常时截断 raw exception cause，避免 secret / upstream body 进入 traceback。

## TEST-113 — Provider Settings UI / Analysis Entry — VERIFIED

目标：在当前没有独立 Web 前端工程的仓库里建立最小、可直接服务的 Provider 设置页面，并只复用既有 Provider API 和 Structured Analysis API。

已建立：
1. `GET /api/v1/settings/llm/ui` 轻量 HTML UI，并从 OpenAPI schema 隐藏；
2. Provider 设置只调用既有 `GET/PUT/DELETE /api/v1/settings/llm` 与 `POST /api/v1/settings/llm/test`；
3. API Key 使用 password input，不使用 localStorage/sessionStorage，不从服务端回填，保存后立即清空；
4. 页面只用 `textContent` 展示返回值，不使用 `innerHTML` 注入；
5. 页面提供 Conversation ID 输入并调用既有 Structured Analysis API；
6. 不新增数据库 schema / migration，不建立第二套 Provider / Analysis 逻辑。

GitHub Actions run `35226450034`：targeted 3 passed、provider config/redaction 7 passed、full 571 passed；临时 workflow 已删除。服务器最终验收完全通过，TEST-113 VERIFIED。

## TEST-114 — Production Authentication Boundary — VERIFIED

目标：消除生产环境直接信任客户端 `X-User-ID` 的身份伪造边界，同时保留 development/test 的兼容迁移窗口。

当前认证契约：
1. `APP_ENV=production` 时禁止客户端 `X-User-ID` 身份声明；
2. production 请求必须使用 `Authorization: Bearer <token>`；
3. Bearer token 与服务端 `AUTH_BEARER_TOKEN` 使用常量时间比较；
4. 合法 token 映射到服务端配置的 `LOCAL_USER_ID`，客户端不提供 user_id；
5. 缺少/错误 Bearer token → HTTP 401；production 使用 `X-User-ID` → HTTP 401；
6. production 未配置 `AUTH_BEARER_TOKEN` → HTTP 503，fail closed；
7. development/test 暂保留旧 `X-User-ID` / local-user fallback，以避免一次性破坏既有回归契约；
8. TEST-113 Provider UI 已切换到 Bearer token，不再手工输入 user id；
9. `AUTH_BEARER_TOKEN` 已纳入日志敏感字段脱敏；
10. 未新增 migration，未修改历史 migration。

GitHub Actions run `35229312839`：auth boundary 7 passed、Provider UI 3 passed、Provider security 7 passed、full pytest 578 passed、1 warning；临时 workflow 已删除。

服务器验收：
- `backend/tests/test_auth_boundary.py`：7 passed；
- `backend/tests/test_llm_provider_settings_ui.py`：3 passed；
- Provider security regression：7 passed；
- full pytest：578 passed in 89.48s；
- `git status --short` blank；
- 相对 TEST-113 baseline `backend/migrations` diff blank；
- 最终业务文件差异与 GitHub 预期一致。

TEST-114 VERIFIED。

## 当前暂停点 / 下一阶段

按用户要求，项目当前暂停在 TEST-114 VERIFIED，不启动 TEST-115。

恢复后优先方向：
1. 从当前单用户、服务端静态 Bearer token 边界升级到真正的多用户 authenticated identity：session/token → server-resolved `user_id`；
2. 逐步移除 development/test 对任意 `X-User-ID` 的兼容依赖，而不是让客户端继续决定身份；
3. 用户登录/注册/session 生命周期、token revoke/rotation、密码或外部身份提供方策略；
4. 继续发布与运行时安全：secret rotation、process environment、reverse-proxy access log、HTTPS/CORS/CSRF 等；
5. 再推进完整产品 UI，而不是提前建立与当前后端契约重复的第二套业务逻辑。

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
- connection test 成功不等于正式 Analysis capability 成功；正式 Analysis 必须继续通过 StructuredAnalysis validation。
- 当前 Provider 不执行隐式自动 retry。
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113/114 verification tag 已创建。
