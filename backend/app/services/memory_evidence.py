"""Request-local citation labels, mapped back only to this exact message batch."""
from copy import deepcopy
import hashlib
from app.services.memory_errors import MemoryProvenanceError


def prepare(context, schema):
    wire=deepcopy(context)
    ids=[m['id'] for m in context['messages']]
    prefix=hashlib.sha256('\0'.join(ids).encode()).hexdigest()[:10]
    mapping={f'B{prefix}-{i+1:02}':id for i,id in enumerate(ids)}
    for message,label in zip(wire['messages'],mapping):
        # Avoid presenting user/conversation IDs as competing citation choices.
        message['id']=label
        for key in ('user_id','conversation_id'):
            message.pop(key,None)
    for key in ('person','relationship'):
        if isinstance(wire.get(key),dict):
            wire[key]={k:v for k,v in wire[key].items() if k!='id' and not k.endswith('_id')}
    wire['allowed_evidence_source_ids']=list(mapping)
    schema=deepcopy(schema)
    schema['properties']['evidence_source_ids']['items']={'type':'string','enum':list(mapping)}
    return wire,schema,mapping


def resolve(result,mapping):
    if not isinstance(result,dict) or not isinstance(result.get('evidence_source_ids'),list):
        return result  # Schema validation reports the shape error.
    canonical=set(mapping.values())
    resolved=[]
    for value in result['evidence_source_ids']:
        if not isinstance(value,str):
            return result
        if value in mapping:
            resolved.append(mapping[value])
        elif value in canonical:
            resolved.append(value)  # Exact current-batch IDs are also valid.
        else:
            raise MemoryProvenanceError()
    return {**result,'evidence_source_ids':resolved}
