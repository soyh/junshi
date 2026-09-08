# Development Handover

更新时间：2026-09-08
当前阶段：TEST-088 — Real LLM + Real User Workflow — ACCEPTANCE / 补证与运行时诊断
当前 Branch：test-088-real-llm-user-workflow
当前 HEAD：b1b6f2eac46ab9c6ad3c039c161a370e6cf9c32c

## 项目目标

本项目是长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人或回复生成器。

核心链路：

`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 架构与安全边界

- AnalysisContext 必须 deterministic、source-backed、read-only。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Fact / Inference / Unknown 必须严格区分；inference、hypothesis、material signal 必须保留 provenance。
- Recommendation 必须经过显式 candidate contract 与 RecommendationProducer。
- 不得自动选择、确认、执行 action，不得自动发送消息、修改 relationship 或伪造 outcome。
- 所有数据必须 user_id 隔离。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- 不得修改历史 migration、重写 migrations.py、修改 conversations/messages 业务逻辑或通过修改测试掩盖错误。

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 ~ TEST-064：VERIFIED
TEST-065 ~ TEST-087：VERIFIED

TEST-087 已锁定 Outcome → Feedback → Learning → Re-analysis → Recommendation 闭环，未新增第二套生命周期、migration 或数据库结构。

## TEST-088 当前验收状态

TEST-088 尚未 VERIFIED。当前结论是：自动化回归通过，真实 LLM 的部分链路已经验证，但真实用户完整闭环尚未完成验收。

已确认：

- 当前分支与 origin 同步，HEAD 为 `b1b6f2eac46ab9c6ad3c039c161a370e6cf9c32c`。
- 工作树 clean。
- 全量自动化测试：`509 passed`。
- 真实 Qwen / DashScope 请求曾返回 HTTP 200。
- StructuredAnalysis 路由曾成功返回，并保留 Fact / Inference / Unknown、evidence provenance 与禁止自动执行约束。
- 真实 person、relationship、conversation、message 数据曾成功写入。

尚未完成或未定位：

1. 曾出现一次 `POST /persons` 500，异常为 SQLite foreign key constraint failed。数据库结构当前未见明显异常，但失败请求使用的真实 user_id、请求体及当时数据库状态尚未核实，因此不得直接修改 Person 逻辑或数据库 FK。
2. StructuredAnalysis 曾出现间歇性 502；DashScope HTTP 请求同时为 200，应用层具体异常尚未定位。不得将其直接归因于 LLM provider 不稳定。
3. 尚未完成一次从真实用户数据开始，经 Strategy、Recommendation、Action Plan、Action Decision、显式确认、Execution、Outcome、Feedback、Learning，再回到下一轮 Analysis 的完整可追踪闭环。

## 下一次新对话的第一步

先不要修改生产代码、测试、migration、数据库或重启服务。首先读取并核对当前 GitHub 分支上的：

- `DEVELOPMENT_HANDOVER.md`
- `docs/DEVELOPMENT_HANDOVER.md`
- TEST-088 相关代码、测试与最近提交

随后继续执行只读诊断，优先确认：

- 当前运行实例与 GitHub HEAD 是否一致；
- `context.py`、persons route/service/repository/schema 及 users/persons migration 的真实契约；
- Person FK 500 的真实请求 user_id 与数据库存在性；
- StructuredAnalysis 502 的完整应用层 traceback；
- 真实用户闭环每个阶段的输入、输出、持久化记录和 provenance。

只有在根因确认后，才允许提出最小修复；未完成真实闭环前不得开始 TEST-089。

## 持续禁止事项

- 不得让 RecommendationProducer 直接消费 StructuredAnalysis。
- 不得把 inference 自动写入 canonical evidence 或 memory。
- 不得自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 不得绕过 user / person / conversation isolation。
- 不得建立第二套 Strategy / Decision / Action Plan / Execution / Learning 生命周期。
- GitHub 能确认的信息不得先要求服务器端查询。
