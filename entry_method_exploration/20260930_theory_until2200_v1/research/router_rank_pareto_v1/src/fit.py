import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import hashlib,json,math,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
C=json.loads((R/'config.locked.json').read_text())
def put(p,v):
    with Path(p).open('x') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def choose(h,t,ix):
    if len(ix)==0:return 0
    sh=h[ix].sum(axis=0,dtype=np.int64);sums=[math.fsum(t[ix,a]) for a in range(4)]
    a=0
    for j in range(1,4):
        if sh[j]>=sh[0] and sums[j]<sums[a]:a=j
    return a
def fit_tree(x,h,t,train):
    nodes=[]
    def rec(ix,depth):
        action=choose(h,t,ix);best_cost=math.fsum(t[ix,action]);pos=len(nodes)
        nodes.append({'feature':-1,'action':int(action),'support':len(ix),'training_seconds_sum':best_cost})
        if depth==C['tree_depth'] or len(ix)<2*C['min_leaf']:return pos
        best=None
        for f in range(6):
            for th in np.unique(np.quantile(x[ix,f],C['split_quantiles'],method='linear')):
                mask=x[ix,f]<=th
                if min(int(mask.sum()),int((~mask).sum()))<C['min_leaf']:continue
                left,right=ix[mask],ix[~mask];al,ar=choose(h,t,left),choose(h,t,right)
                acts=np.where(mask,al,ar);value=math.fsum(t[ix,acts])
                if value<best_cost:best_cost=value;best=(f,float(th),left,right)
        if best is not None:
            f,th,left,right=best
            nodes[pos].update(feature=f,threshold=th,left=rec(left,depth+1),right=rec(right,depth+1))
        return pos
    rec(np.asarray(train),0);return nodes
def predict_tree(nodes,x):
    a=np.empty(len(x),dtype='i4')
    for i,v in enumerate(x):
        j=0
        while nodes[j]['feature']>=0:
            n=nodes[j];j=n['left'] if v[n['feature']]<=n['threshold'] else n['right']
        a[i]=nodes[j]['action']
    return a
def main():
    start=time.perf_counter();all_scores={};frozen={};inputs={};total_models=0
    for ds,c in C['datasets'].items():
        n=c['n'];H=c['H'];out=R/'models'/ds;gt=np.fromfile(c['gt'],'<i8').reshape(n,100)
        assert all(len(set(row))==100 for row in gt)
        x=np.fromfile(c['feature_reference'],'<f8').reshape(n,6);z=np.fromfile(c['state_reference'],'<i4');roles=np.load(c['old_roles']);folds=roles['folds']
        hits=np.empty((n,4,2),dtype='<i2');seconds=np.empty((n,4,2),dtype='<f8');labels=R/'results'/ds/'labels'
        for ki,pt in enumerate(c['points']):
            k,L=pt['K'],pt['L'];p=labels/f'k{k}_L{L}';assert json.loads((p/'complete.json').read_text())['status']=='PASS'
            times=np.fromfile(p/'seconds.f64','<f8').reshape(n,4,3);assert np.isfinite(times).all() and (times>0).all()
            seconds[:,:,ki]=times.mean(axis=2);inputs[str(p/'seconds.f64')]=sha(p/'seconds.f64')
            for a in range(4):
                path=p/f'action{a}'/'ids.i32';ids=np.fromfile(path,'<i4').reshape(n,k)
                assert ((ids>=0)&(ids<c['base_n'])).all() and all(len(set(row))==k for row in ids)
                if k==1:hits[:,a,ki]=ids[:,0]==gt[:,0]
                else:hits[:,a,ki]=[np.isin(row,truth,assume_unique=True).sum() for row,truth in zip(ids,gt)]
                inputs[str(path)]=sha(path)
        expected=np.zeros((n,6,2),dtype='<i4');records=[];fold_models=[]
        for f in range(4):
            train=np.flatnonzero(folds!=f);outer=np.flatnonzero(folds==f);perm=roles['train_shuffle'][f]
            assert not set(train)&set(outer) and set(perm)==set(train)
            fd={'fold':f,'K':{}}
            for ki,pt in enumerate(c['points']):
                k=pt['K'];h=hits[:,:,ki];t=seconds[:,:,ki];target={}
                for method in C['models']:
                    if method=='GlobalPareto':
                        a=choose(h,t,train);m={'action':a};train_actions=np.full(len(train),a,'i4');outer_actions=np.full(len(outer),a,'i4')
                    elif method=='FeaturePareto':
                        nodes=fit_tree(x,h,t,train);m={'nodes':nodes};train_actions=predict_tree(nodes,x[train]);outer_actions=predict_tree(nodes,x[outer])
                    else:
                        zfit=z[train] if method=='StatePareto' else z[perm]
                        table=np.zeros(H,dtype='i4');support=np.zeros(H,dtype='i4')
                        for v in np.unique(zfit):
                            group=train[zfit==v];table[v]=choose(h,t,group);support[v]=len(group)
                        m={'table':table.tolist(),'support':support.tolist()};train_actions=table[zfit];outer_actions=table[z[outer]]
                    target[method]=m;mi=C['methods'].index(method);expected[outer,mi,ki]=outer_actions;total_models+=1
                    for role,rows,acts in [('train',train,train_actions),('outer',outer,outer_actions)]:
                        dh=h[rows,acts].astype('i4')-h[rows,0].astype('i4');dt=t[rows,acts]-t[rows,0]
                        records.append({'fold':f,'K':k,'method':method,'role':role,'n':len(rows),'delta_hits_sum':int(dh.sum()),
                            'delta_recall_pp':float(dh.mean()*100/k),'delta_proxy_seconds_mean':float(dt.mean()),
                            'rescued_queries':int((dh>0).sum()),'damaged_queries':int((dh<0).sum()),'actions':np.bincount(acts,minlength=4).tolist()})
                    assert sum((h[train,train_actions].astype('i4')-h[train,0].astype('i4')).tolist())>=0
                fd['K'][str(k)]=target
            fold_models.append(fd)
        model={'dataset':ds,'H':H,'n':n,'scope':'historically exposed four-fold development, not final deployment model',
            'graph_sha256':sha(c['anchor']['graph']),'W_sha256':sha(c['anchor']['W']),'ids_sha256':sha(c['anchor']['ids']),
            'points':c['points'],'folds':fold_models,'config_sha256':sha(R/'config.locked.json')}
        put(out/'models.json',model);put(out/'fit_metrics.json',records)
        for ki,k in enumerate((1,100)):expected[:,:,ki].tofile(out/f'expected_actions_K{k}.i32')
        np.savez_compressed(out/'development_arrays.npz',hits=hits,seconds=seconds,actions=expected,states=z,folds=folds)
        all_scores[ds]={'default_recall_pct':(hits[:,0,:].mean(0)*[100,1]).tolist(),
            'oracle_gain_pp':((hits.max(1)-hits[:,0,:]).mean(0)*[100,1]).tolist(),
            'models':len(C['models'])*4*2,'new_NSG':0,'new_ANN':0,'fit_role_rows_per_fold':3072,'outer_role_rows_per_fold':1024}
        for p in out.iterdir():frozen[str(p)]=sha(p)
        print('FIT_COMPLETE',ds,flush=True)
    put(R/'reviews/models_frozen.json',{'status':'PASS','unix':time.time(),'seconds':time.perf_counter()-start,'models':total_models,
        'files':frozen,'response_inputs':inputs,'no_outer_label_selection':True,'wall_started':False,'new_NSG':0,'new_ANN':0})
    put(R/'results/fit_overview.json',all_scores);print('ALL_MODELS_FROZEN',total_models,flush=True)
if __name__=='__main__':main()
