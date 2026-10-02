from common import *
from threadpoolctl import threadpool_info
def main():
    started=time.perf_counter();c=json.loads((R/'config.locked.json').read_text());check_inputs(c);guard(started,c)
    assert not (R/'results.json').exists();results={}
    for ds,d in c['datasets'].items():
        begin=time.perf_counter();base,h,ids,mapping,exact,approx=load(d);kind=d['kind'];soft_mode=kind=='soft';H=len(h)
        logits=np.empty((len(ids),H),dtype='f8') if soft_mode else None;labels=np.empty(len(ids),dtype='i4') if not soft_mode else None
        calc=time.perf_counter()
        for lo in range(0,len(ids),2048):
            guard(started,c);x=unit_f32(np.array(base[ids[lo:lo+2048],1:],dtype='f4')).astype('f8');s=x@h.T
            if soft_mode:logits[lo:lo+len(x)]=s/d['temperature']
            else:labels[lo:lo+len(x)]=s.argmax(1)
        dot_seconds=time.perf_counter()-calc;calc=time.perf_counter();missing=np.empty(20000,dtype='u1');metrics=np.empty((20000,4 if soft_mode else 5),dtype='f8' if soft_mode else 'u1')
        for i in range(20000):
            if i%128==0:guard(started,c)
            x,y=mapping[:,i]
            if soft_mode:missing[i],metrics[i]=soft_row(logits,x,y)
            else:
                missing[i]=len(np.setdiff1d(x,y,assume_unique=True));metrics[i]=hard_row(labels,x,y,H)
                assert metrics[i,0]<=2*int(missing[i])
        metric_seconds=time.perf_counter()-calc
        np.savez_compressed(R/(ds+'.npz'),missing=missing,metrics=metrics)
        results[ds]={'kind':kind,'temperature':d['temperature'],'unique_targets':len(ids),'H':H,'unit_hub_sha256':sha(h),'target_ids_sha256':sha(ids),'target_mapping_sha256':sha(mapping),
             'array_sha256':{'missing':sha(missing),'metrics':sha(metrics)},'dot_seconds':dot_seconds,'metric_seconds':metric_seconds,'dataset_seconds':time.perf_counter()-begin,'summary':summary(missing,metrics,kind),
             'fixed_decimal_target_offsets':np.linspace(0,len(ids)-1,32,dtype=int).tolist()}
        print(ds,json.dumps(results[ds]['summary'],ensure_ascii=False),flush=True)
        del logits,labels,base,h,ids,mapping,exact,approx,metrics,missing
    check_inputs(c);guard(started,c);size=sum(p.stat().st_size for p in R.rglob('*') if p.is_file());assert size<c['max_stage_bytes']-150000
    put(R/'results.json',{'status':'READ_ONLY_TARGET_MASS_PENDING_AUDIT','seconds':time.perf_counter()-started,'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'datasets':results,'new_GT':0,'NSG':0,'ANN':0,'new_models':0,'new_confirmation_reads':0,'default_changed':False,'native_identity_claimed':False})
    print('READ ONLY TARGET MASS COMPLETE',time.perf_counter()-started,flush=True)
if __name__=='__main__':main()
