"""Short-lived, tenant-scoped counters only; no prompts, replies or secrets."""
from threading import Lock
from time import monotonic

_lock = Lock()
_items = {}


def publish(user_id, conversation_id, request_id, stage, attempt=0):
    with _lock:
        cutoff = monotonic() - 900
        for key in list(_items):
            if _items[key][0] < cutoff:
                del _items[key]
        if len(_items) >= 2048:
            del _items[min(_items, key=lambda key: _items[key][0])]
        _items[(user_id, conversation_id, request_id)] = (monotonic(), {
            'stage': stage, 'attempt': attempt, 'max_corrections': 3,
        })


def read(user_id, conversation_id, request_id):
    with _lock:
        item = _items.get((user_id, conversation_id, request_id))
        return dict(item[1]) if item and item[0] > monotonic() - 900 else {'stage': 'pending'}
