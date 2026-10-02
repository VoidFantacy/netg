import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent/'hybrid_temperature_factorial_v1';T=R.parent/'temperature_full_build_v1';DS='webvid2_5m_light_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def energies(x,y):
    a=np.sum(x*x,axis=1);b=np.sum(y*y,axis=1);cross=2*np.sum(x*y,axis=1);total=np.sum((x+y)**2,axis=1)
    np.testing.assert_allclose(total,a+b+cross,rtol=2e-13,atol=1e-12)
    return {'label':float(a.sum()),'temperature':float(b.sum()),'cross':float(cross.sum()),'total':float(total.sum()),
        'cross_positive_hubs':int(np.sum(cross>0)),'cross_negative_hubs':int(np.sum(cross<0))},np.stack([a,b,cross,total])
def main():
    assert json.loads((R.parent/'fresh_transfer_v1/reviews/independent_audit.json').read_text())['status']=='PASS'
    start=time.perf_counter();(R/'results').mkdir();(R/'reviews').mkdir();c=json.loads((P/'config.locked.json').read_text())['datasets'][DS]['profiles'];d=c['dimension']
    paths=[Path(__file__),R/'protocol.md',R/'theory.md',P/'config.locked.json',R.parent/'directional_error_v1/results'/f'{DS}.npz']
    paths += [Path(c[key]) for key in ['queries','hub_ids','approx_ids','selected_rows','selected_gt']]
    paths += [P/'models'/DS/m/'construction.npz' for m in ['HybridFixedTemperature','HybridPilotTemperature']]
    paths += [T/'results'/DS/m/'v.f64' for m in ['HybridRectifiedCDF','HybridApproxMedian']]
    paths += [Path(m['W']) for m in c['methods']]
    paths += [T/'results'/DS/m/f for m in ['HybridRectifiedCDF','HybridApproxMedian'] for f in ['W.f32','profile_complete.json']]
    dump(R/'reviews/frozen.json',{'unix':time.time(),'inputs':{str(p):ident(p) for p in dict.fromkeys(paths)}})
    baseline=np.load(R.parent/'directional_error_v1/results'/f'{DS}.npz');truth=baseline['v'];approx=baseline['vp'];norm=np.linalg.norm(truth,axis=1);direction=truth/norm[:,None]
    fixed=np.load(P/'models'/DS/'HybridFixedTemperature/construction.npz')['v'];pilot=np.load(P/'models'/DS/'HybridPilotTemperature/construction.npz')['v']
    models={'HybridPilotTemperature':pilot}
    for m in ['HybridRectifiedCDF','HybridApproxMedian']:models[m]=np.fromfile(T/'results'/DS/m/'v.f64','<f8').reshape(len(norm),d)
    wpaths={m['name']:Path(m['W']) for m in c['methods']}
    for m in ['HybridRectifiedCDF','HybridApproxMedian']:wpaths[m]=T/'results'/DS/m/'W.f32'
    for name,v in {'GT10-soft-t1':truth,'ApproxTarget10':approx,'HybridFixedTemperature':fixed,**models}.items():assert unit(v).astype('f4').tobytes()==wpaths[name].read_bytes(),name
    def tangent(e):return (e-np.sum(e*direction,axis=1)[:,None]*direction)/norm[:,None]
    label=fixed-truth;baselinechord=float(np.sum((unit(approx)-direction)**2));records={};saved={}
    for name,v in models.items():
        temp=v-fixed;np.testing.assert_allclose(label+temp,v-truth,rtol=1e-12,atol=1e-13);details={}
        for measure,a,b in [('raw',label,temp),('scaled',label/norm[:,None],temp/norm[:,None]),('tangent',tangent(label),tangent(temp))]:
            rec,arr=energies(a,b);details[measure]=rec;saved[f'{name}_{measure}_energies']=arr
        chord=float(np.sum((unit(v)-direction)**2));details.update(chord2_sum=chord,chord_ratio_to_approx=chord/baselinechord,
            minimum_radial_ratio=float(np.min(np.sum(v*direction,axis=1)/norm)),nonpositive_radial=int(np.sum(np.sum(v*direction,axis=1)<=0)))
        records[name]=details
    base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:];h=unit(np.array(base[np.fromfile(c['hub_ids'],'<i4')],dtype='f4'))
    q=unit(np.fromfile(c['queries'],'<f4').reshape(20000,d)).astype('f8');rows=np.fromfile(c['selected_rows'],'<i4')
    targets=np.fromfile(c['approx_ids'],'<i4').reshape(20000,100).astype('i8');targets[rows]=np.fromfile(c['selected_gt'],'<i8').reshape(2048,100)
    a=np.zeros((20000,len(h)));da=np.zeros_like(a);temp0=c['old_temperature'];derivative_start=time.perf_counter();maxsumerror=0.;maxrange_excess=-np.inf
    for rank in range(10):
        z=unit(np.array(base[targets[:,rank]],dtype='f4'))
        for lo in range(0,20000,4096):
            hi=min(lo+4096,20000);logits=(z[lo:hi]@h.T).astype('f8');logits-=logits.max(1,keepdims=True);logits/=temp0
            prob=np.exp(logits);prob/=prob.sum(1,keepdims=True);mean=np.sum(prob*logits,axis=1,keepdims=True);dp=prob*(mean-logits)
            maxsumerror=max(maxsumerror,float(np.abs(dp.sum(1)).max()));maxrange_excess=max(maxrange_excess,float(np.max(np.abs(dp).sum(1)-(logits.max(1)-logits.min(1))/2)))
            a[lo:hi]+=prob/10;da[lo:hi]+=dp/10
    np.testing.assert_allclose(h.astype('f8')+a.T@q,fixed,rtol=2e-13,atol=1e-12)
    dv=da.T@q;fdir=unit(fixed);fnorm=np.linalg.norm(fixed,axis=1);dw=(dv-np.sum(dv*fdir,axis=1)[:,None]*fdir)/fnorm[:,None]
    assert maxsumerror<1e-12 and maxrange_excess<1e-12;temperatures={'HybridPilotTemperature':json.loads((P/'models'/DS/'profiles_complete.json').read_text())['pilot_temperature']}
    for name in ['HybridRectifiedCDF','HybridApproxMedian']:temperatures[name]=json.loads((T/'results'/DS/name/'profile_complete.json').read_text())['temperature']
    for name,v in models.items():
        dt=float(np.log(temperatures[name]/temp0));actual_v=v-fixed;actual_w=unit(v)-fdir;rv=actual_v-dt*dv;rw=actual_w-dt*dw
        records[name]['first_order_temperature']={'temperature':temperatures[name],'delta_logT':dt,'raw_displacement_norm':float(np.linalg.norm(actual_v)),
            'raw_relative_remainder_norm':float(np.linalg.norm(rv)/np.linalg.norm(actual_v)),'direction_displacement_norm':float(np.linalg.norm(actual_w)),
            'direction_relative_remainder_norm':float(np.linalg.norm(rw)/np.linalg.norm(actual_w))}
    saved.update(dV_dlogT=dv,dW_dlogT=dw,reference_norm=norm)
    # Store derivatives and scalar per-hub decompositions, not additional candidate profiles.
    np.savez_compressed(R/'results/decomposition.npz',**saved)
    for p,v in json.loads((R/'reviews/frozen.json').read_text())['inputs'].items():assert ident(p)==v
    result={'status':'COMPUTED_PENDING_AUDIT','dataset':DS,'models':records,'fixed_temperature':temp0,'fixed_chord2_sum':float(np.sum((fdir-direction)**2)),
        'approx_chord2_sum':baselinechord,'softmax_derivative_sum_max_error':maxsumerror,'softmax_range_bound_max_excess':maxrange_excess,
        'derivative_seconds':time.perf_counter()-derivative_start,'seconds':time.perf_counter()-start,
        'new_GT':0,'new_NSG':0,'new_ANN':0,'new_profiles':0,'new_graphs':0,'new_performance':False,'default_changed':False}
    assert result['seconds']<300;dump(R/'results/summary.json',result);print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
