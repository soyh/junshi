import sqlite3
from pathlib import Path
from unittest.mock import Mock
import pytest
from app.services.email_challenge import EmailChallengeService, EmailChallengeError


@pytest.fixture
def setup():
    conn=sqlite3.connect(':memory:'); conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE users(id TEXT PRIMARY KEY)')
    conn.executescript((Path(__file__).parents[1]/'migrations/023_account_identity.sql').read_text(encoding='utf-8'))
    mailer=Mock(); now=[1000]
    service=EmailChallengeService('s'*32,mailer,lambda:now[0])
    yield conn,service,mailer,now
    conn.close()


def issue(setup):
    conn,s,mail,_=setup
    identifier=s.send(conn,'a@example.com','register','127.0.0.1');conn.commit()
    return identifier,mail.send.call_args.args[1]


def test_one_time_and_no_plain_code(setup):
    conn,s,_,_=setup; identifier,code=issue(setup)
    assert code != conn.execute('SELECT code_hash FROM email_challenges').fetchone()[0]
    assert s.consume(conn,identifier,'a@example.com','register',code);conn.commit()
    assert not s.consume(conn,identifier,'a@example.com','register',code)


def test_wrong_scope_expiry_and_attempt_limit(setup):
    conn,s,_,now=setup; identifier,code=issue(setup)
    assert not s.consume(conn,identifier,'a@example.com','reset',code);conn.commit()
    for _ in range(5):
        assert not s.consume(conn,identifier,'a@example.com','register','invalid');conn.commit()
    assert not s.consume(conn,identifier,'a@example.com','register',code);conn.commit()
    now[0]+=61;identifier,code=issue(setup);now[0]+=600
    assert not s.consume(conn,identifier,'a@example.com','register',code)


def test_rate_limit_and_send_failure_roll_back(setup):
    conn,s,mail,now=setup;issue(setup)
    with pytest.raises(EmailChallengeError): s.send(conn,'a@example.com','register','127.0.0.1')
    conn.rollback();now[0]+=61;mail.send.side_effect=ValueError('failed')
    with pytest.raises(ValueError): s.send(conn,'a@example.com','register','127.0.0.1')
    conn.rollback()
    assert conn.execute('SELECT COUNT(*) FROM email_challenges').fetchone()[0]==1
    assert conn.execute('SELECT consumed FROM email_challenges').fetchone()[0]==0
