# AI Love Strategist Development Handover

更新时间：2026-09-17
当前阶段：TEST-101 — Execution Scope Isolation — VERIFIED PENDING SERVER ACCEPTANCE
当前 Branch：test-101-execution-scope-isolation
当前 HEAD：99a29fee242e3219aff839131e5606b8495dc673

## 项目目标

本项目是长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人或回复生成器。

核心生命周期：

`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis → Strategy → Recommendation`

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 ~ TEST-064：VERIFIED
TEST-065 ~ TEST-087：VERIFIED
TEST-088：VERIFIED
TEST-089：VERIFIED
TEST-090：VERIFIED
TEST-091 ~ TEST-094：VERIFIED
TEST-095：功能验收 VERIFIED；verification tag 尚待创建
TEST-096：功能验收 VERIFIED；verification tag 尚待创建
TEST-097：功能验收 VERIFIED；verification tag 尚待创建
TEST-098：服务器验收 VERIFIED；verification tag 尚待创建
TEST-099：服务器验收 VERIFIED；verification tag 尚待创建
TEST-100：GitHub Actions 回归通过，待服务器验收
TEST-101：GitHub Actions 回归通过，待服务器验收

## TEST-095 — Core Engine Persistence Closure

目标：补齐真实 Recommendation → Action Plan → Action Decision 的持久化恢复缺口，并保持 Outcome → Feedback → Learning → fresh Analysis → Recommendation 单一生命周期。

关键实现：
- 新增 migration 008 `action_plan_snapshots`；未修改历史 migration 001~007。
- 新增 `ActionPlanSnapshotRepository`，严格按 `user_id + person_id + recommendation_id` 隔离。
- `ActionPlanService` 在真实 DB connection 下恢复 persisted snapshot，并校验当前 canonical evidence。
- `AnalysisActionPlanService` 对 fresh evidence-backed Recommendation 产生 Action Plan 后持久化 snapshot。
- Action Plan 仍为 `proposed + requires_user_confirmation=True`，不得自动确认或执行。

验收：targeted 与全量 pytest 均通过；TEST-095 已锁定单一生命周期闭环。

## TEST-096 — Core Engine Safety Closure

锁定：`Confirmed Action Decision → Explicit Execution → Outcome`。

安全边界：
- Execution 必须引用当前 user/person scope 下的 confirmed Decision。
- rejected / missing / other-scope Decision 不得执行。
- Outcome 必须对应 confirmed Decision 且必须已有 execution。
- 同一 Decision 不得重复 execution / outcome。
- 保持 user/person isolation。
- 对真实跨 scope UUID 与任意客户端字符串 ID 保持既有 HTTP 错误合同。
- 未修改历史 migration 001~008。

GitHub Actions 全量回归在修复后连续两次通过。

## TEST-097 — Evidence-Backed Proposal Freshness

锁定：`Persisted Action Plan Snapshot → Current Canonical Evidence Validation → Explicit Action Decision`。

- snapshot 不是新的 Recommendation truth，只是 lifecycle state recovery mechanism。
- snapshot 恢复时必须验证 Recommendation 与 Action Plan 的全部 `evidence_source_ids` 仍存在于当前 canonical evidence。
- canonical evidence 已失效时，旧 snapshot 从当前可用 proposal context 排除，但不删除历史 snapshot。
- ActionDecision evidence-backed validation 不放宽。
- 未修改历史 migration 001~008。

GitHub Actions 全量 pytest：513 passed，1 warning。

## TEST-098 — Action Plan Snapshot Isolation

锁定 snapshot 的 user/person isolation：
- 相同 recommendation id 在不同 user scope 下可以保存不同 snapshot。
- 查询必须同时匹配 `user_id + person_id`。
- 不得返回其他 user 或其他 person 的 snapshot。

无 production code / migration 修改。服务器 targeted 与全量 pytest 已通过。

## TEST-099 — Action Plan Persistence Gate

锁定：只有真正对应 Action Plan item 的 Recommendation 才能进入 `action_plan_snapshots`。

- orphan Action Plan item 不得被持久化。
- Recommendation / Action Plan / evidence snapshot 的 `evidence_source_ids` 必须保持一致。
- 不修改历史 migration。

服务器 targeted 与全量 pytest 已通过。

## TEST-100 — Action Decision Proposal Gate + Execution Decision Gate

锁定两道显式生命周期边界。

第一道：只有 Action Plan item 同时满足：
- `status == "proposed"`
- `requires_user_confirmation is True`
- 存在 `recommendation_id`

才能进入 Action Decision。

第二道：只有 `confirmed` Action Decision 才能进入 Execution；rejected Decision、重复 execution，以及已有 Outcome 的 Decision 均被阻断。

`ActionDecisionCreate` 继续只允许显式 `confirmed | rejected`，系统不得伪造用户确认。

GitHub Actions targeted + full pytest 均通过；当前分支待服务器验收。

## TEST-101 — Execution Scope Isolation

目标：锁定 Action Execution 对 Action Decision 的 user/person scope 隔离，不允许同一 decision id 在其他 person scope 下被执行。

新增测试：
- `test_execution_uses_exact_user_and_person_scope_for_decision`
- `test_execution_does_not_cross_person_scope`

测试使用与 production service 相同的 scoped repository contract，验证 service 必须以 `(user_id, person_id, decision_id)` 获取 Decision，并在 scope 不匹配时不得创建 execution。

GitHub Actions：
- targeted `backend/tests/test_execution_scope_isolation.py`：通过
- full `pytest -q`：通过
- 临时 TEST-101 validation workflow 已删除，不作为产品代码保留。

当前状态：VERIFIED PENDING SERVER ACCEPTANCE。

## 核心安全边界

1. AnalysisContext 必须 deterministic、source-backed、read-only。
2. LLM 不直接访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
3. StructuredAnalysis 是 derived interpretation，不是 canonical truth。
4. Fact / Inference / Unknown 必须严格区分；Unknown 不得被伪造为事实或成功证据。
5. Recommendation 必须 evidence-backed，并保留 evidence provenance。
6. Action Plan 只能由显式 Recommendation 提案产生，状态为 proposed，并要求用户确认。
7. Action Decision 必须来自显式用户决策；不得自动 confirmed。
8. Execution 必须来自当前 scope 下的 confirmed Action Decision。
9. Outcome 必须来自已执行的 confirmed Action Decision。
10. Feedback / Learning / Re-analysis 不得自动确认、执行或产生 Outcome。
11. persisted snapshot 只能作为状态恢复机制，不能替代 canonical evidence 或 Recommendation truth。
12. user/person/relationship/conversation isolation 必须保持在所有读写路径。
13. 不得自动发送消息，不得自动修改 relationship。
14. 不得建立第二套 Recommendation / Action Plan / Decision / Execution / Outcome / Learning lifecycle。
15. MVP 不引入 PostgreSQL、Redis、Elasticsearch、Vector DB。
16. 不修改历史 migration 001~008；后续 schema 变更必须使用新的 migration 编号。
17. 不使用或修改端口 8899。

## 当前下一审计点

TEST-101 服务器验收通过后，下一阶段优先审计 Action Outcome 的并发幂等边界：当前 `ActionOutcomeService` 使用 read-before-write 防重复，但历史 migration 005 没有 `decision_id` UNIQUE 约束。若确认存在真实并发窗口，应通过新的 migration（不得修改 005）建立数据库级约束，并以独立测试锁定该契约。

同时继续审计：
- Recommendation / Action Plan 不得绕过 Decision 直接进入 Execution。
- Execution 不得绕过 Outcome 生命周期。
- Learning → AnalysisContext 的反馈传播必须真实、可追踪、无跨 scope 污染。
- Feedback / Learning 不得推断未经 evidence 支持的 success 或 relationship impact。

## 验收规则

每个 TEST 完成后必须：
- GitHub 代码与测试通过；
- 必要时进行服务器 targeted + full pytest；
- 检查 `git status --short`；
- 检查历史 migration 未被修改；
- 更新本 handover；
- verification tag 如当前 GitHub connector 无法创建，必须明确记录为 PENDING TAG，不得虚报。
