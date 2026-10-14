import uuid
from unittest.mock import patch
from app.core.database import get_connection
from app.config.settings import get_settings
from app.services.account_deletion import prepare_deletion,cleanup_result,finish_cleanup

def test_deletion_cascades_keeps_other_users_and_cleanup_retries(client,tmp_path,monkeypatch):
    monkeypatch.setattr(get_settings(),'media_storage_directory',str(tmp_path))
    user=str(uuid.uuid4());other=str(uuid.uuid4())
    with get_connection() as c:
        c.execute('INSERT INTO users(id) VALUES(?)',(user,));c.execute('INSERT INTO users(id) VALUES(?)',(other,))
        c.execute('INSERT INTO user_credentials(user_id,username,password_hash) VALUES(?,?,?)',(user,'delete_user','hash'))
        job=prepare_deletion(c,user,user,'主动注销')
    with get_connection() as c:
        assert c.execute('SELECT 1 FROM users WHERE id=?',(user,)).fetchone() is None
        assert c.execute('SELECT 1 FROM users WHERE id=?',(other,)).fetchone()
        assert c.execute('SELECT 1 FROM user_credentials WHERE user_id=?',(user,)).fetchone() is None
        assert c.execute('SELECT reason FROM account_management_audit WHERE target_id=?',(user,)).fetchone()[0]=='主动注销'
        private=tmp_path/user/'file.png';private.parent.mkdir();private.write_bytes(b'private')
        import json
        c.execute('UPDATE account_file_cleanup SET paths_json=? WHERE id=?',(json.dumps([str(private)]),job))
    with patch('pathlib.Path.unlink',side_effect=OSError('locked')):
        assert cleanup_result(job)['cleanup_pending']
    assert private.exists()
    assert finish_cleanup(job)
    assert not private.exists()
