import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.sched_setaffinity(0,range(8))
import json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
def main():
    started=time.perf_counter();cfg=json.loads((R/'config.locked.json').read_text());refs=json.loads((R/'reviews/validation_references.json').read_text());records={}
    for ds,c in cfg['datasets'].items():
        p=Path(c['output']);full=Path(refs[ds]['full_build']);rows=np.fromfile(p/'qgt_demand.rows.i32','<i4');n=len(rows)
        ids=np.fromfile(p/'qgt_demand.ids.i64','<i8').reshape(n,100);dist=np.fromfile(p/'qgt_demand.dist.f32','<f4').reshape(n,100)
        oldids=np.fromfile(full/'qgt5000.ids.i64','<i8').reshape(5000,100)[rows];oldd=np.fromfile(full/'qgt5000.dist.f32','<f4').reshape(5000,100)[rows]
        assert np.array_equal(np.sort(ids,axis=1),np.sort(oldids,axis=1))
        trace=json.loads((p/'qgt_trace.json').read_text());lookup={int(row):i for i,row in enumerate(rows)};prefix_checks=0
        for item in trace:
            i=lookup[item['row']];ranks=item['ranks_read'];assert np.array_equal(ids[i,:ranks],oldids[i,:ranks]);prefix_checks+=ranks
        changed=np.flatnonzero(np.any(dist.view('u4')!=oldd.view('u4'),axis=1));generation=json.loads((p/'qgt_generation.json').read_text());tail=generation[-1]['rows']
        assert all(int(rows[i]) in tail for i in changed)
        idpos=np.argwhere(ids!=oldids);examples=[];d=c['dimension'];base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
        query=np.fromfile(c['qgt_queries'],'<f4').reshape(5000,d+1)[:,1:];max_new=max_old=0.;score_checks=0
        # Compare every node in every altered score row against independent float64 accumulation.
        for i in changed:
            true=np.asarray(base[ids[i]],dtype='f8')@query[rows[i]].astype('f8');old_by_id={int(node):float(value) for node,value in zip(oldids[i],oldd[i])}
            aligned=np.array([old_by_id[int(node)] for node in ids[i]])
            max_new=max(max_new,float(np.max(np.abs(true-dist[i]))));max_old=max(max_old,float(np.max(np.abs(true-aligned))));score_checks+=len(true)
            assert np.max(np.abs(true-dist[i]))<3e-5 and np.max(np.abs(true-aligned))<3e-5
        for i,j in idpos:
            a,b=int(ids[i,j]),int(oldids[i,j]);qa=query[rows[i]].astype('f8')
            examples.append({'row':int(rows[i]),'rank_zero_based':int(j),'new_id':a,'old_id':b,'new_score':float(dist[i,j]),'old_score':float(oldd[i,j]),
                'float64_new_id_score':float(base[a].astype('f8')@qa),'float64_old_id_score':float(base[b].astype('f8')@qa)})
        records[ds]={'generated_rows':n,'ordered_ID_different_positions':len(idpos),'ordered_ID_different_rows':len(np.unique(idpos[:,0])),
            'distance_bit_different_positions':int(np.sum(dist.view('u4')!=oldd.view('u4'))),'distance_bit_different_rows':len(changed),
            'all_changed_rows_within_short_tail':True,'last_batch_size':len(tail),'top100_set_identity':True,'consumed_prefix_ID_identity':True,'consumed_prefix_positions_checked':prefix_checks,
            'max_distance_discrepancy':float(np.max(np.abs(dist-oldd))),'float64_new_max_error':max_new,'float64_old_max_error':max_old,
            'float64_score_checks':score_checks,'ID_mismatch_examples':examples}
    result={'status':'PASS_CONSUMED_IDENTITY_WITH_REPORTED_UNUSED_TIE_ORDER_DIFFERENCE','datasets':records,'seconds':time.perf_counter()-started,'new_GT':0,'new_ANN':0,'new_NSG':0}
    with (R/'reviews/rounding_diagnostic.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
