from cases import *
import hashlib,json,time
from pathlib import Path
from decimal import Decimal,localcontext
from scipy.optimize import linear_sum_assignment
from threadpoolctl import threadpool_info
R=Path(__file__).resolve().parent;TOL=1e-11
def direct(z):
    ans=[]
    for row in z:
        ex=[float(np.exp(v)) for v in row];den=sum(ex);ans.append([v/den for v in ex])
    return np.asarray(ans)
def distance(z,y):
    return np.asarray([[max(a-b)-min(a-b) for b in y] for a in z])
def optimal(c):
    rr,cc=linear_sum_assignment(c);return float(sum(c[r,s] for r,s in zip(rr,cc))/len(rr))
def finger(digest,*values):
    for v in values:
        a=np.asarray(v,dtype='<f8');digest.update(str(a.shape).encode());digest.update(a.tobytes())
def decsoft(row):
    ex=[Decimal(str(float(x))).exp() for x in row];den=sum(ex);return [x/den for x in ex]
def main():
    started=time.perf_counter();conf=json.loads((R/'config.locked.json').read_text());old=json.loads((R/'results.json').read_text());data=np.load(R/'all_comparisons.npz')
    assert not (R/'independent_audit.json').exists()
    def guard():assert time.time()<conf['deadline_unix'] and time.perf_counter()-started<60
    for path,sha in conf['source_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
    for k,sha in old['array_sha256'].items():assert hashlib.sha256(np.ascontiguousarray(data[k]).tobytes()).hexdigest()==sha
    assert old['affinity']==[0] and all(x['num_threads']==1 for x in old['threadpools'])
    dig=hashlib.sha256();decimal_error=0.;all_errors=[];n=0
    with localcontext() as ctx:
        ctx.prec=60
        for i,z,y,v,flag in transport_cases():
            guard();finger(dig,i,z,y,v);p=direct(z);q=direct(y);dd=distance(z,y);cc=2*np.tanh(dd/4)
            pc=np.asarray([[sum(abs(a-b)) for b in q] for a in p]);mass=sum(abs(np.mean(p,axis=0)-np.mean(q,axis=0)))
            lp=optimal(pc);wc=optimal(cc);wd=optimal(dd);row=np.asarray([mass,lp,wc,wd,2*np.tanh(wd/4)])
            np.testing.assert_allclose(row,data['transport'][i],rtol=TOL,atol=TOL);all_errors.append(float(abs(row-data['transport'][i]).max()))
            assert mass<=lp+TOL and lp<=wc+TOL and wc<=row[4]+TOL and row[4]<=wd/2+TOL
            assert np.min(2*np.tanh(distance(z,v)/4)+2*np.tanh(distance(v,y)/4)-cc)>=-TOL
            shifted=z+np.arange(len(z))[:,None]*3+17;np.testing.assert_allclose(direct(shifted),p,rtol=TOL,atol=TOL)
            if flag:
                dp=[decsoft(x) for x in z];dq=[decsoft(x) for x in y];k=Decimal(len(z));h=z.shape[1]
                dm=sum(abs(sum(x[j] for x in dp)/k-sum(x[j] for x in dq)/k) for j in range(h));decimal_error=max(decimal_error,abs(float(dm)-mass))
                for r,a in enumerate(dp):
                    for s,b in enumerate(dq):
                        actual=sum(abs(x-y) for x,y in zip(a,b));dif=[Decimal(str(float(x)))-Decimal(str(float(y))) for x,y in zip(z[r],y[s])]
                        osc=max(dif)-min(dif);ex=(osc/2).exp();bound=2*(ex-1)/(ex+1)
                        assert actual<=bound+Decimal('1e-50');decimal_error=max(decimal_error,abs(float(actual)-pc[r,s]))
                n+=1
    assert n==32
    hardn=0
    for k,x,y in hard_cases():
        finger(dig,k,x,y);cx=[x.count(j) for j in range(3)];cy=[y.count(j) for j in range(3)]
        delta=sum(abs(a-b) for a,b in zip(cx,cy))/k;shared=sum(min(a,b) for a,b in zip(cx,cy));cost=2*(k-shared)/k
        assert abs(cost-delta)<TOL;hardn+=1
    maxnormerr=0.
    for i,u,prior,z,y in aggregate_cases():
        guard();finger(dig,i,u,prior,z,y);a=direct(z);b=direct(y);v=prior.copy();vp=prior.copy();e=np.zeros_like(prior)
        for h in range(7):
            for j in range(8):v[h]+=a[j,h]*u[j];vp[h]+=b[j,h]*u[j];e[h]+=(b[j,h]-a[j,h])*u[j]
        np.testing.assert_allclose(vp-v,e,rtol=TOL,atol=TOL)
        lhs=float(np.sqrt(sum(sum(row*row) for row in e)));bound=sum(sum(abs(b[j]-a[j]))*np.sqrt(sum(u[j]*u[j])) for j in range(8));assert lhs<=bound+TOL
        chord_total=0.
        for h in range(7):
            m=float(np.sqrt(sum(v[h]*v[h])));mp=float(np.sqrt(sum(vp[h]*vp[h])));w=v[h]/m;wp=vp[h]/mp
            chord=float(sum((wp-w)**2));alpha=float(sum(e[h]*w));t=e[h]-alpha*w;rr=float(sum(t*t));formula=2*(1-(m+alpha)/np.hypot(m+alpha,np.sqrt(rr)))
            assert abs(chord-formula)<TOL
            if m+alpha>0:assert chord<=rr/(m+alpha)**2+TOL
            chord_total+=chord
        row=np.asarray([lhs,bound,chord_total]);np.testing.assert_allclose(row,data['aggregate'][i,:3],rtol=TOL,atol=TOL);maxnormerr=max(maxnormerr,float(abs(row-data['aggregate'][i,:3]).max()))
    rows=[]
    for i,s,e in score_cases():
        finger(dig,i,s,e);a=sorted(range(7),key=lambda j:(-s[j],j));b=sorted(range(7),key=lambda j:(-(s[j]+e[j]),j));risk=sum(float(x)**2 for x in e)
        for r in range(1,7):
            margin=s[a[r-1]]-s[a[r]];changed=set(a[:r])!=set(b[:r]);assert margin>0
            assert not changed or margin**2<=2*risk+TOL;rows.append([margin,risk,int(changed)])
    rows=np.asarray(rows);np.testing.assert_allclose(rows,data['score'],rtol=TOL,atol=TOL)
    for tau,lhs,rhs in data['threshold_bounds']:
        direct_lhs=sum(x[2] for x in rows)/len(rows);direct_rhs=sum(x[0]<=tau for x in rows)/len(rows)+2*sum(x[1] for x in rows)/len(rows)/tau**2
        np.testing.assert_allclose([lhs,rhs],[direct_lhs,direct_rhs],rtol=TOL,atol=TOL);assert lhs<=rhs+TOL
    tight_error=0.
    with localcontext() as ctx:
        ctx.prec=60
        for r,lhs,rhs in old['binary_tight']:
            p=decsoft([-r/4,r/4]);q=decsoft([r/4,-r/4]);actual=sum(abs(x-y) for x,y in zip(p,q));dr=Decimal(str(r));ex=(dr/2).exp();bound=2*(ex-1)/(ex+1)
            assert abs(actual-bound)<Decimal('1e-50');tight_error=max(tight_error,abs(float(actual)-lhs),abs(float(bound)-rhs))
    assert dig.hexdigest()==old['input_sha256'];assert hardn==7380 and old['counts']=={'transport':2592,'hard_pairs':7380,'aggregate':512,'score_topr':3072,'thresholds':9}
    assert old['cancellation_mass_error']==0 and abs(old['cancellation_transport']-.8)<TOL
    assert old['same_target_different_temperature_l1']>.2 and old['sign_and_zero_examples']=={'reverse_chord_squared':4,'zero_resultant_formula_inapplicable':True}
    assert np.argmax([1.,1.,0.])!=np.argmax([1.,1.+1e-6,0.]);assert old['ties_can_change_with_arbitrarily_small_error']
    for path,sha in conf['source_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
    guard();audit={'status':'PASS','seconds':time.perf_counter()-started,'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),
       'scope':'shared frozen synthetic input generator; independent direct-exp, linear assignment, loop aggregation, scalar ordering, and fixed Decimal checks',
       'input_sha256':dig.hexdigest(),'counts':old['counts'],'max_transport_comparison_error':max(all_errors),'max_aggregate_comparison_error':maxnormerr,
       'decimal_transport_instances':n,'decimal_probability_l1_max_float_error':decimal_error,'decimal_binary_equality_max_float_error':tight_error,
       'real_data_reads':0,'NSG':0,'ANN':0,'new_GT':0,'new_models':0}
    with (R/'independent_audit.json').open('x') as f:json.dump(audit,f,indent=2);f.write('\n')
    print('INDEPENDENT MATHEMATICAL AUDIT PASS',audit['seconds'],flush=True)
if __name__=='__main__':main()
