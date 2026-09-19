from pathlib import Path

path = Path("DEVELOPMENT_HANDOVER.md")
text = path.read_text(encoding="utf-8")

replacements = [
    (
        """更新时间：2026-09-19
当前阶段：TEST-146 — Re-analysis Workspace — VERIFIED
当前 Branch：`test-146-reanalysis-workspace`
TEST-146 VERIFIED 服务器代码/文档 HEAD：`8a58d056897a2cfbb09ba284c386fe01cb9cbcf7`
TEST-145 post-verification 基线：`ff33b34fa9896259cacd4dc4543486a8afc39df1`""",
        """更新时间：2026-09-19
当前阶段：TEST-147 — Full Product Lifecycle E2E / Release Acceptance — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：`test-147-full-lifecycle-release-acceptance`
TEST-146 post-verification 基线：`dcb4bef6f4d07fddfba80b9448408a1e436a736f`
TEST-146 VERIFIED 服务器代码/文档 HEAD：`8a58d056897a2cfbb09ba284c386fe01cb9cbcf7`
TEST-145 post-verification 基线：`ff33b34fa9896259cacd4dc4543486a8afc39df1`""",
    ),
    (
        """- TEST-008 ~ TEST-146：按既有交接记录 VERIFIED。
- TEST-134 VERIFIED：platform-neutral release runbook / rollback safety contract。""",
        """- TEST-008 ~ TEST-146：按既有交接记录 VERIFIED。
- TEST-147：GitHub self-test passed，服务器最终验收 pending。
- TEST-134 VERIFIED：platform-neutral release runbook / rollback safety contract。""",
    ),
    (
        """## 下一阶段候选

Full Product Lifecycle E2E / Release Acceptance。

TEST-146 已服务器 VERIFIED。下一步允许从本次 post-verification 提交建立新阶段，但必须先审计现有 release preflight / release runbook / runtime probe / backup-readiness 与完整产品生命周期 E2E 覆盖，再锁定下一 TEST 编号和精确 acceptance contract。不得再扩展新的业务生命周期阶段。

## 架构与持续禁止事项""",
        """## TEST-147 — Full Product Lifecycle E2E / Release Acceptance — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

### Acceptance contract 审计

TEST-147 不新增业务生命周期阶段，也不修改生产 API / service / repository / schema / migration / UI。现有 release 层已经具备完整安全契约：
- release preflight 汇总 production config、secure launcher 与 operations readiness，并 fail closed；
- managed SQLite backup 具备 integrity / manifest / SHA-256 verification；
- release runbook 固定 `online_backup → release_preflight → stop_current_process → switch_release → start_candidate_process → verify_liveness → verify_readiness`；
- release switch 是 external platform action；
- code rollback 不等于 database rollback；database restore 永不自动执行，只允许 application fully offline + verified backup 下的显式人工 restore；
- runtime probe 只允许 loopback，8899 保持 forbidden。

现有业务闭环与 release safety tests 之前是分散验证。TEST-147 的唯一新增内容是顶层 acceptance tests，把“真实认证产品闭环”和“完整迁移数据库 release readiness”放进同一阶段验收；没有为了验收复制第二套业务逻辑。

### TEST-147 acceptance tests

新增 `backend/tests/test_full_product_lifecycle_release_acceptance.py`，2 项：

1. authenticated full lifecycle E2E：
   - 真实 `/auth/register` 取得 opaque Bearer session；
   - 真实 HTTP 创建 Person → Relationship → Conversation → Message；
   - 使用 deterministic test provider 隔离外部 LLM 网络依赖，但实际经过现有 Analysis → StrategyRecommendationCandidate → RecommendationProducer → Action Plan service/repository 路径；
   - Action Plan 必须含 explicit action、evidence provenance、`status=proposed`、`requires_user_confirmation=true`；
   - 用户单独显式创建 confirmed Action Decision；
   - Execution 前记录 Outcome 必须返回 409；
   - 用户单独显式创建 Execution，再单独显式记录 `completed` Outcome；
   - canonical Feedback 读取为 `outcome_observed` / `completed`；
   - Learning synthesis 产生 `learning_provenance.status=observed_outcome` 的 memory proposal；
   - memory persist 必须是独立显式 POST，并确认数据库 `memory_updates` 只有一条对应记录；
   - persist 完成后 provider 调用次数仍保持 1，证明 persist 没有自动触发 Re-analysis；
   - 用户随后显式调用 canonical `/recommendation/context`，第二次 provider invocation 消费 observed Feedback + memory learning，产生 fresh derived StructuredAnalysis 与 evidence-backed Recommendation；
   - Recommendation 仍保持 `must_not_auto_select=true`、`must_not_auto_execute=true`；
   - 整个闭环前后 Relationship profile 不变。

2. release acceptance on fully migrated SQLite：
   - 在真实完整 migration fixture DB 上注册用户并写入业务数据；
   - 实际创建 managed online backup + manifest；
   - `check_release_preflight()` 必须同时通过 configuration / secure launcher / database / migrations / verified backup readiness；
   - `build_release_runbook()` 必须保持 backup→preflight→stop→switch→start→live→ready 的固定顺序；
   - candidate start 必须使用 `python -m app.server` 且 loopback-only；
   - live/ready verification 必须使用 `python -m app.probe ... --json`；
   - database restore 必须 `automatic_database_restore=false`、`manual_only=true`、requires application fully offline、requires verified backup。

### 首轮 CI 发现与修正

首轮 GitHub Actions run `35422338837` / job `105842190418`：release acceptance 测试 1/2 通过，full lifecycle case 在 Action Plan gate 停止，因为 test provider 的 hypothesis 只有 recommendation 文本，没有 explicit `action`。现有 `ActionPlanService` 正确拒绝把没有 explicit action 的 Recommendation 提升为 Action Plan；这是 acceptance fixture 不完整，不是生产缺陷。

只修正 test provider，使 hypothesis 显式携带 `action`；没有修改生产代码、没有弱化 gate。修正提交：`4b691aa416cbdaf3ef90448b80b077d1bc4d6a95`。

### GitHub Actions 最终验证

成功 run `35422430074`，job `105842430832`，测试 HEAD `4b691aa416cbdaf3ef90448b80b077d1bc4d6a95`：
- TEST-147 focused：2 passed、1 warning in 0.42s；
- Product Workspace regression through TEST-146：90 passed、1 warning in 6.45s；
- canonical lifecycle / safety closure：17 passed、1 warning in 1.27s；
- release operations acceptance regression：100 passed、1 warning in 1.10s；
- combined targeted：209 passed、1 warning in 8.52s；
- full pytest：826 passed、1 warning in 40.40s。

唯一 pytest warning 仍为 Starlette TestClient 对 `anyio.abc.BlockingPortal` alias 的 deprecation；GitHub runner Node20→Node24 action warning 非测试失败。

### TEST-147 提交

- `014607599e1a6187818ad8f4e0c7acc3faf4f0e8` — 新增 2 项 Full Product Lifecycle / Release Acceptance tests；
- `2f0977a184c46705b6af89a13d1e566b1dc8c0b2` — 临时 TEST-147 validation workflow；
- `4b691aa416cbdaf3ef90448b80b077d1bc4d6a95` — 仅修正 acceptance fixture 的 explicit action；
- `16060d6b953d2e3b529a5d9fce3615d7125e27f4` — GitHub success 后删除临时 validation workflow。

### 服务器最终验收

PENDING。服务器必须验证：
- branch `test-147-full-lifecycle-release-acceptance` 与最终 handover HEAD；
- combined targeted 209；
- full 826；
- 对当前实际数据库先创建 fresh managed online backup，再运行 `python -m app.preflight --json`，必须返回 `ready=true`；
- 在当前 service 正常运行时，loopback `python -m app.probe live --json` 与 `ready --json` 必须成功；
- 不停止/切换当前进程，不执行 restore；
- `git diff --check` 与 `git status --short` 无输出；
- root `DEVELOPMENT_HANDOVER.md` 存在、duplicate handover 不存在；
- TEST-147 临时 workflows 不存在。

TEST-147 只有上述服务器验收全部通过后才可标记 VERIFIED。

## 下一阶段

当前不创建 TEST-148。TEST-147 server VERIFIED 后，产品业务闭环与 release acceptance 基线即完整闭合。若进入实际发布，必须执行已 VERIFIED 的 TEST-134 release runbook；若继续新增阶段，必须先审计新的真实产品/运维缺口，不得为了延长 TEST 编号重复实现既有能力。

## 架构与持续禁止事项""",
    ),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f"missing expected handover block: {old[:140]!r}")
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
