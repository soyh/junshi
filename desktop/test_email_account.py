"""Native registration dialog uses code+email and retains the authenticated client."""
import time
import tkinter as tk
from unittest.mock import Mock,patch
from assistant import Assistant
from email_account import EmailAccountDialog

root=tk.Tk();app=Assistant(root,hotkey=False);root.update()
app.server.delete(0,'end');app.server.insert(0,'https://example.com')
app.username.insert(0,'email_user')
client=Mock(base='https://example.com',token=None)
client.request.side_effect=[{'challenge_id':'a'*36,'message':'已发送测试验证码'},{'access_token':'test-token'},[]]
def wait(dialog):
    deadline=time.monotonic()+5
    while (dialog.busy or app.busy) and time.monotonic()<deadline:
        root.update();time.sleep(.02)
    root.update();assert not dialog.busy and not app.busy
with patch('email_account.Client',return_value=client):
    dialog=EmailAccountDialog(app)
    dialog.email.insert(0,'a@example.com');dialog.password.insert(0,'password-12345')
    dialog.send();wait(dialog)
    dialog.code.insert(0,'123456');dialog.save();wait(dialog)
    assert app.client is client and client.token=='test-token'
    body=client.request.call_args_list[1].args[2]
    assert body['challenge_id']=='a'*36 and body['code']=='123456'
    assert app.active_dialog is None
app.closed=True;root.destroy()
print('Native PC email registration: PASS')
