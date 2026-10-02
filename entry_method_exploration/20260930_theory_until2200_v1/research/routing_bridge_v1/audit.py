import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits

R=Path(__file__).resolve().parent;P=R.parent/'hybrid_temperature_factorial_v1'
C=json.loads((P/'config.locked.json').read_text());S=json.loads((R/'results/summary.json').read_text())

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    start=time.perf_counter();ranks=certs=groups=0;maxscore=0.
    with (R/'reviews/audit_frozen.json').open('x') as f:json.dump({'source':ident(__file__),'summary':ident(R/'results/summary.json')},f,indent=2)
    with threadpool_limits(8):
      for ds,dc in C['datasets'].items():
        ec=dc['evaluate'];n,d=ec['n'],ec['dimension'];z=np.load(R/'results'/f'{ds}.npz')
        q=np.fromfile(ec['queries'],'<f4').reshape(n,d).astype('f8');q/=np.sqrt(np.sum(q*q,axis=1))[:,None]
        hids=np.fromfile(ec['methods'][0]['ids'],'<i4');gt=np.fromfile(ec['gt'],'<i4').reshape(n,100);M={};W={};scores={}
        selected=np.linspace(0,n-1,32,dtype=int)
        for m in ec['methods']:
            name=m['name'];W[name]=np.fromfile(m['W'],'<f4').reshape(-1,d).astype('f8')
            s=np.einsum('nd,hd->nh',q,W[name],optimize=False);scores[name]=s
            top=np.array([sorted(zip(row,hids),key=lambda x:(-x[0],x[1]))[:4] for row in s[selected]])
            assert np.array_equal(np.sort(top[:,:3,1].astype('i4'),axis=1),z[name+'_exact_top3'][selected])
            assert np.allclose(top[:,2,0]-top[:,3,0],z[name+'_gap3_4'][selected],rtol=1e-9,atol=1e-15);ranks+=len(selected)
            M[name]={}
            for p in ec['points']:
                k=p['K'];path=P/'results'/ds/'evaluation'/f'k{k}'/f'{name}_L{p["L"]}'
                ids=np.fromfile(path/'ids.i32','<i4').reshape(n,k);ent=np.fromfile(path/'entry_ids.i32','<i4').reshape(n,3)
                hits=np.fromiter((len(set(ret)&set(truth[:k])) for ret,truth in zip(ids,gt)),dtype='i4',count=n)
                M[name][k]={'hits':hits,'ids':ids,'entries':ent,'bits':np.fromfile(path/'distances.f32','<u4').reshape(n,k),
                            'ndc':np.fromfile(path/'graph_ndc.u64','<u8')}
                assert np.array_equal(ent,z[name+'_actual_top3'])
        for pair in S['datasets'][ds]['comparisons']:
            c,b=pair['method'],pair['reference'];key=c+'_vs_'+b
            cat=np.array([2*int(set(a)!=set(aa))+int(set(r)!=set(rr)) for a,aa,r,rr in zip(z[c+'_exact_top3'],z[b+'_exact_top3'],z[c+'_actual_top3'],z[b+'_actual_top3'])],dtype='u1')
            assert np.array_equal(cat,z[key+'_category']);assert np.bincount(cat,minlength=4).tolist()==pair['category_counts']
            risk=float(np.mean(np.sum((scores[c]-scores[b])**2,axis=1)));maxscore=max(maxscore,abs(risk-pair['score_risk']))
            assert np.isclose(risk,pair['score_risk'],rtol=1e-10,atol=1e-16)
            dw=W[c]-W[b];eps=np.sqrt(np.einsum('hd,hd->h',dw,dw));lookup={int(h):i for i,h in enumerate(hids)}
            for i in selected:
                inside=[lookup[int(h)] for h in z[b+'_exact_top3'][i]];outside=[h for h in range(len(hids)) if h not in inside]
                for label,radius in [('norm',eps),('posthoc',np.abs(scores[c][i]-scores[b][i]))]:
                    cert=all(scores[b][i,a]-radius[a]>scores[b][i,o]+radius[o] for a in inside for o in outside)
                    assert cert==z[key+'_'+label+'_certificate'][i];certs+=1
            for point in pair['points']:
                k=point['K'];cb=M[c][k];bb=M[b][k];delta=cb['hits']-bb['hits'];same=(cat%2)==0
                assert np.array_equal(delta,z[key+f'_K{k}_delta_hits'])
                for field in ['ids','bits','ndc']:assert np.array_equal(cb[field][same],bb[field][same])
                changed=np.any(cb['ids']!=bb['ids'],axis=1);near=z[c+'_near_float_boundary']|z[b+'_near_float_boundary']
                for g in point['groups']:
                    indices=[i for i in range(n) if cat[i]==g['category'] and (g['numeric_group']=='all' or (bool(near[i])==(g['numeric_group']=='near')))]
                    v=delta[indices];assert len(indices)==g['n'] and sum(changed[indices])==g['output_changes']
                    assert sum(x for x in v if x>0)==g['rescues'] and sum(-x for x in v if x<0)==g['damages'];groups+=1
    toy=json.loads((R/'results/toy.json').read_text());assert toy['calls']==len(toy['results'])==12
    for row in toy['results']:
        x=np.array(row['coordinates'],dtype='f4');L=row['L'];n=L+5;assert len(x)==n
        reachable={0};v=1
        while v!=0:reachable.add(v);v=(v+1)%n
        assert len(reachable)==n
        ip=row['metric']=='negative_ip';q=np.float32(1 if ip else 10)
        dist=lambda i:float(-q*x[i] if ip else (q-x[i])*(q-x[i]))
        assert dist(3)<dist(0) and min(range(n),key=dist)==2
        seen=set();pool=[];trace=[]
        def insert(i):
            if i in seen:return
            seen.add(i);trace.append(i);pool.append((dist(i),i,True));pool.sort();del pool[L:]
        for i in row['entries']:insert(i)
        while any(p[2] for p in pool):
            index=next(i for i,p in enumerate(pool) if p[2]);distance,node,_=pool[index];pool[index]=(distance,node,False)
            insert((node+1)%n)
        assert pool[0][1]==row['returned_id'] and trace==row['evaluated_ids']
        assert (row['returned_id']==2)==row['expected_hit']==row['actual_hit']
    frozen=json.loads((R/'reviews/frozen.json').read_text())['inputs']
    for p,v in frozen.items():assert ident(p)==v
    f=json.loads((R/'reviews/toy_frozen.json').read_text());assert ident(R/'toy.cpp')['sha256']==f['source_sha256']
    report={'status':'PASS','exact_ranking_queries':ranks,'independent_certificates':certs,'group_cells':groups,'max_score_risk_error':maxscore,
       'all_queries_hit_counts_recomputed':True,'same_entry_return_bits_and_ndc':True,'toy_native_vs_python_calls':12,
       'source_input_identities':len(frozen),'seconds':time.perf_counter()-start,'independence':'separate formulas and scalar sorting by same agent'}
    with (R/'reviews/independent_audit.json').open('x') as out:json.dump(report,out,indent=2)
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
