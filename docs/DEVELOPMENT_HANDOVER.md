# Development Handover

更新时间：2026-09-18
当前阶段：TEST-128 — Backup Manifest / Checksum / Retention — GITHUB SELF-TEST PASSED / SERVER VALIDATION DEFERRED
当前 Branch：test-128-backup-manifest-retention
TEST-127 VERIFIED 服务器代码 HEAD：`023fb2391d47d692db8b3b1002c5fbb2637be7d3`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-090：按既有交接记录 VERIFIED；TEST-091 CONTRACT LOCKED；TEST-092 VERIFIED；TEST-093 VERIFIED；TEST-094 CONTRACT LOCKED。
TEST-095 ~ TEST-125：按既有交接记录 VERIFIED。
TEST-126 VERIFIED — SQLite online backup + integrity verification；服务器 targeted 8 passed，累计 full 663。
TEST-127 VERIFIED — offline verified restore safety；服务器 targeted 8 passed，累计 full 663；HEAD `023fb2391d47d692db8b3b1002c5fbb2637be7d3`。
TEST-128 GITHUB SELF-TEST PASSED / SERVER VALIDATION DEFERRED — managed backup manifest/checksum/retention；full 672 passed。

## Runtime / Operations 产品化基线

- TEST-122：彻底退役 `X-User-ID` 身份来源。
- TEST-123：基础 HTTP 安全响应头、auth/settings no-store、无 permissive CORS。
- TEST-124：production 强制 `debug=False`，关闭 docs/redoc/openapi。
- TEST-125：统一 `python -m app.server`；production loopback-only、single-worker、no reload、no proxy trust、no Server header。
- TEST-126：SQLite online backup API + WAL-safe snapshot + integrity verification + atomic publish。
- TEST-127：offline-confirmed restore + pre/post integrity verification + atomic replace + stale WAL/SHM cleanup。
- TEST-128：managed backup manifest + SHA-256 + strict verification + retention dry-run/apply。

## TEST-126 / TEST-127 — VERIFIED

服务器累计验收：TEST-127 restore 8、TEST-126 backup 8、TEST-125 launcher 7、TEST-124 surface 4、production auth 8、scope isolation 4、full 663 passed in 123.02s；工作树 clean；migration diff 空；最终文件 diff 精确匹配。

## TEST-128 — Backup Manifest / Checksum / Retention — GITHUB SELF-TEST PASSED

目标：让备份从“存在一个 SQLite 文件”升级为“可审计、可校验、可安全保留/清理的 managed backup”。

实现：
1. 新增 `backend/app/core/backup_manifest.py`；
2. manifest schema version=1，记录 UTC `created_at`、backup basename、`size_bytes`、SHA-256、integrity=`ok`；
3. manifest 使用 sibling temp + fsync + atomic replace 发布；
4. `create_managed_backup()` 先复用 TEST-126 verified backup，再发布 manifest；manifest 发布失败则回滚刚创建的 backup；
5. `verify_backup_manifest()` 严格验证 schema、basename、防路径穿越、size、SHA-256 与 SQLite integrity；
6. backup/manifest 任一被篡改均 fail closed；
7. retention 只从有效 manifest 中发现 managed backups；损坏 manifest、checksum 不匹配或任意手工 SQLite 文件都不会成为删除候选；
8. `keep >= 1`；按 manifest UTC created_at 从新到旧保留；
9. dry-run 为默认，不删除；apply 时先删 manifest 再删 backup，异常时不会留下“manifest 指向已删文件”的危险状态；
10. `backend/app/backup.py` 默认创建 managed backup，并新增 `--verify-manifest`、`--retention-dir`、`--keep`、`--apply-retention`；
11. 无 schema migration；CI 全部只使用 pytest 临时目录。

新增 `backend/tests/test_backup_manifest_retention.py` 9 个契约测试：managed pair 创建/验证、backup tamper、manifest tamper/path traversal、manifest 发布失败回滚、retention dry-run、真实 retention、不删除 unrelated/invalid managed data、keep/directory 参数边界、CLI verify/dry-run。

GitHub Actions run `35314760780`：success；TEST-128 9、TEST-127 8、TEST-126 8、production auth 8、scope 4、full 672 passed、1 warning in 30.40s；临时 workflow 已删除。

为加速推进，TEST-128 服务器验收与 TEST-129 合并。

## 下一阶段

TEST-129 — Operations Readiness Check：只读检查数据库 integrity、migration file/DB application 一致性、最近有效 managed backup 的存在与新鲜度；提供机器可读 JSON/退出码，不输出 secrets；GitHub/服务器验收仍只使用临时库，不读取生产 DB。

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
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~128 verification tag 已创建。
