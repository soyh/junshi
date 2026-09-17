# Development Handover

更新时间：2026-09-17
当前阶段：TEST-121 — Production Bootstrap Retirement — VERIFIED / PAUSED
当前 Branch：test-121-production-bootstrap-retirement
服务器验收代码 HEAD：`43b514a5dfa454b85424b3abe5a96ffb93da0c24`

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
TEST-121 VERIFIED — production bootstrap default retirement；服务器 TEST-121 6、production auth 7、auth-session boundary 7、session management 7、account login 7、password change 8、Auth UI 4、scope isolation 4、full 625 passed in 114.67s；工作树 clean；migration diff blank；服务器 HEAD `43b514a5dfa454b85424b3abe5a96ffb93da0c24`。

## Auth 产品化基线

- TEST-114：production 禁止 `X-User-ID`；静态 bootstrap 仅作迁移兼容。
- TEST-115：DB-backed opaque session，仅存 SHA-256 token hash。
- TEST-116：normalized username + scrypt password；注册/登录签发 server-side session。
- TEST-117：多设备 session list / revoke / rotate；bootstrap 有显式 disable 路径。
- TEST-118：SQLite login throttle / progressive lockout。
- TEST-119：password change 必须 active DB session + current password；成功后全部旧 session revoke 并签发新 session。
- TEST-120：最小可用 Auth UI 只调用既有 VERIFIED API，不复制认证逻辑。
- TEST-121：静态 `AUTH_BEARER_TOKEN → LOCAL_USER_ID` bootstrap 默认关闭；只有显式 `AUTH_BOOTSTRAP_ENABLED=true` 才保留迁移/应急兼容。

## TEST-121 — Production Bootstrap Retirement — VERIFIED

目标：真实 DB account/session 已建立后，让旧静态 bootstrap 从默认开启改为显式 opt-in，降低生产环境继续信任固定 `LOCAL_USER_ID` token 的风险。

已验证：
1. `Settings.auth_bootstrap_enabled` 默认值为 `False`；
2. `.env.example` 默认 `AUTH_BOOTSTRAP_ENABLED=false`；
3. production 仅配置 `AUTH_BEARER_TOKEN`、但未显式启用 bootstrap 时，该静态 token 返回 `401 invalid bearer token`；
4. 显式 `AUTH_BOOTSTRAP_ENABLED=true` 后旧兼容 token 仍可使用；
5. DB-backed account sessions 在 bootstrap disabled 时正常；
6. register/login 公共入口正常；
7. production 无 bootstrap、无 bearer 时要求 bearer token；
8. development/test `X-User-ID` 兼容路径未在本阶段修改；
9. 无新 migration，未修改历史 migration 001~013。

GitHub Actions run `35248850831`：full 625 passed、1 warning。

服务器验收：
- `backend/tests/test_auth_bootstrap_retirement.py`：6 passed；
- `backend/tests/test_auth_boundary.py`：7 passed；
- `backend/tests/test_auth_session_boundary.py`：7 passed；
- `backend/tests/test_auth_session_management.py`：7 passed；
- `backend/tests/test_auth_account_login.py`：7 passed；
- `backend/tests/test_auth_password_change.py`：8 passed；
- `backend/tests/test_auth_account_ui.py`：4 passed；
- execution/action-plan scope isolation：4 passed；
- full pytest：625 passed in 114.67s；
- `git status --short` blank；
- migration diff blank；
- `.env` 未显式设置 `AUTH_BOOTSTRAP_ENABLED`，因此当前运行配置采用代码默认 `false`。

TEST-121 VERIFIED。

## 当前暂停点

按用户要求临时暂停，不启动 TEST-122。

恢复后应先重新审计当前 GitHub HEAD，再决定 TEST-122。优先候选：
1. development/test `X-User-ID` 长期兼容路径收口；
2. runtime HTTP security boundary：CORS / Host / proxy trust / security headers；
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
