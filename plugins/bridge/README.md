# 自动回复通道插件（PC 端）

这个目录是随 Windows 客户端一起打包的桥接插件：微信 / 小红书 / Soul 三个平台的自动回复。

## 在 PC 客户端里使用

1. 打开客户端 → 登录后的「连接与账号」卡片 → **通道插件**
2. 填写军师账号密码（与登录同一套）
3. 选择平台：微信 / 小红书 / Soul
4. 先保持「试运行 = 是」，点 **保存并启动**
5. 点 **刷新状态**，应看到对应通道「在线 · 今日回复 N」
6. 确认草稿质量后，把试运行改为「否」，重新保存并启动

配置与状态文件位于：

```
%LOCALAPPDATA%\JunshiPC\bridge\
  config.toml       # 服务器、账号、平台、静默时段、日上限
  state.sqlite3     # 联系人映射与去重
  config.log        # 运行日志（按 5MB 轮转）
  bridge.pid        # 运行中的进程号
```

## 打包结构

```
JunshiPC/
  JunshiPC.exe
  JunshiBridge/
    JunshiBridge.exe     # 通道桥接（由 build_windows.py 一起构建）
    ...
```

`desktop/build_windows.py` 会先构建客户端，再构建 `plugins/bridge/run_bridge.py`，
把 `JunshiBridge/` 复制进安装目录；构建结束的冒烟检查会确认 exe 存在。

## 构建依赖

- Python 3.11/3.12（WeChat 通道依赖 `winsdk`，没有 3.13 wheel）
- `pip install -r plugins/bridge/requirements.txt`（httpx、wechatauto-replica）
- `pip install playwright`（小红书 / Soul 通道）
- 微信通道需要微信 4.1.12+ 已登录；小红书 / Soul 需要先扫码登录一次（浏览器 profile 在
  `%LOCALAPPDATA%\JunshiPC\bridge\profiles\`）

## 注意

- 桥接是独立进程，崩溃不会影响客户端；状态以服务端 `/api/v1/bridge/status` 心跳为准。
- 消息写入使用 `/api/v1/pc/messages`（幂等），平台来源记录在 `message_platform_sources`。
- 同一个人物的所有平台消息进入同一主会话；平台身份在「平台账号」里管理。
