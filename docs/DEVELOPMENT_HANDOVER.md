# Development Handover

更新时间：2026-09-17
当前阶段：TEST-121 — Production Bootstrap Retirement — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-121-production-bootstrap-retirement
TEST-120 VERIFIED 服务器代码 HEAD：`456cd94bacb85655c53a892f23cba742af76d925`
TEST-120 VERIFIED handover commit：`eaafcd69570a191ec6584345bdcc7bce1cb8c2b2`

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
TEST-120 VERIFIED — FastAPI-served account/session UI；服务器 Auth UI 4、password change 8、login throttle 8、account login 7、session management 7、Provider UI 3、scope isolation 4、full 619 passed in 116.18s；工作树 clean；migration diff blank；服务器 HEAD `456cd94bacb85655c53a892f23cba742af76d925`。
TEST-121 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — production bootstrap default retirement；GitHub TEST-121 6、production auth 7、auth-session boundary 7、session management 7、account login 7、password change 8、Auth UI 4、scope isolation 4、full 625 passed；无新 migration。

## Auth 产品化基线

- TEST-114：production 禁止 `X-User-ID`；静态 bootstrap 仅作迁移兼容。
- TEST-115：DB-backed opaque session，仅存 SHA-256 token hash。
- TEST-116：normalized username + scrypt password；注册/登录签发 server-side session。
- TEST-117：多设备 session list / revoke / rotate；bootstrap 有显式 disable 路径。
- TEST-118：SQLite login throttle / progressive lockout。
- TEST-119：password change 必须 active DB session + current password；成功后全部旧 session revoke 并签发新 session。
- TEST-120：最小可用 Auth UI 只调用既有 VERIFIED API，不复制认证逻辑。
- TEST-121：静态 `AUTH_BEARER_TOKEN → LOCAL_USER_ID` bootstrap 默认关闭；仅显式 opt-in 时保留迁移兼容。

## TEST-121 — Production Bootstrap Retirement — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：在真实 DB account/session 已建立后，让旧静态 bootstrap 从“默认开启”变成“显式 opt-in”，减少生产环境误配置后继续信任固定 `LOCAL_USER_ID` token 的风险。

已完成：
1. `Settings.auth_bootstrap_enabled` 默认值由 `True` 改为 `False`；
2. `.env.example` 改为 `AUTH_BOOTSTRAP_ENABLED=false`，注释明确只允许显式 migration / emergency compatibility window 使用；
3. production 中配置了 `AUTH_BEARER_TOKEN` 但 bootstrap disabled 时，该静态 token 返回 `401 invalid bearer token`；
4. `AUTH_BOOTSTRAP_ENABLED=true` + 配置静态 token 时，TEST-114 兼容路径仍可显式使用；
5. enabled bootstrap 但没有配置 token、且没有 active session 时，原有 fail-closed `503 production authentication is not configured` 语义保留；
6. DB-backed account sessions 在 bootstrap disabled 时仍可正常访问 protected API；
7. register/login 公共入口在 bootstrap disabled production 下保持正常；
8. production 无 bootstrap、无 bearer 时统一 `401 bearer token required`；
9. TEST-114 / TEST-115 旧回归测试改为显式声明何时需要 transitional bootstrap，不再隐式依赖默认开启；
10. development/test `X-User-ID` 兼容路径本阶段未修改；
11. 无新 migration，未修改历史 migration 001~013。

新增 `backend/tests/test_auth_bootstrap_retirement.py` 6 个测试，覆盖：
- Settings 默认 bootstrap disabled；
- `.env.example` 默认 bootstrap disabled；
- production 静态 token 默认拒绝且不回显；
- 显式 opt-in 后静态 bootstrap 仍可使用；
- bootstrap disabled 时 register/login + DB session 正常；
- production 无 bootstrap/session 时要求 bearer token。

更新既有测试：
- `backend/tests/test_auth_boundary.py`：旧 static bootstrap 成功/缺失 token 场景改为显式 `bootstrap_enabled=True`；
- `backend/tests/test_auth_session_boundary.py`：仅需要 bootstrap exchange 的测试显式 opt-in，其余 DB session 测试在 bootstrap disabled 下运行。

GitHub Actions run `35248850831`：
- TEST-121 bootstrap retirement：6 passed；
- production auth regression：7 passed；
- auth session boundary regression：7 passed；
- session management regression：7 passed；
- account login regression：7 passed；
- password change regression：8 passed；
- Auth Account UI regression：4 passed；
- execution/action-plan scope isolation：4 passed；
- full pytest：625 passed、1 warning in 33.07s；
- warning 为已知 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 validation workflow 已删除。

当前等待服务器验收后再标记 TEST-121 VERIFIED。

## 下一阶段候选

TEST-121 服务器通过后重新审计决定 TEST-122。优先候选：
1. development/test `X-User-ID` 长期兼容路径收口；
2. runtime HTTP security boundary：CORS / host / proxy trust / security headers；
3. Provider Settings UI 与 Auth UI 统一入口；
4. HTTPS / reverse proxy / access log / deployment release checklist；
5. account recovery 仍必须等待真实 verified channel。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~121 verification tag 已创建。
