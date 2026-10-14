"""Password-encrypted, account-scoped business data transfer, never credentials."""
import base64
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config.settings import get_settings
from app.core.database import get_connection

TABLES = ('persons', 'relationships', 'conversations', 'messages', 'interactions',
          'action_decisions', 'action_executions', 'action_outcomes', 'memory_updates',
          'action_plan_snapshots', 'model_references', 'conversation_model_reference_overrides',
          'person_memories', 'person_update_events', 'person_platform_accounts',
          'conversation_platform_sources', 'media_attachments')
MAX_BYTES = 64 * 1024 * 1024
MAX_ENCRYPTED = 96 * 1024 * 1024
MAGIC = b'JUNSHI-ACCOUNT-1\n'


def cipher(password, salt):
    if not 12 <= len(password) <= 256:
        raise ValueError('迁移密码须为 12–256 个字符')
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000).derive(password.encode('utf8'))
    return Fernet(base64.urlsafe_b64encode(key))


def seal(payload, password):
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    if len(raw) > MAX_BYTES:
        raise ValueError('数据包超过 64 MiB，未截断或导出部分数据；请使用管理员完整备份迁移')
    salt = os.urandom(16)
    return MAGIC + salt + cipher(password, salt).encrypt(raw)


def unseal(raw, password):
    if len(raw) > MAX_ENCRYPTED or not raw.startswith(MAGIC):
        raise ValueError('不是受支持的数据包，或文件过大')
    salt = raw[len(MAGIC):len(MAGIC)+16]
    try:
        data = cipher(password, salt).decrypt(raw[len(MAGIC)+16:])
        if len(data) > MAX_BYTES:
            raise ValueError('数据包过大')
        payload = json.loads(data)
    except (InvalidToken, UnicodeError, json.JSONDecodeError):
        raise ValueError('密码错误或数据包损坏，未导入') from None
    if not isinstance(payload, dict) or payload.get('format') != 'junshi-account-v1' or payload.get('migrations') != 21:
        raise ValueError('数据包版本不兼容')
    return payload


def export_account(user_id, password):
    root = Path(get_settings().media_storage_directory).resolve()
    with get_connection() as conn:
        # Prevent concurrent deletion of media during this bounded snapshot.
        conn.execute('BEGIN IMMEDIATE')
        tables = {t: [dict(r) for r in conn.execute(f'SELECT * FROM {t} WHERE user_id=?', (user_id,))] for t in TABLES}
        blobs = {}
        total = len(json.dumps(tables, ensure_ascii=False).encode('utf8'))
        for row in tables['media_attachments']:
            path = Path(row['storage_path'])
            if path.is_symlink() or not path.resolve().is_relative_to(root / user_id):
                raise ValueError('媒体路径异常，完整导出已停止')
            if not path.is_file() or path.stat().st_size > MAX_BYTES - total:
                raise ValueError('媒体缺失或数据包过大，未导出部分数据')
            with path.open('rb') as stream:
                content = stream.read(MAX_BYTES - total + 1)
            if hashlib.sha256(content).hexdigest() != row['sha256'] or len(content) != row['size_bytes']:
                raise ValueError('媒体完整性检查失败，未导出')
            encoded = base64.b64encode(content).decode('ascii')
            total += len(encoded)
            if total > MAX_BYTES:
                raise ValueError('数据包超过 64 MiB，请使用管理员备份迁移')
            blobs[row['id']] = encoded
            row['storage_path'] = ''
            row['analysis_claim_token'] = None
            row['analysis_claimed_at'] = None
    return seal({'format': 'junshi-account-v1', 'migrations': 21, 'tables': tables, 'media': blobs}, password)


def validate_payload(conn, payload):
    tables = payload.get('tables')
    blobs = payload.get('media')
    if not isinstance(tables, dict) or set(tables) != set(TABLES) or not isinstance(blobs, dict):
        raise ValueError('数据包内容不完整')
    for table, rows in tables.items():
        columns = {r['name'] for r in conn.execute(f'PRAGMA table_info({table})')}
        # Older account packages predate the optional explicit-guide flag.
        if table == 'model_references' and 'is_guide' in columns and isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and set(row) == columns - {'is_guide'}:
                    row['is_guide'] = 0
        if not isinstance(rows, list) or any(not isinstance(r, dict) or set(r) != columns for r in rows):
            raise ValueError('数据结构不兼容，未导入')
        if any(any(not isinstance(v, (str, int, float, type(None))) for v in row.values()) for row in rows):
            raise ValueError('字段格式错误')
    # Every reference must resolve INSIDE the archive, never to another user's row.
    for table, rows in tables.items():
        for fk in conn.execute(f'PRAGMA foreign_key_list({table})'):
            if fk['table'] == 'users':
                continue
            if fk['table'] not in tables:
                raise ValueError('不支持的数据依赖')
            valid = {r[fk['to']] for r in tables[fk['table']]}
            if any(row[fk['from']] is not None and row[fk['from']] not in valid for row in rows):
                raise ValueError('数据包存在外部或缺失的关联')
    people = {r['id'] for r in tables['persons']}
    for table, rows in tables.items():
        if any('person_id' in r and r['person_id'] not in people for r in rows):
            raise ValueError('人物关联不完整')
    accounts = {r['id']: r for r in tables['person_platform_accounts']}
    conversations = {r['id']: r for r in tables['conversations']}
    for source in tables['conversation_platform_sources']:
        if accounts[source['account_id']]['person_id'] != conversations[source['conversation_id']]['person_id']:
            raise ValueError('平台账号与会话人物不一致')
    if set(blobs) != {r['id'] for r in tables['media_attachments']}:
        raise ValueError('媒体数据不完整')
    return tables, blobs


def import_account(user_id, raw, password):
    payload = unseal(raw, password)
    created = []
    try:
        with get_connection() as conn:
            conn.execute('BEGIN IMMEDIATE')
            if any(conn.execute(f'SELECT 1 FROM {t} WHERE user_id=? LIMIT 1', (user_id,)).fetchone() for t in TABLES):
                raise ValueError('目标账号已有业务数据；请使用空白账号导入，现有数据未覆盖')
            tables, blobs = validate_payload(conn, payload)
            root = Path(get_settings().media_storage_directory).resolve()
            directory = root / user_id
            if directory.is_symlink() or not directory.resolve().is_relative_to(root) or directory.resolve() == root:
                raise ValueError('目标媒体目录异常')
            directory.mkdir(parents=True, exist_ok=True)
            conn.execute('PRAGMA defer_foreign_keys=ON')
            for table in TABLES:
                for original in tables[table]:
                    row = dict(original)
                    row['user_id'] = user_id
                    if table == 'media_attachments':
                        try:
                            content = base64.b64decode(blobs[row['id']], validate=True)
                        except (ValueError, TypeError):
                            raise ValueError('媒体内容损坏') from None
                        if len(content) != row['size_bytes'] or hashlib.sha256(content).hexdigest() != row['sha256']:
                            raise ValueError('媒体校验失败')
                        path = directory / (str(uuid4()) + '.bin')
                        with path.open('xb') as stream:
                            created.append(path)
                            stream.write(content)
                        row['storage_path'] = str(path)
                        row['analysis_claim_token'] = None
                        row['analysis_claimed_at'] = None
                    columns = list(row)
                    conn.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", list(row.values()))
            if conn.execute('PRAGMA foreign_key_check').fetchone():
                raise ValueError('关联校验失败，未导入')
        return {'imported': True, 'counts': {t: len(rows) for t, rows in tables.items()}}
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
