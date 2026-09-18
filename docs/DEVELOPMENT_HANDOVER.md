# Development Handover

更新时间：2026-09-18
当前阶段：TEST-126 — SQLite Online Backup / Integrity Verification — GITHUB SELF-TEST PASSED / SERVER VALIDATION DEFERRED
当前 Branch：test-126-sqlite-online-backup
TEST-125 VERIFIED 服务器代码 HEAD：`e018aac176ed5214baf6b1084b91f3ed550436b7`

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
TEST-123 VERIFIED — HTTP security response boundary；服务器累计验收通过；full 636 passed；HEAD `77eddc8f84547cf5acae89142a463b7e64d72d78`。
TEST-124 VERIFIED — production FastAPI debug/docs surface hardening；服务器累计验收通过；GitHub full 640 passed。
TEST-125 VERIFIED — secure Uvicorn launcher；服务器 full 647 passed；HEAD `e018aac176ed5214baf6b1084b91f3ed550436b7`。
TEST-126 GITHUB SELF-TEST PASSED / SERVER VALIDATION DEFERRED — SQLite online backup + integrity verification；full 655 passed。

## Runtime / Operations 产品化基线

- TEST-122：彻底退役 `X-User-ID` 身份来源。
- TEST-123：基础 HTTP 安全响应头、auth/settings no-store、无 permissive CORS。
- TEST-124：production 强制 `debug=False`，关闭 docs/redoc/openapi。
- TEST-125：统一 `python -m app.server`；production loopback-only、single-worker、no reload、no proxy trust、no Server header。
- TEST-126：SQLite online backup API + WAL-safe consistent snapshot + integrity verification + atomic publish。

## TEST-124 / TEST-125 — VERIFIED

服务器累计验收全部符合预期：TEST-125 7、TEST-124 4、TEST-123 6、TEST-122 4、production auth 8、Auth UI 4、Provider UI 3、scope isolation 4、full 647 passed in 121.15s；工作树 clean；migration diff 空；文件 diff 精确匹配。TEST-124 / TEST-125 VERIFIED。

## TEST-126 — SQLite Online Backup / Integrity Verification — GITHUB SELF-TEST PASSED

目标：建立可在线执行、可验证、不会因 WAL 文件复制遗漏已提交数据的 SQLite 备份基础。

实现：
1. 新增 `backend/app/core/backup.py`；
2. `verify_database()` 使用只读连接执行 `PRAGMA integrity_check`，结果必须严格为 `ok`；
3. `create_verified_backup()` 使用 `sqlite3.Connection.backup()` 创建一致性 snapshot；
4. source 只读打开，支持 WAL 源库；
5. destination 已存在时拒绝覆盖；source=destination、source 不存在均 fail closed；
6. 先写 destination 同目录 sibling temp；完整 backup 后 integrity-check + fsync；
7. 只有验证通过才 `os.replace()` 原子发布；
8. 所有异常路径都清理临时文件，失败时不发布半成品；
9. 新增 `backend/app/backup.py` CLI：支持显式 source/destination、默认 UTC timestamp 备份名以及 `--verify-only`；
10. GitHub/CI 未读取或修改生产数据库，只使用 pytest `tmp_path` 临时库；
11. 无 schema migration。

新增 `backend/tests/test_sqlite_online_backup.py` 8 个契约测试：
- healthy DB integrity；
- corrupt DB rejection；
- data-preserving backup；
- writer 保持打开、WAL autocheckpoint disabled 时仍能捕获 committed WAL data；
- missing source / same destination fail closed；
- existing destination never overwritten；
- forced verification failure 不发布 partial backup 且 temp 清理；
- timestamp default destination 与 CLI verify-only contract。

GitHub Actions run `35313426634`：success；
- TEST-126：8 passed；
- TEST-125：7 passed；
- TEST-124：4 passed；
- TEST-123：6 passed；
- production auth：8 passed；
- scope isolation：4 passed；
- full pytest：655 passed、1 warning in 36.43s；
- 临时 validation workflow 已删除。

为加速推进，TEST-126 服务器验收与 TEST-127 合并执行，当前不标记 SERVER VERIFIED。

## 下一阶段

TEST-127 — Offline Verified Restore Safety：
1. restore 必须显式确认 application/database 已 offline；
2. restore source 必须先通过 TEST-126 integrity verification；
3. 先复制到 destination 同目录临时文件并再次验证，再原子替换 target；
4. 成功替换后清理 stale `-wal` / `-shm` sidecars，避免旧 WAL 被应用到新数据库；
5. 未显式 offline confirmation、损坏 backup、backup=destination 必须 fail closed；
6. GitHub/服务器验收只操作临时库，不恢复生产数据库；
7. 无 schema migration。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~126 verification tag 已创建。
