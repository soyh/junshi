"""Authenticated desktop management using the existing per-user server APIs."""
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import urlsplit

PROVIDERS = ('qwen', 'deepseek', 'kimi', 'openai', 'gemini', 'openai_compatible')
PLATFORMS = {'微信':'wechat','抖音':'douyin','探探':'tantan','陌陌':'momo','Soul':'soul','其他':'other'}


SECTION_OPEN = '\u25be'   # ▾
SECTION_CLOSED = '\u25b8'  # ▸


class Section:
    """Collapsible group: a clickable caption that shows or hides its body."""

    def __init__(self, parent, title, open=True, note=''):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill='x', pady=(2, 6))
        self.open = tk.BooleanVar(value=open)
        self.title = title
        header = ttk.Frame(self.frame)
        header.pack(fill='x')
        self.caption = ttk.Label(header, text=self._caption(), cursor='hand2', foreground='#1f5fbf')
        self.caption.pack(side='left')
        self.caption.bind('<Button-1>', lambda _event: self.toggle())
        self.caption.bind('<Enter>', lambda _event: self.caption.configure(foreground='#0b3d8c'))
        self.caption.bind('<Leave>', lambda _event: self.caption.configure(foreground='#1f5fbf'))
        if note:
            ttk.Label(header, text=note, foreground='#666').pack(side='left', padx=(8, 0))
        ttk.Separator(self.frame, orient='horizontal').pack(fill='x', pady=(2, 0))
        self.body = ttk.Frame(self.frame, padding=(16, 2, 2, 2))
        if open:
            self.body.pack(fill='x')
        self.widgets = []

    def _caption(self):
        return f'{SECTION_OPEN if self.open.get() else SECTION_CLOSED} {self.title}'

    def toggle(self):
        self.open.set(not self.open.get())
        if self.open.get():
            self.body.pack(fill='x')
        else:
            self.body.forget()
        self.caption.configure(text=self._caption())

    def entry(self, dialog, key, label, value='', choices=None, secret=False):
        widget = dialog.entry(key, label, value, choices, secret, parent=self.body)
        self.widgets.append(widget)
        return widget


def scrollable(parent):
    """Wrap a frame in a vertical scroll area and return the inner frame."""
    canvas = tk.Canvas(parent, borderwidth=0, highlightthickness=0)
    bar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind('<Configure>', lambda _event: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=inner, anchor='nw', tags='inner')
    canvas.bind('<Configure>', lambda event: canvas.itemconfigure('inner', width=event.width))
    canvas.configure(yscrollcommand=bar.set)
    canvas.pack(side='left', fill='both', expand=True)
    bar.pack(side='right', fill='y')

    def wheel(event):
        # Leave nested editors (rules text, logs) to their own scrolling.
        if str(event.widget.winfo_class()) in {'Text', 'Listbox'}:
            return None
        canvas.yview_scroll(-1 * (event.delta // 120), 'units')
        return 'break'

    canvas.bind_all('<MouseWheel>', wheel)
    return inner


def create_person_with_conversation(client, state, name, nickname, title):
    if not name.strip() or not title.strip():
        raise ValueError('人物姓名和首个会话名称都需要填写。')
    if 'person' not in state:
        if state.get('uncertain'):
            raise ValueError('人物创建结果不确定。请关闭窗口并刷新人物列表核对，不要重复创建。')
        state['uncertain'] = True
        state['person'] = client.request('POST', '/persons', {'name':name.strip(), 'nickname':nickname.strip() or None})
    person = state['person']
    # A lost conversation response can be reconciled on the newly created person.
    conversations = client.request('GET', '/conversations?person_id='+person['id'])
    conversation = next((c for c in conversations if c.get('title') == title.strip()), None)
    if conversation is None:
        conversation = client.request('POST', '/conversations', {'person_id':person['id'], 'title':title.strip()})
    return person, conversation


def model_payload(values, editing=False):
    payload = {k:values[k].strip() for k in ('name','provider','base_url','model')}
    if not all(payload.values()): raise ValueError('请填写配置名称、供应商、接口地址和模型名称。')
    if payload['provider'] not in PROVIDERS: raise ValueError('请选择支持的供应商。')
    parsed = urlsplit(payload['base_url'])
    if parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('模型接口地址无效，请填写完整的 HTTP(S) API 地址。')
    try: timeout = float(values['timeout_seconds'])
    except ValueError: raise ValueError('超时秒数需为数字。') from None
    if not 0 < timeout <= 300: raise ValueError('超时秒数必须大于 0 且不超过 300。')
    payload['timeout_seconds'] = timeout
    key = values['api_key'].strip()
    if key: payload['api_key'] = key
    elif not editing: raise ValueError('新建模型配置需要填写 API 密钥。')
    return payload


class Dialog:
    def __init__(self, app, title):
        self.app, self.client = app, app.client
        self.window = tk.Toplevel(app.root)
        self.window.title(title); self.window.transient(app.root)
        self.window.minsize(520, 260)
        self.window.grab_set()
        app.active_dialog = self
        self.frame = ttk.Frame(self.window,padding=14); self.frame.pack(fill='both',expand=True)
        self.message = tk.StringVar()
        self.widgets = []; self.secrets = []; self.busy = False
        self.window.protocol('WM_DELETE_WINDOW',self.close)

    def entry(self, key, label, value='', choices=None, secret=False, parent=None):
        parent = parent if parent is not None else self.frame
        ttk.Label(parent,text=label).pack(anchor='w',pady=(6,0))
        widget = ttk.Combobox(parent,values=choices,state='readonly') if choices else ttk.Entry(parent,show='*' if secret else '')
        widget.pack(fill='x'); widget.set(value) if choices else widget.insert(0,value)
        self.widgets.append((widget,'readonly' if choices else 'normal'))
        if secret:self.secrets.append(widget)
        return widget

    def fit(self, width=900, height=640):
        """Centre the dialog and cap it to the usable part of the screen."""
        self.window.update_idletasks()
        screen_w, screen_h = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        width, height = min(width, max(480, screen_w - 80)), min(height, max(360, screen_h - 120))
        left, top = max(0, (screen_w - width) // 2), max(0, (screen_h - height) // 2 - 20)
        self.window.geometry(f'{width}x{height}+{left}+{top}')
        return self.window

    def button(self, row, text, command):
        widget=ttk.Button(row,text=text,command=command);widget.pack(side='left',padx=3,pady=5)
        self.widgets.append((widget,'normal'));return widget

    def footer(self):
        ttk.Label(self.frame,textvariable=self.message,wraplength=520).pack(fill='x',pady=8)

    def close(self):
        if self.busy:return
        for field in self.secrets:field.delete(0,'end')
        self.app.active_dialog=None
        self.window.grab_release();self.window.destroy()

    def perform(self, work, done):
        if self.busy:return
        self.busy=True;self.app.lock(True)
        for widget,_ in self.widgets:widget.configure(state='disabled')
        self.message.set('正在处理，请等待…')
        def finish(result,error):
            self.busy=False;self.app.lock(False)
            for widget,state in self.widgets:widget.configure(state=state)
            if error:
                self.message.set(error)
            else:done(result)
        def run():
            try:result=work();error=None
            except Exception as exc:
                result=None;error=str(exc) if isinstance(exc,ValueError) else '操作未完成，请核对服务器记录后重试。'
            self.app.events.put(lambda:finish(result,error))
        threading.Thread(target=run,daemon=True).start()


class PersonDialog(Dialog):
    def __init__(self,app):
        super().__init__(app,'新建人物与首个会话')
        self.name=self.entry('name','人物姓名（必填）')
        self.nickname=self.entry('nickname','昵称（选填）')
        self.title=self.entry('title','首个会话名称（必填）','日常聊天')
        self.state={};self.input_values=None
        row=ttk.Frame(self.frame);row.pack(fill='x')
        self.button(row,'创建人物和会话 / 续接',self.save)
        self.button(row,'关闭',self.close);self.footer()

    def save(self):
        values=(self.name.get().strip(),self.nickname.get().strip(),self.title.get().strip())
        if not values[0] or not values[2]:return self.message.set('请填写人物姓名和首个会话名称。')
        if len(values[0])>200 or len(values[1])>200:return self.message.set('姓名和昵称不能超过 200 字。')
        if self.input_values and values!=self.input_values:
            return self.message.set('已开始创建，请保持原输入续接；需要修改时请先关闭并核对已有记录。')
        self.input_values=values
        def done(result):
            person,conversation=result;app=self.app
            app.people.append(person)
            app.person['values']=[p.get('nickname') or p['name'] for p in app.people];app.person.current(len(app.people)-1)
            app.accounts=[];app.account['values']=['未标注 / 旧会话'];app.account.current(0)
            app.conversations=[conversation];app.conversation['values']=[conversation['title']];app.conversation.current(0)
            app.invalidate();app.status.set('人物与首个会话已创建并选中，可添加平台账号或直接导入。')
            self.close()
        def work():
            try:return create_person_with_conversation(self.client,self.state,*values)
            except ValueError as exc:
                if 'person' in self.state:
                    raise ValueError('人物已创建，首个会话尚未确认完成。保持原输入点击续接即可。原因：'+str(exc)) from None
                raise
        self.perform(work,done)


class AccountDialog(Dialog):
    def __init__(self,app):
        self.person=app.selected_person()
        super().__init__(app,'为当前人物新建平台账号')
        self.platform=self.entry('platform','平台','微信',list(PLATFORMS))
        self.handle=self.entry('handle','平台账号 ID（必填，不是密码）')
        self.display=self.entry('display','显示名称（选填）')
        index=app.conversation.current()
        self.conversation=app.conversations[index] if index>=0 else None
        self.bind=tk.BooleanVar(value=bool(self.conversation and app.selected_account() is None))
        check=ttk.Checkbutton(self.frame,text='将当前会话整体绑定到新平台账号',variable=self.bind)
        check.pack(anchor='w',pady=8);self.widgets.append((check,'normal'))
        self.saved=None;self.frozen=None
        row=ttk.Frame(self.frame);row.pack(fill='x')
        self.button(row,'保存 / 续接',self.save);self.button(row,'关闭',self.close);self.footer()

    def save(self):
        payload={'platform':PLATFORMS[self.platform.get()],'account_handle':self.handle.get().strip(),'display_name':self.display.get().strip()}
        binding=self.bind.get()
        if not payload['account_handle']:return self.message.set('请填写平台账号 ID。')
        if any(len(payload[k])>120 for k in ('account_handle','display_name')):return self.message.set('账号 ID 和显示名称不能超过 120 字。')
        if binding and not self.conversation:return self.message.set('当前没有会话，请取消会话绑定，保存后新建会话。')
        if self.frozen and self.frozen!=(payload,binding):return self.message.set('请保持原输入续接，或关闭后核对服务器记录。')
        self.frozen=(payload,binding)
        def work():
            if not self.saved:
                accounts=self.client.request('GET',f'/persons/{self.person}/platform-accounts')
                self.saved=next((a for a in accounts if a['platform']==payload['platform'] and a['account_handle']==payload['account_handle']),None)
                if not self.saved:self.saved=self.client.request('POST',f'/persons/{self.person}/platform-accounts',payload)
            if binding:self.client.request('PUT',f'/conversations/{self.conversation["id"]}/platform-source',{'account_id':self.saved['id']})
            return self.client.request('GET',f'/persons/{self.person}/platform-accounts')
        def done(accounts):
            app=self.app;app.accounts=accounts
            app.account['values']=['未标注 / 旧会话']+[f"{a['platform']} · {a['display_name'] or a['account_handle']} ({a['account_handle']})" for a in accounts]
            app.account.current(1+next(i for i,a in enumerate(accounts) if a['id']==self.saved['id']))
            self.close();app.change_account()
        self.perform(work,done)


class ModelDialog(Dialog):
    def __init__(self,app):
        super().__init__(app,'我的大模型设置（仅当前账号）')
        self.profiles=[];self.selected=None
        self.selector=self.entry('profile','已保存的配置','新建配置',['新建配置'])
        self.selector.bind('<<ComboboxSelected>>',self.select)
        self.fields={k:self.entry(k,label,value,choices,secret) for k,label,value,choices,secret in (
            ('name','配置名称','','',False),('provider','供应商','qwen',PROVIDERS,False),
            ('base_url','API 接口地址（包含供应商要求的 /v1 等路径）','','',False),
            ('model','具体模型名称','','',False),('api_key','API 密钥（修改时留空表示保留原密钥）','','',True),
            ('timeout_seconds','请求超时（秒，最多 300）','60','',False))}
        row=ttk.Frame(self.frame);row.pack(fill='x')
        self.button(row,'保存配置',self.save);self.button(row,'设为回复模型',lambda:self.action('activate'))
        self.button(row,'设为视觉模型',lambda:self.action('vision'))
        row=ttk.Frame(self.frame);row.pack(fill='x')
        self.button(row,'测试连接',lambda:self.action('test'));self.button(row,'删除配置',lambda:self.action('delete'))
        self.button(row,'刷新',self.reload);self.button(row,'关闭',self.close)
        self.footer();self.reload()

    def reload(self,select_id=None):
        def work():return self.client.request('GET','/settings/llm/profiles'),self.client.request('GET','/settings/llm/vision')
        def done(result):
            self.profiles,vision=result
            self.selector['values']=['新建配置']+[p['name']+(' · 当前回复模型' if p['is_active'] else '') for p in self.profiles]
            index=next((i+1 for i,p in enumerate(self.profiles) if p['id']==select_id),0)
            self.selector.current(index);self.select()
            self.message.set('配置仅属于当前登录账号。'+('当前视觉模型：'+vision['name']+' / '+vision['model'] if vision else '尚未选择视觉模型。'))
        self.perform(work,done)

    def select(self,*_):
        index=self.selector.current();self.selected=self.profiles[index-1] if index>0 else None
        for key,field in self.fields.items():
            value='' if key=='api_key' else str((self.selected or {}).get(key,{'provider':'qwen','timeout_seconds':60}.get(key,'')))
            if key=='provider':field.set(value)
            else:field.delete(0,'end');field.insert(0,value)

    def save(self):
        try:payload=model_payload({k:v.get() for k,v in self.fields.items()},editing=bool(self.selected))
        except ValueError as exc:return self.message.set(str(exc))
        selected=self.selected
        self.fields['api_key'].delete(0,'end')
        def work():
            try:return self.client.request('PUT' if selected else 'POST','/settings/llm/profiles'+('/'+selected['id'] if selected else ''),payload)
            finally:payload.pop('api_key',None)
        self.perform(work,lambda result:self.reload(result['id']))

    def action(self,action):
        if not self.selected:return self.message.set('请先保存并选择一项配置。')
        profile=self.selected['id']
        if action=='test' and not messagebox.askyesno('测试模型连接','将调用该配置的模型接口，可能产生少量费用。继续？',parent=self.window):return
        if action=='delete' and not messagebox.askyesno('删除模型配置','删除当前账号的这项模型配置？',parent=self.window):return
        def work():
            if action=='vision':return self.client.request('PUT','/settings/llm/vision',{'profile_id':profile})
            if action=='delete':return self.client.request('DELETE','/settings/llm/profiles/'+profile)
            return self.client.request('POST',f'/settings/llm/profiles/{profile}/{action}')
        def done(result):
            if action=='test':self.message.set(str((result or {}).get('message') or ('连接测试通过' if (result or {}).get('status')=='ok' else '测试未通过，请检查配置。')))
            else:self.reload(profile if action!='delete' else None)
        self.perform(work,done)
