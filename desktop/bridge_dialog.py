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
        self.headless = self.entry(
            "headless", "无头模式（网页自动回复，不弹窗口）", "是", choices=["是", "否"]
        )
        ttk.Label(
            self.frame,
            text="提示：小红书 / Soul 首次启动、或登录态过期时会自动打开可见浏览器窗口供扫码，登录成功后记录登录态并转为无头运行；「刷新状态」显示本机每个通道的当前状态，不再读取服务器汇总。",
            wraplength=560,
        ).pack(anchor="w")

        row = ttk.Frame(self.frame)
        row.pack(fill="x")
        self.button(row, "保存配置", self.save)
        self.button(row, "启动", self.start_profile)
        self.button(row, "停止", self.stop_profile)
        self.button(row, "启动全部", self.start_all)
        self.button(row, "刷新状态", self.refresh)
        self.button(row, "关闭", self.close)

        self.text = tk.Text(self.frame, height=5, wrap="word", state="disabled")
        self.text.pack(fill="both", expand=True, pady=(6, 0))
        self.footer()
        self.reload()
        self.window.after(15000, self._auto_refresh)

    def _auto_refresh(self):
        try:
            if self.window.winfo_exists():
                self.refresh()
                self.window.after(15000, self._auto_refresh)
        except Exception:
            pass

    # -- profile list -----------------------------------------------------
    def reload(self, select=None):
        self.profiles = {item["id"]: item for item in bp.list_profiles()}
        self.listbox.delete(0, "end")
        order = list(self.profiles)
        for index, profile_id in enumerate(order):
            item = self.profiles[profile_id]
            dot = "●" if item["running"] else "○"
            label = bp.CHANNELS.get(item["channel"], item["channel"])
            self.listbox.insert("end", f"{dot} {item['name']} · {label} · {item.get('status', '')}")
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
        self.headless.set("是" if item.get("headless", True) else "否")
        state = item.get("status") or ("运行中" if item["running"] else "未运行")
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
            "headless": self.headless.get() == "是",
        }

    def new_profile(self):
        try:
            values = self._values()
        except ValueError as exc:
            self.message.set(str(exc))
            return
        label = self.channel.get()
        values["name"] = f"{label}通道"
        values["channel"] = bp.CHANNEL_LABELS.get(label, "wechat")
        try:
            profile_id = bp.create_profile(**values)
        except (ValueError, OSError) as exc:
            self.message.set(str(exc))
            return
        self.current = profile_id
        self.reload(select=profile_id)
        self.message.set("已新建通道配置，可直接点「启动」。")

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
        before = self.profiles.get(self.current, {})
        try:
            bp.save_profile(self.current, **self._values())
        except ValueError as exc:
            self.message.set(str(exc))
            return
        changed = (
            before.get("running")
            and before.get("channel") != self._values()["channel"]
        )
        self.reload(select=self.current)
        self.message.set(
            "配置已保存；平台通道变更需先「停止」再「启动」才会生效。" if changed else "配置已保存。"
        )

    def start_profile(self):
        if not self.current:
            self.message.set("请先新建并保存通道配置。")
            return
        if self.profiles.get(self.current, {}).get("running"):
            self.message.set("该通道已在运行；如更换了平台，请先「停止」再「启动」。")
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

    def start_all(self):
        started, failed = 0, []
        for profile_id, item in list(self.profiles.items()):
            if item.get("running"):
                continue
            try:
                bp.start(profile_id)
                started += 1
            except (ValueError, OSError) as exc:
                failed.append(f"{item['name']}：{exc}")
        self.reload(select=self.current)
        self.message.set(
            f"已启动 {started} 个通道。" + (" 失败：" + "；".join(failed) if failed else "")
        )

    def refresh(self):
        if self.busy:
            return
        self.reload(select=self.current)
        self.perform(lambda: bp.status_lines(list(self.profiles.values())), self.render)

    def render(self, lines):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")
        running = sum(1 for item in self.profiles.values() if item["running"])
        self.message.set(f"状态以本机当前为准；运行中的通道：{running} 个。")
