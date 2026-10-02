import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import hashlib,json,shutil,datetime
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent.parent;ROOT=P.parents[1];OLD=ROOT/'entry_method_exploration/20260921_comparison_direction_pilot_v1';C=json.loads((OLD/'config.locked.json').read_text());I={}
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(p):I[str(p)]=ident(p);return json.loads(p.read_text())
def raw(p,t):I[str(p)]=ident(p);return np.fromfile(p,t)
def load(p):I[str(p)]=ident(p);return np.load(p)
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
dump(R/'reviews/prepare_frozen_v2.json',{'files':{str(p):ident(p) for p in [R/'protocol.md',Path(__file__),OLD/'config.locked.json']}})
settings={};sample={};deadline=datetime.datetime.fromisoformat('2026-09-22T13:15:00+00:00').timestamp()
for i,(ds,dc) in enumerate(C['datasets'].items()):sample[ds]=np.sort(np.random.default_rng(2026092227+i).choice(4096,256,replace=False)).tolist()
dump(R/'reviews/sample_frozen_v2.json',{'seed':2026092227,'source':'E118 fit4096','positions':sample})
for ds,dc in C['datasets'].items():
    p=R/'inputs_v2'/ds;p.mkdir();idx=np.array(sample[ds]);d=dc['dimension'];src=OLD/'inputs'/ds/'fit';q=raw(src/'queries.f32','<f4').reshape(4096,d);gt=raw(src/'gt.i64','<i8').reshape(4096,100);rows=raw(src/'row_ids.i64','<i8');ids=raw(Path(dc['anchor']['ids']),'<i4');H=len(ids);A=H+1
    q[idx].tofile(p/'queries.f32');gt[idx].tofile(p/'gt.i64');rows[idx].tofile(p/'source_rows.i64');idx.astype('i8').tofile(p/'original_positions.i64')
    lab=OLD/'results'/ds/'labels';blocks=read(lab/'complete.json')['blocks'];arrays={key:[] for key in ['hits1','hits100','masks','ndc','hashes','top1','entries']}
    for b in sorted(blocks,key=lambda x:x['start']):
        bp=lab/f"block_{b['start']}";n=b['n']
        for key,file,typ,shape in [('hits1','hits1.u8','u1',(n,A)),('hits100','hits100.u8','u1',(n,A)),('masks','masks.u64','<u8',(n,A,2)),('ndc','ndc.u64','<u8',(n,A)),('hashes','return_hashes.u64','<u8',(n,A)),('top1','top1_ids.i32','<i4',(n,A)),('entries','baseline_entries.i32','<i4',(n,3))]:arrays[key].append(raw(bp/file,typ).reshape(shape))
    arrays={k:np.concatenate(v)[idx] for k,v in arrays.items()};arrays['hashes'].tofile(p/'low_return_hashes.u64');arrays['entries'].tofile(p/'baseline_entries.i32')
    for name,stage,slot in [('E123TargetService','e123_target_service_gate_v1',3),('E124SemanticService19k','e124_semantic_service_ridge_v1',3)]:
        mod='models_v2' if name.startswith('E123') else 'models';z=load(P/'stages'/stage/mod/ds/'oof.npz');assert np.array_equal(z['rows'],rows);arrays[name+'_actions']=z['actions'][idx,slot]
    np.savez(p/'old_reference.npz',**arrays)
    points=[{'K':1,'L':1000},{'K':100,'L':1250}] if ds.startswith('web') else [{'K':100,'L':256}]
    conf={k:dc[k] for k in ['anchor','base','base_n','dimension','index']};conf.update(dataset=ds,n=256,queries=str(p/'queries.f32'),gt=str(p/'gt.i64'),reference_entries=str(p/'baseline_entries.i32'),reference_hashes=str(p/'low_return_hashes.u64'),points=points,block=16,threads=1,deadline_unix=deadline,seconds_cap=3600,max_search_calls=650000)
    dump(p/'config.json',conf);settings[ds]=conf
for name in ['base_engine.hpp','kernels.hpp']:src=OLD/'src'/name;I[str(src)]=ident(src);assert (R/'src'/name).read_bytes()==src.read_bytes()
shutil.copytree(OLD/'src/common',R/'src/common')
for p in (OLD/'src/common').rglob('*'):
    if p.is_file():I[str(p)]=ident(p)
dump(R/'config.locked.json',{'datasets':settings,'sample_n':256,'seed':2026092227,'bootstrap_seed':2026092228,'bootstrap_reps':20000,'max_new_NSG':650000,'deadline_unix':deadline,'pure_diagnostic':True,'new_candidate_eligible':False,'original_K1_Y_L128_reused':True})
for p,v in I.items():assert ident(Path(p))==v
dump(R/'reviews/prepare_inputs.json',I);dump(R/'reviews/prepare_complete.json',{'status':'PASS','files':len(I),'sample_rows':512,'new_searches':0,'new_fits':0,'sample_frozen_before_response_slicing':True})
print('PASS',len(I))
