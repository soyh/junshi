"""Atomic DB removal followed by persistent, retryable private-file cleanup."""
import json
from pathlib import Path
import uuid
from app.config.settings import get_settings
from app.core.database import get_connection
from app.services.account_identity import AccountIdentityService, AccountIdentityError


def checked_paths(user, paths):
    try: valid=str(uuid.UUID(user))==user
    except ValueError: valid=False
    if not valid:
        raise AccountIdentityError('用户标识不正确')
    base=Path(get_settings().media_storage_directory).resolve()/user
    if base.is_symlink(): raise AccountIdentityError('用户附件目录异常')
    for value in paths:
        path=Path(value)
        if path.is_symlink() or not path.resolve().is_relative_to(base):
            raise AccountIdentityError('附件路径异常，未执行账号删除')
    return sorted(set(paths))


def prepare_deletion(conn,actor,target,reason,administrator=False):
    service=AccountIdentityService()
    if administrator:
        service.require_admin(conn,actor)
        if actor==target: raise AccountIdentityError('不能删除当前管理员账号')
    elif actor!=target:
        raise AccountIdentityError('不能注销其他用户')
    if not conn.execute('SELECT 1 FROM users WHERE id=?',(target,)).fetchone():
        raise AccountIdentityError('用户不存在')
    private=Path(get_settings().media_storage_directory).resolve()/target
    paths=[r[0] for r in conn.execute('SELECT storage_path FROM media_attachments WHERE user_id=?',(target,))]
    if private.is_symlink(): raise AccountIdentityError('用户附件目录异常')
    if private.exists():
        paths.extend(str(p) for p in private.rglob('*') if p.is_file() or p.is_symlink())
    paths=checked_paths(target,paths)
    job=str(uuid.uuid4())
    service.audit(conn,actor,target,'delete-account',reason)
    conn.execute('INSERT INTO account_file_cleanup(id,user_id,paths_json) VALUES(?,?,?)',(job,target,json.dumps(paths)))
    identity=conn.execute('SELECT email FROM account_identities WHERE user_id=?',(target,)).fetchone()
    if identity is not None and identity['email']:
        conn.execute('DELETE FROM email_challenges WHERE email=?',(identity['email'],))
    conn.execute('DELETE FROM users WHERE id=?',(target,))
    return job


def finish_cleanup(job):
    with get_connection() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row=conn.execute('SELECT * FROM account_file_cleanup WHERE id=?',(job,)).fetchone()
        if row is None: raise AccountIdentityError('清理任务不存在')
        if row['completed']: return True
        paths=checked_paths(row['user_id'],json.loads(row['paths_json']))
        for value in paths:
            if not conn.execute('SELECT 1 FROM media_attachments WHERE storage_path=? LIMIT 1',(value,)).fetchone():
                Path(value).unlink(missing_ok=True)
        conn.execute("UPDATE account_file_cleanup SET completed=1,paths_json='[]' WHERE id=?",(job,))
    return True


def cleanup_result(job):
    try: finish_cleanup(job)
    except (OSError,AccountIdentityError): return {'status':'deleted','cleanup_pending':True,'cleanup_job':job}
    return {'status':'deleted','cleanup_pending':False}
