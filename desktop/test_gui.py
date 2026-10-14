"""Native window smoke test with synthetic data; run on Windows CI only."""
import io
import time
import tkinter as tk
from unittest.mock import Mock, patch

from PIL import Image
from assistant import Assistant

root = tk.Tk()
app = Assistant(root, hotkey=False)
root.update()
assert root.winfo_width() >= 540
app.client = Mock()
app.people = [{'id': 'p', 'name': 'Synthetic person'}]
app.person['values'] = ['Synthetic person']; app.person.current(0)
app.conversations = [{'id': 'c', 'title': 'Synthetic conversation'}]
app.conversation['values'] = ['Synthetic conversation']; app.conversation.current(0)
app.replace_input('Synthetic incoming message', [])
with patch('assistant.generate', return_value='Synthetic reply'), patch.object(app, 'refresh_memory'):
    app.run_generation()
    deadline = time.monotonic() + 5
    while app.busy and time.monotonic() < deadline:
        root.update(); time.sleep(.02)
    assert not app.busy
    assert app.reply.get('1.0', 'end-1c') == 'Synthetic reply'
    assert not app.job['confirmed']
stream = io.BytesIO(); Image.new('RGB', (4, 4), 'white').save(stream, format='PNG')
with patch('assistant.messagebox.askyesno', return_value=True):
    app.replace_input('', [{'name': 'synthetic.png', 'mime': 'image/png', 'content': stream.getvalue()}])
root.update()
assert app.preview.image is not None
assert app.client.request.call_count == 0  # preview never uploads
app.logout()
assert app.client is None and not app.media
app.closed = True
root.destroy()
print('PC native window, worker result, image preview and logout: PASS')
