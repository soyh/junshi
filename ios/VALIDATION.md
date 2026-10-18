# iOS 验证记录

## TEST-236 · 可恢复创建与平台绑定

验证代码：`5c89ac3ce0759d9befe83bc061f14f9bb48ee9ab`，已合并为主分支提交 `43d8b3711bab7aac3e887681e9d424acab5ba542`。

- [iOS CI](https://github.com/soyh/junshi/actions/runs/38776065464)：模拟器单元与界面测试、无签名设备归档、构建附件与截图导出全部通过。
- [全项目稳定性检查](https://github.com/soyh/junshi/actions/runs/38776065312)：服务端全量、浏览器验收、Windows/Linux 本地安装检查及桌面客户端检查全部通过。
- [代码合并](https://github.com/soyh/junshi/pull/29)。

本版把明确的创建输入拒绝保留为可修改重试；遇到超时或服务器错误仍按“结果未知”保护，避免重复创建。平台账号已创建但会话绑定/刷新失败时，重试只继续后续绑定，不重复创建平台账号。

## TEST-232 · 初始 iOS 预览

验证代码：`020159741d3098348054a9c961c9863d96736840`。

- [iOS CI](https://github.com/soyh/junshi/actions/runs/38583351760)：6 项单元测试、1 项模拟器完整操作测试、无签名设备归档全部通过。
- [既有项目回归](https://github.com/soyh/junshi/actions/runs/38583351544)：通过。
- [代码合并](https://github.com/soyh/junshi/pull/25)。

CI 附件包含模拟器构建、无签名设备归档、SHA256SUMS 和测试截图/报告。Actions 附件有保留期限，并可能要求登录 GitHub；可从源码重新构建。当前没有可安装的正式 IPA，也未上传 TestFlight。

测试使用合成账号、聊天和模拟接口，未连接生产用户账户或付费模型。尚待 Apple 签名、iPhone 真机及系统分享扩展端到端验收。服务器代码、数据库和其他客户端不会因 iOS 源码开发自动部署或改变。
