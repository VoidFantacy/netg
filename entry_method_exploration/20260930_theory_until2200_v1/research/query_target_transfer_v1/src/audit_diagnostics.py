import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
import json, math, time
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[1]
C=json.loads((R/'config.locked.json').read_text())
A=json.loads((R/'results/analysis.json').read_text())

def main():
    start=time.perf_counter(); out={}; maxerr=0.
    for ds,c in C['datasets'].items():
        n,d=c['n'],c['dimension']; a=A['datasets'][ds]
        base=np.memmap(c['base'],dtype='<f4',mode='r').reshape(-1,d+1)[:,1:]
        tr=np.memmap(c['train_queries'],dtype='<f4',mode='r').reshape(-1,d+1)[10000:30000,1:].astype('f8')
        norm=np.sqrt(np.sum(tr*tr,axis=1)); tr/=norm[:,None]
        q=np.fromfile(c['queries'],'<f4').reshape(n,d).astype('f8'); qnorm=np.sqrt(np.sum(q*q,axis=1))
        targets=np.fromfile(c['targets'],'<i4'); bank=base[targets].astype('f8'); hs=set(np.fromfile(c['anchor']['ids'],'<i4').tolist())
        loc=R/'results'/ds/f'k1_L{c["points"][0]["L"]}'
        for name,m in a['mechanism'].items():
            entries=np.fromfile(loc/name/'entry_ids.i32','<i4').reshape(n,3)
            scores=[]; allentries=[]
            for qi,row in enumerate(entries):
                ids=[int(x) for x in row if x>=0]; allentries.extend(ids)
                scores.append(max(float(np.dot(q[qi],base[x].astype('f8'))) for x in ids))
            vals={'max_raw_IP_entry_score_mean':math.fsum(scores)/n,
                  'best_entry_cosine_query_scaled_mean':math.fsum(float(v/s) for v,s in zip(scores,qnorm))/n}
            for key,v in vals.items():
                err=abs(v-m[key]); maxerr=max(maxerr,err); assert err<1e-12,(ds,name,key,err)
            assert m['valid_entries']==len(allentries)
            assert m['entries_inside_H']==sum(x in hs for x in allentries)
            assert m['unique_real_entries']==len(set(allentries))
        slots=np.fromfile(loc/'QueryTarget1/route_slots.i32','<i4')
        sim=np.array([np.dot(q[i],tr[int(s)])/qnorm[i] for i,s in enumerate(slots)])
        assert np.max(np.abs(np.quantile(sim,[0,.1,.5,.9,1])-a['nearest_case_cosine_quantiles']))<1e-12
        diagnostics={}
        for name,vec in [('QueryTarget1',tr),('TargetBank1',bank)]:
            ref=a['exact16_router_diagnostics'][name]
            selected=np.fromfile(loc/name/'route_slots.i32','<i4')[:16]
            argmax=[]; regrets=[]
            for i in range(16):
                scores=np.einsum('ij,j->i',vec,q[i],optimize=False)
                argmax.append(int(np.argmax(scores)))
                regrets.append(float(np.max(scores)-scores[int(selected[i])]))
            assert argmax==ref['float64_full20000_best_slot']
            assert selected.tolist()==ref['online_selected_slot']
            err=float(np.max(np.abs(np.array(regrets)-ref['raw_IP_score_regret'])))
            maxerr=max(maxerr,err); assert err<1e-12
            assert sum(x<=1e-12 for x in regrets)==ref['selected_has_max_score_within_1e_12']
            diagnostics[name]={'argmax_identical':True,'max_score_within_tolerance':sum(x<=1e-12 for x in regrets)}
        out[ds]={'all_entry_scores_and_counts':True,'all_selected_case_cosines':True,'exact16':diagnostics}
    result={'status':'PASS','datasets':out,'max_abs_error':maxerr,'seconds':time.perf_counter()-start,
            'scope':'post-result arithmetic audit only; frozen experiment and analysis unchanged; same agent, not independent personnel',
            'field_semantics':'best_entry_cosine_query_scaled_mean is max raw IP divided by query norm, not base-normalized cosine'}
    with (R/'reviews/diagnostic_audit.json').open('x') as f: json.dump(result,f,ensure_ascii=False,indent=2); f.write('\n')
    print('DIAGNOSTIC_AUDIT_PASS',maxerr,flush=True)

if __name__=='__main__':main()
