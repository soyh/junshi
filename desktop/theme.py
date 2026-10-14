"""Blue and warm-white desktop palette; native keyboard and focus behavior."""
import tkinter as tk
from tkinter import ttk

PAGE = '#eaf3fc'
INK = '#284861'
BLUE = '#287bc1'


def install_theme(root):
    root.configure(background=PAGE)
    root.option_add('*TCombobox*Listbox.font', ('Microsoft YaHei UI', 10))
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Microsoft YaHei UI', 10), foreground=INK,
                    background='#ffffff', bordercolor='#c4d9ed',
                    lightcolor='#ffffff', darkcolor='#b6cee3')
    style.configure('Page.TFrame', background=PAGE)
    style.configure('TLabel', background='#ffffff', foreground=INK)
    style.configure('Title.TLabel', background=PAGE, foreground='#225c8e', font=('Microsoft YaHei UI', 19, 'bold'))
    style.configure('Subtitle.TLabel', background=PAGE, foreground='#6283a0', font=('Microsoft YaHei UI', 10))
    style.configure('TLabelframe', background='#ffffff', relief='raised', borderwidth=2,
                    bordercolor='#ccdfef', lightcolor='#ffffff', darkcolor='#b1c9df')
    style.configure('TLabelframe.Label', background='#ffffff', foreground='#2d6795', font=('Microsoft YaHei UI', 10, 'bold'))
    style.configure('TEntry', fieldbackground='#f7fbff', padding=(6, 3), bordercolor='#c4d9ed')
    style.map('TEntry', bordercolor=[('focus', '#428fd0')])
    style.configure('TCombobox', fieldbackground='#f7fbff', padding=(6, 3), arrowsize=14)
    style.map('TCombobox', fieldbackground=[('readonly', '#f7fbff'), ('disabled', '#edf2f6')],
              foreground=[('disabled', '#8c9baa')])
    style.configure('TButton', background='#eff7ff', foreground='#326992', padding=(6, 3),
                    relief='raised', borderwidth=2, anchor='center')
    style.map('TButton', background=[('disabled', '#edf2f6'), ('pressed', '#c6e1f7'), ('active', '#deeffd')],
              foreground=[('disabled', '#8c9baa')], relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
    style.configure('Primary.TButton', background=BLUE, foreground='#ffffff', bordercolor='#236dad',
                    lightcolor='#64a6dc', darkcolor='#195b94', font=('Microsoft YaHei UI', 10, 'bold'))
    style.map('Primary.TButton', background=[('disabled', '#d6e3ee'), ('pressed', '#1e609a'), ('active', '#388dd0')],
              foreground=[('disabled', '#8298ab'), ('!disabled', '#ffffff')])
    style.configure('Status.TLabel', background='#fff9ef', foreground='#74634c', padding=(10, 8))
    style.configure('TPanedwindow', background=PAGE)
    style.configure('Vertical.TScrollbar', background='#cbdff0', troughcolor=PAGE, arrowsize=12)


def text_surface(widget):
    widget.configure(background='#f8fbff', foreground=INK, insertbackground=BLUE,
                     selectbackground='#c9e5fc', selectforeground='#193f62',
                     relief='flat', borderwidth=0, highlightthickness=1,
                     highlightbackground='#d6e5f2', highlightcolor='#428fd0',
                     padx=12, pady=10, spacing1=2, spacing3=4, font=('Microsoft YaHei UI', 11))


def raised_card(parent, title, row=None, column=0):
    shadow = tk.Frame(parent, background='#cfdfed', borderwidth=0)
    if row is None:
        shadow.pack(fill='both', expand=True, pady=(0, 8), padx=(0, 3))
    else:
        shadow.grid(row=row, column=column, sticky='nsew', pady=(0, 8), padx=(0, 6))
    card = ttk.LabelFrame(shadow, text=title, padding=8)
    card.pack(fill='both', expand=True, padx=(0, 3), pady=(0, 3))
    return card


def scroll_page(root):
    """Keep all actions reachable on short displays and at enlarged system DPI."""
    shell = ttk.Frame(root, style='Page.TFrame')
    shell.pack(fill='both', expand=True)
    canvas = tk.Canvas(shell, background=PAGE, highlightthickness=0)
    bar = ttk.Scrollbar(shell, orient='vertical', command=canvas.yview)
    canvas.configure(yscrollcommand=bar.set)
    bar.pack(side='right', fill='y'); canvas.pack(side='left', fill='both', expand=True)
    frame = ttk.Frame(canvas, padding=16, style='Page.TFrame')
    window = canvas.create_window(0, 0, anchor='nw', window=frame)
    frame.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>', lambda event: canvas.itemconfigure(window, width=event.width))
    def wheel(event):
        if event.widget.winfo_toplevel() != root or event.widget.winfo_class() in ('Text', 'TCombobox'):
            return
        if frame.winfo_height() > canvas.winfo_height():
            canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
    root.bind('<MouseWheel>', wheel, add='+')
    return frame, canvas
