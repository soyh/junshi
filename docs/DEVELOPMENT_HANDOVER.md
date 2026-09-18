# Development Handover

更新时间：2026-09-18
当前阶段：TEST-133 — Supervisor-Neutral Runtime Contract — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-133-supervisor-runtime-contract
TEST-131 VERIFIED 服务器代码 HEAD：`d58d20c495bc20f14bbc5bbdb3657fb19bf0b657`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-125：按既有交接记录 VERIFIED。
TEST-126 VERIFIED — SQLite online backup + integrity verification；服务器 full 663。
TEST-127 VERIFIED — offline verified restore safety；服务器 full 663。
TEST-128 VERIFIED — managed backup manifest/checksum/retention；服务器累计 full 691。
TEST-129 VERIFIED — read-only operations readiness；服务器累计 full 691。
TEST-130 VERIFIED — release preflight；服务器累计 full 691；HEAD `876cfd727943931606d4d7213f6ad6432d7cb250`。
TEST-131 VERIFIED — HTTP liveness / runtime readiness；服务器 TEST-131 9 passed、full 700 passed；HEAD `d58d20c495bc20f14bbc5bbdb3657fb19bf0b657`。
TEST-132 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — loopback-only local runtime probe CLI；GitHub full 711。
TEST-133 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — supervisor-neutral runtime lifecycle contract；GitHub full 722。

## Runtime / Operations 产品化基线

- TEST-122：彻底退役 `X-User-ID` 身份来源。
- TEST-123：基础 HTTP 安全响应头、auth/settings no-store、旧 `/health` cache contract 保持兼容、无 permissive CORS。
- TEST-124：production 强制 `debug=False`，关闭 docs/redoc/openapi。
- TEST-125：统一 `python -m app.server`；production loopback-only、single-worker、no reload、no proxy trust、no Server header。
- TEST-126：WAL-safe SQLite online backup + integrity verification + atomic publish。
- TEST-127：offline-confirmed restore + pre/post integrity verification + atomic replace + stale WAL/SHM cleanup。
- TEST-128：managed backup manifest + SHA-256 + strict verification + safe retention。
- TEST-129：read-only database/migration/backup readiness report + machine-readable exit status。
- TEST-130：release preflight 汇总 production config、secure launcher、operations readiness；部署前 fail closed。
- TEST-131：HTTP liveness 与 runtime readiness 分离；高频 probe 不执行 backup checksum/integrity。
- TEST-132：本机 loopback-only runtime probe CLI，供任意 supervisor/编排器调用。
- TEST-133：平台无关 supervisor lifecycle contract，统一启动前 gate、启动、probe、退出与失败重启语义。

## TEST-131 — VERIFIED

- `/health` 保持原兼容契约；
- `/health/live` 固定 200，不访问数据库；
- `/health/ready` 只读检查 SQLite 可访问性与 migration 精确一致性，ready=200 / not-ready=503；
- SQLite 使用 `mode=ro` + `sqlite_master`，兼容服务器 SQLite 3.26.0；
- 不运行 migration、不做 backup checksum/integrity；
- GitHub 兼容性修复 run `35333640165` full 700；
- 服务器最终复验：TEST-131 9 passed in 0.98s，full 700 passed in 118.87s，working tree clean，migration diff 空。

## TEST-132 — Local Runtime Probe CLI — GITHUB SELF-TEST PASSED

目标：提供不依赖 curl、systemd、Nginx、Docker 或具体云厂商的本机运行探针。

实现：
1. `backend/app/core/runtime_probe.py` + CLI `python -m app.probe live|ready [--json]`；
2. 只允许 loopback host，非 loopback 在发请求前拒绝；
3. 明确拒绝 port 8899；
4. HTTP client `trust_env=False`、`follow_redirects=False`，默认超时 2 秒；
5. live/ready 严格验证 TEST-131 响应契约；ready 503 归一化；
6. 不回显响应正文、网络异常细节、host/port 或 secret；
7. CLI 以 exit code 0/1 表示健康/失败；
8. 无 schema migration，不启动/停止现有服务。

GitHub Actions run `35335559052`：TEST-132 11、TEST-131 9、TEST-130 10、TEST-125 7、TEST-123 6、production auth 8、scope 4、full 711 passed、1 warning in 34.91s；临时 workflow 已删除。

## TEST-133 — Supervisor-Neutral Runtime Contract — GITHUB SELF-TEST PASSED

目标：在不选定 systemd/Nginx/Docker/云厂商的情况下，给任意进程管理器提供同一套安全生命周期契约。

实现：
1. 新增 `backend/app/core/supervision.py`；
2. 新增 CLI `python -m app.supervision --json`；
3. contract schema version=1；
4. startup gate 固定为 `python -m app.preflight --json`，必须 exit 0；
5. process 固定为 `python -m app.server`；
6. 复用 TEST-125 `_uvicorn_options()`，要求 production、loopback、workers=1、reload=false、proxy_headers=false、forwarded_allow_ips=""、server_header=false；
7. 明确拒绝 port 8899；
8. liveness/readiness 直接复用 TEST-132 `python -m app.probe live|ready --json`；
9. shutdown contract：SIGTERM，建议 30 秒 graceful window，之后才 SIGKILL escalation；
10. restart contract：on-failure，建议 5 秒 delay，clean exit 不自动重启；
11. 所有命令均为 argument vector，不通过 shell；
12. 输出不包含 auth token、DashScope key、LLM encryption key 或 database path；
13. 无 schema migration，不启动/停止任何进程。

GitHub Actions run `35335884679`：success；
- TEST-133：11 passed；
- TEST-132：11 passed；
- TEST-131：9 passed；
- TEST-130：10 passed；
- TEST-125：7 passed；
- production auth：8 passed；
- scope isolation：4 passed；
- full pytest：722 passed、1 warning in 32.82s；
- warning 仍为 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 workflow 已删除。

## 当前服务器验收节点

一次性验收 TEST-132 + TEST-133：
- 只运行 pytest / git diff / git status；
- 不执行 `python -m app.probe` 对真实服务发请求；
- 不执行 `python -m app.supervision`；
- 不运行 preflight/server，不启动/停止/restart uvicorn；
- 不修改 `.env`，不触碰 8899；
- 无 migration 预期。

## 下一阶段候选

TEST-134 在 TEST-132/133 服务器通过后重新审计。优先候选：正式 deployment runbook artifact / release checklist automation，但不提前假设 systemd、Nginx、域名或 TLS termination 方案。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~133 verification tag 已创建。
