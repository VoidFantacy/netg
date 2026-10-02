import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits

R=Path(__file__).resolve().parent
P=R.parent/'hybrid_temperature_factorial_v1'
C=json.loads((P/'config.locked.json').read_text())

def identity(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def dump(p,value):
    with Path(p).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def batch(dc,point,method):
    n=dc['n'];k=point['K'];p=P/'results'/dc['dataset']/'evaluation'/f'k{k}'/f'{method["name"]}_L{point["L"]}'
    return {'entries':np.fromfile(p/'entry_ids.i32','<i4').reshape(n,3),
            'ids':np.fromfile(p/'ids.i32','<i4').reshape(n,k),
            'bits':np.fromfile(p/'distances.f32','<u4').reshape(n,k),
            'ndc':np.fromfile(p/'graph_ndc.u64','<u8')}

def main():
    started=time.perf_counter();(R/'results').mkdir();(R/'reviews').mkdir(exist_ok=True)
    assert json.loads((P/'reviews/independent_audit.json').read_text())['status']=='PASS'
    paths=[Path(__file__),R/'protocol.md',R/'theory.md',P/'config.locked.json',P/'reviews/seal.json']
    for d in C['datasets'].values():
        e=d['evaluate'];paths += [Path(e['queries']),Path(e['gt'])]
        for m in e['methods']:paths += [Path(m['W']),Path(m['ids']),Path(m['graph'])]
    dump(R/'reviews/frozen.json',{'unix':time.time(),'inputs':{str(p):identity(p) for p in dict.fromkeys(paths)}})
    allresults={}
    with threadpool_limits(8):
      for ds,dc in C['datasets'].items():
        ec=dc['evaluate'];n,d=ec['n'],ec['dimension'];methods=ec['methods']
        q=np.fromfile(ec['queries'],'<f4').reshape(n,d).astype('f8');qn=np.linalg.norm(q,axis=1);q/=qn[:,None]
        sigma=q.T@q/n;gt=np.fromfile(ec['gt'],'<i4').reshape(n,100)
        aligned=np.load(P/'results'/f'{ds}.aligned.npz')
        hubids=np.fromfile(methods[0]['ids'],'<i4');H=len(hubids);save={};modeldata=[];modelresults=[]
        for m in methods:
            name=m['name'];w=np.fromfile(m['W'],'<f4').reshape(H,d).astype('f8');s=q@w.T
            rank=np.lexsort((np.broadcast_to(hubids,s.shape),-s),axis=1)
            top=rank[:,:3];exact=np.sort(hubids[top],axis=1);gap=s[np.arange(n),rank[:,2]]-s[np.arange(n),rank[:,3]]
            u=2**-24;gamma=(d+2)*u/(1-(d+2)*u);rho=gamma*(np.linalg.norm(w,axis=1).max()+1/qn)
            near=gap<=2*rho
            base=batch(ec,ec['points'][0],m);real=base['entries'];assert (np.diff(real,axis=1)>0).all()
            assert np.array_equal(real,batch(ec,ec['points'][1],m)['entries'])
            missed=np.any(real!=exact,axis=1)
            modelresults.append({'method':name,'exact_top3_disagrees_with_router':int(missed.sum()),
                'near_float_boundary':int(near.sum()),'disagreement_away_from_float_boundary':int((missed&~near).sum()),
                'gap3_4_quantiles':np.quantile(gap,[0,.01,.1,.5,.9,1]).tolist(),
                'score_computations':n*H})
            modeldata.append({'w':w,'s':s,'top':top,'exact':exact,'real':real,'missed':missed,'near':near})
            for key,value in [('exact_top3',exact),('actual_top3',real),('gap3_4',gap),('float_radius',rho),('near_float_boundary',near),('router_disagreement',missed)]:save[name+'_'+key]=value
        pairresults=[]
        for j in range(1,len(methods)):
          for ref in [0,1]:
            if j==ref:continue
            c,b=modeldata[j],modeldata[ref];name=methods[j]['name'];reference=methods[ref]['name'];pair=name+'_vs_'+reference
            dw=c['w']-b['w'];eps=np.linalg.norm(dw,axis=1);dscores=c['s']-b['s'];near=c['near']|b['near']
            score_risk=float(np.mean(np.sum(dscores**2,axis=1)));cov_risk=float(np.sum((dw@sigma)*dw))
            assert np.isclose(score_risk,cov_risk,rtol=1e-10,atol=1e-16)
            inc=np.zeros((n,H),bool);np.put_along_axis(inc,b['top'],True,axis=1)
            def certificate(radius):
                return np.min(np.where(inc,b['s']-radius,np.inf),axis=1)>np.max(np.where(~inc,b['s']+radius,-np.inf),axis=1)
            normcert=certificate(eps[None,:]);postcert=certificate(np.abs(dscores))
            exactchange=np.any(c['exact']!=b['exact'],axis=1);realchange=np.any(c['real']!=b['real'],axis=1)
            assert not np.any(exactchange&(normcert|postcert))
            assert np.all(realchange.astype('i4')<=exactchange.astype('i4')+c['missed']+b['missed'])
            category=exactchange.astype('u1')*2+realchange.astype('u1')
            points=[]
            for point in ec['points']:
                K=point['K'];cb=batch(ec,point,methods[j]);bb=batch(ec,point,methods[ref]);same=~realchange
                for key in ['ids','bits','ndc']:assert np.array_equal(cb[key][same],bb[key][same])
                hitc=aligned[f'K{K}_{name}_hits'];hitb=aligned[f'K{K}_{reference}_hits'];delta=hitc.astype('i4')-hitb
                assert np.all(np.abs(delta)/K<=realchange)
                changed=np.any(cb['ids']!=bb['ids'],axis=1);groups=[]
                for code in range(4):
                  for numeric in ['all','away','near']:
                    mask=category==code
                    if numeric=='away':mask &= ~near
                    if numeric=='near':mask &= near
                    groups.append({'category':code,'numeric_group':numeric,'n':int(mask.sum()),'output_changes':int(changed[mask].sum()),
                        'rescues':int(np.maximum(delta[mask],0).sum()),'damages':int(np.maximum(-delta[mask],0).sum()),
                        'positive_queries':int((delta[mask]>0).sum()),'negative_queries':int((delta[mask]<0).sum())})
                points.append({'K':K,'L':point['L'],'groups':groups})
                save[pair+f'_K{K}_delta_hits']=delta;save[pair+f'_K{K}_output_changed']=changed
            pairresults.append({'method':name,'reference':reference,'score_risk':score_risk,'covariance_risk':cov_risk,
                'unweighted_chord_sum':float(np.sum(dw**2)),'score_risk_per_chord':score_risk/float(np.sum(dw**2)),
                'norm_certificate':int(normcert.sum()),'posthoc_score_certificate':int(postcert.sum()),
                'exact_changes':int(exactchange.sum()),'actual_changes':int(realchange.sum()),'near_float_boundary_either':int(near.sum()),
                'category_counts':np.bincount(category,minlength=4).tolist(),'points':points})
            save[pair+'_category']=category;save[pair+'_norm_certificate']=normcert;save[pair+'_posthoc_certificate']=postcert
        np.savez_compressed(R/'results'/f'{ds}.npz',**save)
        allresults[ds]={'models':modelresults,'comparisons':pairresults}
        print(ds,json.dumps({'models':modelresults,'pairs':[{k:v for k,v in p.items() if k!='points'} for p in pairresults]}),flush=True)
    for path,value in json.loads((R/'reviews/frozen.json').read_text())['inputs'].items():assert identity(path)==value
    dump(R/'results/summary.json',{'status':'COMPUTED_PENDING_AUDIT','datasets':allresults,'seconds':time.perf_counter()-started,
        'new_real_NSG':0,'new_router_calls':0,'new_GT':0,'new_models':0,'default_changed':False,
        'category_labels':['same_exact_same_actual','same_exact_changed_actual','changed_exact_same_actual','changed_exact_changed_actual']})

if __name__=='__main__':main()
