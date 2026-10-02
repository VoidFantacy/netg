import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,shutil,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits,threadpool_info

R=Path(__file__).resolve().parent
P=R.parent/'energy_fresh_transfer_v1'
C=json.loads((P/'config.locked.json').read_text())

def ident(path):
    p=Path(path)
    return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def dump(path,value):
    with Path(path).open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def location(case,point,method):
    return P/'results'/case/f'k{point["K"]}'/f'{method["name"]}_L{point["L"]}'

def read_batch(case,c,point,method):
    p=location(case,point,method);n,k=c['n'],point['K']
    return {'entries':np.fromfile(p/'entry_ids.i32','<i4').reshape(n,3),
            'ids':np.fromfile(p/'ids.i32','<i4').reshape(n,k),
            'bits':np.fromfile(p/'distances.f32','<u4').reshape(n,k),
            'ndc':np.fromfile(p/'graph_ndc.u64','<u8')}

def main():
    started=time.perf_counter()
    for path in ['independent_audit.json','small_gap_float64_audit.json']:
        assert json.loads((P/'reviews'/path).read_text())['status']=='PASS'
    assert json.loads((P/'reviews/seal.json').read_text())['status']=='AUDITED_COMPLETE'
    assert json.loads((P/'reviews/active_process.json').read_text())['pid'] is None
    assert shutil.disk_usage(R).free>=6*1024**3
    assert sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file())+8*1024**2<=1024**3
    (R/'results').mkdir();(R/'reviews').mkdir(exist_ok=True)
    paths=[R/'protocol.md',R/'theory.md',*R.glob('*.py'),P/'config.locked.json',P/'reviews/seal.json',P/'results/summary.json']
    for case,c in C['cases'].items():
        paths += [Path(c['queries']),Path(c['gt'])]
        for m in c['methods']:
            paths += [Path(m[key]) for key in ['ids','W','graph']]
            for point in c['points']:
                paths += [location(case,point,m)/fn for fn in ['ids.i32','distances.f32','entry_ids.i32','graph_ndc.u64','complete.json']]
    frozen={str(p):ident(p) for p in dict.fromkeys(paths)}
    dump(R/'reviews/frozen.json',{'unix':time.time(),'files':frozen})
    old=json.loads((P/'results/summary.json').read_text());results={}
    with threadpool_limits(8):
      for case,c in C['cases'].items():
        n,d=c['n'],c['dimension'];methods=c['methods']
        q=np.fromfile(c['queries'],'<f4').reshape(n,d).astype('f8');norm=np.linalg.norm(q,axis=1)
        assert np.all(norm>0);q/=norm[:,None];second_moment=q.T@q/n
        truth=np.fromfile(c['gt'],'<i4').reshape(n,100)
        hubids=np.fromfile(methods[0]['ids'],'<i4');H=len(hubids)
        models=[];model_stats=[];save={};all_batches={}
        for method in methods:
            name=method['name'];assert np.array_equal(np.fromfile(method['ids'],'<i4'),hubids)
            w=np.fromfile(method['W'],'<f4').reshape(H,d).astype('f8');scores=q@w.T
            rank=np.lexsort((np.broadcast_to(hubids,scores.shape),-scores),axis=1);top=rank[:,:3]
            exact=np.sort(hubids[top],axis=1);gap=scores[np.arange(n),rank[:,2]]-scores[np.arange(n),rank[:,3]]
            unit_roundoff=2**-24;gamma=(d+2)*unit_roundoff/(1-(d+2)*unit_roundoff)
            radius=gamma*(np.linalg.norm(w,axis=1).max()+1/norm);near=gap<=2*radius
            batches={}
            for point in c['points']:
                k=point['K'];b=read_batch(case,c,point,method)
                b['sets']=[set(row.tolist()) for row in b['ids']]
                b['correct']=[s&set(gt[:k].tolist()) for s,gt in zip(b['sets'],truth)]
                b['hits']=np.array([len(s) for s in b['correct']],dtype='i2');batches[k]=b
            real=batches[1]['entries'];assert np.array_equal(real,batches[100]['entries'])
            assert np.all(np.diff(real,axis=1)>0)
            missed=np.any(exact!=real,axis=1)
            models.append({'w':w,'scores':scores,'top':top,'exact':exact,'real':real,'missed':missed,'near':near})
            all_batches[name]=batches
            model_stats.append({'method':name,'router_disagrees_with_exact':int(missed.sum()),
                'near_float_boundary':int(near.sum()),'router_disagreement_away':int((missed&~near).sum()),
                'gap3_4_quantiles':np.quantile(gap,[0,.01,.1,.5,.9,1]).tolist(),'score_computations':n*H})
            for key,value in [('exact_top3',exact),('actual_top3',real),('gap3_4',gap),('float_radius',radius),('near_float_boundary',near)]:
                save[name+'__'+key]=value
        pairs=[]
        for j in range(1,len(methods)):
          for ref in range(j):
            cand,base=models[j],models[ref];name=methods[j]['name'];reference=methods[ref]['name'];key=name+'__vs__'+reference
            dw=cand['w']-base['w'];eps=np.linalg.norm(dw,axis=1);delta_scores=cand['scores']-base['scores']
            risk=float(np.mean(np.sum(delta_scores**2,axis=1)));matrix_risk=float(np.sum((dw@second_moment)*dw))
            assert np.isclose(risk,matrix_risk,atol=1e-16,rtol=1e-10)
            inc=np.zeros((n,H),bool);np.put_along_axis(inc,base['top'],True,axis=1)
            def certificate(radius):
                left=np.min(np.where(inc,base['scores']-radius,np.inf),axis=1)
                right=np.max(np.where(~inc,base['scores']+radius,-np.inf),axis=1)
                return left>right
            normcert=certificate(eps[None,:]);postcert=certificate(np.abs(delta_scores))
            exactchange=np.any(cand['exact']!=base['exact'],axis=1);actualchange=np.any(cand['real']!=base['real'],axis=1)
            assert not np.any(exactchange&(normcert|postcert))
            assert np.all(actualchange.astype('i4')<=exactchange.astype('i4')+cand['missed']+base['missed'])
            category=exactchange.astype('u1')*2+actualchange.astype('u1');near=cand['near']|base['near']
            points=[]
            for point in c['points']:
                k=point['K'];cb=all_batches[name][k];bb=all_batches[reference][k]
                for item in ['ids','bits','ndc']:assert np.array_equal(cb[item][~actualchange],bb[item][~actualchange])
                gain=np.array([len(a-b) for a,b in zip(cb['correct'],bb['correct'])],dtype='i2')
                loss=np.array([len(b-a) for a,b in zip(cb['correct'],bb['correct'])],dtype='i2')
                delta=cb['hits']-bb['hits'];assert np.array_equal(delta,gain-loss)
                ordered_change=np.any(cb['ids']!=bb['ids'],axis=1)
                set_change=np.array([a!=b for a,b in zip(cb['sets'],bb['sets'])])
                correct_change=(gain+loss)>0
                assert np.all(correct_change<=set_change) and np.all(set_change<=actualchange)
                assert np.all(np.abs(delta)/k<=correct_change)
                previous=next(row for p in old['cases'][case]['points'] if p['K']==k for row in p['comparisons'] if row['method']==name and row['reference']==reference)
                assert int(gain.sum())==previous['rescue_members'] and int(loss.sum())==previous['damage_members']
                assert int(ordered_change.sum())==previous['output_id_changes'] and int(actualchange.sum())==previous['entry_changes']
                groups=[]
                for code in range(4):
                  for numeric in ['all','away','near']:
                    mask=category==code
                    if numeric=='away':mask &= ~near
                    if numeric=='near':mask &= near
                    groups.append({'category':code,'numeric_group':numeric,'n':int(mask.sum()),
                        'ordered_output_changes':int(ordered_change[mask].sum()),'output_set_changes':int(set_change[mask].sum()),
                        'correct_set_changes':int(correct_change[mask].sum()),'rescue_members':int(gain[mask].sum()),'damage_members':int(loss[mask].sum()),
                        'net_positive_members':int(np.maximum(delta[mask],0).sum()),'net_negative_members':int(np.maximum(-delta[mask],0).sum()),
                        'within_query_cancelled_members_per_side':int(np.minimum(gain[mask],loss[mask]).sum()),
                        'positive_queries':int((delta[mask]>0).sum()),'negative_queries':int((delta[mask]<0).sum())})
                points.append({'K':k,'L':point['L'],'groups':groups})
                for label,value in [('delta_hits',delta),('gain_members',gain),('loss_members',loss),('ordered_changed',ordered_change),('set_changed',set_change)]:
                    save[key+f'__K{k}__'+label]=value
            chord=float(np.sum(dw**2))
            pairs.append({'method':name,'reference':reference,'score_risk':risk,'second_moment_risk':matrix_risk,
                'stored_W_squared_difference_sum':chord,'score_risk_per_stored_W_difference':risk/chord if chord else None,
                'norm_certificate':int(normcert.sum()),'posthoc_certificate':int(postcert.sum()),
                'exact_changes':int(exactchange.sum()),'actual_changes':int(actualchange.sum()),'near_float_boundary_either':int(near.sum()),
                'category_counts':np.bincount(category,minlength=4).tolist(),'points':points})
            for label,value in [('category',category),('norm_certificate',normcert),('posthoc_certificate',postcert)]:save[key+'__'+label]=value
        np.savez_compressed(R/'results'/f'{case}.npz',**save)
        results[case]={'dataset':c['dataset'],'batch':c['batch'],'n':n,'models':model_stats,'comparisons':pairs}
        assert time.perf_counter()-started<180
        print(case,'COMPLETE',flush=True)
      pools=threadpool_info()
    for path,value in frozen.items():assert ident(path)==value
    assert all(p['num_threads']<=8 for p in pools)
    dump(R/'results/summary.json',{'status':'COMPUTED_PENDING_AUDIT','cases':results,'seconds':time.perf_counter()-started,
        'threadpools':pools,'new_GT':0,'new_NSG':0,'new_ANN':0,'new_models':0,'default_changed':False,
        'category_labels':['same_exact_same_actual','same_exact_changed_actual','changed_exact_same_actual','changed_exact_changed_actual']})
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=8*1024**2
    print('ALL CASES COMPUTED',flush=True)

if __name__=='__main__':main()
