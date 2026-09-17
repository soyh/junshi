# Development Handover

更新时间：2026-09-17
当前阶段：TEST-115 — Auth Session / Server-resolved User Boundary — VERIFIED
当前 Branch：test-115-auth-session-boundary
服务器验收代码 HEAD：`a76c6907fa51afeee0076822601745c8ac3e4fb2`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-090：按既有交接记录 VERIFIED；TEST-091 CONTRACT LOCKED；TEST-092 VERIFIED；TEST-093 VERIFIED；TEST-094 CONTRACT LOCKED。

TEST-095 VERIFIED — Recommendation / Action Plan 跨请求 persistence bridge；migration 008。
TEST-096 VERIFIED — Decision → Execution → Outcome safety。
TEST-097 VERIFIED — evidence-backed proposal freshness。
TEST-098 VERIFIED — Action Plan snapshot isolation。
TEST-099 VERIFIED — Action Plan persistence gate。
TEST-100 VERIFIED — proposal gate + execution gate。
TEST-101 VERIFIED — Execution user/person/decision scope isolation；full 526 passed。
TEST-102 VERIFIED — Outcome DB idempotency；migration 009；full 528 passed。
TEST-103 VERIFIED — duplicate Outcome → HTTP 409；full 529 passed。
TEST-104 VERIFIED — user-scoped LLM Provider config；migration 010；full 530 passed。
TEST-105 VERIFIED — Provider Runtime Routing；full 532 passed。
TEST-106 VERIFIED — Provider Runtime Materialization；full 533 passed。
TEST-107 VERIFIED — Provider Connection Test；full 539 passed。
TEST-108 VERIFIED — Provider Error Contract。
TEST-109 VERIFIED — Provider Base URL Contract。
TEST-110 VERIFIED — Provider Capability / StructuredAnalysis Contract；full 553 passed。
TEST-111 VERIFIED — Provider Timeout / 429 / No-Retry Contract；full 562 passed。
TEST-112 VERIFIED — Provider Log Redaction / Exception Boundary；full 568 passed。
TEST-113 VERIFIED — Provider Settings UI / Analysis Entry；服务器 full 571 passed；HEAD `b59b7625ffd8a391835545852ce981871da32580`。
TEST-114 VERIFIED — Production Authentication Boundary；服务器 auth 7、UI 3、security 7、full 578 passed；验收代码 HEAD `693946882ca780eafc0367dfa26a3b7f0ea06f84`。
TEST-115 VERIFIED — DB-backed opaque Auth Session / Server-resolved User Boundary；服务器 session 7、TEST-114 auth regression 7、scope isolation 4、full 585 passed in 95.17s；工作树 clean；相对 TEST-114 migration diff 仅 `011_auth_sessions.sql`；验收 HEAD `a76c6907fa51afeee0076822601745c8ac3e4fb2`。

## TEST-115 — VERIFIED

目标：在不破坏 TEST-114 生产认证边界的前提下，把身份解析从“单个静态 token → LOCAL_USER_ID”升级为真正支持多用户的“opaque session token → server-resolved users.id”。

已建立：
1. migration 011 `auth_sessions`：`id / user_id / token_hash / expires_at / revoked_at / created_at`；
2. token 使用 `secrets.token_urlsafe(32)`，数据库只保存 SHA-256 token hash，不保存原始 bearer；
3. session 支持 expiry / revoke；
4. `get_current_user_id()` 优先解析 DB session，再兼容 TEST-114 静态 bootstrap token；
5. production 继续拒绝客户端 `X-User-ID`；
6. `POST /api/v1/auth/sessions` 只能为已认证的自己创建 session，客户端不能指定 user_id；
7. `DELETE /api/v1/auth/session` 只吊销当前真实 DB session；
8. 不同 session 可映射不同 users，并继续复用 Person / Relationship / Conversation scope isolation；
9. 不修改历史 migration 001~010。

服务器验收：
- `backend/tests/test_auth_session_boundary.py`：7 passed；
- `backend/tests/test_auth_boundary.py`：7 passed；
- execution/action-plan scope isolation：4 passed；
- full pytest：585 passed in 95.17s；
- `git status --short` blank；
- migration diff：仅 `A backend/migrations/011_auth_sessions.sql`；
- 最终文件差异与 GitHub 预期一致。

TEST-115 VERIFIED。

## 下一阶段

TEST-116：账号凭据注册/登录 → server-issued session；客户端不再需要静态 bootstrap token 完成日常登录。密码凭据必须不可逆哈希保存，登录失败不得泄露账号存在性，并继续复用 TEST-115 session 与既有 user scope isolation。

## 架构与持续禁止事项

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed 且等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 relationship 或伪造 Outcome。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle。
- 所有数据必须 user_id 隔离；Person / Relationship / Conversation 不得跨 scope 混用。
- 不修改历史 migration；新增 schema 使用新 migration。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-115 verification tag 已创建。
