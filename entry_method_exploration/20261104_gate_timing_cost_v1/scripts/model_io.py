from common import *
CHEAP=[i for i in range(24) if i!=14]
STATE=[5,6,7,8,9,10,15,16,17]
DT=np.dtype([('m','<i4',(14,)),('f','<f4',(106,))])
def load_labels(ds,K,L):
    p=R/'storage/labels'/ds/f'k{K}_L{L}'
    raw=np.frombuffer(gzip.open(p/'labels.bin.gz','rb').read(),DT)
    m=raw['m'].copy();f=raw['f'][:,:104].copy();times=raw['f'][:,104:].copy()
    assert len(raw)==read(p/'complete.json')['rows']
    assert np.isfinite(f).all() and np.isfinite(times).all()
    starts=np.r_[0,np.flatnonzero(np.diff(m[:,0]))+1];ends=np.r_[starts[1:],len(m)]
    groups={int(m[s,0]):np.arange(s,e) for s,e in zip(starts,ends)}
    y=np.column_stack([m[:,4]-m[:,5],m[:,8]-m[:,9]]).astype('float64')
    g=np.frombuffer(gzip.open(p/'gate.f32.gz','rb').read(),'<f4').reshape(3072,12).copy()
    return p,m,f,times,groups,y,g
def tree_export(model,n=104):
    trees=[]
    for stage in model._predictors:
        nodes=stage[0].nodes
        trees.append([dict(f=int(x['feature_idx']),t=float(x['num_threshold']),l=int(x['left']),r=int(x['right']),v=float(x['value']),leaf=bool(x['is_leaf'])) for x in nodes])
    return dict(type='hgb',feature_count=n,bias=float(model._baseline_prediction[0,0]),trees=trees,threshold=0.,gate_all_off=False)
def single_tree_export(model):
    t=model.tree_
    ns=[dict(f=int(t.feature[i]),t=float(t.threshold[i]),l=int(t.children_left[i]),r=int(t.children_right[i]),v=float(t.value[i,0,0]),leaf=bool(t.children_left[i]<0)) for i in range(t.node_count)]
    return dict(type='hgb',feature_count=12,bias=0.,trees=[ns],threshold=0.,gate_all_off=False)
def predict_tree(model,X):
    X=np.asarray(X,dtype='float64')
    result=np.full(len(X),model['bias'],dtype='float64')
    for tree in model['trees']:
        nodes=np.zeros(len(X),dtype='int64');pending=np.ones(len(X),bool)
        while pending.any():
            for ni in np.unique(nodes[pending]):
                take=np.flatnonzero(pending & (nodes==ni));n=tree[int(ni)]
                if n['leaf']:result[take]+=n['v'];pending[take]=False
                else:nodes[take]=np.where(X[take,n['f']]<=n['t'],n['l'],n['r'])
    return result
def student_predict(model,f,node_emb,node_ids):
    def arr(k):return np.asarray(model[k],dtype='float64')
    q=np.column_stack([f[:,24:40],f[:,STATE]]).astype('float64')
    q=(q-arr('q_mean'))/arr('q_scale')
    h=np.maximum(q@arr('qw1').T+arr('qb1'),0)
    emb=(h@arr('qw2').T+arr('qb2')).reshape(-1,2,32)
    idx=np.searchsorted(node_ids,model['_ids'])
    assert np.array_equal(node_ids[idx],model['_ids'])
    cheap=(f[:,CHEAP].astype('float64')-arr('c_mean'))/arr('c_scale')
    pred=np.einsum('nbi,ni->nb',emb,node_emb[idx])/np.sqrt(32.)+cheap@arr('cw').T+arr('cb')
    return pred
def select(groups,pred,teacher,y,lam=0.):
    rows=[]
    for qi,ix in groups.items():
        fast=[];cascade=[]
        for b in range(2):
            order=ix[np.argsort(-pred[ix,b],kind='stable')]
            shortlist=list(dict.fromkeys([int(ix[0])]+[int(i) for i in order[:5]]))
            # Tie follows original distance rank, same as C++ ordering.
            shortlist.sort()
            fast.append(int(order[0]));cascade.append(max(shortlist,key=lambda i:(teacher[i,b],-i)))
        utilities=[teacher[cascade[0],0]-lam*.25,teacher[cascade[1],1]-lam]
        b=int(np.argmax(utilities));enabled=max(utilities)>0
        rows.append(dict(q=qi,fast=fast,cascade=cascade,action_budget=b if enabled else -1,
                         action_index=cascade[b] if enabled else -1,
                         action_gain=float(y[cascade[b],b]) if enabled else 0.))
    return rows
