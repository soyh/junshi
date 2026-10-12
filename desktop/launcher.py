"""Windowed entry point: no local server, database or model runtime."""
import argparse
import ctypes
import json
import sys
from pathlib import Path


def main():
    import tkinter as tk
    from tkinter import messagebox
    from PIL import Image, ImageTk
    from assistant import Assistant
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', metavar='REPORT')
    args = parser.parse_args()
    mutex = None
    if sys.platform == 'win32' and not args.self_test:
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel.CreateMutexW.restype = ctypes.c_void_p
        mutex = kernel.CreateMutexW(None, False, 'Local\\JunshiPCDesktop217')
        if not mutex:
            raise RuntimeError('Cannot initialize desktop instance')
        if ctypes.get_last_error() == 183:
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel.CloseHandle(mutex)
            root = tk.Tk(); root.withdraw()
            messagebox.showinfo('客户端已运行', '请按 Ctrl+Alt+J 唤起已有小窗，或从任务栏打开。', parent=root)
            root.destroy()
            return
    root = tk.Tk()
    root.title('AI 恋爱军师 · PC 客户端')
    app = Assistant(root, hotkey=not bool(args.self_test))
    root.title('AI 恋爱军师 · PC 客户端 217.1')
    root.report_callback_exception = lambda *_: messagebox.showerror('操作未完成', '界面操作未完成，请重试。已提交的服务器记录不会删除。', parent=root)
    if args.self_test:
        root.update()
        preview = ImageTk.PhotoImage(Image.new('RGB', (4, 4), 'white'), master=root)
        app.preview.configure(image=preview)
        app.incoming.insert('1.0', 'Synthetic incoming')
        app.submit(lambda: 'Synthetic reply', lambda value: app.reply.insert('1.0', value))
        import time
        deadline = time.monotonic() + 5
        while app.busy and time.monotonic() < deadline:
            root.update(); time.sleep(.02)
        assert app.reply.get('1.0', 'end-1c') == 'Synthetic reply'
        app.logout()
        assert app.client is None and not app.media
        Path(args.self_test).write_text(json.dumps({'status':'PASS','frozen':bool(getattr(sys,'frozen',False)), 'window':True,'image':True,'worker':True}), encoding='utf-8')
        app.closed = True
        root.destroy()
    else:
        root.mainloop()
    if mutex:
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle(mutex)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if '--self-test' in sys.argv:
            import traceback
            Path(sys.argv[sys.argv.index('--self-test')+1]).write_text(json.dumps({'status':'FAIL','traceback':traceback.format_exc()}),encoding='utf-8')
            raise SystemExit(1)
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw()
        messagebox.showerror('客户端启动失败', '请完整解压客户端压缩包后重试，不要单独移动 exe。服务器及网页不受影响。', parent=root)
        root.destroy()
        raise SystemExit(1)
