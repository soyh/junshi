# 开发与仓库维护

## 结构和基线

后端 FastAPI、SQLite；页面由 `backend/app/ui/` 提供，不需要额外的前端构建。`app/` 是根目录导入兼容层，运行入口为 `python -m app.server`。迁移在启动时应用，历史迁移 001–020 保持不变。

本次默认分支整合以 TEST-214 为功能基线。早期 main 与验收分支没有共同祖先，因此通过基于旧 main 的整合提交导入完整已验收文件树，保留旧 main 历史及所有阶段分支，不强制重写历史。

后续从 main 创建功能分支，经测试后合入 main；`test-*` 旧分支用于历史追溯，不批量删除，不将独立实验分支自动合入。`release.json` 记录功能来源，而不是冒充当前提交 SHA。

## 验证

在隔离副本安装依赖后：

```sh
cd backend
python -m pytest -q
```

主分支 CI 在 Ubuntu/Python 3.11 上执行全量测试；另外运行本地安装冒烟测试（Windows 与 Linux）和关键浏览器验收。浏览器测试使用模拟模型，不需要真实 API Key。

```sh
python -m pip install playwright==1.55.0
python -m playwright install chromium
# Linux 首次安装可使用 --with-deps
cd backend
PYTHONPATH=. python tests/card_morph_browser.py
```

Windows 手动浏览器测试可先设置 `$env:PYTHONPATH='.'`。已有部分运维测试依赖 Unix 文件权限与目录语义，全量验收以 Linux CI 为准；Windows 本地安装由独立冒烟验证覆盖。

不要在真实数据目录运行测试。不要更改测试来掩盖业务错误。修改后确认历史迁移、用户隔离、秘密配置及回退能力未受破坏。

## 资料发布

公开代码、脱敏设计文档、参数化脚本与合成测试样例。个人上传文档、聊天截图、生产日志、服务器地址、数据库及密钥保存在仓库外。阶段专用上传包和服务器脚本可能含个人路径或主机信息，不应整目录提交。CI 的发布检查辅助拦截私有文件名和明显密钥，但不能代替人工检查。
