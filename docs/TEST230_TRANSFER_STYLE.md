# TEST-230 数据迁移入口样式修复

网页人物选择页的“PC 数据迁移 · 完整导出 / 导入”入口，收起时改为透明背景小字，与底部设置入口一致；展开时保留蓝白操作面板和键盘焦点提示。

候选提交 `21eb024dce5cd96510267c0eaecc2d4a220279c9`。GitHub 完整回归、浏览器验收及 Windows/Linux 安装检查通过。无新增迁移，数据库 001–023；迁移业务和客户端不变。PC 229 / Android 1.0.0-rc4 无需重装。

[修复下载页](https://github.com/soyh/junshi/releases/tag/test-230-transfer-entry-style) 提供代码包、源码、文档、上线脚本和校验值。上线脚本兼容 TEST-228/TEST-229 基线，先执行服务器隔离专项和全量，再停服备份、切换、HTTPS 验收。失败回退代码，保留数据库和私人配置。此资料发布不等于生产上线完成。

服务器操作：校验并上传 test230.bundle 与 deploy-test230.sh 后，以 root 执行 `bash deploy-test230.sh /home/ubuntu/test230.bundle`。上线后刷新网页检查入口收起、展开和导入导出控件；不要以真实数据测试破坏性操作。
