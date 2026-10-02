import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[name]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits

R=Path(__file__).resolve().parent;P=R.parent/'energy_fresh_transfer_v1'
C=json.loads((P/'config.locked.json').read_text())

def ident(path):
    p=Path(path)
    return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    started=time.perf_counter();s=json.loads((R/'results/summary.json').read_text())
    old=json.loads((P/'results/summary.json').read_text());frozen=json.loads((R/'reviews/frozen.json').read_text())['files']
    for p,v in frozen.items():assert ident(p)==v
    scalar_ranks=certificates=cells=same_entry_checks=returned_vectors=0;max_risk_error=0.
    with threadpool_limits(8):
      for case,c in C['cases'].items():
        n,d=c['n'],c['dimension'];stats=s['cases'][case];saved=np.load(R/'results'/f'{case}.npz')
        query=np.fromfile(c['queries'],'<f4').reshape(n,d).astype('f8');norm=np.sqrt(np.sum(query*query,axis=1));query/=norm[:,None]
        moment=np.einsum('ni,nj->ij',query,query,optimize=True)/n
        truth=np.fromfile(c['gt'],'<i4').reshape(n,100).astype('i8');offset=np.arange(n,dtype='i8')[:,None]*c['base_n']
        ids=np.fromfile(c['methods'][0]['ids'],'<i4');H=len(ids);models={};batches={}
        for method in c['methods']:
            name=method['name'];W=np.fromfile(method['W'],'<f4').reshape(H,d).astype('f8');models[name]=W
            ms=next(x for x in stats['models'] if x['method']==name)
            top=saved[name+'__exact_top3'];actual=saved[name+'__actual_top3'];gap=saved[name+'__gap3_4'];radius=saved[name+'__float_radius'];near=saved[name+'__near_float_boundary']
            assert np.array_equal(near,gap<=2*radius)
            miss=np.any(top!=actual,axis=1)
            assert ms['router_disagrees_with_exact']==int(miss.sum()) and ms['router_disagreement_away']==int((miss&~near).sum())
            assert ms['near_float_boundary']==int(near.sum())
            np.testing.assert_allclose(ms['gap3_4_quantiles'],np.quantile(gap,[0,.01,.1,.5,.9,1]),rtol=1e-13,atol=1e-15)
            for qi in np.linspace(0,n-1,64,dtype='i4'):
                score=np.sum(W*query[qi],axis=1);order=sorted(range(H),key=lambda h:(-score[h],int(ids[h])))
                assert sorted(ids[order[:3]].tolist())==top[qi].tolist()
                assert abs(float(score[order[2]]-score[order[3]])-float(gap[qi]))<1e-13
                u=2**-24;bound=(d+2)*u/(1-(d+2)*u)*(max(np.sqrt(np.sum(W*W,axis=1)))+1/norm[qi])
                assert abs(bound-radius[qi])<1e-15;scalar_ranks+=1
            for point in c['points']:
                k=point['K'];path=P/'results'/case/f'k{k}'/f'{name}_L{point["L"]}'
                out=np.fromfile(path/'ids.i32','<i4').reshape(n,k);codes=out.astype('i8')+offset
                correct=np.isin(codes,(truth[:,:k]+offset).ravel(),assume_unique=True)
                entries=np.fromfile(path/'entry_ids.i32','<i4').reshape(n,3)
                np.testing.assert_array_equal(entries,actual)
                b={'ids':out,'codes':codes,'correct':correct,'entries':entries,
                   'bits':np.fromfile(path/'distances.f32','<u4').reshape(n,k),'ndc':np.fromfile(path/'graph_ndc.u64','<u8')}
                batches[(name,k)]=b;returned_vectors+=n
                previous=next(x for p in old['cases'][case]['points'] if p['K']==k for x in p['methods'] if x['method']==name)
                assert int(correct.sum())==previous['hits']
        for pair in stats['comparisons']:
            name,ref=pair['method'],pair['reference'];key=name+'__vs__'+ref
            W,B=models[name],models[ref];dw=W-B;eps=np.sqrt(np.sum(dw*dw,axis=1))
            exactchange=np.any(saved[name+'__exact_top3']!=saved[ref+'__exact_top3'],axis=1)
            realchange=np.any(saved[name+'__actual_top3']!=saved[ref+'__actual_top3'],axis=1)
            category=2*exactchange.astype('u1')+realchange;near=saved[name+'__near_float_boundary']|saved[ref+'__near_float_boundary']
            np.testing.assert_array_equal(category,saved[key+'__category'])
            assert np.bincount(category,minlength=4).tolist()==pair['category_counts']
            assert int(realchange.sum())==pair['actual_changes'] and int(exactchange.sum())==pair['exact_changes']
            score_d=query@dw.T;risk=float(np.sum(score_d*score_d)/n)
            other=float(np.einsum('hi,ij,hj->',dw,moment,dw,optimize=True))
            np.testing.assert_allclose([pair['score_risk'],pair['second_moment_risk'],other],risk,rtol=1e-10,atol=1e-16)
            max_risk_error=max(max_risk_error,abs(risk-other),abs(risk-pair['score_risk']))
            assert np.isclose(float(np.sum(dw*dw)),pair['stored_W_squared_difference_sum'],rtol=1e-13,atol=1e-15)
            for qi in np.linspace(0,n-1,32,dtype='i4'):
                base=np.sum(B*query[qi],axis=1);cand=np.sum(W*query[qi],axis=1)
                inside=np.isin(ids,saved[ref+'__exact_top3'][qi]);post=np.abs(cand-base)
                for rad,label in [(eps,'norm_certificate'),(post,'posthoc_certificate')]:
                    value=min((base-rad)[inside])>max((base+rad)[~inside])
                    assert value==bool(saved[key+'__'+label][qi]);certificates+=1
            for label in ['norm_certificate','posthoc_certificate']:
                assert pair[label]==int(saved[key+'__'+label].sum())
                assert not np.any(exactchange&saved[key+'__'+label])
            for point in pair['points']:
                k=point['K'];a,b=batches[(name,k)],batches[(ref,k)]
                for field in ['ids','bits','ndc']:
                    np.testing.assert_array_equal(a[field][~realchange],b[field][~realchange]);same_entry_checks+=int((~realchange).sum())
                gain=np.sum(a['correct']&~np.isin(a['codes'],b['codes'].ravel(),assume_unique=True),axis=1)
                loss=np.sum(b['correct']&~np.isin(b['codes'],a['codes'].ravel(),assume_unique=True),axis=1)
                delta=a['correct'].sum(1)-b['correct'].sum(1);ordered=np.any(a['ids']!=b['ids'],axis=1)
                setchange=np.any(np.sort(a['ids'],axis=1)!=np.sort(b['ids'],axis=1),axis=1)
                assert np.array_equal(delta,gain-loss)
                for label,v in [('gain_members',gain),('loss_members',loss),('delta_hits',delta),('ordered_changed',ordered),('set_changed',setchange)]:
                    np.testing.assert_array_equal(v,saved[key+f'__K{k}__'+label])
                for group in point['groups']:
                    mask=category==group['category']
                    if group['numeric_group']=='near':mask&=near
                    if group['numeric_group']=='away':mask&=~near
                    checks={'n':int(mask.sum()),'ordered_output_changes':int(ordered[mask].sum()),'output_set_changes':int(setchange[mask].sum()),
                        'correct_set_changes':int(((gain+loss)[mask]>0).sum()),'rescue_members':int(gain[mask].sum()),'damage_members':int(loss[mask].sum()),
                        'net_positive_members':int(delta[mask][delta[mask]>0].sum()),'net_negative_members':int(-delta[mask][delta[mask]<0].sum()),
                        'within_query_cancelled_members_per_side':int(sum(min(x,y) for x,y in zip(gain[mask],loss[mask]))),
                        'positive_queries':int((delta[mask]>0).sum()),'negative_queries':int((delta[mask]<0).sum())}
                    for field,value in checks.items():assert group[field]==value,(case,key,k,field)
                    assert checks['rescue_members']-checks['net_positive_members']==checks['within_query_cancelled_members_per_side']
                    assert checks['damage_members']-checks['net_negative_members']==checks['within_query_cancelled_members_per_side'];cells+=1
                previous=next(x for p in old['cases'][case]['points'] if p['K']==k for x in p['comparisons'] if x['method']==name and x['reference']==ref)
                assert int(gain.sum())==previous['rescue_members'] and int(loss.sum())==previous['damage_members']
                assert np.isclose(delta.sum()/(n*k)*100,previous['delta_recall_pp'],rtol=0,atol=1e-14)
        assert time.perf_counter()-started<180
        print(case,'AUDIT PASS',flush=True)
    for p,v in frozen.items():assert ident(p)==v
    assert scalar_ranks==1024 and certificates==1536 and cells==576 and returned_vectors==131072
    result={'status':'PASS','seconds':time.perf_counter()-started,'scalar_top3_queries':scalar_ranks,'scalar_certificates':certificates,
            'full_query_group_cells':cells,'same_entry_array_query_checks':same_entry_checks,'returned_query_vectors':returned_vectors,
            'maximum_score_risk_identity_error':max_risk_error,'identities':len(frozen),'source':ident(__file__),
            'independent_scope':'same agent, separate scalar and encoded-set implementation','new_GT':0,'new_NSG':0,'new_ANN':0,'default_changed':False}
    with (R/'reviews/independent_audit.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print('ALL AUDITS PASS',result['seconds'],flush=True)

if __name__=='__main__':main()
