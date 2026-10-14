"""Validate helper syntax and health gates without connecting to a server."""
import json,re,sys,tempfile
from pathlib import Path
script=Path(__file__).with_name('deploy.sh').read_text(encoding='utf-8')
for n,block in enumerate(re.findall(r"<<'PY'\n(.*?)\nPY",script,re.S)):
    compile(block,f'inline-helper-{n}','exec')
health=re.findall(r"<<'PY'\n(.*?)\nPY",script,re.S)[0]
with tempfile.TemporaryDirectory() as folder:
    p=Path(folder)/'health.json'
    cases=[('ready',23,True),('ready',22,False),('not_ready',23,False)]
    original=sys.argv
    try:
        sys.argv=['check-health',str(p)]
        for status,count,accepted in cases:
            p.write_text(json.dumps({'status':status,'database':{'ok':True},'migrations':{'ok':True,'expected_count':count,'applied_count':count}}))
            try:exec(compile(health,'health-gate','exec'),{});actual=True
            except AssertionError:actual=False
            assert actual==accepted
    finally:sys.argv=original
assert 'app.restore' not in script and 'run_migrations' not in script and 'set_key' not in script
print('Inline syntax, exact migration health gate and code-only rollback checks: PASS')
