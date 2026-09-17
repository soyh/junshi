# Development Handover

更新时间：2026-09-17
当前阶段：TEST-125 — Secure Uvicorn Launcher Contract — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-125-secure-uvicorn-launcher
TEST-123 VERIFIED 服务器代码 HEAD：`77eddc8f84547cf5acae89142a463b7e64d72d78`

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
TEST-124 GITHUB SELF-TEST PASSED / SERVER VALIDATION DEFERRED — production FastAPI debug/docs surface hardening；full 640 passed。
TEST-125 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — secure Uvicorn launcher；full 647 passed。

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
- TEST-124：production 强制 `debug=False`，并关闭 `/docs`、`/redoc`、`/openapi.json`；development/test 保留文档与可选 debug。
- TEST-125：仓库内统一 `python -m app.server` launcher；production 仅允许 loopback bind，单 worker、无 reload、无 proxy header trust、无默认 Server header。

## TEST-122 / TEST-123 — VERIFIED

TEST-122：彻底结束 `X-User-ID` 作为身份来源；历史隔离测试改由 pytest 适配器转换成真实 DB user + opaque Bearer session；服务器累计验收 all pass。

TEST-123：统一 `nosniff` / `DENY` / `no-referrer` 安全响应头；auth/settings `Cache-Control: no-store`；默认无 permissive CORS；Bearer token 不切换 Cookie；服务器累计验收 all pass。

## TEST-124 — Production Surface Hardening — GITHUB SELF-TEST PASSED

目标：避免 production 暴露调试行为与交互式 API schema surface，同时不破坏 development/test 使用体验。

实现与验证：
1. `backend/app/main.py` 新增 `_fastapi_surface_options(settings)`；
2. `APP_ENV=production` 时，无论 `APP_DEBUG` 是否误设为 true，FastAPI 强制 `debug=False`；
3. production 的 `/docs`、`/redoc`、`/openapi.json` 均关闭；
4. development/test 继续保留 docs/openapi，并按 `APP_DEBUG` 控制 debug；
5. `backend/tests/test_production_surface_hardening.py`：4 passed；
6. 无新 migration，历史 migration 001~013 未修改。

GitHub Actions run `35253423403`：TEST-124 4、TEST-123 6、TEST-122 4、production auth 8、Auth UI 4、Provider UI 3、scope isolation 4、full 640 passed、1 warning in 33.43s；临时 workflow 已删除。

为加速推进，TEST-124 与 TEST-125 一次性服务器验收。

## TEST-125 — Secure Uvicorn Launcher Contract — GITHUB SELF-TEST PASSED

目标：把服务器启动安全参数从“人工命令习惯”收进仓库内可测试契约，避免未来部署时无意开启公网监听、reload 或未经定义的 forwarded/proxy trust。

实现：
1. 新增 `backend/app/server.py`，项目根目录可通过兼容 `app` package 使用 `python -m app.server`；
2. `_uvicorn_options(settings)` 使用 `HOST` / `PORT` / `LOG_LEVEL`；
3. production 只接受 loopback host：`127.0.0.1`、`::1`、`localhost`；`0.0.0.0` 等 public/wildcard bind 直接 `RuntimeError`；
4. development 可显式使用非 loopback host；
5. 固定 `workers=1`，保持当前 SQLite MVP 单进程运行边界；
6. 固定 `reload=False`；
7. 固定 `proxy_headers=False` 与 `forwarded_allow_ips=""`，当前不信任 forwarded client/scheme；
8. 固定 `server_header=False`；
9. `main()` 使用 import string `app.main:app` 调用 `uvicorn.run()`；
10. 新增 `backend/tests/test_secure_uvicorn_launcher.py` 7 个测试；
11. 无新 migration，历史 migration 001~013 未修改；
12. 本阶段没有修改或重启当前服务器进程，也没有触碰 8899。

GitHub Actions run `35253778818`：success；
- TEST-125 launcher：7 passed；
- TEST-124 regression：4 passed；
- TEST-123 regression：6 passed；
- TEST-122 regression：4 passed；
- production auth：8 passed；
- Auth UI：4 passed；
- Provider UI：3 passed；
- scope isolation：4 passed；
- full pytest：647 passed、1 warning in 32.26s；
- 临时 validation workflow 已删除。

当前等待服务器一次性验收 TEST-124 + TEST-125。

## 下一阶段候选

服务器通过后继续强力推进 TEST-126。当前优先候选：SQLite online backup / integrity / restore safety contract；只在测试临时库上验证，不直接操作生产数据库。

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
