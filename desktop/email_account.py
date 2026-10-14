from tkinter import ttk
from management import Dialog
from client import Client
from registration import validate

class EmailAccountDialog(Dialog):
    def __init__(self,app,purpose='register'):
        super().__init__(app,'邮箱验证注册' if purpose=='register' else '邮箱找回密码')
        self.client=Client(app.server.get());self.purpose=purpose;self.challenge=None
        self.name=self.entry('name','账号（3–64 位，英文字母、数字、. _ -）',app.username.get()) if purpose=='register' else None
        self.email=self.entry('email','邮箱地址')
        self.password=self.entry('password','密码（12–256 字符，无强制特殊符号）',secret=True)
        self.code=self.entry('code','六位验证码（10 分钟内有效）')
        row=ttk.Frame(self.frame);row.pack(fill='x')
        self.button(row,'发送验证码',self.send)
        self.button(row,'确认注册' if purpose=='register' else '重置密码',self.save)
        self.button(row,'关闭',self.close);self.footer()

    def send(self):
        email=self.email.get().strip()
        def done(result):
            self.challenge=(email,result['challenge_id']);self.message.set(result['message'])
        self.perform(lambda:self.client.request('POST','/auth/email/code',{'email':email,'purpose':self.purpose},timeout=30),done)

    def save(self):
        email,password,code=self.email.get().strip(),self.password.get(),self.code.get()
        if not self.challenge or self.challenge[0]!=email:return self.message.set('请先发送本次验证码')
        name=self.name.get() if self.name else 'reset-user'
        try:validate(name,password)
        except ValueError as exc:return self.message.set(str(exc))
        payload={'email':email,'challenge_id':self.challenge[1],'code':code}
        if self.purpose=='register':payload.update(username=name,password=password)
        else:payload['new_password']=password
        def done(result):
            if self.purpose=='register':
                self.client.token=result['access_token'];self.app.client=self.client
                self.app.username.delete(0,'end');self.app.username.insert(0,name)
            self.app.password.delete(0,'end');self.challenge=None;self.close()
            if self.purpose=='register':self.app.refresh_people()
            else:self.app.logout();self.app.status.set('密码已重置，请重新登录')
        self.perform(lambda:self.client.request('POST','/auth/email/register' if self.purpose=='register' else '/auth/email/reset-password',payload,timeout=30),done)
