# AI Love Strategist Development Handover

更新时间：2026-09-18
当前阶段：TEST-135 — Authenticated Product Shell — VERIFIED
当前 Branch：test-135-authenticated-product-shell
TEST-135 VERIFIED 服务器代码 HEAD：`a2792c0207b1d43e6ad488c6deefec9e679f460f`
TEST-133 VERIFIED 服务器代码 HEAD：`74a9c5a976be094d9dd2d51e764ab457965f83ec`
TEST-133 验收闭环文档基线：`6066e6b108592df427f265291c7af968c681a3d2`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-135：按既有交接记录 VERIFIED。
TEST-134 VERIFIED — platform-neutral release runbook / rollback safety contract。
TEST-135 VERIFIED — authenticated single-page product shell。

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

## TEST-134 — Release Runbook Contract — VERIFIED

目标：把 TEST-126~133 的既有能力组合成可验证的发布/回滚顺序，而不是新增第二套运行逻辑。

实现：
1. `backend/app/core/deployment.py` + 只读 CLI `python -m app.deployment --json`；CLI 只输出计划，不执行任何步骤；
2. 发布顺序固定为 `online_backup → release_preflight → stop_current_process → switch_release → start_candidate_process → verify_liveness → verify_readiness`；
3. online backup 必须在 release switch 前成功；preflight 必须在停止进程前成功；
4. release switch 是 external platform action，不自动操作 Git/systemd/Nginx/Docker；
5. stop/start/probe 复用 TEST-133/132；
6. code rollback 与 database rollback 严格分离；发布失败不会自动 restore 数据库；
7. DB restore 仅在明确需要 schema/data rollback、应用完全离线且 backup 已验证时人工执行 `app.restore --offline-confirmed`；
8. 命令为 argv，不经 shell，不嵌入 secrets/database path；production-only、loopback-only、拒绝 8899；
9. 无 schema migration，不启动/停止真实进程。

GitHub Actions：
- 第一轮 CI `35355252345`：11 pass / 1 fail，失败为测试错误地把安全标志 `reserved_port_8899_forbidden=true` 当成实际使用 8899；生产实现无错误；
- 修正测试后 run `35355369005` success：TEST-134 12、TEST-133 11、TEST-132 11、TEST-131 9、TEST-130 10、restore 8、backup 8、production auth 8、scope 4；full 734 passed、1 warning in 30.29s。

服务器最终累计验收于 TEST-135 HEAD `a2792c0207b1d43e6ad488c6deefec9e679f460f` 完成：TEST-134/135 targeted 18 passed，full 740 passed，`git diff --check` 和 `git status --short` 均无输出。TEST-134 正式锁定 VERIFIED。

## TEST-135 — Authenticated Product Shell — VERIFIED

目标：解决旧 Auth UI 与 Provider UI 登录态无法安全跨页衔接的问题，让普通用户拥有一个真正统一的产品入口，同时继续坚持 session token 只存在当前页面内存。

实现：
1. 新增 `backend/app/ui/product_shell.py`；
2. 新增 `backend/app/ui/routes.py`，提供顶层 `/app`，隐藏于 OpenAPI；
3. `backend/app/main.py` 挂载 product shell，并对 `/app` 设置 `Cache-Control: no-store`；基础安全头继续由 TEST-123 middleware 统一提供；
4. `/app` 同页完成 register/login/logout/session management、LLM Provider 管理与 Structured Analysis；
5. 登录/注册返回的 opaque session token 只保存于 `let currentAccessToken` 页面内存变量；不写 `localStorage`、`sessionStorage`、URL、DOM token input 或 X-User-ID；刷新/关闭页面即丢失；
6. Provider 操作直接复用 `/api/v1/settings/llm` 与 `/test`；API Key 输入为 password，load/save/delete 后清空，服务端不回传 key；
7. Structured Analysis 继续调用现有 `/api/v1/conversations/{id}/analysis/structured`，不另写分析逻辑；
8. authenticated controls 登录前 disabled；session rotate 后用服务器新 token 替换页面内存 token；logout 清空 token 和敏感输入；
9. 原 `/api/v1/auth/ui` 与 `/api/v1/settings/llm/ui` 保留，旧 VERIFIED 入口和测试不变；
10. Workspace 只说明当前核心后端模块，不伪造 Person/Relationship/Conversation 等尚未完成的产品页面；
11. 无 schema migration。

GitHub Actions run `35356010017`：success；TEST-135 6、Auth UI 4、Provider UI 3、HTTP security 6、Account login 7、Session management 7、Password change 8、Production auth 8、Scope isolation 4；full 740 passed、1 warning in 29.93s。

服务器第一次累计验收在 `8e62e788387992e37c976152f5120d45e1ad39a1` 上暴露一个 cwd-dependent 测试缺陷：`tests/test_auth_bootstrap_retirement.py::test_env_example_disables_bootstrap_by_default` 使用 `Path(".env.example")`，从 `backend/` 工作目录运行时错误寻找 `backend/.env.example`。这是测试 cwd 假设，不是生产代码失败。

修复提交 `416dc6c3f5d1769161fb688eb4a8c7f12920e16b`：改为从 `Path(__file__).resolve().parents[2]` 定位仓库根目录，仍校验同一个根目录 `.env.example`，未修改 production code、migration、`.env` 或运行时配置。GitHub Actions server-parity run `35362679263` 从 `backend/` 工作目录验证：bootstrap 6 passed、TEST-134/135 18 passed、full 740 passed、1 warning in 36.70s。

服务器最终复跑于 `a2792c0207b1d43e6ad488c6deefec9e679f460f`：
- `tests/test_auth_bootstrap_retirement.py`：6 passed；
- `tests/test_release_runbook_contract.py + tests/test_authenticated_product_shell.py`：18 passed；
- full pytest：740 passed in 124.80s；
- `git diff --check` 无输出；
- `git status --short` 无输出。

TEST-135 正式锁定 VERIFIED。

## 下一阶段

TEST-136 — Authenticated Core Workspace：把真正的业务 Workspace 接入统一 `/app`。优先复用并接入 Person / Relationship / Conversation 已有 API，严格保持 bearer session、user scope 与 existing canonical contracts；不在本阶段一次性重写 Recommendation / Action Plan / Execution / Outcome 全链路 UI。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~135 verification tag 已创建。