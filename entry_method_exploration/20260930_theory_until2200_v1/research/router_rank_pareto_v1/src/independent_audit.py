import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import hashlib,json,math,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
    with Path(p).open('x') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def select(group,h,t):
    if len(group)==0:return 0
    # Explicit member loops, independent from fit.py's vector reductions.
    scores=[];baseline=sum(int(h[i,0]) for i in group)
    for a in range(4):
        nh=sum(int(h[i,a]) for i in group);tt=math.fsum(float(t[i,a]) for i in group)
        scores.append((tt,a) if nh>=baseline else (math.inf,a))
    return min(scores)[1]
def traverse(nodes,x):
    out=[]
    for row in x:
        j=0;depth=0
        while nodes[j]['feature']!=-1:
            nd=nodes[j];j=nd['right'] if row[nd['feature']]>nd['threshold'] else nd['left'];depth+=1;assert depth<=2
        out.append(nodes[j]['action'])
    return np.array(out,'i4')
def verify_tree(nodes,group,x,h,t,depth=0,j=0):
    a=select(group,h,t);assert a==nodes[j]['action'] and len(group)==nodes[j]['support']
    objective=math.fsum(float(t[i,a]) for i in group);best=None
    if depth<2 and len(group)>=1024:
        for f in range(6):
            # Quantile primitive is shared; all group selection/value arithmetic is separate.
            for threshold in sorted(set(np.quantile(x[group,f],[i/10 for i in range(1,10)],method='linear').tolist())):
                left=[int(i) for i in group if x[i,f]<=threshold];right=[int(i) for i in group if x[i,f]>threshold]
                if min(len(left),len(right))<512:continue
                al,ar=select(left,h,t),select(right,h,t)
                cost=math.fsum(float(t[i,al if x[i,f]<=threshold else ar]) for i in group)
                if cost<objective:objective=cost;best=(f,threshold,left,right)
    if best is None:assert nodes[j]['feature']==-1
    else:
        f,th,left,right=best;assert nodes[j]['feature']==f and nodes[j]['threshold']==th
        verify_tree(nodes,left,x,h,t,depth+1,nodes[j]['left']);verify_tree(nodes,right,x,h,t,depth+1,nodes[j]['right'])
def main():
    start=time.perf_counter();analysis=read(R/'results/analysis.json');jobs=read(R/'reviews/jobs_complete.json');assert jobs['status']=='PASS'
    rng=np.random.default_rng(C['bootstrap_seed']);records={};parity_inputs={};max_error=0.;all_return_rows=0;all_models=0
    for ds,c in C['datasets'].items():
        n=c['n'];gt=np.fromfile(c['gt'],'<i8').reshape(n,100);h=np.zeros((n,4,2),'i4');t=np.zeros((n,4,2),'f8');returns={};distance={}
        ranks=np.fromfile(c['ranked_reference'],'<i4').reshape(n,3);z=np.fromfile(c['state_reference'],'<i4');x=np.fromfile(c['feature_reference'],'<f8').reshape(n,6)
        for ki,pt in enumerate(c['points']):
            K,L=pt['K'],pt['L'];p=R/'results'/ds/'labels'/f'k{K}_L{L}';raw=np.fromfile(p/'seconds.f64','<f8').reshape(n,4,3)
            for i in range(n):
                for a in range(4):t[i,a,ki]=sum(map(float,raw[i,a]))/3
            for a in range(4):
                b=p/f'action{a}';ids=np.fromfile(b/'ids.i32','<i4').reshape(n,K);dd=np.fromfile(b/'distances.f32','<f4').reshape(n,K);entries=np.fromfile(b/'entry_ids.i32','<i4').reshape(n,3)
                assert np.isfinite(dd).all()
                if a==0:assert np.array_equal(entries,np.sort(ranks,axis=1))
                else:assert np.array_equal(entries[:,0],ranks[:,a-1]) and (entries[:,1:]==-1).all()
                for i in range(n):
                    row=ids[i].tolist();assert len(set(row))==K and all(0<=v<c['base_n'] for v in row)
                    h[i,a,ki]=int(row[0]==gt[i,0]) if K==1 else len(set(row).intersection(set(gt[i].tolist())))
                returns[ki,a]=ids;distance[ki,a]=dd;all_return_rows+=n
        old=np.load(R/'models'/ds/'development_arrays.npz');assert np.array_equal(h,old['hits']);assert np.max(np.abs(t-old['seconds']))<1e-14
        roles=np.load(c['old_roles']);folds=roles['folds'];model=read(R/'models'/ds/'models.json');expected=np.zeros((n,6,2),'i4')
        for f in range(4):
            tr=np.flatnonzero(folds!=f);outer=np.flatnonzero(folds==f);perm=roles['train_shuffle'][f]
            for ki,K in enumerate((1,100)):
                for mi,name in enumerate(C['methods'][2:],start=2):
                    m=model['folds'][f]['K'][str(K)][name]
                    if name=='GlobalPareto':
                        a=select(tr,h[:,:,ki],t[:,:,ki]);assert a==m['action'];expected[outer,mi,ki]=a
                    elif name=='FeaturePareto':
                        verify_tree(m['nodes'],tr,x,h[:,:,ki],t[:,:,ki]);expected[outer,mi,ki]=traverse(m['nodes'],x[outer])
                    else:
                        groupstates=z[tr] if name=='StatePareto' else z[perm];table=np.zeros(c['H'],'i4');support=np.zeros(c['H'],'i4')
                        for state in sorted(set(groupstates.tolist())):
                            group=[int(tr[j]) for j in range(len(tr)) if groupstates[j]==state]
                            table[state]=select(group,h[:,:,ki],t[:,:,ki]);support[state]=len(group)
                        assert table.tolist()==m['table'] and support.tolist()==m['support'];expected[outer,mi,ki]=table[z[outer]]
                    all_models+=1
        assert np.array_equal(expected,old['actions'])
        # Restore historical target-budget outputs independently of the new scorer.
        historical=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/research/target_budget_fullH_v1'
        pos=np.fromfile(historical/'inputs_v2'/ds/'original_positions.i64','<i8');assert len(pos)==256
        oldgt=np.fromfile(historical/'inputs_v2'/ds/'gt.i64','<i8').reshape(256,100);assert np.array_equal(gt[pos],oldgt)
        hubs=np.fromfile(c['anchor']['ids'],'<i4');slot={int(v):i+1 for i,v in enumerate(hubs)};historical_checks=0
        for ki,pt in enumerate(c['points']):
            K,L=pt['K'],pt['L']
            if ds.startswith('yandex') and K==1:
                p=Path(c['old_labels_root']);complete=read(p/'complete.json')
                for block in complete['blocks']:
                    lo,nb=block['start'],block['n'];path=p/f'block_{lo}'/'top1_ids.i32';arr=np.fromfile(path,'<i4').reshape(nb,c['H']+1)
                    parity_inputs[str(path)]=ident(path)
                    for j in range(nb):
                        i=lo+j
                        for a in range(4):
                            action=0 if a==0 else slot[int(ranks[i,a-1])]
                            assert int(returns[ki,a][i,0])==int(arr[j,action]);historical_checks+=1
            else:
                root=historical/'results'/ds/f'K{K}_L{L}'
                for lo in range(0,256,16):
                    b=root/f'block_{lo}';ii=np.memmap(b/'ids.i32',dtype='<i4',mode='r',shape=(16,c['H']+1,K));dd=np.memmap(b/'distances.f32',dtype='<f4',mode='r',shape=(16,c['H']+1,K))
                    for name in ('ids.i32','distances.f32'):parity_inputs[str(b/name)]=ident(b/name)
                    for j in range(16):
                        i=int(pos[lo+j])
                        for a in range(4):
                            action=0 if a==0 else slot[int(ranks[i,a-1])]
                            assert np.array_equal(returns[ki,a][i],ii[j,action]) and np.array_equal(distance[ki,a][i].view('u4'),dd[j,action].view('u4'));historical_checks+=1
        selected=np.stack([h[np.arange(n)[:,None],expected[:,:,ki],ki] for ki in range(2)],axis=2)
        difference=selected-selected[:,:1,:];raw_values=difference.reshape(n,12).astype('i8');boot=np.zeros((C['bootstrap_reps'],12),'f8')
        groups=[np.flatnonzero(folds==f) for f in range(4)];scale=np.tile([100.,1.],6)/n
        for lo in range(0,len(boot),128):
            m=min(128,len(boot)-lo);ix=np.concatenate([g[rng.integers(0,len(g),size=(m,len(g)))] for g in groups],axis=1)
            counts=np.array([np.bincount(row,minlength=n) for row in ix],dtype='i8');boot[lo:lo+m]=(counts@raw_values)*scale
        boot=boot.reshape(-1,6,2);wall=read(R/'results'/ds/'wall/timings.json')
        for ki,pt in enumerate(c['points']):
            K=pt['K'];claimed=analysis['datasets'][ds]['points'][str(K)]
            for mi,name in enumerate(C['methods']):
                rr=claimed['methods'][name];delta=difference[:,mi,ki];rec=float(selected[:,mi,ki].sum()*100/(n*K))
                assert abs(rr['recall_pct']-rec)<1e-12 and abs(rr['delta_recall_pp']-float(delta.sum()*100/(n*K)))<1e-12
                ci=np.quantile(boot[:,mi,ki],[.025,.975]);error=np.max(np.abs(ci-rr['delta_recall_95pct_descriptive_interval_pp']));max_error=max(max_error,float(error));assert error<1e-10
                sec=[row['seconds'] for row in wall if row['K']==K and row['method']==name];assert len(sec)==3
                assert abs(3*n/math.fsum(sec)-rr['qps_pooled'])<1e-9
                actions=np.fromfile(R/'results'/ds/'wall'/f'k{K}_L{pt["L"]}'/f'{name}.actions.i32','<i4');assert np.array_equal(actions,expected[:,mi,ki])
            for name,rr in claimed['State_vs_controls'].items():
                mi=C['methods'].index(name);ci=np.quantile(boot[:,2,ki]-boot[:,mi,ki],[.025,.975]);err=np.max(np.abs(ci-rr['State_minus_control_recall_interval_pp']));max_error=max(max_error,float(err));assert err<1e-10
        records[ds]={'scored_return_rows':n*4*2,'independently_recomputed_models':32,'historical_return_vectors_restored':historical_checks,
            'OOF_actions_all_exact':True,'GT_member_loop_exact':True,'native_wall_actions_exact':True,'greedy_tree_all_splits_verified':True}
    assert all_models==64 and all_return_rows==65536
    assert jobs['new_NSG']==594688 and jobs['new_ANN']==610816,(jobs['new_NSG'],jobs['new_ANN'])
    for p,v in read(R/'reviews/run_frozen.json')['files'].items():assert ident(p)==v,p
    for p,v in read(R/'reviews/consumed_inputs.json').items():assert ident(p)==v,p
    for p,v in read(R/'reviews/models_frozen.json')['files'].items():assert ident(p)['sha256']==v,p
    for p,v in parity_inputs.items():assert ident(p)==v,p
    put(R/'reviews/historical_parity_inputs.json',parity_inputs)
    put(R/'reviews/independent_audit.json',{'status':'PASS','seconds':time.perf_counter()-start,'datasets':records,'new_NSG':0,'new_ANN':0,
        'all_primary_return_rows_rescored':all_return_rows,'all_models_recomputed':all_models,'max_bootstrap_interval_error_pp':max_error,
        'native_job_counts_reconciled':True,'protected_sources_models_inputs_unchanged':True,
        'independence':'Same agent, separate set scoring, member-loop action fitting and count-weighted integer bootstrap; quantile primitive shared. Not an independent person.'})
    print('INDEPENDENT_AUDIT_PASS',records,max_error,time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
