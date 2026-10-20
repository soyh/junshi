"""Tk dialog for the bundled multi-profile auto-reply channel plugin."""

import tkinter as tk
from tkinter import messagebox, ttk

import bridge_plugin as bp
from management import Dialog


class BridgeDialog(Dialog):
    def __init__(self, app):
        super().__init__(app, "自动回复通道插件（多开）")
        self.profiles = {}
        self.current = None

        ttk.Label(self.frame, text="通道配置（每个配置独立账号、平台登录态与进程，可同时运行）").pack(anchor="w")
        ttk.Label(
            self.frame,
            text="微信：一个 Windows 会话只能登录一个微信号，多开需不同 Windows 用户或虚拟机；小红书 / Soul：每个配置独立浏览器登录态，可并行。",
            wraplength=560,
        ).pack(anchor="w")
        list_row = ttk.Frame(self.frame)
        list_row.pack(fill="both", expand=True, pady=(4, 6))
        self.listbox = tk.Listbox(list_row, height=6, exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_row, command=self.listbox.yview)
        scroll.pack(side="left", fill="y")
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.bind("<<ListboxSelect>>", lambda _event: self.load_selected())

        row = ttk.Frame(self.frame)
        row.pack(fill="x")
        self.button(row, "新建通道", self.new_profile)
        self.button(row, "删除当前", self.delete_profile)
        self.button(row, "全部停止", self.stop_all)

        self.name = self.entry("name", "配置名称", "新通道")
        self.server = self.entry("server", "服务器", app.server.get())
        self.username = self.entry("username", "军师账号", app.username.get())
        self.password = self.entry("password", "军师密码", "", secret=True)
        self.channel = self.entry("channel", "平台通道", "微信", choices=list(bp.CHANNELS.values()))
        self.dry_run = self.entry("dry_run", "先试运行（只生成不发送）", "是", choices=["是", "否"])
        self.quiet = self.entry("quiet", "静默时段（开始-结束）", "03:00-05:30")
        self.cap = self.entry("cap", "每日回复上限", "30")
        self.verify = self.entry("verify", "校验 HTTPS 证书", "是", choices=["是", "否"])

        row = ttk.Frame(self.frame)
        row.pack(fill="x")
        self.button(row, "保存配置", self.save)
        self.button(row, "启动", self.start_profile)
        self.button(row, "停止", self.stop_profile)
        self.button(row, "刷新状态", self.refresh)
        self.button(row, "关闭", self.close)

        self.text = tk.Text(self.frame, height=5, wrap="word", state="disabled")
        self.text.pack(fill="both", expand=True, pady=(6, 0))
        self.footer()
        self.reload()

    # -- profile list -----------------------------------------------------
    def reload(self, select=None):
        self.profiles = {item["id"]: item for item in bp.list_profiles()}
        self.listbox.delete(0, "end")
        order = list(self.profiles)
        for index, profile_id in enumerate(order):
            item = self.profiles[profile_id]
            dot = "●" if item["running"] else "○"
            label = bp.CHANNELS.get(item["channel"], item["channel"])
            self.listbox.insert("end", f"{dot} {item['name']} · {label} · {item['username']}")
        if not order:
            self.current = None
            return
        target = select or self.current or order[0]
        if target not in self.profiles:
            target = order[0]
        index = order.index(target)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(index)
        self.load_selected()

    def load_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        profile_id = list(self.profiles)[selection[0]]
        item = self.profiles[profile_id]
        self.current = profile_id
        self._fill(self.name, item["name"])
        self._fill(self.server, item["server"])
        self._fill(self.username, item["username"])
        self._fill(self.password, item["password"])
        self.channel.set(bp.CHANNELS.get(item["channel"], "微信"))
        self.dry_run.set("是" if item["dry_run"] else "否")
        self.quiet.delete(0, "end"); self.quiet.insert(0, f"{item['quiet'][0]}-{item['quiet'][1]}")
        self.cap.delete(0, "end"); self.cap.insert(0, str(item["daily_cap"]))
        self.verify.set("是" if item["verify_tls"] else "否")
        state = "运行中" if item["running"] else "未运行"
        self.message.set(f"{item['name']}：{state}")

    @staticmethod
    def _fill(widget, value):
        widget.delete(0, "end")
        widget.insert(0, value or "")

    # -- actions ----------------------------------------------------------
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
            "name": self.name.get(),
            "server": self.server.get(),
            "username": self.username.get(),
            "password": self.password.get(),
            "channel": bp.CHANNEL_LABELS.get(self.channel.get(), "wechat"),
            "dry_run": self.dry_run.get() == "是",
            "daily_cap": cap,
            "quiet": (start, end),
            "verify_tls": self.verify.get() == "是",
        }

    def new_profile(self):
        profile_id = bp.create_profile()
        self.current = profile_id
        self.reload(select=profile_id)
        self._fill(self.name, "新通道")
        self.message.set("已新建配置，填写后点「保存配置」。")

    def delete_profile(self):
        if not self.current:
            return
        item = self.profiles.get(self.current, {})
        if not messagebox.askyesno("删除通道", f"删除「{item.get('name', self.current)}」及其登录态？", parent=self.window):
            return
        bp.delete_profile(self.current)
        self.current = None
        self.reload()
        self.message.set("已删除。")

    def save(self):
        if not self.current:
            self.message.set("请先新建通道配置。")
            return
        try:
            bp.save_profile(self.current, **self._values())
        except ValueError as exc:
            self.message.set(str(exc))
            return
        self.reload(select=self.current)
        self.message.set("配置已保存。")

    def start_profile(self):
        if not self.current:
            self.message.set("请先新建并保存通道配置。")
            return
        try:
            bp.save_profile(self.current, **self._values())
            pid = bp.start(self.current)
        except (ValueError, OSError) as exc:
            self.message.set(str(exc))
            return
        self.reload(select=self.current)
        self.message.set(f"已启动（进程 {pid}）。")

    def stop_profile(self):
        if not self.current:
            return
        stopped = bp.stop(self.current)
        self.reload(select=self.current)
        self.message.set("已停止。" if stopped else "该通道未在运行。")

    def stop_all(self):
        count = bp.stop_all()
        self.reload()
        self.message.set(f"已停止 {count} 个通道。")

    def refresh(self):
        if self.busy:
            return
        self.reload(select=self.current)
        if not getattr(self.app, "client", None):
            self.message.set("请先在主界面登录军师服务器，再刷新在线状态。")
            return
        client = self.app.client
        self.perform(lambda: bp.status_lines(bp.fetch_status(client)), self.render)

    def render(self, lines):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")
        running = sum(1 for item in self.profiles.values() if item["running"])
        self.message.set(f"在线状态已刷新；本机运行中的通道：{running} 个。")
