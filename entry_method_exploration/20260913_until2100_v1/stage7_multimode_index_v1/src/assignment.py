from common import *
def recover(c):
    d=c['dim'];h=c['hub_count']
    P=np.fromfile(c['P'],np.float32).reshape(h,d)
    Q=normalize(np.fromfile(c['queries_file'],np.float32,count=20000*d).reshape(20000,d))
    GT=np.fromfile(c['gt_file'],np.int64,count=20000*100).reshape(20000,100)
    R=normalize(np.fromfile(c['raw_hubs'],np.float32).reshape(h,d))
    base=np.memmap(c['base_file'],np.float32,mode='r').reshape(-1,d+1)
    A=np.zeros((20000,h),np.float64)
    for rank in range(10):
        T=normalize(np.asarray(base[GT[:,rank],1:],np.float32))
        for start in range(0,20000,4096):
            end=min(start+4096,20000);s=T[start:end]@R.T
            if c['temperature'] is None:
                a=np.zeros(s.shape,np.float64);a[np.arange(end-start),np.argmax(s,axis=1)]=1
            else:
                a=s.astype(np.float64);a-=a.max(1,keepdims=True);a/=c['temperature'];np.exp(a,out=a);a/=a.sum(1,keepdims=True)
            A[start:end]+=a/10
    assert digest(A)==c['original_assignments_sha']
    S=R.astype(float)+A.T@Q.astype(float)
    assert (S/np.linalg.norm(S,axis=1,keepdims=True)).astype(np.float32).tobytes()==P.tobytes()
    return A,Q.astype(float),R.astype(float),P
