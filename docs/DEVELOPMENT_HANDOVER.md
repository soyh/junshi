# Development Handover

更新时间：2026-09-17
当前阶段：TEST-119 — Password Change / Credential Rotation — VERIFIED
当前 Branch：test-119-password-change
服务器验收代码 HEAD：`04b3c84e7ebdd7250db4bbcf15b7f333b93f0e77`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-090：按既有交接记录 VERIFIED；TEST-091 CONTRACT LOCKED；TEST-092 VERIFIED；TEST-093 VERIFIED；TEST-094 CONTRACT LOCKED。

TEST-095 VERIFIED — Recommendation / Action Plan persistence bridge；migration 008。
TEST-096 VERIFIED — Decision → Execution → Outcome safety。
TEST-097 VERIFIED — evidence-backed proposal freshness。
TEST-098 VERIFIED — Action Plan snapshot isolation。
TEST-099 VERIFIED — Action Plan persistence gate。
TEST-100 VERIFIED — proposal / execution gate。
TEST-101 VERIFIED — Execution scope isolation；full 526。
TEST-102 VERIFIED — Outcome DB idempotency；migration 009；full 528。
TEST-103 VERIFIED — duplicate Outcome → HTTP 409；full 529。
TEST-104 VERIFIED — user-scoped LLM Provider config；migration 010；full 530。
TEST-105 VERIFIED — Provider Runtime Routing；full 532。
TEST-106 VERIFIED — Provider Runtime Materialization；full 533。
TEST-107 VERIFIED — Provider Connection Test；full 539。
TEST-108 VERIFIED — Provider Error Contract。
TEST-109 VERIFIED — Provider URL Contract。
TEST-110 VERIFIED — Provider Capability / StructuredAnalysis；full 553。
TEST-111 VERIFIED — Provider Timeout / 429 / No-Retry；full 562。
TEST-112 VERIFIED — Provider Log Redaction；full 568。
TEST-113 VERIFIED — Provider Settings UI；服务器 full 571；HEAD `b59b7625ffd8a391835545852ce981871da32580`。
TEST-114 VERIFIED — Production Authentication Boundary；服务器 full 578；HEAD `693946882ca780eafc0367dfa26a3b7f0ea06f84`。
TEST-115 VERIFIED — DB-backed opaque Auth Session；migration 011；服务器 full 585；HEAD `a76c6907fa51afeee0076822601745c8ac3e4fb2`。
TEST-116 VERIFIED — Account credentials / login → server-issued session；migration 012；服务器 full 592；HEAD `bf84a5c068813693715fa0b09ce5458d59b7356e`。
TEST-117 VERIFIED — Multi-device session management / bootstrap retirement；服务器 full 599；HEAD `af4995a8e5fccd8586e63e3e76191552ecb317b1`。
TEST-118 VERIFIED — SQLite login throttle / progressive lockout；服务器 targeted 8、account login 7、session management 7、auth session 7、production auth 7、scope isolation 4、full 607 passed in 111.95s；工作树 clean；migration diff 仅 `013_auth_login_throttle.sql`；服务器 HEAD `c3f542a1b034bdfb0278eaace838efcd7c868ac7`。
TEST-119 VERIFIED — authenticated password change / credential rotation；服务器 targeted 8、TEST-118 throttle 8、account login 7、session management 7、auth session 7、production auth 7、scope isolation 4、full 615 passed in 113.91s；工作树 clean；migration diff blank；服务器 HEAD `04b3c84e7ebdd7250db4bbcf15b7f333b93f0e77`。

## Auth 产品化基线

- TEST-114：production 禁止 `X-User-ID`；静态 `AUTH_BEARER_TOKEN → LOCAL_USER_ID` 仅作迁移 bootstrap。
- TEST-115：opaque session 只存 SHA-256 hash，支持 expiry/revoke，服务端解析到 `users.id`。
- TEST-116：normalized username + scrypt password；服务器生成 user_id；注册/登录签发同一 session。
- TEST-117：session list/current/revoke-other/rotate；静态 bootstrap 有显式 disable 路径。
- TEST-118：SQLite username-subject login throttle / progressive lockout，不依赖 Redis 或未验证代理 IP。
- TEST-119：改密必须同时持有真实 DB session 并重新验证 current password；成功后撤销同用户全部旧 session，再签发新的唯一继续 session。

## TEST-119 — Password Change / Credential Rotation — VERIFIED

目标：建立 authenticated password change，不把“已有 session”当作足够的改密凭据；改密后立即切断所有旧设备 session，避免旧 session 在 credential rotation 后继续存活。

已建立：
1. `PUT /api/v1/auth/password`，请求只接受 `current_password / new_password`，两者均为 `SecretStr`；客户端不能提交 `user_id`；
2. 只允许真实 active DB auth session 改密；静态 bootstrap token 即使可认证，也不能调用 password change；
3. 服务端再次校验 current password；错误时统一 `401 invalid current password`，不回显输入密码；
4. new password 继续使用 TEST-116 `scrypt_v1` 参数和随机 salt，不增加第二套 password hash 实现；
5. password hash 更新、旧 session 全量 revoke、新 session 创建都发生在同一 SQLite transaction；任一步失败均回滚；
6. 改密成功后同用户全部既有 session立即失效，返回新的 opaque session；
7. 新 password 可重新登录，旧 password 不再可用；
8. session revocation 严格按 `user_id`，其他用户 session 不受影响；
9. `AuthSessionService.revoke_all_for_user()` 只作用于指定 user scope；
10. 不新增 migration，不修改历史 migration 001~013；不实现没有验证渠道的 account recovery。

服务器验收：
- `backend/tests/test_auth_password_change.py`：8 passed；
- `backend/tests/test_auth_login_throttle.py`：8 passed；
- `backend/tests/test_auth_account_login.py`：7 passed；
- `backend/tests/test_auth_session_management.py`：7 passed；
- `backend/tests/test_auth_session_boundary.py`：7 passed；
- `backend/tests/test_auth_boundary.py`：7 passed；
- execution/action-plan scope isolation：4 passed；
- full pytest：615 passed in 113.91s；
- `git status --short` blank；
- migration diff blank；
- 最终文件差异与 GitHub 预期一致。

TEST-119 VERIFIED。

## 下一阶段

仓库审计确认当前没有 SMTP、短信、Twilio/SendGrid/Resend、OAuth/OIDC 或其他可验证 account recovery channel；因此不得伪造 forgot-password / recovery credential 流程。

TEST-120 优先转向 Auth Account UI：
1. 用现有 FastAPI-served UI 方式提供 register/login/account/session 页面，不引入 Node 前端；
2. UI 调用 TEST-116~119 已 VERIFIED API，不建立第二套认证逻辑；
3. access token 只保存在页面内存，不进入 localStorage/sessionStorage；
4. 支持 session list / revoke other / rotate / logout / password change；
5. password change 返回的新 token 必须替换页面内当前 token；
6. 明确提示 account recovery 当前不可用，不提供伪恢复按钮；
7. 后续再处理 bootstrap 默认关闭、development `X-User-ID` 退场、release/runtime security 与完整产品 UI。

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
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~119 verification tag 已创建。
