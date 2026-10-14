import sys
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit('Python 3.11 or newer is required.')
try:
    import tkinter
    import PIL
except ImportError:
    path = str(Path(__file__).resolve().parent / 'requirements.txt').replace("'", "''")
    executable = sys.executable.replace("'", "''")
    print('PC assistant needs tkinter (included with standard Windows Python) and Pillow.')
    print('Install the desktop dependency using PowerShell:')
    print(f"& '{executable}' -m pip install -r '{path}'")
    raise SystemExit(1)

from assistant import Assistant
root = tkinter.Tk()
Assistant(root)
root.mainloop()
