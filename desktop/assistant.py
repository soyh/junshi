"""Windows PC companion: explicit clipboard capture and server-backed replies."""
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, simpledialog
import webbrowser

from PIL import Image, ImageTk

from client import Client
from clipboard_media import capture, files_snapshot
from pc_workflow import new_job, generate, confirm_sent
from preferences import load_server, save_server
from management import PersonDialog, AccountDialog, ModelDialog
from registration import ACCOUNT_HINT, PASSWORD_HINT, validate
from email_account import EmailAccountDialog
from theme import install_theme, text_surface, raised_card

CHINA = timezone(timedelta(hours=8))


def now_text():
    value = datetime.now(CHINA)
    return f'{value.year:04d}年{value.month:02d}月{value.day:02d}日 {value.hour:02d}:{value.minute:02d}:{value.second:02d}'


def timestamp(value):
    try:
        return datetime.strptime(value.strip(), '%Y年%m月%d日 %H:%M:%S').replace(tzinfo=CHINA).isoformat()
    except ValueError:
        raise ValueError('时间请使用 年月日 和 24 小时制，例如 2026年10月11日 20:30:00') from None


class Assistant:
    def __init__(self, root, hotkey=True):
        self.root = root
        self.root.title('AI 恋爱军师 · PC 助手')
        install_theme(root)
        screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
        if sys.platform == 'win32':
            work = wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(work), 0):
                screen_w, screen_h = work.right-work.left, work.bottom-work.top
        width, height = min(1040, screen_w-40), min(800, screen_h-60)
        self.root.geometry(f'{width}x{height}')
        self.root.minsize(min(880, width), min(620, height))
        self.events = queue.Queue()
        self.client = None
        self.busy = False
        self.media = []
        self.job = None
        self.job_key = None
        self.people = []
        self.accounts = []
        self.conversations = []
        self.hotkey_thread = None
        self.closed = False
        self.active_dialog = None
        self.controls = []
        frame = ttk.Frame(root, padding=10, style='Page.TFrame')
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1, uniform='message')
        frame.rowconfigure(3, weight=1, uniform='message')
        header = ttk.Frame(frame, style='Page.TFrame'); header.grid(row=0, column=0, sticky='ew', pady=(0, 7))
        ttk.Label(header, text='AI 恋爱军师', style='Title.TLabel', font=('Microsoft YaHei UI', 15, 'bold')).pack(side='left')
        ttk.Label(header, text='让每一次回应，都多一点温度', style='Subtitle.TLabel').pack(side='right')
        top = ttk.Frame(frame, style='Page.TFrame'); top.grid(row=1, column=0, sticky='ew')
        top.columnconfigure(0, weight=1, uniform='top'); top.columnconfigure(1, weight=1, uniform='top')
        login = raised_card(top, '  连接与账号  ', row=0, column=0)
        self.server = self.entry(login, '服务器', load_server(), label_width=8)
        self.username = self.entry(login, '用户名', label_width=8)
        self.password = self.entry(login, '密码', secret=True, label_width=8)
        ttk.Label(login, text=ACCOUNT_HINT, wraplength=420).pack(anchor='w')
        ttk.Label(login, text=PASSWORD_HINT, wraplength=420).pack(anchor='w')
        row = ttk.Frame(login); row.pack(fill='x')
        self.button(row, '登录', self.login)
        self.button(row, '注册', lambda: self.open_email_account())
        self.button(row, '打开主页面', self.open_main)
        self.button(row, '退出登录', self.logout)
        self.button(row, '大模型设置', lambda: self.open_management(ModelDialog))
        self.button(row, '通道插件', self.open_bridge)
        selection = raised_card(top, '  选择这次对话  ', row=0, column=1)
        self.person = self.combo(selection, '人物', self.change_person)
        self.account = self.combo(selection, '平台账号', self.change_account)
        self.conversation = self.combo(selection, '会话', lambda *_: self.invalidate())
        actions = ttk.Frame(selection); actions.pack(fill='x')
        self.button(actions, '新建人物', lambda: self.open_management(PersonDialog))
        self.button(actions, '新建平台账号', lambda: self.open_management(AccountDialog))
        self.button(actions, '新建会话', self.create_conversation)
        self.button(actions, '刷新人物', self.refresh_people)
        upper = raised_card(frame, '  对方说了什么  ·  消息与附件  ', row=2)
        lower = raised_card(frame, '  这样回复试试  ·  可编辑后复制  ', row=3)
        upper.columnconfigure(0, weight=1); upper.rowconfigure(0, weight=1)
        lower.columnconfigure(0, weight=1); lower.rowconfigure(0, weight=1)
        body = ttk.Frame(upper); body.grid(row=0, column=0, sticky='nsew')
        self.incoming = scrolledtext.ScrolledText(body, height=2, wrap='word'); self.incoming.pack(side='left', fill='both', expand=True)
        text_surface(self.incoming)
        self.preview = ttk.Label(body, text='无附件', wraplength=110); self.preview.pack(side='right', padx=(8,0))
        incoming_footer = ttk.Frame(upper); incoming_footer.grid(row=1, column=0, sticky='ew')
        time_box = ttk.Frame(incoming_footer); time_box.pack(side='left', fill='x', expand=True)
        self.incoming_time = self.entry(time_box, '北京时间', now_text(), label_width=8)
        row = ttk.Frame(incoming_footer); row.pack(side='right', padx=(6,0))
        self.button(row, '读取剪贴板', self.read_clipboard)
        self.button(row, '选择图片 / 视频', self.choose_files)
        self.button(row, '清空输入', self.clear_input)
        self.button(row, '分析并生成 / 重试', self.run_generation)
        self.reply = scrolledtext.ScrolledText(lower, height=2, wrap='word'); self.reply.grid(row=0, column=0, sticky='nsew')
        text_surface(self.reply)
        reply_footer = ttk.Frame(lower); reply_footer.grid(row=1, column=0, sticky='ew')
        time_box = ttk.Frame(reply_footer); time_box.pack(side='left', fill='x', expand=True)
        self.reply_time = self.entry(time_box, '发送时间', now_text(), label_width=8)
        row = ttk.Frame(reply_footer); row.pack(side='right', padx=(6,0))
        self.button(row, '一键复制', self.copy_reply)
        self.button(row, '确认已发送', self.confirm)
        self.button(row, '换一条', self.regenerate)
        self.status = tk.StringVar(value='登录后选择人物与平台。Ctrl+Alt+J 唤起并读取剪贴板；不会自动上传。')
        bottom = ttk.Frame(frame, style='Page.TFrame'); bottom.grid(row=4, column=0, sticky='ew')
        status_label = ttk.Label(bottom, textvariable=self.status, wraplength=620, style='Status.TLabel')
        status_label.pack(side='left', fill='x', expand=True)
        status_label.bind('<Configure>', lambda event: status_label.configure(wraplength=max(240, event.width-24)))
        row = ttk.Frame(bottom); row.pack(side='right', padx=(6,0))
        self.button(row, '收起窗口', self.hide)
        self.button(row, '退出助手', self.close)
        self.root.protocol('WM_DELETE_WINDOW', self.hide)
        self.root.after(100, self.poll)
        if hotkey and sys.platform == 'win32':
            thread = threading.Thread(target=self.hotkey_loop, daemon=True)
            thread.start()

    def entry(self, parent, title, value='', secret=False, label_width=24):
        row = ttk.Frame(parent); row.pack(fill='x', pady=2)
        ttk.Label(row, text=title, width=label_width).pack(side='left')
        entry = ttk.Entry(row, width=14, show='*' if secret else '')
        entry.insert(0, value); entry.pack(side='left', fill='x', expand=True)
        self.controls.append((entry, 'normal'))
        return entry

    def combo(self, parent, title, callback):
        row = ttk.Frame(parent); row.pack(fill='x', pady=2)
        ttk.Label(row, text=title, width=8).pack(side='left')
        box = ttk.Combobox(row, width=14, state='readonly'); box.pack(side='left', fill='x', expand=True)
        box.bind('<<ComboboxSelected>>', callback); self.controls.append((box, 'readonly'))
        return box

    def button(self, parent, text, command):
        primary = text in ('登录', '分析并生成 / 重试', '一键复制')
        button = ttk.Button(parent, text=text, command=command, width=0, style='Primary.TButton' if primary else 'TButton')
        button.pack(side='left', padx=2, pady=3)
        self.controls.append((button, 'normal'))
        return button

    def poll(self):
        if self.closed:
            return
        try:
            while True:
                callback = self.events.get_nowait()
                callback()
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def lock(self, busy):
        self.busy = busy
        for widget, state in self.controls:
            widget.configure(state='disabled' if busy else state)
        self.incoming.configure(state='disabled' if busy else 'normal')
        self.reply.configure(state='disabled' if busy else 'normal')

    def submit(self, work, done):
        if self.busy:
            return
        self.lock(True)
        def worker():
            try:
                result = work()
                self.events.put(lambda: self.finish(done, result))
            except Exception as exc:
                # Client errors are sanitized; don't display unknown internals.
                text = str(exc) if isinstance(exc, ValueError) else '操作失败，请检查服务器状态或依赖。已保存的记录会保留。'
                self.events.put(lambda: self.finish(lambda _: self.status.set(text), None))
        threading.Thread(target=worker, daemon=True).start()

    def finish(self, done, result):
        self.lock(False)
        done(result)

    def report(self, text):
        self.events.put(lambda: self.status.set(text))

    def login(self, register=False):
        try:
            client = Client(self.server.get())
        except ValueError as exc:
            return self.status.set(str(exc))
        username, password = self.username.get(), self.password.get()
        if register:
            try:
                validate(username, password)
            except ValueError as exc:
                return self.status.set(str(exc))
        self.password.delete(0, 'end')
        def work():
            session = client.request('POST', '/auth/register' if register else '/auth/login', {'username': username, 'password': password}, timeout=30)
            client.token = session['access_token']
            people = client.request('GET', '/persons', timeout=30)
            return people
        def done(people):
            self.client = client; self.people = people
            try:
                save_server(client.base)
            except OSError:
                pass  # Address persistence is optional; login remains usable.
            self.person['values'] = [p.get('nickname') or p['name'] for p in people]
            self.person.set(''); self.account.set(''); self.conversation.set('')
            self.accounts = []; self.conversations = []; self.invalidate()
            self.status.set('已连接。可在此新建人物、平台账号并配置模型；完整数据迁移仍在主页面操作。')
        self.submit(work, done)

    def open_email_account(self,purpose='register'):
        if self.busy:return
        if self.active_dialog:self.active_dialog.window.lift();return
        try:EmailAccountDialog(self,purpose)
        except ValueError as exc:self.status.set(str(exc))

    def open_bridge(self):
        if self.busy:return
        if self.active_dialog:self.active_dialog.window.lift();return
        try:
            from bridge_dialog import BridgeDialog
            BridgeDialog(self)
        except ValueError as exc:self.status.set(str(exc))

    def open_management(self, dialog):
        if not self.client:return self.status.set('请先登录服务器。')
        if self.busy:return
        if self.active_dialog:
            self.active_dialog.window.lift();return
        try:dialog(self)
        except ValueError as exc:self.status.set(str(exc))

    def refresh_people(self):
        if not self.client:return self.status.set('请先登录。')
        def done(people):
            self.people=people;self.person['values']=[p.get('nickname') or p['name'] for p in people]
            self.person.set('');self.account.set('');self.conversation.set('')
            self.accounts=[];self.conversations=[];self.account['values']=();self.conversation['values']=()
            self.invalidate();self.status.set('人物列表已刷新，请重新选择人物。')
        self.submit(lambda:self.client.request('GET','/persons'),done)

    def selected_person(self):
        index = self.person.current()
        if not self.client or index < 0:
            raise ValueError('请先登录并选择人物')
        return self.people[index]['id']

    def invalidate(self):
        self.job = None; self.job_key = None
        self.reply.delete('1.0', 'end')

    def change_person(self, *_):
        self.invalidate(); self.account.set(''); self.conversation.set('')
        self.accounts = []; self.conversations = []
        try:
            person = self.selected_person()
        except ValueError as exc:
            return self.status.set(str(exc))
        def done(accounts):
            self.accounts = accounts
            self.account['values'] = ['未标注 / 旧会话'] + [f"{a['platform']} · {a['display_name'] or a['account_handle']} ({a['account_handle']})" for a in accounts]
            self.account.current(0); self.change_account()
        self.submit(lambda: self.client.request('GET', f'/persons/{person}/platform-accounts'), done)

    def selected_account(self):
        index = self.account.current()
        return self.accounts[index-1]['id'] if index > 0 else None

    def change_account(self, *_):
        self.invalidate(); self.conversation.set(''); self.conversations = []
        person, account = self.selected_person(), self.selected_account()
        def work():
            conversations = self.client.request('GET', f'/conversations?person_id={person}')
            return [c for c in conversations if (self.client.request('GET', f'/conversations/{c["id"]}/platform-source') or {}).get('id') == account]
        def done(conversations):
            self.conversations = conversations
            self.conversation['values'] = [c.get('title') or '未命名会话' for c in conversations]
            if conversations: self.conversation.current(0)
            self.status.set('请选择会话；来自同一人物的各平台共用长期档案。')
        self.submit(work, done)

    def create_conversation(self):
        try: person = self.selected_person()
        except ValueError as exc: return self.status.set(str(exc))
        account = self.selected_account()
        title = simpledialog.askstring('新建会话','请填写会话名称：',initialvalue='日常聊天',parent=self.root)
        if title is None:return
        title=title.strip()
        if not title:return self.status.set('会话名称不能为空。')
        def work():
            conversation = self.client.request('POST', '/conversations', {'person_id': person, 'title': title})
            if account:
                self.client.request('PUT', f'/conversations/{conversation["id"]}/platform-source', {'account_id': account})
            return conversation
        def done(conversation):
            self.conversations.insert(0, conversation)
            self.conversation['values'] = [c.get('title') or '未命名会话' for c in self.conversations]
            self.conversation.current(0); self.invalidate(); self.status.set('已新建会话。')
        self.submit(work, done)

    def replace_input(self, text, media):
        if text == self.incoming.get('1.0', 'end-1c') and media == self.media and (text.strip() or media):
            self.status.set('剪贴板与窗口内容相同，保留当前导入和重试状态。')
            return
        if self.incoming.get('1.0', 'end-1c').strip() or self.media:
            if not messagebox.askyesno('替换输入', '替换窗口中已有内容？服务器上已保存的记录不会删除。'):
                return
        self.invalidate(); self.media = media
        self.incoming.delete('1.0', 'end'); self.incoming.insert('1.0', text)
        self.incoming_time.delete(0, 'end'); self.incoming_time.insert(0, now_text())
        self.preview.configure(image='', text='无附件'); self.preview.image = None
        if media:
            names = '\n'.join(f'{m["name"]} · {len(m["content"])/1024:.0f} KiB' for m in media)
            self.preview.configure(text=names)
            if media[0]['mime'].startswith('image/'):
                try:
                    image = Image.open(io.BytesIO(media[0]['content'])); image.thumbnail((140, 80))
                    photo = ImageTk.PhotoImage(image)
                    self.preview.configure(image=photo, compound='left'); self.preview.image = photo
                except Exception:
                    self.preview.configure(text=names + '\n无法预览，请核对附件格式')
        self.status.set('已读取到本地窗口，尚未上传。请确认人物、平台、内容和时间。视频上传后按关键帧识别。')

    def read_clipboard(self):
        if self.busy: return
        try:
            text, media = capture(self.root.clipboard_get)
            self.replace_input(text, media)
        except Exception as exc:
            self.status.set(str(exc) if isinstance(exc, ValueError) else '剪贴板暂时不可读取，请重试或选择附件。')

    def choose_files(self):
        names = filedialog.askopenfilenames(filetypes=[('图片与视频', '*.png *.jpg *.jpeg *.webp *.gif *.mp4 *.webm *.mov')])
        if not names: return
        try: self.replace_input('', files_snapshot(names))
        except ValueError as exc: self.status.set(str(exc))

    def clear_input(self):
        self.replace_input('', [])

    def run_generation(self):
        try:
            person = self.selected_person()
            index = self.conversation.current()
            if index < 0: raise ValueError('请选择或新建当前平台的会话')
            conversation = self.conversations[index]['id']
            text = self.incoming.get('1.0', 'end-1c')
            if not text.strip() and not self.media: raise ValueError('请先读取文字、图片或视频')
            sent_at = timestamp(self.incoming_time.get())
        except ValueError as exc: return self.status.set(str(exc))
        key = hashlib.sha256(json.dumps([person, conversation, text, sent_at, [hashlib.sha256(m['content']).hexdigest() for m in self.media]]).encode()).hexdigest()
        if key != self.job_key:
            self.job = new_job(person, conversation, text, list(self.media), sent_at); self.job_key = key
        elif self.job['confirmed']:
            return self.status.set('这条回复已登记发送，请先读取新的对方消息。')
        job, client = self.job, self.client
        def done(draft):
            self.reply.delete('1.0', 'end'); self.reply.insert('1.0', draft)
            self.reply_time.delete(0, 'end'); self.reply_time.insert(0, now_text())
            self.status.set('建议已生成。复制不会记为已发送；请实际发送后点击确认。')
            self.refresh_memory(client, job)
        self.submit(lambda: generate(client, job, self.report), done)

    def regenerate(self):
        if self.job and self.job['confirmed']:
            return self.status.set('此回复已登记发送，请读取新的对方消息。')
        self.run_generation()

    def refresh_memory(self, client, job):
        def work():
            try: client.request('POST', f'/persons/{job["person"]}/memory/refresh', timeout=30)
            except Exception:
                self.events.put(lambda: self.status.set('回复已保留；长期档案更新暂未安排成功，可在主页面重试。') if self.job is job and self.client is client else None)
        threading.Thread(target=work, daemon=True).start()

    def copy_reply(self):
        text = self.reply.get('1.0', 'end-1c')
        if not text.strip(): return self.status.set('还没有可复制的建议')
        self.root.clipboard_clear(); self.root.clipboard_append(text)
        self.status.set('已复制，尚未记为发送。请到聊天软件粘贴发送后再确认。')

    def confirm(self):
        if not self.job: return self.status.set('请先生成回复')
        text = self.reply.get('1.0', 'end-1c')
        if not text.strip(): return self.status.set('回复不能为空')
        try: sent_at = timestamp(self.reply_time.get())
        except ValueError as exc: return self.status.set(str(exc))
        if not messagebox.askyesno('确认已发送', '你是否已在聊天软件发送下方最终文字？这里只登记记录，不会代你发送。'):
            return
        job, client = self.job, self.client
        def done(saved):
            self.status.set('已登记发送并保留服务器记录。' if saved else '已经登记过，不会重复添加。')
            self.refresh_memory(client, job)
        self.submit(lambda: confirm_sent(client, job, text, sent_at), done)

    def open_main(self):
        try:
            client = self.client or Client(self.server.get())
        except ValueError as exc:
            return self.status.set(str(exc))
        def opened(url):
            if webbrowser.open(url):
                self.status.set('已打开主页面。' if not client.token else '已打开主页面并衔接当前账号。')
            else:
                self.status.set('无法打开默认浏览器，请检查系统默认浏览器后重试。')
        self.submit(client.browser_url, opened)

    def logout(self):
        self.client = None; self.people = []; self.accounts = []; self.conversations = []
        self.person.set(''); self.account.set(''); self.conversation.set('')
        self.person['values'] = (); self.account['values'] = (); self.conversation['values'] = ()
        self.incoming.delete('1.0', 'end'); self.media = []; self.preview.configure(image='', text='无附件')
        self.invalidate(); self.password.delete(0, 'end'); self.status.set('已清除本机登录状态和窗口内容。')

    def activate(self):
        if self.busy: return
        if self.active_dialog:
            self.root.deiconify();self.active_dialog.window.lift();return
        self.root.deiconify(); self.root.lift(); self.root.attributes('-topmost', True)
        self.root.after(800, lambda: self.root.attributes('-topmost', False))
        self.read_clipboard()

    def hotkey_loop(self):
        user32 = ctypes.windll.user32
        self.hotkey_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        if not user32.RegisterHotKey(None, 1, 0x0002 | 0x0001 | 0x4000, ord('J')):
            self.hotkey_thread = None
            self.events.put(lambda: self.status.set('Ctrl+Alt+J 已被其他程序占用，仍可点击读取剪贴板。'))
            return
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == 0x0312:
                    self.events.put(self.activate)
        finally:
            user32.UnregisterHotKey(None, 1)

    def hide(self):
        if self.hotkey_thread:
            self.root.withdraw()
        else:
            self.root.iconify()

    def close(self):
        if self.busy:
            return messagebox.showinfo('正在处理', '请等待本次操作结束后退出，避免丢失重试状态。')
        if not messagebox.askyesno('退出助手', '退出后快捷键停止工作，未提交的窗口内容不会保存。确定退出？'):
            return
        self.closed = True
        if self.hotkey_thread and sys.platform == 'win32':
            ctypes.windll.user32.PostThreadMessageW(self.hotkey_thread, 0x0012, 0, 0)
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    Assistant(root)
    root.mainloop()
