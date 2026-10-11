# 当前开发交接

## 已验收功能基线

- TEST-214：`125c918f759786cec56e61e07411d794fed210cf`。
- 已有功能、人物卡连续翻转放大和工作区淡入保持原实现。
- 数据库迁移 001–020；此次仓库整理不增加迁移。
- TEST-214 Linux CI 全量 1274 项通过，并有浏览器验收；后续整理提交由 Stable release checks 再验收。

## 本次整理

默认分支收纳最新已验收应用、文档导航、Windows/Linux 本地初始化、发布隐私检查和持续集成。main 早期独立历史保留；阶段分支继续用于追溯。当前功能源码与 TEST-214 保持一致，不包含未验收的独立开发修改。

入口：[README](README.md)、[本地安装](docs/LOCAL_DEPLOYMENT.md)、[运维](docs/OPERATIONS.md)、[开发说明](docs/DEVELOPMENT.md)、[发布范围](docs/PRIVACY_AND_PUBLISHING.md)。

## 持续维护约束

- 历史迁移不改写；新需求使用新增迁移。
- 模型密钥按账号隔离，不回退到其他用户的配置。
- 用户聊天、人物档案、原始参考文档、日志、数据库与密钥禁止提交。
- 先隔离验证，再按明确目标部署；CI 不自动部署生产。
- 此仓库不携带原服务器的用户数据和私人运维参数。

[早期交接索引](docs/history/DEVELOPMENT_HANDOVER_PRE_CONSOLIDATION.md) 链接已有阶段记录，仅供追溯。

## TEST-216 PC 助手

新增原生 Windows 小窗、显式剪贴板文字/图片/本地视频读取、人物多平台账号、会话来源、操作幂等及用户级加密业务迁移。新增迁移 021，历史 001–020 不变。完整功能边界与使用步骤见 [TEST-216](docs/TEST-216-pc-assistant.md)。生产升级前先在副本上验收迁移和媒体完整导出。
