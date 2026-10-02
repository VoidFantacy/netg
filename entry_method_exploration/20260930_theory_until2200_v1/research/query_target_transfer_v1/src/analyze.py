import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
    with Path(p).open('x') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def fv(p,d):return np.memmap(p,dtype='<f4',mode='r').reshape(-1,d+1)[:,1:]
def main():
    start=time.perf_counter();assert read(R/'reviews/jobs_complete.json')['status']=='PASS';rng=np.random.default_rng(C['bootstrap_seed']);result={}
    for ds,c in C['datasets'].items():
        n,d=c['n'],c['dimension'];root=R/'results'/ds;gt=np.fromfile(c['GT'],'<i4').reshape(n,100);hits=np.zeros((n,6,2),dtype='i4');sets={};data={}
        for ki,pt in enumerate(c['points']):
            K,L=pt['K'],pt['L'];gsets=[set(row[:K]) for row in gt];sets[ki]={};data[ki]={}
            for mi,name in enumerate(C['methods']):
                loc=root/f'k{K}_L{L}'/name;ids=np.fromfile(loc/'ids.i32','<i4').reshape(n,K);assert (ids>=0).all() and (ids<c['base_n']).all()
                hitsets=[set(row)&g for row,g in zip(ids,gsets)];assert all(len(set(row))==K for row in ids);sets[ki][name]=hitsets;hits[:,mi,ki]=[len(x) for x in hitsets]
                data[ki][name]={'entry_ids':np.fromfile(loc/'entry_ids.i32','<i4').reshape(n,3),'slots':np.fromfile(loc/'route_slots.i32','<i4'),'route_ndc':np.fromfile(loc/'route_ndc.u64','<u8'),'graph_ndc':np.fromfile(loc/'graph_ndc.u64','<u8')}
        np.savez(root/'score_arrays.npz',hits=hits)
        delta=hits-hits[:,:1,:];flat=(delta*np.array([100.,1.])).reshape(n,12);boot=np.empty((C['bootstrap_reps'],12))
        for lo in range(0,len(boot),128):
            m=min(128,len(boot)-lo);ix=rng.integers(0,n,size=(m,n));boot[lo:lo+m]=flat[ix].mean(1)
        boot=boot.reshape(-1,6,2);timings=read(root/'timings.json');points={}
        for ki,pt in enumerate(c['points']):
            K,L=pt['K'],pt['L'];wall={}
            for name in C['methods']:
                rows=sorted([x for x in timings if x['K']==K and x['method']==name],key=lambda x:x['repeat']);assert [x['repeat'] for x in rows]==[0,1,2]
                wall[name]=np.array([x['seconds'] for x in rows]);assert (wall[name]>0).all()
            methods={};baseline=wall['Default3'];base_pool=3*n/baseline.sum()
            for mi,name in enumerate(C['methods']):
                h=delta[:,mi,ki];t=wall[name];qps=n/t;pool=3*n/t.sum();a=data[ki][name];added=sum(len(x-y) for x,y in zip(sets[ki][name],sets[ki]['Default3']));lost=sum(len(y-x) for x,y in zip(sets[ki][name],sets[ki]['Default3']));assert added-lost==h.sum()
                methods[name]={'recall_pct':float(hits[:,mi,ki].mean()*100/K),'total_hits':int(hits[:,mi,ki].sum()),'delta_recall_pp':float(h.mean()*100/K),'delta_recall_95pct_descriptive_interval_pp':np.quantile(boot[:,mi,ki],[.025,.975]).tolist(),
                    'rescued_queries':int((h>0).sum()),'damaged_queries':int((h<0).sum()),'net_positive_hits':int(h[h>0].sum()),'net_negative_hits':int(-h[h<0].sum()),'true_member_added':added,'true_member_lost':lost,
                    'seconds':t.tolist(),'qps_each':qps.tolist(),'qps_pooled':float(pool),'delta_qps_pooled_pct':float((pool/base_pool-1)*100),'paired_repeat_delta_qps_pct':((baseline/t-1)*100).tolist(),'extra_us_per_query':float((t.mean()-baseline.mean())/n*1e6),
                    'route_ndc_mean':float(a['route_ndc'].mean()),'graph_ndc_mean':float(a['graph_ndc'].mean()),'total_ndc_mean':float((a['route_ndc']+a['graph_ndc']).mean()),'R_nonnegative_and_QPS_positive_mean_only':bool(h.sum()>=0 and pool>base_pool)}
            controls={};mainsets=sets[ki]['QueryTarget1']
            for mi,name in enumerate(C['methods']):
                if mi==2:continue
                h=hits[:,2,ki]-hits[:,mi,ki];add=sum(len(x-y) for x,y in zip(mainsets,sets[ki][name]));loss=sum(len(y-x) for x,y in zip(mainsets,sets[ki][name]));assert add-loss==h.sum()
                controls[name]={'main_minus_control_recall_pp':float(h.mean()*100/K),'interval_pp':np.quantile(boot[:,2,ki]-boot[:,mi,ki],[.025,.975]).tolist(),'main_relative_QPS_pct':float((wall[name].sum()/wall['QueryTarget1'].sum()-1)*100),'rescued_queries':int((h>0).sum()),'damaged_queries':int((h<0).sum()),'true_member_added':add,'true_member_lost':loss}
            points[str(K)]={'K':K,'L':L,'methods':methods,'main_vs_controls':controls}
        for name in C['methods']:
            assert np.array_equal(data[0][name]['slots'],data[1][name]['slots']) and np.array_equal(data[0][name]['entry_ids'],data[1][name]['entry_ids'])
        base=fv(c['base'],d);train=fv(c['train_queries'],d)[10000:30000].astype('f8');train/=np.linalg.norm(train,axis=1)[:,None];query=np.fromfile(c['queries'],'<f4').reshape(n,d).astype('f8');target=np.fromfile(c['targets'],'<i4');targetvec=np.asarray(base[target],dtype='f8');hids=np.fromfile(c['anchor']['ids'],'<i4')
        mechanism={};entryscores={};normq=np.linalg.norm(query,axis=1)
        for name in C['methods']:
            entries=data[0][name]['entry_ids'];entryscore=np.full((n,3),-np.inf)
            for j in range(3):
                ok=entries[:,j]>=0;entryscore[ok,j]=np.einsum('ij,ij->i',query[ok],np.asarray(base[entries[ok,j]],dtype='f8'))
            best=entryscore.max(1);entryscores[name]=best;mechanism[name]={'max_raw_IP_entry_score_mean':float(best.mean()),'best_entry_cosine_query_scaled_mean':float((best/normq).mean()),'valid_entries':int((entries>=0).sum()),'entries_inside_H':int(np.isin(entries[entries>=0],hids).sum()),'unique_real_entries':int(len(np.unique(entries[entries>=0])))}
        slots=data[0]['QueryTarget1']['slots'];sim=np.einsum('ij,ij->i',query/normq[:,None],train[slots]);qscan=query[:16]@train.T;tscan=query[:16]@targetvec.T;diagnostics={}
        for name,score in [('QueryTarget1',qscan),('TargetBank1',tscan)]:
            selected=data[0][name]['slots'][:16];maxima=score.max(1);chosen=score[np.arange(16),selected];argmax=score.argmax(1)
            diagnostics[name]={'n':16,'float64_full20000_best_slot':argmax.tolist(),'online_selected_slot':selected.tolist(),'selected_equals_argmax':int((selected==argmax).sum()),'selected_has_max_score_within_1e_12':int((maxima-chosen<=1e-12).sum()),'raw_IP_score_regret':(maxima-chosen).tolist(),'note':'diagnostic only; float64 ranking versus float32 ANN includes rounding and ties; no online retuning'}
        result[ds]={'n':n,'points':points,'mechanism':mechanism,'nearest_case_cosine_quantiles':np.quantile(sim,[0,.1,.5,.9,1]).tolist(),'main_entry_score_minus_controls_mean':{name:float((entryscores['QueryTarget1']-score).mean()) for name,score in entryscores.items()},'exact16_router_diagnostics':diagnostics,'history_exposed':True,'training_query_n':20000,'unique_training_targets':int(len(np.unique(target)))}
    put(R/'results/analysis.json',{'status':'COMPLETE_DESCRIPTIVE_RECALL_QPS_COMPARISON','datasets':result,'default_changed':False,'bootstrap_seed':C['bootstrap_seed'],'bootstrap_reps':C['bootstrap_reps'],'bootstrap_scope':'query paired with same indices across K; history exposed development data','QPS_intervals':'three observed repetitions only, no population confidence interval','seconds':time.perf_counter()-start})
    for ds,r in result.items():print(ds,{k:v['methods']['QueryTarget1'] for k,v in r['points'].items()},flush=True)
if __name__=='__main__':main()
