# Development Handover

更新时间：2026-09-17
当前阶段：TEST-116 — Account Credentials / Login → Server-issued Session — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-116-account-login-session
TEST-115 VERIFIED 基线：`a76c6907fa51afeee0076822601745c8ac3e4fb2`

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

TEST-102 VERIFIED — DB-level Outcome idempotency；migration 009 `uq_action_outcomes_decision`；full 528 passed。

TEST-103 VERIFIED — Outcome DB duplicate → HTTP 409；full 529 passed。

TEST-104 VERIFIED — user-scoped LLM Provider configuration；migration 010 `user_llm_provider_configs`；full 530 passed。

TEST-105 VERIFIED — Provider Runtime Routing；full 532 passed。

TEST-106 VERIFIED — Provider Runtime Materialization；full 533 passed。

TEST-107 VERIFIED — Provider Connection Test；full 539 passed。

TEST-108 VERIFIED — Provider Error Contract。

TEST-109 VERIFIED — Provider Base URL Contract。

TEST-110 VERIFIED — Provider Capability / StructuredAnalysis Contract；full 553 passed。

TEST-111 VERIFIED — Provider Timeout / 429 / No-Retry Contract；full 562 passed。

TEST-112 VERIFIED — Provider Log Redaction / Exception Boundary；full 568 passed。

TEST-113 VERIFIED — Provider Settings UI / Structured Analysis Entry；服务器 targeted 3、provider config/redaction 7、full 571 passed；服务器 HEAD `b59b7625ffd8a391835545852ce981871da32580`。

TEST-114 VERIFIED — Production Authentication Boundary；服务器 auth 7、UI 3、security 7、full 578 passed；production 禁止 `X-User-ID`，使用静态 Bearer bootstrap；服务器验收代码 HEAD `693946882ca780eafc0367dfa26a3b7f0ea06f84`。

TEST-115 VERIFIED — DB-backed opaque Auth Session / Server-resolved User Boundary；服务器 session 7、TEST-114 auth regression 7、scope isolation 4、full 585 passed in 95.17s；工作树 clean；相对 TEST-114 只新增 migration 011；服务器 HEAD `a76c6907fa51afeee0076822601745c8ac3e4fb2`。

TEST-116 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — 本地账号凭据注册/登录 → server-issued TEST-115 session；GitHub account/login 7、session regression 7、production auth regression 7、scope isolation 4、full 592 passed；新增 migration 012，未修改历史 migration 001~011。

## TEST-104 ~ TEST-112 — Provider 产品化与安全边界

- user-scoped OpenAI-compatible Provider 配置：API Key / Base URL / Model / Timeout。
- API Key 通过 Fernet 加密持久化；GET 不返回原始 key。
- persisted provider configuration 会真实进入所有 Analysis 路由和 Provider constructor。
- 独立 connection test 与正式 StructuredAnalysis capability 分离。
- Provider URL、timeout、429、no-retry、error normalization 均有契约测试。
- `SecretStr` + centralized logging redaction 保护 API Key / Authorization / Bearer / encryption key。
- Provider/service 归一化未知异常时截断 raw exception cause，避免 secret 泄漏。

## TEST-113 — Provider Settings UI — VERIFIED

当前仓库没有独立 Node/Web 前端工程，因此建立 FastAPI-served 最小设置 UI：
1. `GET /api/v1/settings/llm/ui`；
2. 只复用现有 Provider API 与 Structured Analysis API；
3. API Key password input，不持久化到 localStorage/sessionStorage，不回填；
4. 状态输出使用 `textContent`，不使用 `innerHTML` 注入；
5. TEST-114 后 UI 使用 Bearer token，不再手工提交 user_id。

## TEST-114 — Production Authentication Boundary — VERIFIED

生产认证契约：
1. `APP_ENV=production` 禁止客户端 `X-User-ID`；
2. Bearer token 与服务端 `AUTH_BEARER_TOKEN` 常量时间比较；
3. 静态合法 token 仅映射到 `LOCAL_USER_ID`，作为 bootstrap compatibility；
4. 缺 token / 错 token → 401；production 未配置 auth token → 503 fail closed；
5. development/test 暂保留 legacy `X-User-ID` 兼容，以避免一次破坏历史回归；
6. auth token 纳入日志脱敏。

## TEST-115 — Auth Session / Server-resolved User Boundary — VERIFIED

目标：从静态 bootstrap token 迈向真正多用户的 server-resolved identity。

已建立：
1. migration 011 `auth_sessions`：`id / user_id / token_hash / expires_at / revoked_at / created_at`；
2. opaque token 使用 `secrets.token_urlsafe(32)`，数据库只存 SHA-256 token hash；
3. session 支持 expiry / revoke；
4. `get_current_user_id()` 优先把 Bearer session 解析到 `users.id`，再兼容 TEST-114 静态 bootstrap；
5. `POST /api/v1/auth/sessions` 只能为已认证的自己创建 session，客户端不能指定 user_id；
6. `DELETE /api/v1/auth/session` 只吊销当前真实 DB session；
7. 不同 session 可以解析到不同 users，并继续复用既有 Person / Relationship / Conversation scope isolation。

服务器验收：
- `backend/tests/test_auth_session_boundary.py`：7 passed；
- `backend/tests/test_auth_boundary.py`：7 passed；
- execution/action-plan scope isolation：4 passed；
- full pytest：585 passed in 95.17s；
- `git status --short` blank；
- migration diff：仅 `A backend/migrations/011_auth_sessions.sql`；
- 最终文件差异与 GitHub 预期一致。

TEST-115 VERIFIED。

## TEST-116 — Account Credentials / Login → Server-issued Session — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：让普通用户无需静态 bootstrap token 即可注册/登录，并由服务器签发 TEST-115 opaque session；客户端仍不能决定 user_id。

本阶段新增：
1. migration 012 `user_credentials`：`user_id` 主键/外键、唯一 normalized `username`、`password_hash`、timestamps；
2. `POST /api/v1/auth/register`：服务器生成 UUID `users.id`，写入 credential，并直接签发 TEST-115 session；
3. `POST /api/v1/auth/login`：username/password 验证成功后签发新的 TEST-115 session；
4. username trim + lowercase normalization，允许 `[A-Za-z0-9._-]`，长度 3~64；
5. 注册密码至少 12 字符；credential request 使用 `SecretStr` 且 `extra=forbid`，明确拒绝客户端传 `user_id` 等额外身份字段；
6. 密码使用 Python 标准库 `hashlib.scrypt`，随机 salt，参数 `N=16384, r=8, p=1`，数据库不保存明文密码；
7. 登录时使用 constant-time digest compare；未知 username 也执行 dummy password verification，再统一返回 `401 {"detail":"invalid credentials"}`，避免通过错误响应区分账号存在性；
8. 登录产生的新 session 与注册 session 映射同一 server-side user scope；
9. 不改变 TEST-114 bootstrap fallback，不建立第二套 token/session 实现；
10. 不修改历史 migration 001~011，不新增 PostgreSQL/Redis/ES/向量库。

新增 `backend/tests/test_auth_account_login.py` 7 个测试，覆盖：
- register → server-resolved user session；
- normalized username / scrypt password hash / token hash 持久化；
- login → 同一 user scope 的新 session；
- wrong password 与 unknown user 相同失败契约；
- case-insensitive duplicate username；
- 短密码注册拒绝且不落库；
- 客户端 selected `user_id` 被 schema 拒绝。

GitHub Actions run `35235920273`：
- TEST-116 account/login：7 passed；
- TEST-115 auth session regression：7 passed；
- TEST-114 production auth regression：7 passed；
- execution/action-plan scope isolation：4 passed；
- full pytest：592 passed、1 warning；
- 临时 validation workflow 已删除。

当前等待服务器验收后再标记 TEST-116 VERIFIED。

## 下一阶段候选

TEST-116 服务器验收通过后优先：
1. TEST-117 多设备 session 管理 / list / revoke-other / rotation，并定义 bootstrap token 退场路径；
2. 登录暴力尝试防护与 rate-limit / lockout 契约；
3. password change / credential rotation / account recovery 边界；
4. 逐步移除 development/test 对任意 `X-User-ID` 的兼容依赖；
5. release/runtime security：secret rotation、reverse-proxy access log、HTTPS/CORS/CSRF；
6. 完整产品 UI / login flow。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~116 verification tag 已创建。
