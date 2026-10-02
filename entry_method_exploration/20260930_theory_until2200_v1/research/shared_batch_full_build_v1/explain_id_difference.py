"""Post-audit attribution of exactly the already-identified ID disagreements; no new search."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from graph_decode import decode_graph

R=Path(__file__).resolve().parent
def main():
    start=time.perf_counter();cfg=json.loads((R/'config.locked.json').read_text());refs=json.loads((R/'reviews/validation_references.json').read_text())
    name='yandex_t2i_official10M_ip_v1__Default';c=cfg['cases'][name];ref=refs[name];old=Path(ref['full_default']);new=Path(c['output']);d=c['dimension']
    assert json.loads((R/'reviews/audit_exit.json').read_text())['exit_code']==0
    plan=json.loads((R/'reviews/float64_plan.json').read_text())[c['dataset']]['changed_source_rows']
    assert plan==[6141,13980]
    paths=[old/'v.f64',old/'W.f32',new/'W.f32',old/'fit20000.ids.i64',new/'fit20000.ids.i64',old/'router.hnsw',new/'router.hnsw']
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with threadpool_limits(8):
        base=np.memmap(c['base'],'<f4',mode='r',shape=(c['base_n'],d+1))[:,1:];ids=np.fromfile(new/'ids.i32','<i4')
        unit=lambda x:x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
        h=unit(np.array(base[ids],dtype='f4'));q=np.fromfile(c['fit_queries'],'<f4').reshape(20000,d)
        oi=np.memmap(old/'fit20000.ids.i64','<i8',mode='r',shape=(20000,100));ni=np.memmap(new/'fit20000.ids.i64','<i8',mode='r',shape=(20000,11))
        v=np.fromfile(old/'v.f64','<f8').reshape(len(h),d).copy();records=[]
        for row in plan:
            rec={'source_row':row,'versions':{}};aa={}
            for ver,target in [('old',oi[row,:10]),('new',ni[row,:10])]:
                z=unit(np.array(base[target],dtype='f4'));sf=z@h.T;sd=z.astype('f8')@h.astype('f8').T
                lab=sf.argmax(1);assert np.array_equal(lab,sd.argmax(1));ranked=np.sort(sd,axis=1);margin=ranked[:,-1]-ranked[:,-2]
                assert np.all(margin>1e-5)
                a=np.zeros(len(h))
                for slot in lab:a[slot]+=.1
                aa[ver]=a
                rec['versions'][ver]={'target_ids':target.tolist(),'hub_slots':lab.tolist(),'hub_ids':ids[lab].tolist(),
                    'target_scores_float64':(np.asarray(base[target],dtype='f8')@q[row].astype('f8')).tolist(),
                    'min_hard_assignment_margin_float64':float(margin.min())}
            delta=aa['new']-aa['old'];rec['changed_mass']=[{'slot':int(i),'hub_id':int(ids[i]),'delta':float(delta[i])} for i in np.flatnonzero(delta)]
            v+=delta[:,None]*unit(q[row:row+1]).astype('f8');records.append(rec)
        predicted=unit(v).astype('f4');actual=np.fromfile(new/'W.f32','<f4').reshape(len(h),d);oldw=np.fromfile(old/'W.f32','<f4').reshape(len(h),d)
        np.testing.assert_allclose(predicted,actual,rtol=0,atol=5e-8)
        changed=np.flatnonzero(np.any(actual.view('u4')!=oldw.view('u4'),axis=1))
        go=decode_graph(old/'router.hnsw');gn=decode_graph(new/'router.hnsw');a=go[-1];b=gn[-1]
        graph={'old_edges':sum(len(z) for node in a for z in node[2]),'new_edges':sum(len(z) for node in b for z in node[2]),
               'nodes_with_changed_adjacency':sum(x[2]!=y[2] for x,y in zip(a,b))}
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v for p,v in before.items())
    out={'status':'PASS_ATTRIBUTION_ONLY','seconds':time.perf_counter()-start,'input_sha256':before,'queries':records,
         'changed_W_hub_slots':changed.tolist(),'changed_W_hub_ids':ids[changed].tolist(),
         'old_V_plus_only_identified_mass_changes_max_W_error':float(np.max(np.abs(predicted.astype('f8')-actual))),
         'old_V_plus_only_identified_mass_changes_W_bits_identity':bool(np.array_equal(predicted.view('u4'),actual.view('u4'))),
         'graph':graph,'new_GT':0,'new_NSG':0,'new_ANN':0,'new_model_export':False,
         'interpretation':'Explains observed batch-dependent boundary and mass changes; no label patch, rerun, or reuse of old quality for new Yandex Default'}
    with (R/'reviews/id_difference_explanation.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out),flush=True)

if __name__=='__main__':main()
