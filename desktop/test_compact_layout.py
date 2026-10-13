"""Verify primary controls remain visible on short desktop work areas."""
import tkinter as tk
from assistant import Assistant

root = tk.Tk()
app = Assistant(root, hotkey=False)
for width, height in ((1040, 800), (1000, 680), (880, 620)):
    root.geometry(f'{width}x{height}')
    root.update()
    for widget, _ in app.controls:
        assert widget.winfo_ismapped(), str(widget)
        x = widget.winfo_rootx()-root.winfo_rootx()
        y = widget.winfo_rooty()-root.winfo_rooty()
        assert 0 <= x and x+widget.winfo_width() <= root.winfo_width(), (width,height,str(widget),'width')
        assert 0 <= y and y+widget.winfo_height() <= root.winfo_height(), (width,height,str(widget),'height')
        if widget.winfo_class() == 'TButton':
            assert widget.winfo_width() >= widget.winfo_reqwidth(), (width,height,widget.cget('text'),'clipped button')
    assert app.incoming.winfo_height() >= 45, (height, app.incoming.winfo_height())
    assert app.reply.winfo_height() >= 45, (height, app.reply.winfo_height())
app.closed = True
root.destroy()
print('Compact layout at 1040x800, 1000x680 and 880x620: PASS')
