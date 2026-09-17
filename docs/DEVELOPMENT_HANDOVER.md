# Development Handover

更新时间：2026-09-17
当前阶段：TEST-117 — Multi-device Session Management / Bootstrap Retirement — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-117-session-management
TEST-116 VERIFIED 服务器代码基线：`bf84a5c068813693715fa0b09ce5458d59b7356e`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-090：按既有交接记录 VERIFIED；TEST-091 CONTRACT LOCKED；TEST-092 VERIFIED；TEST-093 VERIFIED；TEST-094 CONTRACT LOCKED。

TEST-095 VERIFIED — Recommendation / Action Plan 跨请求 persistence bridge；migration 008 `action_plan_snapshots`。
TEST-096 VERIFIED — confirmed Decision → explicit Execution → Outcome safety；scope / duplicate / conflict gates。
TEST-097 VERIFIED — evidence-backed proposal freshness；stale snapshot 排除但不删除。
TEST-098 VERIFIED — Action Plan snapshot user/person isolation。
TEST-099 VERIFIED — Action Plan persistence gate。
TEST-100 VERIFIED — proposal gate + execution gate。
TEST-101 VERIFIED — Execution 精确 user/person/decision scope isolation；full 526 passed。
TEST-102 VERIFIED — DB-level Outcome idempotency；migration 009；full 528 passed。
TEST-103 VERIFIED — Outcome DB duplicate → HTTP 409；full 529 passed。
TEST-104 VERIFIED — user-scoped LLM Provider configuration；migration 010；full 530 passed。
TEST-105 VERIFIED — Provider Runtime Routing；full 532 passed。
TEST-106 VERIFIED — Provider Runtime Materialization；full 533 passed。
TEST-107 VERIFIED — Provider Connection Test；full 539 passed。
TEST-108 VERIFIED — Provider Error Contract。
TEST-109 VERIFIED — Provider Base URL Contract。
TEST-110 VERIFIED — Provider Capability / StructuredAnalysis Contract；full 553 passed。
TEST-111 VERIFIED — Provider Timeout / 429 / No-Retry Contract；full 562 passed。
TEST-112 VERIFIED — Provider Log Redaction / Exception Boundary；full 568 passed。
TEST-113 VERIFIED — Provider Settings UI / Structured Analysis Entry；服务器 full 571 passed；服务器 HEAD `b59b7625ffd8a391835545852ce981871da32580`。
TEST-114 VERIFIED — Production Authentication Boundary；服务器 full 578 passed；服务器 HEAD `693946882ca780eafc0367dfa26a3b7f0ea06f84`。
TEST-115 VERIFIED — DB-backed opaque Auth Session / Server-resolved User Boundary；服务器 full 585 passed；服务器 HEAD `a76c6907fa51afeee0076822601745c8ac3e4fb2`。
TEST-116 VERIFIED — 本地账号凭据注册/登录 → server-issued TEST-115 session；服务器 account/login 7、session regression 7、production auth regression 7、scope isolation 4、full 592 passed in 102.24s；工作树 clean；相对 TEST-115 仅新增 migration 012；服务器 HEAD `bf84a5c068813693715fa0b09ce5458d59b7356e`。
TEST-117 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — 多设备 session list/current/revoke/rotate + 静态 bootstrap 显式退场开关；GitHub targeted 7、TEST-116 7、TEST-115 7、TEST-114 7、scope isolation 4、full 599 passed；无新 migration，未修改历史 migration 001~012。

## TEST-104 ~ TEST-112 — Provider 产品化与安全边界

- user-scoped OpenAI-compatible Provider 配置：API Key / Base URL / Model / Timeout。
- API Key 通过 Fernet 加密持久化；GET 不返回原始 key。
- persisted provider configuration 会真实进入所有 Analysis 路由和 Provider constructor。
- 独立 connection test 与正式 StructuredAnalysis capability 分离。
- Provider URL、timeout、429、no-retry、error normalization 均有契约测试。
- `SecretStr` + centralized logging redaction 保护 API Key / Authorization / Bearer / encryption key。
- Provider/service 归一化未知异常时截断 raw exception cause，避免 secret 泄漏。

## TEST-113 ~ TEST-116 — Auth 产品化基线

TEST-113：FastAPI-served Provider Settings UI，Bearer token 调用既有 Provider/Analysis API，不持久化 API Key 到浏览器 storage。

TEST-114：production 禁止客户端 `X-User-ID`；静态 `AUTH_BEARER_TOKEN → LOCAL_USER_ID` 作为迁移 bootstrap；错误 token → 401，未配置且无 active session → 503 fail closed。

TEST-115：migration 011 `auth_sessions`；opaque token 只存 SHA-256 hash；支持 expiry/revoke；Bearer session 服务端解析到 `users.id`。

TEST-116：migration 012 `user_credentials`；注册/登录使用 normalized username + `hashlib.scrypt` password hash；服务器生成 user_id；成功后签发 TEST-115 session；错误账号/密码统一 `401 invalid credentials`。

## TEST-117 — Multi-device Session Management / Bootstrap Retirement — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：让同一账号可安全管理多个 server-issued session，并为 TEST-114 静态 bootstrap token 建立显式退场路径；不新增第二套 token 实现，不新增数据库 schema。

已建立：
1. `GET /api/v1/auth/sessions`：返回当前用户所有未过期、未吊销 session，仅暴露 `id / expires_at / created_at / current`，不返回 access token 或 token hash；
2. `DELETE /api/v1/auth/sessions/{session_id}`：只能按当前 authenticated `user_id` 撤销自己的 session；跨用户 session id 返回 404，不泄露归属；
3. `DELETE /api/v1/auth/sessions/others`：必须由真实 DB session 调用，一次撤销同用户除当前 session 外的其他 active sessions；
4. `POST /api/v1/auth/session/rotate`：必须由真实 DB session 调用；原 session 立即 revoke，返回新的 TEST-115 opaque session；旧 token 随即失效；
5. 静态 bootstrap token 不能伪装为可 rotation 的 DB session；
6. 新增 `AUTH_BOOTSTRAP_ENABLED`，默认 `true` 保持 TEST-114 兼容；设置为 `false` 后静态 `AUTH_BEARER_TOKEN` 不再被身份解析接受，但 TEST-116 account-issued DB session 继续正常工作；
7. `.env.example` 明确 bootstrap credential 为迁移期配置；
8. 未新增 migration，未修改历史 migration 001~012。

新增 `backend/tests/test_auth_session_management.py` 7 个测试，覆盖：
- session list / current marker / 不泄露 token；
- revoke 单个其他 session；
- 跨用户 session id revoke 隔离；
- revoke-other 保留当前 session；
- rotate 后旧 token 失效、新 token 有效；
- bootstrap token 不能 rotation；
- bootstrap disable 后静态 token 失效，但账号 session 继续有效。

GitHub Actions run `35238143687`：
- TEST-117 session management：7 passed；
- TEST-116 account/login regression：7 passed；
- TEST-115 auth session regression：7 passed；
- TEST-114 production auth regression：7 passed；
- execution/action-plan scope isolation：4 passed；
- full pytest：599 passed、1 warning in 102.56s；
- 临时 validation workflow 已删除。

当前等待服务器验收后再标记 TEST-117 VERIFIED。

## 下一阶段候选

TEST-117 服务器通过后优先：
1. TEST-118 登录暴力尝试防护 / rate-limit / progressive lockout 契约，避免 auth endpoint 被高频猜测；
2. password change / credential rotation / account recovery 边界；
3. 逐步把 `AUTH_BOOTSTRAP_ENABLED` 默认值切换到关闭，并最终移除静态 bootstrap；
4. 逐步移除 development/test 对任意 `X-User-ID` 的兼容依赖；
5. release/runtime security：secret rotation、reverse-proxy access log、HTTPS/CORS/CSRF；
6. 完整产品 login/session UI。

## 架构与持续禁止事项

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed 且等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 relationship 或伪造 Outcome。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle。
- 所有数据必须 user_id 隔离；Person / Relationship / Conversation 不得跨 scope 混用。
- 不修改历史 migration；新增 schema 必须使用新 migration。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- connection test 成功不等于正式 Analysis capability 成功；正式 Analysis 必须继续通过 StructuredAnalysis validation。
- 当前 Provider 不执行隐式自动 retry。
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~117 verification tag 已创建。
