"""Checkpoint the existing HBKM arithmetic without changing its assignments."""
from common import *

def cluster(km,X,k,rng,path,max_iters=20):
    N,D=X.shape;assert N>k
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        with np.load(path,allow_pickle=False) as z:
            labels=z['labels'];centroids=z['centroids'];sizes=z['sizes'];next_iter=int(z['next_iter']);done=bool(z['done']);rng.bit_generator.state=json.loads(str(z['rng']))
        assert len(labels)==N and centroids.shape==(k,D)
        if done:return labels,centroids
    else:
        centroids=km._init_centroids_kmeanspp(X,k,rng);sizes=np.full(k,N/k,dtype='f8');labels=np.full(N,-1,dtype='i4');next_iter=0
    for t in range(next_iter,max_iters):
        new_labels=km._assign_balanced(X,centroids,.01,sizes,N/k)
        new_centroids=np.zeros((k,D),dtype='f4');new_sizes=np.zeros(k,dtype='f8')
        for j in range(k):
            mask=new_labels==j;cnt=int(mask.sum());new_sizes[j]=cnt
            new_centroids[j]=X[mask].mean(axis=0) if cnt else X[rng.integers(0,N)]
        converged=np.array_equal(new_labels,labels)
        if not converged:labels,sizes,centroids=new_labels,new_sizes,new_centroids
        done=converged or t+1==max_iters
        tmp=path.with_suffix('.npz.tmp')
        with tmp.open('wb') as f:np.savez(f,labels=labels,centroids=centroids,sizes=sizes,next_iter=np.int64(t+1),done=np.bool_(done),rng=np.array(json.dumps(rng.bit_generator.state)))
        tmp.replace(path);print('HBKM_CHECKPOINT',path.stem,'iteration',t+1,'done',done,flush=True)
        if done:break
    assert len(np.unique(labels))==k,'balanced k-means collapsed'
    return labels,centroids

def hbkm(km,X,out):
    out=Path(out);rng=np.random.default_rng(42)
    labels,_=cluster(km,X,32,rng,out/'level1.npz');clusters=[]
    for i in range(32):
        ids=np.where(labels==i)[0];assert len(ids)>16
        child,_=cluster(km,X[ids],16,rng,out/f'level2_{i:02}.npz')
        for j in range(16):clusters.append(ids[child==j])
    assert len(clusters)==512 and sum(map(len,clusters))==len(X)
    return clusters
