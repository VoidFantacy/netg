from common import *
import itertools
def main():
    rng=np.random.default_rng(20260930164);n=0;maxerr=0.
    for k in (1,2,3,4):
        for shared in range(k+1):
            for rep in range(4):
                z=rng.normal(size=(2*k,5));x=np.arange(k);y=np.concatenate([x[:shared],np.arange(k,2*k-shared)])
                missing,result=soft_row(z,x,y);assert missing==k-shared
                p=soft(z[x]);q=soft(z[y]);pc=abs(p[:,None,:]-q[None,:,:]).sum(2);d=np.ptp(z[x][:,None,:]-z[y][None,:,:],axis=2);cc=2*np.tanh(d/4)
                def brute(c):return min(sum(c[j,t] for j,t in enumerate(perm))/k for perm in itertools.permutations(range(k)))
                full=np.asarray([abs(p.mean(0)-q.mean(0)).sum(),brute(pc),brute(cc),brute(d)])
                np.testing.assert_allclose(full,result,rtol=1e-12,atol=1e-12);maxerr=max(maxerr,float(abs(full-result).max()));n+=1
    assert n==56
    put(R/'fixture_result.json',{'status':'PASS','cases':n,'max_common_cancellation_error':maxerr,'real_inputs_read':0})
    print('COMMON ATOM FIXTURE PASS',n,maxerr,flush=True)
if __name__=='__main__':main()
