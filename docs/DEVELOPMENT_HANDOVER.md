# Development Handover

更新时间：2026-09-18
当前阶段：TEST-131 — HTTP Liveness / Runtime Readiness Boundary — VERIFIED
当前 Branch：test-131-http-runtime-health
TEST-131 VERIFIED 服务器代码 HEAD：`d58d20c495bc20f14bbc5bbdb3657fb19bf0b657`
TEST-130 VERIFIED 服务器代码 HEAD：`876cfd727943931606d4d7213f6ad6432d7cb250`

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
TEST-131 VERIFIED — HTTP liveness / runtime readiness；服务器 TEST-131 9 passed，full 700 passed；HEAD `d58d20c495bc20f14bbc5bbdb3657fb19bf0b657`。

## Runtime / Operations 产品化基线

- TEST-122：彻底退役 `X-User-ID` 身份来源。
- TEST-123：基础 HTTP 安全响应头、auth/settings no-store、旧 `/health` 保持非强制 no-store、无 permissive CORS。
- TEST-124：production 强制 `debug=False`，关闭 docs/redoc/openapi。
- TEST-125：统一 `python -m app.server`；production loopback-only、single-worker、no reload、no proxy trust、no Server header。
- TEST-126：WAL-safe SQLite online backup + integrity verification + atomic publish。
- TEST-127：offline-confirmed restore + pre/post integrity verification + atomic replace + stale WAL/SHM cleanup。
- TEST-128：managed backup manifest + SHA-256 + strict verification + safe retention。
- TEST-129：read-only database/migration/backup readiness report + machine-readable exit status。
- TEST-130：release preflight 汇总 production config、secure launcher、operations readiness；部署前 fail closed。
- TEST-131：HTTP liveness 与 runtime readiness 分离；高频 probe 不执行 backup checksum/integrity。

## TEST-126 ~ TEST-130 — VERIFIED

TEST-130 服务器最终验收：
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

## TEST-131 — HTTP Liveness / Runtime Readiness Boundary — VERIFIED

目标：区分“进程活着”与“当前能够安全接业务请求”，同时不把 TEST-129/130 的重型运维检查塞进高频 HTTP probe。

实现：
1. 保留现有 `/health` body 与 TEST-123 cache contract，不改变兼容行为；
2. 新增 `/health/live`：固定 200，完全不访问数据库；
3. 新增 `/health/ready`：只读检查 SQLite 文件可访问性与 migration 精确一致性；ready=200，not-ready=503；
4. SQLite probe 使用 `mode=ro` + `SELECT name FROM sqlite_master LIMIT 1`；`sqlite_master` 兼容服务器 SQLite 3.26.0，同时会真实读取数据库 header/schema，因此既不创建缺失 DB，也能拒绝非 SQLite/corrupt 文件；
5. `backend/app/core/readiness.py` 仅增加只读 public migration-state helper，TEST-129 原有 database integrity + managed backup freshness 行为不变；
6. runtime readiness 不运行 migration、不执行 `PRAGMA integrity_check`、不扫描 backup manifest、不计算 backup SHA-256；
7. `/health/ready` 只输出 database ok/error、migration expected/applied count 与归一化错误；不输出绝对路径、migration 版本列表、backup 信息或 secrets；
8. 新 `/health/live` 与 `/health/ready` 使用 `Cache-Control: no-store`；旧 `/health` 按 TEST-123 保持非强制 no-store；
9. 无 schema migration。

GitHub CI 发现并修复的边界问题，没有修改旧 VERIFIED 测试：
- run `35332656349`：最初使用 `SELECT 1`，不会读取 SQLite 文件页，损坏文件被误判可访问；改为真实读取 schema；
- run `35332731512`：targeted 全过，但 full 暴露 TEST-123 旧 `/health` cache contract 冲突；保留旧 `/health` 行为，只对新 probe no-store；
- run `35333000258`：上述版本在 GitHub success，full 700；
- 首次服务器验收发现服务器 SQLite 3.26.0 对 `sqlite_schema` 不兼容：TEST-131 3 failed / 6 passed，其他 TEST-123/124/129/130/auth/scope 全通过，full 697 passed / 3 failed；
- 随后将 probe 从 `sqlite_schema` 改为长期兼容的 `sqlite_master`，语义不变；
- 兼容性修复 GitHub run `35333640165`：TEST-131 9、TEST-123 6、TEST-130 10、TEST-129 9、TEST-124 4、production auth 8、scope 4、full 700 passed；
- 临时 workflow 已删除。

服务器最终复验：
- Python sqlite3 module：2.6.0；SQLite runtime：3.26.0；
- TEST-131：9 passed in 0.98s；
- full pytest：700 passed in 118.87s；
- branch / HEAD 精确为 `test-131-http-runtime-health` / `d58d20c495bc20f14bbc5bbdb3657fb19bf0b657`；
- working tree clean；migration diff 空；
- TEST-130→131 文件 diff 精确为 `backend/app/core/readiness.py`、`backend/app/core/runtime_health.py`、`backend/app/main.py`、`backend/tests/test_runtime_health.py`、`docs/DEVELOPMENT_HANDOVER.md`。

## 下一阶段

TEST-132 — 重新审计部署后的 process supervision / probe runbook 边界：
1. 不预设 Nginx、systemd、域名或公网拓扑；
2. 优先建立仓库内可测试、可生成的 supervisor contract / runbook，使部署层明确使用 TEST-125 `python -m app.server`、TEST-131 `/health/live` 和 `/health/ready`；
3. 不信任 forwarded headers，不触碰 8899；
4. 不启动/停止现有服务，不修改服务器 `.env`；
5. 无必要不新增 schema migration。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~131 verification tag 已创建。
