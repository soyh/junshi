# Development Handover

更新时间：2026-09-18
当前阶段：TEST-125 — Secure Uvicorn Launcher Contract — VERIFIED
当前 Branch：test-125-secure-uvicorn-launcher
服务器验收代码 HEAD：`e018aac176ed5214baf6b1084b91f3ed550436b7`

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
TEST-122 VERIFIED — legacy `X-User-ID` retired；服务器累计验收通过；GitHub full 630 passed。
TEST-123 VERIFIED — HTTP security response boundary；服务器累计验收通过；full 636 passed；服务器 HEAD `77eddc8f84547cf5acae89142a463b7e64d72d78`。
TEST-124 VERIFIED — production FastAPI debug/docs surface hardening；服务器 cumulative validation passed；GitHub full 640 passed。
TEST-125 VERIFIED — secure Uvicorn launcher；服务器 targeted 全通过、full 647 passed in 121.15s；工作树 clean；migration diff 空；服务器 HEAD `e018aac176ed5214baf6b1084b91f3ed550436b7`。

## Auth / Runtime 产品化基线

- TEST-114：production 禁止 `X-User-ID`；静态 bootstrap 仅作迁移兼容。
- TEST-115：DB-backed opaque session，仅存 SHA-256 token hash。
- TEST-116：normalized username + scrypt password；注册/登录签发 server-side session。
- TEST-117：多设备 session list / revoke / rotate；bootstrap 有显式 disable 路径。
- TEST-118：SQLite login throttle / progressive lockout。
- TEST-119：password change 必须 active DB session + current password；成功后全部旧 session revoke 并签发新 session。
- TEST-120：最小可用 Auth UI 只调用既有 VERIFIED API，不复制认证逻辑。
- TEST-121：静态 `AUTH_BEARER_TOKEN → LOCAL_USER_ID` bootstrap 默认关闭；只有显式 `AUTH_BOOTSTRAP_ENABLED=true` 才保留迁移/应急兼容。
- TEST-122：`X-User-ID` 在 production/development/test 均拒绝，不允许客户端通过 header 选择 `user_id`。
- TEST-123：全局基础安全响应头；auth/settings 响应 `Cache-Control: no-store`；默认无 permissive CORS；Bearer 不切换 Cookie。
- TEST-124：production 强制 `debug=False`，关闭 `/docs`、`/redoc`、`/openapi.json`。
- TEST-125：统一 `python -m app.server` launcher；production 仅 loopback bind、单 worker、无 reload、无 proxy-header trust、无默认 Server header。

## TEST-124 — Production Surface Hardening — VERIFIED

1. `APP_ENV=production` 时 FastAPI 强制 `debug=False`；
2. production 关闭 `/docs`、`/redoc`、`/openapi.json`；
3. development/test 保留 docs/openapi 与可选 debug；
4. GitHub run `35253423403`：TEST-124 4 passed，full 640 passed；
5. 服务器累计验收：TEST-124 4 passed，相关回归全部通过；
6. 无 migration。

## TEST-125 — Secure Uvicorn Launcher Contract — VERIFIED

1. 新增 `backend/app/server.py`，标准入口 `python -m app.server`；
2. production 仅接受 `127.0.0.1` / `::1` / `localhost`；
3. production wildcard/public bind 直接拒绝；
4. `workers=1`、`reload=False`；
5. `proxy_headers=False`、`forwarded_allow_ips=""`；
6. `server_header=False`；
7. GitHub run `35253778818`：launcher 7 passed，full 647 passed；
8. 服务器验收：launcher 7、TEST-124 4、TEST-123 6、TEST-122 4、production auth 8、Auth UI 4、Provider UI 3、scope isolation 4、full 647 passed；
9. 工作树 clean；migration diff 为空；
10. 本阶段未启动额外服务、未修改 `.env`、未触碰 8899。

## 下一阶段

TEST-126 — SQLite Online Backup / Integrity Verification：
1. 使用 SQLite online backup API 创建一致性快照；
2. 支持 WAL 源库，不通过文件复制拼接 WAL；
3. 备份先落临时文件，验证 `PRAGMA integrity_check` 后原子发布；
4. source 不存在、source=destination、损坏数据库必须 fail closed；
5. 提供可测试 CLI，但 GitHub/服务器验收阶段只操作临时库，不直接备份生产数据库；
6. 不新增 schema migration。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~125 verification tag 已创建。
