import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
import json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]; C=json.loads((R/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def put(p,x):
    with Path(p).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def main():
    start=time.perf_counter();assert read(R/'reviews/jobs_complete.json')['status']=='PASS';rng=np.random.default_rng(C['bootstrap_seed']);result={}
    for ds,c in C['datasets'].items():
        root=R/'results'/ds;n=c['n'];g=np.fromfile(c['GT'],'<i4').reshape(n,100)
        hits=np.zeros((n,6,3),dtype='i4');hitsets={};raw={};timings=read(root/'timings.json');wall={}
        for pi,p in enumerate(c['points']):
            K,L=p['K'],p['L'];gt=[set(x[:K]) for x in g]
            for mi,name in enumerate(C['methods']):
                loc=root/f'k{K}_L{L}'/name;ids=np.fromfile(loc/'ids.i32','<i4').reshape(n,K)
                assert (ids>=0).all() and (ids<c['base_n']).all() and all(len(set(x))==K for x in ids)
                hitsets[pi,mi]=[set(x)&t for x,t in zip(ids,gt)];hits[:,pi,mi]=[len(x) for x in hitsets[pi,mi]]
                raw[pi,mi]={key:np.fromfile(loc/file,dtype).reshape(shape) for key,file,dtype,shape in [('entries','entry_ids.i32','<i4',(n,3)),('slots','route_slots.i32','<i4',(n,)),('route_ndc','route_ndc.u64','<u8',(n,)),('graph_ndc','graph_ndc.u64','<u8',(n,))]}
                rows=sorted([x for x in timings if x['K']==K and x['L']==L and x['method']==name],key=lambda x:x['repeat'])
                assert [x['repeat'] for x in rows]==[0,1,2]
                wall[pi,mi]=np.array([x['seconds'] for x in rows]);assert (wall[pi,mi]>0).all()
        for pi in range(1,6):
            for mi in range(3):
                for key in ['entries','slots','route_ndc']:assert np.array_equal(raw[pi,mi][key],raw[0,mi][key])
        np.savez(root/'score_arrays.npz',hits=hits)
        scale=np.array([100./p['K'] for p in c['points']]);normalized=hits*scale[None,:,None]
        flat=normalized.reshape(n,18);boot=np.empty((C['bootstrap_reps'],18))
        for lo in range(0,len(boot),128):
            m=min(128,len(boot)-lo);ix=rng.integers(0,n,size=(m,n));boot[lo:lo+m]=flat[ix].mean(axis=1)
        boot=boot.reshape(-1,6,3)
        def compare(ai,am,bi,bm):
            assert c['points'][ai]['K']==c['points'][bi]['K'];K=c['points'][ai]['K']
            delta=hits[:,ai,am]-hits[:,bi,bm];bt=boot[:,ai,am]-boot[:,bi,bm]
            added=sum(len(x-y) for x,y in zip(hitsets[ai,am],hitsets[bi,bm]));lost=sum(len(y-x) for x,y in zip(hitsets[ai,am],hitsets[bi,bm]));assert added-lost==delta.sum()
            speed=(wall[bi,bm].sum()/wall[ai,am].sum()-1)*100
            qs1=n/wall[ai,am];qs0=n/wall[bi,bm]
            return {'delta_recall_pp':float(delta.mean()*100/K),'descriptive_interval_pp':np.quantile(bt,[.025,.975]).tolist(),
                    'delta_QPS_pct':float(speed),'paired_repeat_delta_QPS_pct':((wall[bi,bm]/wall[ai,am]-1)*100).tolist(),
                    'extra_us_per_query':float((wall[ai,am].mean()-wall[bi,bm].mean())/n*1e6),
                    'rescued_queries':int((delta>0).sum()),'damaged_queries':int((delta<0).sum()),
                    'net_positive_hits':int(delta[delta>0].sum()),'net_negative_hits':int(-delta[delta<0].sum()),'true_member_added':added,'true_member_lost':lost,
                    'empirical_dominates':bool(delta.sum()>=0 and speed>0),
                    'all_three_paired_QPS_faster':bool((wall[ai,am]<wall[bi,bm]).all()),
                    'QPS_ranges_overlap':bool(max(qs1.min(),qs0.min())<=min(qs1.max(),qs0.max()))}
        points={}
        for pi,p in enumerate(c['points']):
            K,L=p['K'],p['L'];methods={}
            for mi,name in enumerate(C['methods']):
                t=wall[pi,mi];rr=raw[pi,mi]
                methods[name]={'recall_pct':float(hits[:,pi,mi].mean()*100/K),'hits':int(hits[:,pi,mi].sum()),'seconds':t.tolist(),'qps_each':(n/t).tolist(),'qps_pooled':float(3*n/t.sum()),'route_NDC':float(rr['route_ndc'].mean()),'graph_NDC':float(rr['graph_ndc'].mean()),'total_NDC':float((rr['route_ndc']+rr['graph_ndc']).mean()),'vs_Default3':compare(pi,mi,pi,0)}
            points[f'k{K}_L{L}']={'K':K,'L':L,'methods':methods,'TargetBank_vs_DefaultRank1':compare(pi,2,pi,1)}
        cross=[];threshold={}
        for K in (1,100):
            pis=[i for i,p in enumerate(c['points']) if p['K']==K]
            for ai in pis:
                for bm in (0,1):
                    for bi in pis:
                        cross.append({'K':K,'TargetBank_L':c['points'][ai]['L'],'control':C['methods'][bm],'control_L':c['points'][bi]['L'],**compare(ai,2,bi,bm)})
            threshold[str(K)]={}
            for name in C['methods']:
                eligible=[v for v in points.values() if v['K']==K and v['methods'][name]['recall_pct']>=90.]
                if not eligible:threshold[str(K)][name]=None;continue
                selected=max(eligible,key=lambda x:(x['methods'][name]['qps_pooled'],-x['L']))
                m=selected['methods'][name];threshold[str(K)][name]={'L':selected['L'],'recall_pct':m['recall_pct'],'qps_pooled':m['qps_pooled'],'qps_each':m['qps_each']}
        result[ds]={'n':n,'points':points,'all_TargetBank_cross_budget_comparisons':cross,'fastest_measured_R90':threshold,'historical_development_only':True}
    put(R/'results/analysis.json',{'status':'COMPLETE_FROZEN_LOCAL_CURVE','datasets':result,'bootstrap_seed':C['bootstrap_seed'],'bootstrap_reps':C['bootstrap_reps'],'interval_scope':'query paired; same resampling across all K and L; historical exposure and multiple comparison; descriptive only','timing_scope':'pooled and three actual repetitions, no population speed interval','default_changed':False,'seconds':time.perf_counter()-start})
    for ds,d in result.items():print(ds,'R90',d['fastest_measured_R90'],'empirical_dominances',[x for x in d['all_TargetBank_cross_budget_comparisons'] if x['empirical_dominates']],flush=True)
if __name__=='__main__':main()
