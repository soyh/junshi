"""Per-user foreground priority; current production uses one worker."""
from collections import Counter
from threading import Lock
_lock=Lock()
_active=Counter()

def enter(user_id):
    with _lock:_active[user_id]+=1

def leave(user_id):
    with _lock:
        _active[user_id]-=1
        if _active[user_id]<=0:_active.pop(user_id,None)

def busy(user_id):
    with _lock:return bool(_active[user_id])
