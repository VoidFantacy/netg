from cases import *
import hashlib,json,math,time
from pathlib import Path
from threadpoolctl import threadpool_info
R=Path(__file__).resolve().parent
TOL=1e-11
def soft(z):
    e=np.exp(z-np.max(z,axis=-1,keepdims=True));return e/e.sum(axis=-1,keepdims=True)
def cost(z,y):
    diff=z[:,None,:]-y[None,:,:];return np.ptp(diff,axis=-1)
def assign(c):return min(float(c[np.arange(len(c)),p].mean()) for p in itertools.permutations(range(len(c))))
def finger(digest,*values):
    for v in values:
        a=np.asarray(v,dtype='<f8');digest.update(str(a.shape).encode());digest.update(a.tobytes())
def main():
    started=time.perf_counter();conf=json.loads((R/'config.locked.json').read_text())
    assert not (R/'results.json').exists() and not (R/'all_comparisons.npz').exists()
    def guard():assert time.time()<conf['deadline_unix'] and time.perf_counter()-started<60
    for path,sha in conf['source_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
    dig=hashlib.sha256();rows=[];trimin=np.inf;shiftmax=0.;decimal_rows=[]
    for i,z,y,v,decimal_flag in transport_cases():
        guard();finger(dig,i,z,y,v);p=soft(z);q=soft(y);d=cost(z,y);c=2*np.tanh(d/4)
        mass=float(abs(p.mean(0)-q.mean(0)).sum());lp=assign(abs(p[:,None,:]-q[None,:,:]).sum(2));wc=assign(c);wd=assign(d);jensen=2*math.tanh(wd/4)
        assert mass<=lp+TOL and lp<=wc+TOL and wc<=jensen+TOL and jensen<=wd/2+TOL
        tri=2*np.tanh(cost(z,v)/4)+2*np.tanh(cost(v,y)/4)-c;assert tri.min()>=-TOL;trimin=min(trimin,float(tri.min()))
        shifts=np.arange(len(z),dtype=float)[:,None]*3+17
        err=max(float(abs(soft(z+shifts)-p).max()),float(abs(cost(z+shifts,y-shifts)-d).max()));assert err<TOL;shiftmax=max(shiftmax,err)
        rows.append([mass,lp,wc,wd,jensen]);
        if decimal_flag:decimal_rows.append(i)
    transport=np.asarray(rows);assert transport.shape==(2592,5) and len(decimal_rows)==32
    hardn=0
    for k,x,y in hard_cases():
        finger(dig,k,x,y);c=2*(np.asarray(x)[:,None]!=np.asarray(y)[None,:]);wc=assign(c);delta=abs(np.bincount(x,minlength=3)-np.bincount(y,minlength=3)).sum()/k
        assert abs(wc-delta)<TOL;hardn+=1
    assert hardn==7380
    rows=[]
    for i,u,prior,z,y in aggregate_cases():
        guard();finger(dig,i,u,prior,z,y);a=soft(z);b=soft(y);v=prior+a.T@u;vp=prior+b.T@u;e=vp-v
        np.testing.assert_allclose(e,(b-a).T@u,atol=TOL,rtol=TOL)
        lhs=np.linalg.norm(e);bound=np.sum(abs(b-a).sum(1)*np.linalg.norm(u,axis=1));assert lhs<=bound+TOL
        m=np.linalg.norm(v,axis=1);mp=np.linalg.norm(vp,axis=1);assert np.min(m)>1e-8 and np.min(mp)>1e-8
        w=v/m[:,None];wp=vp/mp[:,None];alpha=np.sum(e*w,axis=1);t=e-alpha[:,None]*w;rr=np.sum(t*t,axis=1);chord=np.sum((wp-w)**2,axis=1)
        formula=2*(1-(m+alpha)/np.sqrt((m+alpha)**2+rr));np.testing.assert_allclose(chord,formula,atol=TOL,rtol=TOL)
        ok=m+alpha>0;assert np.all(chord[ok]<=rr[ok]/(m[ok]+alpha[ok])**2+TOL)
        rows.append([lhs,bound,float(chord.sum()),float(abs(chord-formula).max())])
    aggregate=np.asarray(rows);score=[];ms=[];ss=[];changes=[]
    for i,s,e in score_cases():
        guard();finger(dig,i,s,e);a=np.argsort(-s,kind='stable');b=np.argsort(-(s+e),kind='stable');risk=float(e@e)
        for r in range(1,7):
            margin=float(s[a[r-1]]-s[a[r]]);changed=set(a[:r])!=set(b[:r]);assert margin>0
            assert not changed or margin**2<=2*risk+TOL
            assert changed<=min(1.,2*risk/margin**2)+TOL
            score.append([margin,risk,int(changed)]);ms.append(margin);ss.append(risk);changes.append(changed)
    score=np.asarray(score);thresholds=np.asarray([.0001,.001,.01,.05,.1,.2,.5,1.,2.]);bounds=[]
    for tau in thresholds:
        lhs=float(np.mean(changes));rhs=float(np.mean(np.asarray(ms)<=tau)+2*np.mean(ss)/tau**2);assert lhs<=rhs+TOL;bounds.append([float(tau),lhs,rhs])
    tight=[]
    for r in (0.,1e-6,.01,.1,1.,4.,20.):
        p=soft(np.asarray([[-r/4,r/4]]))[0];q=soft(np.asarray([[r/4,-r/4]]))[0]
        lhs=float(abs(p-q).sum());rhs=2*math.tanh(r/4);assert abs(lhs-rhs)<TOL;tight.append([r,lhs,rhs])
    cancellation=float(abs(np.mean([[.9,.1],[.1,.9]],axis=0)-np.mean([[.5,.5],[.5,.5]],axis=0)).sum());assert cancellation==0
    hardcost=assign(abs(np.asarray([[.9,.1],[.1,.9]])[:,None,:]-np.asarray([[.5,.5],[.5,.5]])[None,:,:]).sum(2));assert abs(hardcost-.8)<TOL
    z=np.asarray([[1.,-1.]]);temp_change=float(abs(soft(z)-soft(z/2)).sum());assert temp_change>.2
    tie_s=np.asarray([1.,1.,0.]);tie_e=np.asarray([0.,1e-6,0.]);assert np.argmax(tie_s)!=np.argmax(tie_s+tie_e) and tie_s[0]-tie_s[1]==0
    # Fixed sign/zero counterexamples are contractual checks, not a unit() fallback.
    v=np.asarray([1.,0.]);reverse=-v;zero=np.zeros(2);assert np.sum((reverse-v)**2)==4 and np.linalg.norm(zero)==0
    np.savez_compressed(R/'all_comparisons.npz',transport=transport,aggregate=aggregate,score=score,threshold_bounds=np.asarray(bounds))
    arrid={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in [('transport',transport),('aggregate',aggregate),('score',score)]}
    guard();assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<conf['max_stage_bytes']-16384
    result={'status':'MATHEMATICAL_CHECKS_PENDING_AUDIT','seconds':time.perf_counter()-started,'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),
       'input_sha256':dig.hexdigest(),'array_sha256':arrid,'counts':{'transport':len(transport),'hard_pairs':hardn,'aggregate':len(aggregate),'score_topr':len(score),'thresholds':len(bounds)},
       'decimal_rows':decimal_rows,'transport_min_slacks':np.min(np.diff(transport[:,:3],axis=1),axis=0).tolist(),'triangle_min_slack':trimin,'shift_max_error':shiftmax,
       'binary_tight':tight,'cancellation_mass_error':cancellation,'cancellation_transport':hardcost,'same_target_different_temperature_l1':temp_change,
       'sign_and_zero_examples':{'reverse_chord_squared':4,'zero_resultant_formula_inapplicable':True},'ties_can_change_with_arbitrarily_small_error':True,
       'real_data_reads':0,'NSG':0,'ANN':0,'new_GT':0,'default_changed':False}
    with (R/'results.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('MATHEMATICAL CHECKS PASS',result['counts'],result['seconds'],flush=True)
if __name__=='__main__':main()
