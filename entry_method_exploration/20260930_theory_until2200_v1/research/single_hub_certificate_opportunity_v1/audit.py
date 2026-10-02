import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits,threadpool_info

R=Path(__file__).resolve().parent

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    started=time.perf_counter();c=json.loads((R/'config.locked.json').read_text());result=json.loads((R/'results.json').read_text())
    def guard():assert time.time()<c['deadline_unix'] and time.perf_counter()-started<300
    def sha(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
    guard();assert result['status']=='OPPORTUNITY_DIAGNOSTIC_PENDING_AUDIT'
    assert result['affinity']==list(range(8)) and all(x['num_threads']<=8 for x in result['threadpools'])
    for p,v in c['small_identity'].items():assert ident(p)==v,p
    records={}
    with threadpool_limits(8):
        for ds,d in c['datasets'].items():
            guard();dim=d['dimension'];n=d['base_n'];r=result['datasets'][ds];stored=np.load(R/(ds+'.npz'))
            for k,v in r['array_sha256'].items():assert sha(stored[k])==v
            raw=np.memmap(d['base'],'<f4',mode='r',shape=(n,dim+1));base=raw[:,1:]
            maxval=-1.;maxrow=-1;t=time.perf_counter()
            # Different chunk size and reduction; verify all vectors against the saved outward M.
            for lo in range(0,n,32768):
                guard();x=np.asarray(base[lo:lo+32768],dtype='f8');assert np.isfinite(x).all()
                sq=np.einsum('ij,ij->i',x,x,optimize=False)
                assert np.all(sq<=r['M_outward']**2)
                at=int(sq.argmax())
                if sq[at]>maxval:maxval=float(sq[at]);maxrow=lo+at
            norm_seconds=time.perf_counter()-t
            np.testing.assert_allclose(maxval,r['max_squared_norm'],rtol=2e-13,atol=1e-15)
            assert sum(x['n'] for x in r['blocks'])==n and r['blocks'][0]['lo']==0
            for j,b in enumerate(r['blocks']):
                assert b['lo']==j*65536 and b['n']==min(65536,n-b['lo'])
                x=np.asarray(base[b['max_row']],dtype='f8');np.testing.assert_allclose(x.dot(x),b['max_squared_norm'],rtol=2e-13,atol=1e-15)
            hubs=np.fromfile(d['hub_ids'],'<i4');h0=np.array(base[hubs],dtype='f4')
            hn=np.sqrt(np.sum(h0*h0,axis=1,dtype='f4'))
            hf=h0/np.maximum(hn[:,None],np.float32(1e-12));assert sha(hf)==r['H_f32_sha256'];h=hf.astype('f8')
            q=np.fromfile(d['fit_queries'],'<f4').reshape(20000,dim).astype('f8')
            qn=np.sqrt(np.einsum('ij,ij->i',q,q,optimize=False));np.testing.assert_allclose(qn,stored['qnorm'],rtol=2e-13,atol=1e-15)
            scores=np.einsum('nd,hd->nh',q,h,optimize=False);nearest=scores.argmax(1).astype('i4')
            assert np.array_equal(nearest,stored['nearest'])
            hd=np.empty((len(h),len(h)),dtype='f8')
            for i in range(len(h)):
                x=h-h[i];hd[i]=np.sqrt(np.einsum('ij,ij->i',x,x,optimize=False))
            delta=np.empty(len(q),dtype='f8')
            for lo in range(0,len(q),256):
                guard();hi=min(lo+256,len(q));rr=nearest[lo:hi];row=np.arange(hi-lo)
                numerator=scores[lo:hi][row,rr,None]-scores[lo:hi];denom=qn[lo:hi,None]*hd[rr]
                val=np.divide(numerator,denom,out=np.zeros_like(numerator),where=denom>0);val[row,rr]=np.inf
                delta[lo:hi]=np.maximum(0,np.minimum(1,val.min(1)))
            np.testing.assert_allclose(delta,stored['delta'],rtol=2e-10,atol=2e-12)
            u=np.sqrt(np.maximum(0,1-delta**2));np.testing.assert_allclose(u,stored['u'],rtol=2e-12,atol=2e-12)
            all_scores={};maxerr=0.
            for name,path,dtype in [('exact',d['exact_ids'],'<i8'),('approx',d['approx_ids'],'<i4')]:
                ii=np.memmap(path,dtype,mode='r',shape=(20000,100))[:,:10];tau=np.full(20000,np.inf)
                # Rank-wise rescoring instead of main's query-block 3D reduction.
                for rank in range(10):
                    guard();x=np.asarray(base[ii[:,rank]],dtype='f8');v=np.sum(x*q,axis=1);tau=np.minimum(tau,v)
                t=tau/(r['M_outward']*qn);np.testing.assert_allclose(t,stored['t_'+name],rtol=2e-12,atol=2e-12)
                maxerr=max(maxerr,float(np.max(np.abs(t-stored['t_'+name]))));slack=t-u;old=r['comparisons'][name]
                assert int(np.sum(slack>1e-10))==old['positive_outside_buffer']
                assert int(np.sum(slack < -1e-10))==old['negative_outside_buffer']
                assert int(np.sum(np.abs(slack)<=1e-10))==old['buffer_band'];all_scores[name]=t
            mandatory=np.flatnonzero((all_scores['exact']-u>=-1e-10)|(all_scores['approx']-u>=-1e-10))
            assert len(mandatory)<=64 and mandatory.tolist()==r['mandatory_rows']
            assert set(range(0,20000,625))<=set(r['audit_rows']) and set(mandatory)<=set(r['audit_rows'])
            # Witnesses directly compute q dot (h_a-h_b), independent of score subtraction and Gram distances.
            max_delta_err=0.
            for i in r['audit_rows']:
                a=int(nearest[i]);other=np.asarray([j for j in range(len(h)) if j!=a]);dif=h[a]-h[other]
                nn=np.linalg.norm(dif,axis=1);v=np.divide(dif@q[i],nn*qn[i],out=np.zeros(len(other)),where=nn>0)
                actual=max(0,min(1,float(v.min())));err=abs(actual-float(stored['delta'][i]));max_delta_err=max(max_delta_err,err)
                assert err<2e-12
            records[ds]={'full_base_norm_rows':n,'norm_audit_seconds':norm_seconds,'max_norm_audit_row':maxrow,
                         'all_query_geometry':20000,'candidate_dot_products':400000,'direct_margin_queries':len(r['audit_rows']),
                         'max_tau_ratio_difference':maxerr,'max_direct_delta_difference':max_delta_err,
                         'no_positive_in_either_mode':all(v['positive_outside_buffer']==0 for v in r['comparisons'].values())}
            print(ds,'INDEPENDENT OPPORTUNITY AUDIT PASS',flush=True)
    for p,v in c['small_identity'].items():assert ident(p)==v,p
    for p,v in c['large_identity'].items():
        st=Path(p).stat();assert (st.st_size,st.st_mtime_ns)==(v['bytes'],v['mtime_ns'])
    guard();assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<2*1024**2
    audit={'status':'PASS','seconds':time.perf_counter()-started,'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),
           'scope':'same agent, independent reductions/chunking, complete norm and geometry passes plus direct witness margins',
           'datasets':records,'new_exact_GT':0,'NSG':0,'ANN':0,'native_float32_replacement_certified':False}
    with (R/'independent_audit.json').open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
    print('ALL OPPORTUNITY AUDITS PASS',audit['seconds'],flush=True)

if __name__=='__main__':main()
