from pathlib import Path
import os,sys,tempfile
from cryptography.fernet import Fernet
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='junshi-contract-') as folder:
    try:
        os.environ.update(DATABASE_PATH=str(Path(folder)/'test.sqlite3'),APP_ENV='development',LOG_DIR=str(Path(folder)/'logs'),LLM_CONFIG_ENCRYPTION_KEY=Fernet.generate_key().decode())
        sys.path[:0]=[str(root/'backend'),str(root/'desktop')]
        from app.core.database import get_connection
        from app.core.migrations import run_migrations
        from app.core.context import get_current_user_id
        from app.main import app
        from fastapi.testclient import TestClient
        from management import create_person_with_conversation,model_payload
        run_migrations()
        with get_connection() as db:db.execute("INSERT INTO users(id) VALUES ('test218')")
        app.dependency_overrides[get_current_user_id]=lambda:'test218'
        with TestClient(app) as web:
            class Adapter:
                def request(self,method,path,payload=None):
                    r=web.request(method,'/api/v1'+path,json=payload)
                    assert r.status_code in (200,201,204),(path,r.status_code,r.text)
                    return r.json() if r.content else None
            client=Adapter()
            person,conversation=create_person_with_conversation(client,{},'Synthetic','','First named conversation')
            account=client.request('POST',f'/persons/{person["id"]}/platform-accounts',{'platform':'wechat','account_handle':'synthetic','display_name':'Synthetic'})
            client.request('PUT',f'/conversations/{conversation["id"]}/platform-source',{'account_id':account['id']})
            values={'name':'Synthetic model','provider':'qwen','base_url':'https://example.com/v1','model':'synthetic-model','api_key':'synthetic-key','timeout_seconds':'60'}
            model=client.request('POST','/settings/llm/profiles',model_payload(values))
            assert 'api_key' not in model and model['api_key_configured']
            model=client.request('PUT','/settings/llm/profiles/'+model['id'],model_payload({**values,'api_key':''},editing=True))
            assert model['api_key_configured']
            client.request('POST','/settings/llm/profiles/'+model['id']+'/activate')
            assert client.request('GET','/settings/llm')['model']=='synthetic-model'
            vision=client.request('PUT','/settings/llm/vision',{'profile_id':model['id']})
            assert vision['profile_id']==model['id']
            print('Actual TEST-216 API contract: person + named conversation + platform + model create/update/activate/vision PASS')
    finally:
        import logging
        logging.shutdown()
