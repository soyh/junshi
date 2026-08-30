# AI Love Strategist Development Handover

更新时间：2026-08-30
当前阶段：TEST-082 — Execution / Action Decision Closure — IN PROGRESS
当前 Branch：test-082-execution-action-decision-closure
上一阶段：TEST-081 — Recommendation Producer Contract — VERIFIED

---

## 信息检索优先级（强制）

凡是需要检索、确认或定位的内容，首先从 GitHub 仓库 `soyh/junshi` 当前开发分支及历史代码、测试、文档中查找。只有 GitHub 找不到时，才能要求服务器端查询，并必须说明原因及命令。

不得在尚未完成 GitHub 检索前，要求用户通过服务器端 grep、sed、日志或数据库查询来确认本可由仓库确认的信息。

---

## 产品最终目标与实现路线

本项目不是单纯聊天机器人或回复生成器，而是长期关系管理 + AI 恋爱决策辅助系统。

最终核心闭环：

`关系对象 → 人物档案 → 聊天/现实互动 → 时间线 → Canonical Evidence → Fact / Inference / Unknown → 关系状态 → Recommendation → Action Plan → User Decision / Confirmation → Execution → Outcome / Feedback → Learning / Memory Update → 重新判断`

必须严格区分：

- Fact：canonical data / canonical evidence 支持的现实信息。
- Inference：基于事实形成的 derived interpretation，必须保留 provenance。
- Unknown：证据不足时保持未知，不得由模型猜测补全。
- Recommendation：基于当前证据、推断、未知及关系状态形成的决策建议；不等同于事实、推断或 action candidate。

最终系统目标是形成“AI 恋爱军师”，而不是“AI 回复生成器”。

### 后续总路线

开发策略从“持续堆叠功能”切换为“优先打通真实可运行的关系决策闭环”。不再以 schema / service / test 数量作为主要进度指标，而以真实用户能否完成一次可追踪、可解释、可反馈的关系决策循环作为 MVP 核心验收标准。

Phase 1 — Core Data Foundation：基本完成。

Phase 2 — Evidence / Analysis / Strategy：主体已完成，持续完善边界。

Phase 3 — Decision → Execution Closure：当前阶段。优先打通 Recommendation → Action Plan → User Decision / Confirmation → Execution → Outcome。

Phase 4 — End-to-End AI Relationship Loop：建立 Person → Conversation / Interaction → Timeline → Evidence → Analysis → Recommendation → Action Plan → Decision → Execution → Outcome → Feedback → Re-analysis 的系统级闭环。

Phase 5 — Real LLM + Real User Workflow：在闭环稳定后接入真实 LLM 与真实用户工作流，确保 LLM 只负责解释、归纳、推断和候选建议，系统负责事实、provenance、状态、确认、执行和结果记录。

Phase 6 — Relationship Memory / Learning：基于现实执行结果和用户确认形成长期关系记忆与状态更新；禁止把 AI 推断自动当成事实或长期记忆。

Phase 7 — Optimization / Scale：在 MVP 闭环稳定后，再增加人物画像增强、关系趋势、风险检测、策略优化、多候选策略、策略效果统计等高级能力。

### 六条持续原则

1. 不为 schema 而 schema。
2. 不为 test 数量而 test。
3. 不让 LLM 直接成为事实来源。
4. 不让 inference 自动变成 memory。
5. 不让 Recommendation 绕过 User Confirmation。
6. 每增加一个能力，都必须回答它如何进入完整关系闭环。

---

## 架构冻结

正式契约：`docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`

主链：

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Human Confirmation → Execution / Outcome`

冻结规则：

- AnalysisContext 是 deterministic、source-backed、read-only 的 LLM 输入。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- StructuredAnalysis 中 inference / hypothesis / material signal 必须保留 evidence provenance。
- unknown 不得被模型猜测自动提升为事实。
- Strategy、Strategic Reply、Action Plan 只能消费既有 derived analysis，不建立第二套生命周期。
- LLM 不得自动确认 decision、执行 action、发送消息、修改 relationship state、写入 learning history 或伪造 outcome。
- StructuredAnalysis 当前为 request-scoped output；如未来持久化，必须独立设计并新增 migration。
- Provider：Qwen / DashScope OpenAI-compatible API；provider adapter 与上层 contract 解耦。

---

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 Strategy Decision Lifecycle — VERIFIED
TEST-046 Strategy Decision Lifecycle Synthesis — VERIFIED
TEST-047 Strategy Decision Learning Input — VERIFIED
TEST-048 Strategy Decision Learning Synthesis — VERIFIED
TEST-049 Strategy Decision Learning Bridge — VERIFIED
TEST-050 Strategy Decision Learning Synthesis Bridge — VERIFIED
TEST-051 Learning Strategy Recommendation Bridge — VERIFIED
TEST-052 Learning Strategy Strategic Reply Bridge — VERIFIED
TEST-053 Learning Strategy Action Plan Bridge — VERIFIED
TEST-054 Learning Strategy Downstream Candidate Contract — VERIFIED
TEST-055 Learning Strategy Downstream Constraint Contract — VERIFIED
TEST-056 Learning Strategy Downstream Memory Update Semantics — VERIFIED
TEST-057 Learning Strategy Downstream Candidate Parity — VERIFIED
TEST-058 Learning Strategy Source Provenance — VERIFIED
TEST-059 Learning Strategy Provenance Immutability — VERIFIED
TEST-060 Learning Strategy Source Provenance Completeness — VERIFIED
TEST-061 Learning Strategy Provenance Parity — VERIFIED
TEST-062 Learning Strategy Decision Provenance Parity — VERIFIED
TEST-063 Learning Strategy Decision Constraint Parity — VERIFIED
TEST-064 Learning Strategy Decision Learning Evidence Completeness — VERIFIED
TEST-065 Analysis Context learning-strategy bridge — VERIFIED
TEST-066 Analysis Context relationship-state bridge — VERIFIED
TEST-067 Analysis Context canonical evidence bridge — VERIFIED
TEST-068 Analysis Context conversation evidence bridge — VERIFIED
TEST-069 Analysis Context evidence contract sync — VERIFIED
TEST-070 Analysis LLM Service — VERIFIED
TEST-071 Structured Analysis Strategy Bridge — VERIFIED
TEST-072 Analysis → Strategy Orchestration — VERIFIED
TEST-073 Qwen Provider Integration — VERIFIED
TEST-074 Analysis → Strategy formal entrypoint — VERIFIED
TEST-075 StructuredAnalysis → Strategy Decision 最小消费契约 — VERIFIED
TEST-076 StructuredAnalysis → Strategic Reply 消费契约 — VERIFIED
TEST-077 Strategic Reply downstream boundary — VERIFIED
TEST-078 StructuredAnalysis → Action Plan 消费契约 — VERIFIED
TEST-079 Learning Strategy → Action Plan HTTP Response Contract — VERIFIED
TEST-080 StructuredAnalysis → Action Plan Candidate Boundary — VERIFIED
TEST-081 Recommendation Producer Contract — VERIFIED

---

## TEST-081 正式状态

TEST-081 已完成服务器验收并通过完整回归：Recommendation 专项及相关 downstream 测试通过，完整 `pytest -q`：489 passed；`git diff --check` 通过；working tree clean；无 migration / database schema 变化；未改变 action_decisions / action_executions / action_outcomes 生命周期。

核心边界：

- Recommendation 是 typed、explicit、evidence-backed candidate。
- StructuredAnalysis 不得直接成为 Recommendation 或 Action Candidate。
- Recommendation Producer 不写数据库、不确认 decision、不执行 action、不发送消息。
- 合法 Recommendation 进入既有 Action Plan / Strategic Reply downstream。
- Decision / Confirmation / Execution / Outcome 保持独立生命周期。

TEST-081 提交链已保留于 `test-081-recommendation-producer-contract` 历史；最终验收状态为 VERIFIED。

---

## TEST-082 — Execution / Action Decision Closure

### 目标

不新增第二套执行生命周期，而是审计并锁定现有 `Action Decision → Confirmation → Execution → Outcome` 的正式业务闭环，使 Recommendation / Action Plan 能够安全进入用户确认与执行边界，并明确系统不得自动执行。

### 精确契约

`Recommendation → Action Plan → Action Decision → User Confirmation → Execution → Outcome`

必须满足：

- Recommendation / Action Plan 只能产生候选或 proposal，不能自动创建已确认、已执行或已完成的业务结果。
- Action Decision 必须保留其来源 action / recommendation / evidence provenance（以当前代码已有字段和生命周期为准），不得凭空产生事实。
- Confirmation 是明确的人类控制边界；未确认的 proposal 不得进入 execution。
- Execution 只能消费已确认 decision；禁止 pending / rejected / unconfirmed decision 自动执行。
- Outcome 必须代表真实执行结果；系统不得由 recommendation、analysis 或 decision 文本伪造 outcome。
- Execution / Outcome 不应反向修改 canonical evidence，除非现有正式生命周期明确允许且经过独立契约；本 TEST-082 不新增隐式副作用。
- 不修改数据库 schema，不新增 migration，不创建第二套 Decision / Execution / Outcome 生命周期。
- 不允许 LLM 直接确认、执行、发送消息或伪造结果。

### TEST-082 最小修改面

优先只修改：

- 现有 Action Decision / Confirmation / Execution 边界中实际缺失的 contract 或 validation。
- 对应最小测试文件，用于锁定未确认不得执行、确认后才能执行、outcome 只能来自真实 execution result 等边界。
- 如现有实现已经满足某项契约，只补测试，不改生产代码。

明确禁止：

- 不扩张 Recommendation Producer。
- 不重新设计 Action Plan。
- 不新增数据库表 / migration。
- 不接入新的 LLM 能力。
- 不自动发送真实消息。
- 不把 execution outcome 当成 AI inference。

### TEST-082 验收门槛

- 针对现有 Action Decision / Confirmation / Execution / Outcome 的专项测试全部通过。
- 相关 Recommendation / Action Plan downstream 回归全部通过。
- 完整 `pytest -q` 通过。
- `git diff --check` 通过。
- working tree clean。
- 无新增 migration / schema 变化。
- 明确证明 unconfirmed decision 无法执行，confirmed decision 才能进入 execution，outcome 不由 analysis / recommendation 自动生成。

---

## 数据库与运行约束

当前 migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。

TEST-045 ~ 当前阶段默认不新增 migration，不改变 action_decisions、action_executions、action_outcomes 的既有生命周期。

Route → Service → Repository → SQLite。

所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

---

## 持续禁止事项

- 不得把 StructuredAnalysis 直接转换为 Recommendation。
- 不得把 StructuredAnalysis 直接转换为 Action Candidate。
- 不得让 LLM 进入 canonical evidence、persistence、learning context、decision persistence 或 execution 层。
- 不得自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 不得为了测试方便绕过 user / person / conversation isolation。
- 不得建立第二套 Strategy / Decision / Strategic Reply / Action Plan 生命周期。
- 不得为了填充 Action Plan 而绕过 canonical evidence → recommendation → confirmation 链。
- 不得在 GitHub 已能确认时要求服务器端查询。

---

## 下一步执行规则

TEST-082 从 GitHub 当前分支开始。先审计现有 Action Decision / Confirmation / Execution / Outcome 实现与测试，只有确认真实缺口后才进行最小修改。完成后执行专项回归和完整回归，再更新 handover 并进入 TEST-083。
