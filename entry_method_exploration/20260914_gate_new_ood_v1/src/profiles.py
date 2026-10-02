from common import *
import sys, shutil

def build(ds):
    assert ds=='laion10m_acsg_v1';inp=RUN/'inputs'/ds;out=RUN/'models'/ds
    c=json.loads((inp/'manifest.json').read_text());base=vecs(c['paths']['base_path']);gt=vecs(c['paths']['drl_train_gt_path'],'i4')[10000:30000];q=unit(vecs(c['paths']['drl_train_query_path'])[10000:30000]);h=np.fromfile(inp/'gt10.hubs.f32','f4').reshape(-1,q.shape[1]);t=time.time();tn=unit(base[gt[:,0]]);gaps=[]
    for lo in range(0,20000,4096):
        s=tn[lo:lo+4096]@h.T;top=np.partition(s,-2,axis=1)[:,-2:];gaps.extend((top.max(axis=1)-top.min(axis=1)).tolist())
    temperature=max(float(np.median(gaps)),1e-4);a={name:np.zeros((20000,len(h)),dtype='f8') for name in ['gt10_hard','gt10_soft_t1']}
    for rank in range(10):
        targets=unit(base[gt[:,rank]])
        for lo in range(0,20000,4096):
            hi=min(lo+4096,20000);s=targets[lo:hi]@h.T;best=s.argmax(axis=1);a['gt10_hard'][np.arange(lo,hi),best]+=.1
            x=s.astype('f8');x-=x.max(axis=1,keepdims=True);x/=temperature;np.exp(x,out=x);x/=x.sum(axis=1,keepdims=True);a['gt10_soft_t1'][lo:hi]+=x/10
    for name,weights in a.items():
        p=out/name;p.mkdir(parents=True,exist_ok=True);assert not (p/'W.f32').exists()
        assert np.max(np.abs(weights.sum(axis=1)-1))<1e-12
        sums=h.astype('f8')+weights.T@q.astype('f8');w=(sums/np.maximum(np.linalg.norm(sums,axis=1,keepdims=True),1e-12)).astype('f4');w.tofile(p/'W.f32');dump(p/'manifest.json',dict(variant=name,temperature=temperature if name.endswith('t1') else None,fit=[10000,30000],GT_rank_weights='1/10',assignment_sha256=hashlib.sha256(weights.tobytes()).hexdigest(),W_sha256=sha(p/'W.f32'),shared_build_seconds=time.time()-t))
    cal=dict(formal=False,threads=1,index=c['paths']['index'],queries=str(inp/'cal.f32'),n=1024,L=[128],methods=[dict(name=name,W=str(out/name/'W.f32'),ids=str(inp/'gt10.ids.i32')) for name in a])
    dump(out/'cal_config.json',cal)

def select(ds):
    inp=RUN/'inputs'/ds;out=RUN/'models'/ds;result=out/'cal_results';assert json.loads((result/'complete.json').read_text())['status']=='PASS';gt=np.fromfile(inp/'cal.gt.i32','i4').reshape(1024,100)[:,:10];records=[]
    for name in ['gt10_hard','gt10_soft_t1']:
        p=result/(name+'_L128');ids=np.fromfile(p/'ids.i32','i4').reshape(1024,10);hits=np.array([len(set(map(int,a))&set(map(int,b))) for a,b in zip(ids,gt)]);ndc=np.fromfile(p/'graph_ndc.u64','u8');records.append(dict(name=name,hits=int(hits.sum()),graph_ndc=int(ndc.sum())))
    records.sort(key=lambda x:(-x['hits'],x['graph_ndc'],x['name']!='gt10_hard'));selected=records[0]['name'];shutil.copy2(out/selected/'W.f32',inp/'gt10.W.f32');dump(out/'gt10_selection.json',dict(selected=selected,rule='cal L128 hits desc; graphNDC asc; hard first',all_candidates=records,W_sha256=sha(inp/'gt10.W.f32'),no_test_access=True))

if __name__=='__main__':globals()[sys.argv[1]](sys.argv[2])
