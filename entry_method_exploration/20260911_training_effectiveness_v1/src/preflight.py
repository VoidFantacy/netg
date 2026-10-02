from common import *
import numpy as np

assert read(E30/'state.json')['status']=='COMPLETE'
assert read(E30/'reviews/final_audit.json')['status']=='PASS'
assert not (O/'reviews/protected_before.json').exists()
old=read(E30/'reviews/protected_before.json');checks={}
for item in old:
    now=identity(item['path']);assert now==item,item['path'];checks[item['path']]=now
for p in E30.rglob('*'):
    if p.is_file():checks[str(p)]=identity(p)
dump(O/'reviews/protected_before.json',list(checks.values()))
assert (O/'src/train.py').read_text().split('\ndef learning_rate')[0].rstrip()==(E30/'src/train.py').read_text().split('\ndef fit(')[0].rstrip()
assert sha(O/'src/test_objective.py')==sha(E30/'src/test_objective.py')
recovery=[];files=[O/'protocol.md']+list((O/'src').glob('*.py'))
for ds in DS:
    for p in (O/'inputs'/ds).rglob('*'):
        if p.is_file():assert sha(p)==sha(E30/'inputs'/ds/p.relative_to(O/'inputs'/ds));files.append(p)
    c=read(O/'inputs'/ds/'fit/config.json');n,d,h=c['num_queries'],c['dim'],c['hub_count']
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(float)
    q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(float);q/=np.linalg.norm(q,axis=1,keepdims=True)
    ts=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
    for key in ['queries_file','gt_file','row_ids','hub_ids']:files.append(Path(c[key]))
    files += [E24/'models'/ds/'gt10_hard/W.f32',E28/'inputs'/ds/'proposals/triples.i32',E28/'labels'/ds/'hits.u8',E28/'labels'/ds/'graph_ndc.u32']
    for cell in CELLS:
        a=np.fromfile(E30/'models'/ds/cell/'A.f64',np.float64).reshape(d,d)
        w=p+p@a.T;w/=np.linalg.norm(w,axis=1,keepdims=True)
        oldw=np.fromfile(E30/'models'/ds/cell/'W.f32',np.float32).reshape(h,d)
        assert np.allclose(w,oldw,atol=2e-8,rtol=1e-7)
        accepted=np.fromfile(O/'inputs'/ds/'teachers'/(cell+'.u8'),np.uint8).reshape(n,56).astype(bool)
        ls=[]
        for b in range(0,n,512):
            z=q[b:b+512]@w.T/.05;s=np.take_along_axis(z[:,None,:],ts[b:b+512],axis=2).sum(2)
            ls.extend(np.max(s+.1*(~accepted[b:b+512]),axis=1)-np.max(np.where(accepted[b:b+512],s,-np.inf),axis=1))
        obj=float(np.mean(ls)+100*np.square(w-p).sum(1).mean());curve=read(E30/'models'/ds/cell/'training_curve.json')
        assert abs(obj-curve[-1]['objective'])<1e-8
        recovery.append(dict(dataset=ds,cell=cell,old_objective=obj,initial=curve[0],first_update=curve[1],last=curve[-1],source=identity(E30/'models'/ds/cell/'model.json')))
dump(O/'reviews/preflight.json',dict(status='PASS',protected_files=len(checks),core_math_source_identical=True,teacher_bytes_identical=True,old_model_recovery=recovery,NSG_calls=0,new_labels=0,heldout_access=False))
freeze(O/'reviews/frozen_before_training.json',files)
dump(O/'state.json',dict(status='PREFLIGHT_COMPLETE_TRAINING_PENDING',training_runs=0,real_search_calls=0,heldout_access=False))
print('PREFLIGHT_PASS',len(checks),flush=True)
