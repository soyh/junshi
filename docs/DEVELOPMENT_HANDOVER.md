# Development Handover

更新时间：2026-09-18
当前阶段：TEST-131 — HTTP Liveness / Runtime Readiness Boundary — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-131-http-runtime-health
TEST-130 VERIFIED 服务器代码 HEAD：`876cfd727943931606d4d7213f6ad6432d7cb250`
TEST-130 验收闭环文档基线：`58ba08d802a0ca213b5e9045c46648a98ca152dd`

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
TEST-131 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — HTTP liveness / runtime readiness；GitHub full 700。

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

## TEST-131 — HTTP Liveness / Runtime Readiness Boundary — GITHUB SELF-TEST PASSED

目标：区分“进程活着”与“当前能够安全接业务请求”，同时不把 TEST-129/130 的重型运维检查塞进高频 HTTP probe。

实现：
1. 保留现有 `/health` body 与 TEST-123 cache contract，不改变兼容行为；
2. 新增 `/health/live`：固定 200，完全不访问数据库；
3. 新增 `/health/ready`：只读检查 SQLite 文件可访问性与 migration 精确一致性；ready=200，not-ready=503；
4. SQLite probe 使用 `mode=ro` + `SELECT name FROM sqlite_schema LIMIT 1`，既不创建缺失 DB，也能拒绝非 SQLite/corrupt 文件；
5. `backend/app/core/readiness.py` 仅增加只读 public migration-state helper，TEST-129 原有 database integrity + managed backup freshness 行为不变；
6. runtime readiness 不运行 migration、不执行 `PRAGMA integrity_check`、不扫描 backup manifest、不计算 backup SHA-256；
7. `/health/ready` 只输出 database ok/error、migration expected/applied count 与归一化错误；不输出绝对路径、migration 版本列表、backup 信息或 secrets；
8. 新 `/health/live` 与 `/health/ready` 使用 `Cache-Control: no-store`；旧 `/health` 按 TEST-123 保持非强制 no-store；
9. 无 schema migration。

CI 发现并修复了两个真实边界问题，没有修改旧 VERIFIED 测试：
- 第一轮 run `35332656349`：`SELECT 1` 不读取 SQLite 文件页，损坏文件被误判可访问；改为读取 `sqlite_schema`；
- 第二轮 run `35332731512`：targeted 全过，但 full 暴露 TEST-123 旧 `/health` cache contract 冲突；保留旧 `/health` 行为，只对新 probe no-store；
- 最终 run `35333000258`：success。

最终 GitHub 结果：
- TEST-131 runtime health：9 passed；
- TEST-130 preflight：10 passed；
- TEST-129 readiness：9 passed；
- TEST-124 production surface：4 passed；
- production auth：8 passed；
- scope isolation：4 passed；
- full pytest：700 passed、1 warning in 34.93s；
- warning 仍为 Starlette TestClient / anyio BlockingPortal deprecation，与本阶段无关；
- 临时 workflow 已删除。

当前等待服务器验收 TEST-131。服务器验收只运行 pytest / git diff / git status，不启动或重启 uvicorn，不执行 backup/restore/readiness/preflight CLI，不修改 `.env`，不触碰 8899。

## 下一阶段候选

TEST-131 服务器通过后重新审计决定 TEST-132。优先考虑部署后的 probe/runbook 契约或 process supervision 边界，但不提前假设 Nginx/systemd/域名方案。

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
