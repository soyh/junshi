# 文档目录

## 当前维护入口

- [统一项目总览与下载](PROJECT_OVERVIEW.md)

- [本地安装](LOCAL_DEPLOYMENT.md)
- [运维、升级与恢复](OPERATIONS.md)
- [开发与仓库结构](DEVELOPMENT.md)
- [隐私与发布范围](PRIVACY_AND_PUBLISHING.md)
- [当前交接](../DEVELOPMENT_HANDOVER.md)
- [可移植加密恢复工具](PORTABLE_RECOVERY.md)

## 功能设计记录

- 参考资料：[目录检索](TEST-200-reference-catalog.md)、[全局指南](TEST-201-global-reference-guide.md)
- 聊天导入：[发送者识别与映射](TEST-203-named-chat-import.md)
- 回复生成：[长历史预算](TEST-204-long-history-budget.md)、[最新消息](TEST-205-reply-freshness.md)、[纠正恢复](TEST-206-latest-turn-recovery.md)
- 长期档案：[更新与审计](TEST-207-person-memory-latency.md)、[失败恢复](TEST-208-memory-recovery.md)、[统一精简档案](TEST-210-uniform-person-profile.md)
- [分析与策略契约](ANALYSIS_LLM_STRATEGY_CONTRACT.md)

`TEST-*` 文档描述对应阶段的设计，不表示当前生产状态。TEST-211–214 页面导航与卡片动画的实现和浏览器验收位于 `backend/app/ui/`、`backend/tests/*browser.py` 及对应 Git 分支。

## 历史资料

[早期开发交接](history/DEVELOPMENT_HANDOVER_PRE_CONSOLIDATION.md)、[首用户验收流程](FIRST_USER_UAT.md)、`ops/first_user_uat/` 和其余 TEST 编号资料用于追溯。历史环境路径、测试数量与阶段结论不应替代当前安装说明，也不要把历史部署命令直接当作新安装命令。

- [PC 小窗、多平台人物、完整迁移（TEST-216）](TEST-216-pc-assistant.md)
