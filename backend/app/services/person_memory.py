"""Derived, tenant-scoped memory with optimistic publication and an atomic audit."""
import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone

from app.core.database import get_connection
from app.schemas.person_memory import PersonMemoryProposal

_guard = threading.Lock()
_running = set()


def now():
    return datetime.now(timezone.utc).isoformat()


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def record_event(conn, user_id, person_id, source, outcome, reason, before, after, evidence=()):
    conn.execute("INSERT INTO person_update_events VALUES (?,?,?,?,?,?,?,?,?,?)", (
        str(uuid.uuid4()), user_id, person_id, source, outcome, reason,
        dump(before), dump(after), dump(list(evidence)), now(),
    ))


def snapshot(conn, user_id, person_id):
    person = conn.execute("SELECT * FROM persons WHERE id=? AND user_id=?", (person_id, user_id)).fetchone()
    if person is None:
        raise ValueError("Person not found")
    messages = [dict(row) for row in conn.execute(
        "SELECT m.* FROM messages m JOIN conversations c ON c.id=m.conversation_id AND c.user_id=m.user_id "
        "WHERE c.person_id=? AND m.user_id=? ORDER BY julianday(m.sent_at),m.created_at,m.rowid",
        (person_id, user_id),
    )]
    hashes = {m['id']: hashlib.sha256(dump(m).encode()).hexdigest() for m in messages}
    relationship = conn.execute(
        "SELECT * FROM relationships WHERE person_id=? AND user_id=? ORDER BY created_at,id LIMIT 1",
        (person_id, user_id),
    ).fetchone()
    row = conn.execute("SELECT * FROM person_memories WHERE person_id=? AND user_id=?", (person_id, user_id)).fetchone()
    summary = json.loads(row['summary_json']) if row else {}
    coverage = json.loads(row['coverage_json']) if row else {}
    stale = any(hashes.get(key) != value for key, value in coverage.items())
    return {"person": dict(person), "relationship": dict(relationship) if relationship else None,
            "messages": messages, "hashes": hashes, "summary": summary, "coverage": coverage,
            "revision": row['revision'] if row else 0, "stale": stale,
            "updated_at": row['updated_at'] if row else None}


def read_memory(conn, user_id, person_id, *, limit=20, offset=0):
    s = snapshot(conn, user_id, person_id)
    latest = conn.execute(
        'SELECT outcome FROM person_update_events WHERE user_id=? AND person_id=? ORDER BY created_at DESC,id DESC LIMIT 1',
        (user_id, person_id),
    ).fetchone()
    events = []
    for row in conn.execute(
        "SELECT * FROM person_update_events WHERE user_id=? AND person_id=? ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?",
        (user_id, person_id, limit, offset),
    ):
        event = dict(row)
        for key in ('before', 'after', 'evidence'):
            event[key] = json.loads(event.pop(key + '_json'))
        events.append(event)
    return {"summary": {} if s['stale'] else s['summary'], "stale": s['stale'],
            "covered_count": 0 if s['stale'] else len(s['coverage']), "total_count": len(s['messages']),
            "updated_at": s['updated_at'], "revision": s['revision'], "events": events,
            "has_more": conn.execute("SELECT COUNT(*) FROM person_update_events WHERE user_id=? AND person_id=?", (user_id,person_id)).fetchone()[0] > offset + len(events),
            "running": (user_id, person_id) in _running,
            "latest_outcome": latest['outcome'] if latest else None}


def context_memory(conn, user_id, person_id, messages):
    s = snapshot(conn, user_id, person_id)
    if s['stale'] or not s['summary']:
        return None, messages
    recent = {m['id'] for m in messages[-16:]}
    for senders in ({'user', 'person'}, {'person'}):
        latest = next((m for m in reversed(messages) if m.get('sender_type') in senders), None)
        if latest:
            recent.add(latest['id'])
    retained = [m for m in messages if m['id'] in recent or m['id'] not in s['coverage']]
    return {"derived": True, "summary": s['summary'], "updated_at": s['updated_at'],
            "covered_count": len(s['coverage']), "original_message_count": len(messages),
            "rule": "This is a derived historical summary, not canonical evidence. New messages override outdated interpretations; preserve uncertainty and explicit boundaries."}, retained


def refresh_memory(user_id, person_id, provider, *, max_batches=4):
    key = (user_id, person_id)
    with _guard:
        if key in _running:
            return {"status": "running"}
        _running.add(key)
    try:
        for _ in range(max_batches):
            with get_connection() as conn:
                s = snapshot(conn, user_id, person_id)
            coverage = {} if s['stale'] else s['coverage'].copy()
            remaining = [m for m in s['messages'] if m['id'] not in coverage]
            if not remaining:
                if s['stale']:
                    with get_connection() as conn:
                        conn.execute('BEGIN IMMEDIATE')
                        current = snapshot(conn,user_id,person_id)
                        if current['revision']==s['revision'] and current['hashes']==s['hashes']:
                            conn.execute("UPDATE person_memories SET summary_json='{}',coverage_json='{}',revision=revision+1,updated_at=? WHERE person_id=? AND user_id=?",(now(),person_id,user_id))
                            record_event(conn,user_id,person_id,'ai','invalidated','原聊天已全部删除，清除失效摘要。',{'summary':s['summary']},{'summary':{}})
                return {"status": "current"}
            batch = []
            from app.config.settings import get_settings
            byte_limit = max(1000,min(48000,get_settings().llm_input_budget_tokens-len(dump(s['summary']).encode())-8000))
            for message in remaining[:32]:
                if batch and len(dump(batch + [message]).encode()) > byte_limit:
                    break
                batch.append(message)
            payload = {"person": s['person'], "relationship": s['relationship'],
                       "previous_summary": {} if s['stale'] else s['summary'], "messages": batch,
                       "remaining_message_count": len(remaining)-len(batch)}
            proposal = PersonMemoryProposal.model_validate(provider.summarize_person(payload))
            ids = {m['id'] for m in batch}
            if not set(proposal.evidence_source_ids).issubset(ids):
                raise ValueError("invalid memory provenance")
            summary = proposal.model_dump(include={'description', 'facts', 'inferences', 'constraints', 'unknowns'})
            coverage.update({m['id']: s['hashes'][m['id']] for m in batch})
            with get_connection() as conn:
                # Acquire the write reservation only after the network call.
                conn.execute('BEGIN IMMEDIATE')
                current = snapshot(conn, user_id, person_id)
                if (current['revision'] != s['revision'] or current['hashes'] != s['hashes']
                        or current['relationship'] != s['relationship'] or current['person'] != s['person']):
                    record_event(conn,user_id,person_id,'ai','discarded','分析期间原始资料发生变化，本次结果未应用。',{}, {})
                    return {"status": "superseded"}
                before = {"summary": s['summary'], "relationship": s['relationship']}
                rel = s['relationship']
                # Never publish an old-history batch's relationship as today's
                # state while newer unprocessed messages are still pending.
                complete = len(coverage) == len(s['messages'])
                if complete and (proposal.relationship_status is not None or proposal.relationship_stage is not None):
                    if rel is None:
                        from app.repositories.relationship import RelationshipRepository
                        rel = dict(RelationshipRepository().create(conn,user_id,person_id,'unknown','unknown',None,None,None))
                    conn.execute("UPDATE relationships SET status=?,stage=?,updated_at=? WHERE id=? AND user_id=?", (
                        proposal.relationship_status or rel['status'], proposal.relationship_stage or rel['stage'], now(), rel['id'],user_id))
                    rel = dict(conn.execute('SELECT * FROM relationships WHERE id=? AND user_id=?',(rel['id'],user_id)).fetchone())
                conn.execute("INSERT INTO person_memories VALUES (?,?,?,?,?,?) ON CONFLICT(person_id) DO UPDATE SET revision=excluded.revision,summary_json=excluded.summary_json,coverage_json=excluded.coverage_json,updated_at=excluded.updated_at", (
                    person_id,user_id,s['revision']+1,dump(summary),dump(coverage),now()))
                record_event(conn,user_id,person_id,'ai','updated',
                             ('原始记录已变更，本批重新建立摘要。' if s['stale'] else '')+proposal.reason,before,
                             {"summary":summary,"relationship":rel,"covered_count":len(coverage),
                              "total_count":len(s['messages']),"relationship_update_deferred":not complete,
                              "from":batch[0]['sent_at'],"to":batch[-1]['sent_at']},proposal.evidence_source_ids)
        return {"status": "partial"}
    except Exception:
        # Never persist provider bodies, credentials or arbitrary exception text.
        with get_connection() as conn:
            if conn.execute('SELECT 1 FROM persons WHERE id=? AND user_id=?',(person_id,user_id)).fetchone():
                record_event(conn,user_id,person_id,'ai','failed','档案分析未完成：模型请求或结果校验失败；本批变更未应用。',{}, {})
        return {"status": "failed"}
    finally:
        with _guard:
            _running.discard(key)


def background_refresh(user_id, person_id):
    from app.api.routes.analysis_strategic_reply import _build_provider
    try:
        with get_connection() as conn:
            provider = _build_provider(conn, user_id)
    except Exception:
        with get_connection() as conn:
            if conn.execute('SELECT 1 FROM persons WHERE id=? AND user_id=?',(person_id,user_id)).fetchone():
                record_event(conn,user_id,person_id,'ai','failed','模型配置不可用，本次未修改档案。',{}, {})
        return {'status':'failed'}
    return refresh_memory(user_id, person_id, provider)
