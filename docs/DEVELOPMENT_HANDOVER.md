# Development Handover

更新时间：2026-09-18
当前阶段：TEST-134 — Release Runbook Contract — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-134-release-runbook-contract
TEST-133 VERIFIED 服务器代码 HEAD：`74a9c5a976be094d9dd2d51e764ab457965f83ec`
TEST-133 验收闭环文档基线：`6066e6b108592df427f265291c7af968c681a3d2`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-133：按既有交接记录 VERIFIED。
TEST-134 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — platform-neutral release runbook / rollback safety contract；GitHub full 734。

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
- TEST-132：本机 loopback-only runtime probe CLI。
- TEST-133：平台无关 supervisor lifecycle contract。
- TEST-134：平台无关 release runbook，明确 backup/preflight/stop/switch/start/probe/rollback 顺序和数据库回滚安全门槛。

## TEST-132 / TEST-133 — VERIFIED

服务器最终验收：用户确认 all pass，结果符合预期；TEST-132/133 正式锁定 VERIFIED。

TEST-132：`python -m app.probe live|ready --json`；loopback-only、拒绝 8899、`trust_env=False`、不跟随 redirect、短超时、错误去敏。

TEST-133：`python -m app.supervision --json`；startup gate=`app.preflight`，process=`app.server`，live/ready probe，SIGTERM 30s graceful window，on-failure restart，不绑定具体 systemd/Nginx/Docker/云厂商。

## TEST-134 — Release Runbook Contract — GITHUB SELF-TEST PASSED

目标：把 TEST-126~133 的既有能力组合成可验证的发布/回滚顺序，而不是新增第二套运行逻辑。

实现：
1. 新增 `backend/app/core/deployment.py`；
2. 新增只读 contract CLI `python -m app.deployment --json`；CLI 只输出计划，不执行 backup/stop/start/restore；
3. 固定发布顺序：`online_backup → release_preflight → stop_current_process → switch_release → start_candidate_process → verify_liveness → verify_readiness`；
4. online backup 固定复用 `python -m app.backup`，必须在 release switch 前成功；
5. release preflight 固定复用 `python -m app.preflight --json`，必须在停止当前进程前成功；
6. release switch 明确为 external platform action，不自动操作 Git/systemd/Nginx/Docker；必须保留运行配置、数据库和 backups；
7. stop/start/probe 直接复用 TEST-133/132 契约：SIGTERM→grace→SIGKILL、`python -m app.server`、live→ready；
8. 普通 code rollback 与 database rollback 严格分离；发布失败不会自动 restore 数据库；
9. 只有明确判断 schema/data 必须回滚时，才允许人工使用 `python -m app.restore --backup <verified-backup-path> --offline-confirmed`；要求应用完全离线、backup 已验证；
10. 所有命令保持 argument vector，不通过 shell；不嵌入 auth token、DashScope key、LLM encryption key 或 database path；
11. production-only、loopback-only、拒绝 port 8899；
12. 无 schema migration，不启动/停止任何真实进程。

第一轮 CI `35355252345`：11 passed / 1 failed。失败是新测试把安全标志 `reserved_port_8899_forbidden=true` 误判成“使用了 8899”；生产实现无错误。测试修正为只禁止实际 `"port": 8899`，同时要求安全标志存在。

第二轮 GitHub Actions run `35355369005`：success；
- TEST-134：12 passed；
- TEST-133：11 passed；
- TEST-132：11 passed；
- TEST-131：9 passed；
- TEST-130：10 passed；
- TEST-127 restore：8 passed；
- TEST-126 backup：8 passed；
- production auth：8 passed；
- scope isolation：4 passed；
- full pytest：734 passed、1 warning in 30.29s；
- warning 仍为 Starlette TestClient / anyio BlockingPortal deprecation；
- 临时 workflow 已删除。

当前等待服务器验收 TEST-134。服务器验收只需 pytest / git diff / git status，不执行 `app.deployment`、backup/restore/preflight/server/probe，不修改 `.env`，不触碰 8899。

## 下一阶段候选

TEST-134 服务器通过后重新审计 TEST-135。当前优先从“运维契约细分”切回“普通用户可用产品壳”：审计已有 Auth UI、Provider Settings UI 与业务 API，优先建立统一安全导航/应用入口，而不是继续拆更细的 deployment contract。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~134 verification tag 已创建。
