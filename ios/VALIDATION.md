# TEST-232 验证记录

验证代码：`020159741d3098348054a9c961c9863d96736840`。

- [iOS CI](https://github.com/soyh/junshi/actions/runs/38583351760)：6 项单元测试、1 项模拟器完整操作测试、无签名设备归档全部通过。
- [既有项目回归](https://github.com/soyh/junshi/actions/runs/38583351544)：通过。
- [代码合并](https://github.com/soyh/junshi/pull/25)。

CI 附件包含模拟器构建、无签名设备归档、SHA256SUMS 和测试截图/报告。Actions 附件有保留期限，并可能要求登录 GitHub。可以从源码重新构建。当前没有可安装的正式 IPA，也未上传 TestFlight。

测试使用合成账号、聊天和模拟接口，未连接生产用户账户或付费模型。尚待 Apple 签名、iPhone 真机及系统分享扩展端到端验收。服务器代码、数据库和其他客户端未因本次开发部署而变化。
