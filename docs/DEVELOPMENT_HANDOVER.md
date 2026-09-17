# Development Handover

更新时间：2026-09-17
当前阶段：TEST-123 — HTTP Security Boundary — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-123-http-security-boundary
TEST-121 VERIFIED 服务器代码 HEAD：`43b514a5dfa454b85424b3abe5a96ffb93da0c24`

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
TEST-118 VERIFIED — SQLite login throttle / progressive lockout；服务器 full 607；migration 013；HEAD `c3f542a1b034bdfb0278eaace838efcd7c868ac7`。
TEST-119 VERIFIED — authenticated password change / credential rotation；服务器 full 615；HEAD `04b3c84e7ebdd7250db4bbcf15b7f333b93f0e77`。
TEST-120 VERIFIED — FastAPI-served account/session UI；服务器 full 619；HEAD `456cd94bacb85655c53a892f23cba742af76d925`。
TEST-121 VERIFIED — production bootstrap default retirement；服务器 full 625；HEAD `43b514a5dfa454b85424b3abe5a96ffb93da0c24`。
TEST-122 GITHUB SELF-TEST PASSED / SERVER VALIDATION DEFERRED — legacy `X-User-ID` retired；full 630 passed。
TEST-123 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — HTTP security response boundary；full 636 passed。

## Auth / Runtime 产品化基线

- TEST-114：production 禁止 `X-User-ID`；静态 bootstrap 仅作迁移兼容。
- TEST-115：DB-backed opaque session，仅存 SHA-256 token hash。
- TEST-116：normalized username + scrypt password；注册/登录签发 server-side session。
- TEST-117：多设备 session list / revoke / rotate；bootstrap 有显式 disable 路径。
- TEST-118：SQLite login throttle / progressive lockout。
- TEST-119：password change 必须 active DB session + current password；成功后全部旧 session revoke 并签发新 session。
- TEST-120：最小可用 Auth UI 只调用既有 VERIFIED API，不复制认证逻辑。
- TEST-121：静态 `AUTH_BEARER_TOKEN → LOCAL_USER_ID` bootstrap 默认关闭；只有显式 `AUTH_BOOTSTRAP_ENABLED=true` 才保留迁移/应急兼容。
- TEST-122：`X-User-ID` 在 production/development/test 均拒绝，不允许客户端通过 header 选择 `user_id`；development/test 无 Bearer 时仅固定 `LOCAL_USER_ID` fallback。
- TEST-123：全局基础安全响应头；auth/settings 响应 `Cache-Control: no-store`；默认不开放 permissive CORS；Bearer token 仍由响应 body 返回，不切换 Cookie。

## TEST-122 — Legacy X-User-ID Retirement — GITHUB SELF-TEST PASSED

目标：彻底结束 `X-User-ID` 作为身份来源的长期兼容路径。

实现与验证：
1. `get_current_user_id()` 在任何环境收到 `X-User-ID` 都返回 401；
2. valid DB session 与 `X-User-ID` 同时出现时也拒绝请求，避免 ambiguous identity；
3. development/test 无 Bearer、无旧 header 时仍固定使用 `LOCAL_USER_ID` fallback；
4. 原 full suite 有 47 个历史隔离测试用旧 header 模拟多用户。未恢复生产逻辑，而是在 pytest `client` fixture 内将非 auth-contract 测试中的旧 header 转换为真实 DB user + opaque session，再发送 `Authorization: Bearer <session>`；
5. 所有 `test_auth_*` 契约测试绕过适配器，继续直接验证应用拒绝 `X-User-ID`；
6. 无新 migration，历史 migration 001~013 未修改。

GitHub Actions：
- 第一轮 `35249866711`：targeted 全绿，full 因 47 个旧隔离测试失败；
- 第二轮 `35250994364`：success；TEST-122 4、production auth 8、bootstrap retirement 6、auth session 7、session management 7、account login 7、password change 8、Auth UI 4、scope isolation 4、full 630 passed、1 warning in 94.97s；
- 临时 workflow 已删除。

TEST-122 服务器验收与 TEST-123 合并执行，因此暂不单独标记 SERVER VERIFIED。

## TEST-123 — HTTP Security Boundary — GITHUB SELF-TEST PASSED

目标：在不假设生产域名、HTTPS termination 或 reverse proxy 拓扑的前提下，先建立与部署环境无关的 HTTP 响应安全底线。

实现：
1. `backend/app/main.py` 增加统一 HTTP middleware；
2. 正常应用响应统一设置：
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: no-referrer`
3. `/api/v1/auth*` 与 `/api/v1/settings*` 额外设置 `Cache-Control: no-store`；
4. health 等非敏感响应不被强制 `no-store`；
5. 默认 app 不启用 permissive CORS，带任意 `Origin` 的 health 响应不返回 `Access-Control-Allow-Origin`；
6. register 继续在 response body 返回 `token_type=bearer` + `access_token`，不写 `Set-Cookie`；
7. 暂不启用 HSTS：尚未锁定 TLS termination；
8. 暂不启用 strict CSP：现有 Auth/Provider UI 仍含 inline assets，需要单独迁移后再收紧；
9. 暂不启用 TrustedHost / proxy trust：生产域名和反代可信边界尚未锁定；
10. 无新 migration，历史 migration 001~013 未修改。

新增 `backend/tests/test_http_security_boundary.py` 6 个契约测试：全局安全头、404 安全头、auth no-store、settings no-store、health 不强制 no-store、无 permissive CORS、Bearer 不落 Cookie。

GitHub Actions run `35252416990`：success；
- TEST-123：6 passed；
- TEST-122：4 passed；
- production auth：8 passed；
- auth session：7 passed；
- account login：7 passed；
- password change：8 passed；
- Auth UI：4 passed；
- Provider UI：3 passed；
- scope isolation：4 passed；
- full pytest：636 passed、1 warning in 33.55s；
- warning 为已知 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 validation workflow 已删除。

当前等待服务器一次性验收 TEST-122 + TEST-123。

## 下一阶段候选

服务器通过后重新审计再定 TEST-124。优先候选：
1. production host / reverse proxy / HTTPS boundary，必须先读取真实部署拓扑再决定 TrustedHost/HSTS/proxy trust；
2. Auth UI 与 Provider Settings UI 统一产品导航；
3. release/runtime checklist、backup/restore、日志轮转和运行监控；
4. account recovery 仍等待真实 verified email/SMS/OIDC channel。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~123 verification tag 已创建。
