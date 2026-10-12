"""Store only the server address. No credentials, drafts or business data."""
import json
import os
import sys
from pathlib import Path

from client import Client


def settings_path():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'JunshiPC' / 'settings.json'


def load_server():
    candidates = [settings_path()]
    if getattr(sys, 'frozen', False):
        candidates.append(Path(sys.executable).parent / 'client-config.json')
    for path in candidates:
        try:
            return Client(json.loads(path.read_text(encoding='utf-8'))['server']).base
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return ''


def save_server(server):
    server = Client(server).base
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'server': server}), encoding='utf-8')
    temporary.replace(path)
