# Development Handover

更新时间：2026-09-18
当前阶段：TEST-130 — Release Preflight — VERIFIED
当前 Branch：test-130-release-preflight
服务器验收代码 HEAD：`876cfd727943931606d4d7213f6ad6432d7cb250`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-125：按既有交接记录 VERIFIED。
TEST-126 VERIFIED — SQLite online backup + integrity verification；服务器 full 663。
TEST-127 VERIFIED — offline verified restore safety；服务器 full 663；HEAD `023fb2391d47d692db8b3b1002c5fbb2637be7d3`。
TEST-128 VERIFIED — managed backup manifest/checksum/retention；服务器 targeted 9 passed，累计 full 691。
TEST-129 VERIFIED — read-only operations readiness；服务器 targeted 9 passed，累计 full 691。
TEST-130 VERIFIED — release preflight；服务器 targeted 10 passed，累计 full 691；HEAD `876cfd727943931606d4d7213f6ad6432d7cb250`。

## Runtime / Operations 产品化基线

- TEST-122：彻底退役 `X-User-ID` 身份来源。
- TEST-123：基础 HTTP 安全响应头、auth/settings no-store、无 permissive CORS。
- TEST-124：production 强制 `debug=False`，关闭 docs/redoc/openapi。
- TEST-125：统一 `python -m app.server`；production loopback-only、single-worker、no reload、no proxy trust、no Server header。
- TEST-126：WAL-safe SQLite online backup + integrity verification + atomic publish。
- TEST-127：offline-confirmed restore + pre/post integrity verification + atomic replace + stale WAL/SHM cleanup。
- TEST-128：managed backup manifest + SHA-256 + strict verification + safe retention。
- TEST-129：read-only database/migration/backup readiness report + machine-readable exit status。
- TEST-130：release preflight 汇总 production config、secure launcher、operations readiness；部署前 fail closed。

## TEST-126 / TEST-127 — VERIFIED

服务器累计验收：restore 8、backup 8、launcher 7、surface 4、production auth 8、scope 4、full 663 passed in 123.02s；工作树 clean；migration diff 空；最终文件 diff 精确匹配。

## TEST-128 — Backup Manifest / Checksum / Retention — VERIFIED

1. `backend/app/core/backup_manifest.py`：manifest schema version=1，记录 UTC created_at、backup basename、size、SHA-256、integrity=ok；
2. manifest 使用 sibling temp + fsync + atomic replace；
3. managed backup 在 manifest 发布失败时回滚新 backup；
4. verify 严格校验 schema、basename/path traversal、size、SHA-256、SQLite integrity；
5. retention 只认有效 manifest，不删除手工 SQLite、损坏 manifest 或 checksum 不匹配 backup；
6. dry-run 默认；apply 时先删 manifest 再删 backup；
7. CLI 新增 `--verify-manifest`、`--retention-dir`、`--keep`、`--apply-retention`；
8. GitHub run `35314760780`：TEST-128 9、TEST-127 8、TEST-126 8、production auth 8、scope 4、full 672 passed；
9. 服务器：TEST-128 9 passed，累计 full 691 passed。

## TEST-129 — Operations Readiness — VERIFIED

1. `backend/app/core/readiness.py` 与 `backend/app/readiness.py`；
2. 数据库只读执行 TEST-126 integrity verification；
3. migration 版本从 `backend/migrations/*.sql` 获取，并与 DB `schema_migrations` 精确比较；缺失、未知、重复版本均 fail closed；
4. backup 只从通过 TEST-128 manifest/checksum/integrity 验证的 managed backups 中选择最近一个；
5. 无有效 backup、backup stale、timestamp 在未来均 fail；
6. 默认最大 backup age 24h，可显式配置；
7. JSON 输出只含 basename、migration 版本/计数、backup age/status，不打印绝对路径或 secret；
8. CLI `python -m app.readiness --json` 以 exit code 0/1 表示 ready/not-ready；
9. GitHub run `35315030038`：TEST-129 9、TEST-128 9、TEST-127 8、TEST-126 8、production auth 8、scope 4、full 681 passed；
10. 服务器：TEST-129 9 passed，累计 full 691 passed。

## TEST-130 — Release Preflight — VERIFIED

1. `backend/app/core/preflight.py` 与 `backend/app/preflight.py`；
2. release preflight 要求 `APP_ENV=production`；
3. 要求 `APP_DEBUG=false`；
4. 要求 `AUTH_BOOTSTRAP_ENABLED=false`；
5. 要求 `LLM_CONFIG_ENCRYPTION_KEY` 已配置，但输出只暴露 boolean；
6. 明确拒绝 `PORT=8899`；
7. 校验 log level；
8. 复用 TEST-125 `_uvicorn_options()`，要求 production loopback、workers=1、reload=false、proxy_headers=false、forwarded_allow_ips=""、server_header=false；public bind fail closed；
9. 复用 TEST-129 operations readiness；
10. CLI `python -m app.preflight --json` 不启动服务，以 exit code 0/1 表示 release ready/not-ready；
11. JSON 不输出 encryption key、auth token、DashScope key 或绝对路径；
12. 无 schema migration。

GitHub Actions run `35315361027`：success；TEST-130 10、TEST-129 9、TEST-128 9、TEST-127 8、TEST-126 8、launcher 7、production auth 8、scope 4、full 691 passed。

服务器最终验收：
- TEST-130：10 passed in 0.34s；
- TEST-129：9 passed in 0.30s；
- TEST-128：9 passed in 0.39s；
- TEST-127：8 passed in 0.20s；
- TEST-126：8 passed in 0.16s；
- launcher：7 passed in 0.05s；
- production auth：8 passed in 1.48s；
- scope isolation：4 passed in 0.04s；
- full pytest：691 passed in 121.76s；
- branch / HEAD 精确匹配；工作树 clean；migration diff 空；TEST-127→130 文件 diff 精确匹配。

## 下一阶段

TEST-131 — HTTP Liveness / Runtime Readiness Boundary：
1. 保留现有 `/health` 兼容契约；
2. 新增轻量 `/health/live`，不得访问数据库；
3. 新增只读 `/health/ready`，仅检查运行时所需的数据库可访问性与 migration 一致性；
4. 不在高频 HTTP readiness 中执行 TEST-129 的 backup checksum/integrity 扫描，backup freshness 继续由 operations readiness / release preflight 负责；
5. not-ready 返回 HTTP 503，错误归一化，不输出数据库绝对路径或 secret；
6. health 响应 `Cache-Control: no-store`；
7. 无 schema migration；CI/服务器仍只使用测试临时库，不触碰 8899。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~130 verification tag 已创建。
