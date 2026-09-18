# Development Handover

更新时间：2026-09-18
当前阶段：TEST-127 — Offline Verified Restore Safety — VERIFIED
当前 Branch：test-127-offline-verified-restore
服务器验收代码 HEAD：`023fb2391d47d692db8b3b1002c5fbb2637be7d3`

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
TEST-126 VERIFIED — SQLite online backup + integrity verification；服务器 8 passed，累计 full 663 passed。
TEST-127 VERIFIED — offline verified restore safety；服务器 8 passed，累计 full 663 passed；服务器 HEAD `023fb2391d47d692db8b3b1002c5fbb2637be7d3`。

## Runtime / Operations 产品化基线

- TEST-122：彻底退役 `X-User-ID` 身份来源。
- TEST-123：基础 HTTP 安全响应头、auth/settings no-store、无 permissive CORS。
- TEST-124：production 强制 `debug=False`，关闭 docs/redoc/openapi。
- TEST-125：统一 `python -m app.server`；production loopback-only、single-worker、no reload、no proxy trust、no Server header。
- TEST-126：SQLite online backup API + WAL-safe consistent snapshot + integrity verification + atomic publish。
- TEST-127：offline-confirmed restore + pre/post integrity verification + atomic replace + stale WAL/SHM cleanup。

## TEST-126 / TEST-127 — VERIFIED

服务器累计验收：TEST-127 restore 8、TEST-126 backup 8、TEST-125 launcher 7、TEST-124 surface 4、production auth 8、scope isolation 4、full 663 passed in 123.02s；工作树 clean；migration diff 空；最终文件 diff 精确匹配。

TEST-126：
1. `sqlite3.Connection.backup()` 创建 WAL-safe 一致性 snapshot；
2. `PRAGMA integrity_check` 必须严格返回 `ok`；
3. sibling temp → integrity_check → fsync → atomic `os.replace()`；
4. source missing / source=destination / existing destination / corrupt DB 均 fail closed；
5. 异常不发布 partial backup；
6. CLI `python -m app.backup` 已建立，但验收阶段未操作生产库。

TEST-127：
1. restore 必须显式 `offline_confirmed=True`；
2. backup 在触碰 destination 前先完整性验证；
3. candidate temp 再验证、chmod 0600、fsync；
4. 仅验证通过后原子替换；
5. 成功后清理 stale `-wal` / `-shm`；
6. 最终 destination 再次 integrity verification；
7. CLI `python -m app.restore` 必须显式 `--offline-confirmed`；
8. 验收阶段未执行 backup/restore CLI、未停止服务、未修改 `.env`、未触碰 8899。

## 下一阶段

TEST-128 — Backup Manifest / Checksum / Retention：
1. 每个备份发布配套 manifest；
2. manifest 记录 schema version、UTC created_at、backup filename、size、SHA-256、integrity 状态；
3. 提供 manifest + file 双重验证；
4. retention 只删除由有效 manifest 明确认领的历史备份，绝不扫描删除任意 SQLite 文件；
5. retention 支持 dry-run，真实删除时 backup + manifest 成对处理；
6. 所有测试继续只使用临时目录和临时 SQLite 数据；
7. 不新增 schema migration。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~127 verification tag 已创建。
