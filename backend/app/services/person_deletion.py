"""Account-scoped hard deletion with retryable, post-commit blob cleanup."""
import hashlib
import json
from pathlib import Path

from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.person import PersonService


def delete_person_data(user_id: str, person_id: str) -> bool:
    root = Path(get_settings().media_storage_directory).resolve()
    key = hashlib.sha256(f'{user_id}:{person_id}'.encode()).hexdigest()
    manifest = root / '.deletions' / f'{key}.json'
    with get_connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        exists = PersonService().get(conn, user_id, person_id) is not None
        if not exists and not manifest.exists():
            return False
        paths = json.loads(manifest.read_text()) if manifest.exists() else []
        if exists:
            paths += [r[0] for r in conn.execute(
                'SELECT storage_path FROM media_attachments WHERE user_id=? AND person_id=?',
                (user_id, person_id))]
        paths = sorted(set(paths))
        for value in paths:
            path = Path(value)
            if path.is_symlink() or not path.resolve().is_relative_to(root / user_id):
                raise ValueError('附件存储路径异常，未执行删除。')
        if paths:
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(json.dumps(paths), encoding='utf-8')
        if exists:
            PersonService().delete(conn, user_id, person_id)
    # Only touch bytes after the database transaction has committed. If an OS
    # error occurs, retain the minimal path manifest and allow the owner to retry.
    with get_connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        for value in paths:
            if not conn.execute('SELECT 1 FROM media_attachments WHERE storage_path=? LIMIT 1', (value,)).fetchone():
                Path(value).unlink(missing_ok=True)
        manifest.unlink(missing_ok=True)
    return True
