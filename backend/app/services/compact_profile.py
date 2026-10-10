"""Uniform profile storage and whole-item, byte-bounded context selection."""
import hashlib
import json
import re
from copy import deepcopy

KINDS=('constraints','facts','preferences','events','unknowns','inferences')


def size(value):
    return len(json.dumps(value,ensure_ascii=False).encode('utf-8'))


def entries(summary):
    if '_profile' in summary:
        return deepcopy(summary['_profile'])
    return [{'id':hashlib.sha256((kind+'\0'+text).encode()).hexdigest()[:24],
             'kind':kind,'text':text,'evidence':[],'active':True,'legacy':True}
            for kind in KINDS for text in summary.get(kind,[])]


def merge(previous,proposal,evidence,complete):
    items=entries(previous)
    index={row['id']:row for row in items}
    changes=[]
    for kind in KINDS:
        for text in getattr(proposal,kind,[]):
            text=text.strip()
            key=hashlib.sha256((kind+'\0'+text).encode()).hexdigest()[:24]
            if key in index:
                continue
            row={'id':key,'kind':kind,'text':text,'evidence':list(evidence),'active':True}
            items.append(row);index[key]=row;changes.append({'before':None,'after':deepcopy(row)})
    # Explicit revisions require new canonical evidence and a recorded reason.
    for key in proposal.superseded_entry_ids:
        if key not in index or key not in {row['id'] for row in entries(previous)}:
            raise ValueError('unknown profile revision target')
        row=index[key]
        if not any(c['after']['kind']==row['kind'] for c in changes if c['before'] is None):
            raise ValueError('profile revision requires an explicit replacement')
        if row['active']:
            before=deepcopy(row);row['active']=False
            row['revision_reason']=proposal.reason;row['revision_evidence']=list(evidence)
            changes.append({'before':before,'after':deepcopy(row)})
    summary=proposal.model_dump(include={'description',*KINDS})
    summary['_profile']=items
    summary['_profile_version']=1
    summary['_consolidated']=complete
    return summary,changes


def terms(text):
    text=text.lower()
    tokens=set(re.findall(r'[a-z0-9]{2,}',text))
    for chunk in re.findall(r'[\u4e00-\u9fff]+',text):
        tokens.update(chunk[i:i+2] for i in range(len(chunk)-1))
    return tokens


def project(summary,messages,budget,*,updated_at=None,covered_count=0,original_message_count=0):
    # UTF-8 bytes conservatively bound tokens, consistent with request budgets.
    limit=min(4096,max(0,int(budget)//10))
    result={'derived':True,'summary':{k:[] for k in KINDS},
            'updated_at':updated_at,'covered_count':covered_count,
            'original_message_count':original_message_count,
            'rule':'Partial derived history. Keep negation, conditions and uncertainty; current evidence takes priority.',
            'omitted_count':0}
    # Consolidation is lossless exact deduplication, never semantic guessing.
    all_items=list({(r['kind'],r['text']):r for r in entries(summary) if r['active']}.values())
    query=terms(' '.join(m.get('content','') for m in messages[-8:]))
    ranked=sorted(enumerate(all_items),key=lambda p:(p[1]['kind']=='constraints',len(terms(p[1]['text']) & query),p[0]),reverse=True)
    result['omitted_count']=len(all_items)
    if size(result)>limit:
        return None
    # Never slice a sentence: a selected assertion retains all its qualifiers.
    for _,row in ranked:
        trial=deepcopy(result)
        trial['summary'][row['kind']].append(row['text'])
        trial['omitted_count']-=1
        if size(trial)<=limit:
            result=trial
    description=summary.get('description','')
    if description and len(description)<=600:
        trial=deepcopy(result);trial['summary']['description']=description
        if size(trial)<=limit:result=trial
    return result


def public_summary(summary):
    return {k:v for k,v in summary.items() if not k.startswith('_')}
