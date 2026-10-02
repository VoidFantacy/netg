"""Version-local utilities. No imported experiment runner or mutable old outputs."""
import os
for _key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key]='1'
os.environ['OMP_DYNAMIC']='FALSE'
import json, hashlib, time, shutil
from pathlib import Path
import numpy as np

RUN=Path(__file__).resolve().parents[1]
ROOT=RUN.parents[1]
def read(p): return json.loads(Path(p).read_text())
def dump(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def ident(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
LOCK=read(RUN/'config.locked.json')
def base_config(ds,role):
    c=LOCK['datasets'][ds];p=RUN/'inputs'/ds/role
    a,b=LOCK['roles'][role]
    return dict(dataset=ds,dimension=c['dimension'],base_n=c['base_n'],base=c['base'],index=c['index'],anchor=c['anchor'],
                threads=1,n=b-a,queries=str(p/'queries.f32'),gt=str(p/'gt.i64'),hub_ids=c['anchor']['ids'],
                seconds_cap=LOCK['job_seconds_cap'],max_search_calls=LOCK['max_search_calls'],
                label_block=LOCK['label_block'],label_repeats=LOCK['label_repeats'],
                trace_single_actions=LOCK['trace_single_actions'],direction_samples_per_query=LOCK['direction_samples_per_query'])
def prepare(role):
    assert role in LOCK['roles']
    if role=='accept':assert (RUN/'reviews/models_frozen.json').exists(), 'freeze models before acceptance payload access'
    records=[]
    for ds,c in LOCK['datasets'].items():
        p=RUN/'inputs'/ds/role;a,b=LOCK['roles'][role];s=c['fit_source'];d=c['dimension']
        if (p/'identity.json').exists():
            record=read(p/'identity.json')
            for item in record['files']:assert ident(item['path'])==item
            records.append(record);continue
        assert not p.exists();p.mkdir(parents=True)
        # Slice only the authorized role; acceptance is not materialized early.
        arrays={
            'queries.f32':np.memmap(s['queries_file'],dtype='<f4',mode='r',shape=(20000,d))[a:b].copy(),
            'row_ids.i64':np.memmap(s['row_ids'],dtype='<i8',mode='r',shape=(20000,))[a:b].copy()}
        if role!='directions':arrays['gt.i64']=np.memmap(s['gt_file'],dtype='<i8',mode='r',shape=(20000,100))[a:b].copy()
        q=arrays['queries.f32'];rows=arrays['row_ids.i64']
        assert np.isfinite(q).all() and (np.linalg.norm(q,axis=1)>0).all()
        assert np.array_equal(rows,np.arange(a+10000,b+10000))
        hashes=[hashlib.sha256(v.tobytes()).hexdigest() for v in q]
        assert len(set(hashes))==len(hashes),'duplicate within query role'
        for other in LOCK['roles']:
            op=RUN/'inputs'/ds/other/'identity.json'
            if op.exists():assert not set(hashes)&set(read(op)['query_hashes']), 'query leakage across roles'
        for name,v in arrays.items():v.tofile(p/name)
        record=dict(dataset=ds,role=role,source_positions=[a,b],source_rows=[int(rows[0]),int(rows[-1])],
                    source_container=s,query_hashes=hashes,files=[ident(p/name) for name in arrays],
                    historically_exposed=True,heldout=False)
        dump(p/'identity.json',record);dump(p/'config.json',base_config(ds,role));records.append(record)
    dump(RUN/'reviews'/f'input_{role}.json',dict(status='PASS',datasets=records))
    return records

def load_labels(ds):
    p=RUN/'results'/ds/'labels';done=read(p/'complete.json');n,A=done['n'],done['A']
    vals={k:[] for k in ('r1','r100','time','ndc','masks')}
    for block in sorted(done['blocks'],key=lambda z:z['start']):
        b=p/f"block_{block['start']}";nb=block['n'];assert block['full_bit_parity']
        vals['r1'].append(np.fromfile(b/'hits1.u8',np.uint8).reshape(nb,A).astype(np.float64))
        vals['r100'].append(np.fromfile(b/'hits100.u8',np.uint8).reshape(nb,A).astype(np.float64)/100)
        vals['time'].append(np.fromfile(b/'seconds.f64',np.float64).reshape(nb,A,2,3))
        vals['ndc'].append(np.fromfile(b/'ndc.u64',np.uint64).reshape(nb,A))
        vals['masks'].append(np.fromfile(b/'masks.u64',np.uint64).reshape(nb,A,2))
    result={k:np.concatenate(v) for k,v in vals.items()}
    assert all(v.shape[0]==n for v in result.values()) and np.all(result['time']>0)
    return result
