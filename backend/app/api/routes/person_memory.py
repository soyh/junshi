from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.person_memory import PersonMemoryCorrection
from app.services.person_memory import read_memory, background_refresh, apply_correction

router = APIRouter(prefix='/persons/{person_id}/memory', tags=['person-memory'])


@router.get('')
def get_memory(person_id: str, limit: int = Query(20,ge=1,le=100), offset: int = Query(0,ge=0),
               user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        try:
            return read_memory(conn,user_id,person_id,limit=limit,offset=offset)
        except ValueError:
            raise HTTPException(404,'Person not found') from None


@router.post('/refresh', status_code=202)
def refresh(person_id: str, background: BackgroundTasks, user_id: str = Depends(get_current_user_id)):
    with get_connection() as conn:
        try:
            state = read_memory(conn,user_id,person_id,limit=1)
        except ValueError:
            raise HTTPException(404,'Person not found') from None
    if not state['running'] and (state['stale'] or state['covered_count'] < state['total_count'] or (state['summary'] and not state['consolidated'])):
        background.add_task(background_refresh,user_id,person_id)
        return {'status':'queued'}
    return {'status':'running' if state['running'] else 'current'}


@router.get('/profile')
def get_profile(person_id: str, offset: int = Query(0,ge=0), limit: int = Query(20,ge=1,le=100),
                user_id: str = Depends(get_current_user_id)):
    from app.services.person_memory import snapshot
    from app.services.compact_profile import entries
    with get_connection() as conn:
        try:s=snapshot(conn,user_id,person_id)
        except ValueError:raise HTTPException(404,'Person not found') from None
        rows=entries(s['summary'])
        return {'items':rows[offset:offset+limit],'total':len(rows),'stale':s['stale'],
                'has_more':offset+limit<len(rows)}


@router.post('/corrections')
def correct(person_id: str, body: PersonMemoryCorrection,
            user_id: str = Depends(get_current_user_id)):
    """Let the person fix a wrong archive entry; it outranks model inference."""
    with get_connection() as conn:
        try:
            return apply_correction(conn, user_id, person_id, action=body.action,
                                    entry_id=body.entry_id, kind=body.kind, text=body.text)
        except ValueError as error:
            if 'Person not found' in str(error):
                raise HTTPException(404, 'Person not found') from None
            raise HTTPException(422, str(error)) from None
