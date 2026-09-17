# Development Handover

更新时间：2026-09-17
当前阶段：TEST-120 — Auth Account / Session UI — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-120-auth-account-ui
TEST-119 VERIFIED 服务器代码 HEAD：`04b3c84e7ebdd7250db4bbcf15b7f333b93f0e77`

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
TEST-119 VERIFIED — authenticated password change / credential rotation；服务器 targeted 8、TEST-118 throttle 8、account login 7、session management 7、auth session 7、production auth 7、scope isolation 4、full 615 passed in 113.91s；工作树 clean；migration diff blank；服务器 HEAD `04b3c84e7ebdd7250db4bbcf15b7f333b93f0e77`。
TEST-120 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — FastAPI-served account/session UI；GitHub targeted UI 4、password change 8、login throttle 8、account login 7、session management 7、Provider UI 3、scope isolation 4、full 619 passed；无新 migration。

## Auth 产品化基线

- TEST-114：production 禁止 `X-User-ID`；静态 bootstrap 仅作迁移兼容。
- TEST-115：DB-backed opaque session，仅存 SHA-256 token hash。
- TEST-116：normalized username + scrypt password；注册/登录签发 server-side session。
- TEST-117：多设备 session list / revoke / rotate；bootstrap 有 disable 路径。
- TEST-118：SQLite login throttle / progressive lockout。
- TEST-119：password change 必须 active DB session + current password；成功后全部旧 session revoke 并签发新 session。
- TEST-120：最小可用 Auth UI 只调用既有 VERIFIED API，不复制认证逻辑。

## TEST-120 — Auth Account / Session UI — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：把 TEST-116~119 已 VERIFIED 的账号认证能力形成最小可用界面，同时保持 token、密码与 recovery 安全边界。

已建立：
1. `GET /api/v1/auth/ui` 返回 FastAPI-served HTML 页面，`include_in_schema=False`；不引入 Node 前端；
2. 页面支持 register / login，并只调用既有 `/api/v1/auth/register` 与 `/api/v1/auth/login`；
3. 当前 session token 只保存在页面 JavaScript 变量 `currentAccessToken` 中，不提供 token 输入框，不写入浏览器持久化 storage，不写入页面 DOM；刷新/关闭页面后需重新登录；
4. authenticated API 统一使用 `Authorization: Bearer <current session>`；不使用 `X-User-ID`；
5. session UI 支持 list、按 id revoke 其他 session、revoke all others、rotate current、logout current；
6. session list 只渲染已由 TEST-117 API 允许暴露的 id/current/created/expires 元数据，不显示 token/token hash；
7. password change 调用 TEST-119 `/api/v1/auth/password`；成功返回的 fresh session 会替换页面内旧 token；current/new password 输入均为 password field，操作后清空；
8. 页面只用 `textContent` / `createElement` 渲染，不使用 `innerHTML`；
9. account recovery 仅明确显示 unavailable；仓库没有 verified email/SMS/OAuth/OIDC recovery channel，因此不提供 recover/reset endpoint 或伪恢复按钮；
10. 无新 migration，未修改历史 migration 001~013。

新增 `backend/tests/test_auth_account_ui.py` 4 个契约测试：
- UI 可访问且隐藏于 OpenAPI；
- token 仅页面内存，页面源中无持久化 storage API、无 `X-User-ID`、无 `innerHTML`、无 access-token input；
- 页面只调用既有 VERIFIED auth/session/password API，敏感输入使用 password field；
- recovery 明确 unavailable 且无 recover/reset/forgot-password 路径。

GitHub Actions：
- 第一轮 run `35244615826`：3 passed / 1 failed；失败原因是页面说明文字本身包含持久化 storage API 名称，测试按严格源代码契约判定失败；未放宽测试，而是修改说明文案，保持页面源完全不包含这些 API 标识；
- 第二轮 run `35244730099`：success；
  - TEST-120 Auth UI：4 passed；
  - TEST-119 password change：8 passed；
  - TEST-118 login throttle：8 passed；
  - account login：7 passed；
  - session management：7 passed；
  - Provider Settings UI：3 passed；
  - execution/action-plan scope isolation：4 passed；
  - full pytest：619 passed、1 warning in 146.23s；
- warning 为已知 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 validation workflow 已删除。

当前等待服务器验收后再标记 TEST-120 VERIFIED。

## 下一阶段候选

TEST-120 服务器通过后重新审计决定 TEST-121。优先检查：
1. production bootstrap 默认关闭/静态 bootstrap 进一步退场；
2. development/test `X-User-ID` 长期兼容路径是否可以收口；
3. release/runtime security：HTTPS、CORS/CSRF、reverse-proxy trust、access log；
4. 将 Provider Settings 与 Auth UI 接入统一产品导航；
5. recovery 必须等真实 verified channel 接入后再实现。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~120 verification tag 已创建。
