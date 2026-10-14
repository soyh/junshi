"""Exercise config preservation and logical-data rollback guard with synthetic files."""
import contextlib
import io
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from dotenv import dotenv_values

script=Path(__file__).with_name('deploy.sh').read_text(encoding='utf-8')
blocks=re.findall(r"<<'PY'\n(.*?)\nPY",script,re.S)
with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
    root=Path(directory);app=root/'app';run=root/'run';(app/'backend').mkdir(parents=True);run.mkdir()
    original="MODEL='fake-key-not-real'\nDATABASE_PATH='/unchanged/path'\n"
    for path in (app/'.env',app/'backend/.env'):path.write_text(original,encoding='utf-8')
    smtp="SMTP_HOST='smtp.example.invalid'\nSMTP_PORT='465'\nSMTP_USERNAME='fake'\nSMTP_PASSWORD='fake-password'\nSMTP_SENDER='fake@example.invalid'\nSMTP_IMPLICIT_TLS='true'\nEMAIL_VERIFICATION_SECRET='"+'s'*32+"'\n"
    (run/'smtp.env').write_text(smtp,encoding='utf-8')
    os.environ['TEST228_APP']=str(app);os.environ['TEST228_RUN']=str(run)
    config_block=next(b for b in blocks if 'dotenv_values,set_key' in b)
    exec(compile(config_block,'config-check','exec'),{})
    for path in (app/'.env',app/'backend/.env'):
        values=dotenv_values(path)
        assert values['MODEL']=='fake-key-not-real' and values['DATABASE_PATH']=='/unchanged/path'
        assert values['EMAIL_REGISTRATION_REQUIRED']=='true'
    db=root/'sample.sqlite3'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE example(id TEXT PRIMARY KEY,content TEXT)')
        conn.execute("INSERT INTO example VALUES('one','original')")
    conn.close()
    def fingerprint():
        output=io.StringIO();old=sys.argv;sys.argv=['fingerprint',str(db)]
        try:
            namespace={}
            with contextlib.redirect_stdout(output):exec(compile(blocks[0],'fingerprint-check','exec'),namespace)
            namespace['db'].close()
        finally:sys.argv=old
        return output.getvalue()
    baseline=fingerprint();assert fingerprint()==baseline
    with sqlite3.connect(db) as conn:conn.execute("INSERT INTO example VALUES('two','new user write')")
    conn.close()
    assert fingerprint()!=baseline
print('SMTP config preservation and new-data rollback guard: PASS')
