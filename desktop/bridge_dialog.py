"""Tk dialog for the bundled auto-reply channel plugin."""

import tkinter as tk
from tkinter import ttk

import bridge_plugin as bp
from management import Dialog


class BridgeDialog(Dialog):
    def __init__(self, app):
        super().__init__(app, "自动回复通道插件")
        summary = bp.load_config_summary()
        quiet = summary.get("quiet", bp.DEFAULT_QUIET)
        self.server = self.entry("server", "服务器", app.server.get() or summary.get("server", ""))
        self.username = self.entry("username", "军师账号", summary.get("username") or app.username.get())
        self.password = self.entry("password", "军师密码", summary.get("password", ""), secret=True)
        channel = bp.CHANNELS.get(summary.get("channel", "wechat"), "微信")
        self.channel = self.entry("channel", "平台通道", channel, choices=list(bp.CHANNELS.values()))
        self.dry_run = self.entry(
            "dry_run",
            "先试运行（只生成不发送）",
            "是" if summary.get("dry_run", True) else "否",
            choices=["是", "否"],
        )
        self.quiet = self.entry("quiet", "静默时段（开始-结束）", f"{quiet[0]}-{quiet[1]}")
        self.cap = self.entry("cap", "每日回复上限", str(summary.get("daily_cap", 30)))
        self.verify = self.entry("verify", "校验 HTTPS 证书", "是" if summary.get("verify_tls", True) else "否", choices=["是", "否"])

        row = ttk.Frame(self.frame)
        row.pack(fill="x")
        self.button(row, "保存并启动", self.save_and_start)
        self.button(row, "停止", self.stop_bridge)
        self.button(row, "刷新状态", self.refresh)
        self.button(row, "关闭", self.close)

        self.text = tk.Text(self.frame, height=7, wrap="word", state="disabled")
        self.text.pack(fill="both", expand=True, pady=(6, 0))
        self.footer()
        self.refresh()

    def _values(self):
        try:
            start, end = [part.strip() for part in self.quiet.get().split("-", 1)]
        except ValueError:
            raise ValueError("静默时段格式应为 03:00-05:30") from None
        try:
            cap = int(self.cap.get().strip() or "30")
        except ValueError:
            raise ValueError("每日回复上限必须是数字") from None
        return {
            "server": self.server.get(),
            "username": self.username.get(),
            "password": self.password.get(),
            "channel": bp.CHANNEL_LABELS.get(self.channel.get(), "wechat"),
            "dry_run": self.dry_run.get() == "是",
            "daily_cap": cap,
            "quiet": (start, end),
            "verify_tls": self.verify.get() == "是",
        }

    def save_and_start(self):
        if self.busy:
            return
        try:
            values = self._values()
            path = bp.save_config(**values)
            pid = bp.start(path)
        except ValueError as exc:
            self.message.set(str(exc))
            return
        except OSError as exc:
            self.message.set(f"启动失败：{exc}")
            return
        self.message.set(f"已保存并启动（进程 {pid}）。日志：{path.with_suffix('.log')}")

    def stop_bridge(self):
        if self.busy:
            return
        stopped = bp.stop()
        self.message.set("已停止通道进程。" if stopped else "当前没有运行中的通道进程。")

    def refresh(self):
        if self.busy:
            return
        if not getattr(self.app, "client", None):
            self.message.set("请先在主界面登录军师服务器，再刷新通道状态。")
            return
        client = self.app.client
        self.perform(lambda: bp.status_lines(bp.fetch_status(client)), self.render)

    def render(self, lines):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")
        self.message.set("通道进程运行中。" if bp.is_running() else "通道进程未运行。")
