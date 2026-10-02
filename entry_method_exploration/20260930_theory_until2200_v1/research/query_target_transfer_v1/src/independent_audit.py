import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import hashlib,json,math,struct,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];C=json.loads((R/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
    with Path(p).open('x') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def fv(p,d):
    a=np.memmap(p,dtype='<f4',mode='r').reshape(-1,d+1);assert np.all(a[:,0].view('<i4')==d);return a[:,1:]
def parse_graph(path,d,n):
    blob=Path(path).read_bytes();fmt='<6QiI3QdQ';header=struct.unpack_from(fmt,blob);off0,cap,count,stride,labeloff,dataoff,maxlevel,entry,maxm,maxm0,m,mult,efc=header;pos=struct.calcsize(fmt)
    assert (off0,cap,count,maxm,maxm0,m,efc)==(0,n,n,16,32,16,200) and 0<=entry<n and maxlevel>=0
    assert dataoff==4+32*4 and labeloff==dataoff+d*4 and stride==labeloff+8
    vectors=np.ndarray((n,d),dtype='<f4',buffer=blob,offset=pos+dataoff,strides=(stride,4)).copy();labels=np.ndarray((n,),dtype='<u8',buffer=blob,offset=pos+labeloff,strides=(stride,)).copy();assert np.array_equal(labels,np.arange(n))
    edges=[];levels=np.zeros(n,dtype='i4')
    for i in range(n):
        deg=struct.unpack_from('<I',blob,pos+i*stride)[0];assert 0<=deg<=32
        nb=struct.unpack_from('<'+str(deg)+'I',blob,pos+i*stride+4);assert all(0<=j<n and j!=i for j in nb) and len(set(nb))==deg;edges.append((i,0,nb))
    pos+=n*stride
    for i in range(n):
        size=struct.unpack_from('<I',blob,pos)[0];pos+=4;assert size%68==0;levels[i]=size//68
        for l in range(levels[i]):
            deg=struct.unpack_from('<I',blob,pos+l*68)[0];assert 0<=deg<=16;nb=struct.unpack_from('<'+str(deg)+'I',blob,pos+l*68+4);assert all(0<=j<n and j!=i for j in nb) and len(set(nb))==deg;edges.append((i,l+1,nb))
        pos+=size
    assert pos==len(blob) and levels.max()==maxlevel and levels[entry]==maxlevel
    assert all(all(levels[j]>=l for j in nb) for i,l,nb in edges)
    return vectors,{'nodes':n,'directed_edges':sum(len(nb) for _,_,nb in edges),'maxlevel':int(maxlevel),'entry':int(entry),'all_labels_and_neighbor_levels_valid':True}
def main():
    start=time.perf_counter();jobs=read(R/'reviews/jobs_complete.json');assert jobs['status']=='PASS' and jobs['new_NSG']==397440 and jobs['new_ANN']==397056 and jobs['new_graphs']==4
    for j in jobs['jobs']:assert j['exit_code']==0 and j['max_threads']==1 and j['stopped'] is None and j['max_observed_rss']<=C['maxrss_bytes']
    for doc in ('run_frozen.json','models_frozen.json'):
        for p,v in read(R/'reviews'/doc)['files'].items():assert ident(p)==v,p
    for p,v in read(R/'reviews/consumed_inputs.json').items():assert ident(p)==v,p
    for p,v in read(R/'reviews/large_inputs_stat.json').items():
        st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
    analysis=read(R/'results/analysis.json');rng=np.random.default_rng(C['bootstrap_seed']);srng=np.random.default_rng(C['shuffle_seed']);audit={};max_ci_error=0.;return_rows=0
    for ds,c in C['datasets'].items():
        n,d=c['n'],c['dimension'];root=R/'results'/ds;ar=analysis['datasets'][ds];target=np.fromfile(c['targets'],'<i4');train=fv(c['train_queries'],d)[10000:30000];base=fv(c['base'],d);q=np.fromfile(c['queries'],'<f4').reshape(n,d)
        tg=np.memmap(c['train_GT'],dtype='<i4',mode='r').reshape(30000,101);assert np.all(tg[:,0]==100) and np.array_equal(target,tg[10000:30000,1]);perm=srng.permutation(20000);assert np.array_equal(perm,np.fromfile(c['shuffle_rows'],'<i4'));assert np.array_equal(target[perm],np.fromfile(c['shuffled_targets'],'<i4'))
        trainhash={hashlib.sha256(x.tobytes()).digest() for x in train};assert not trainhash.intersection(hashlib.sha256(x.tobytes()).digest() for x in q)
        qv,qmeta=parse_graph(c['query_graph'],d,20000);tv,tmeta=parse_graph(c['target_graph'],d,20000);assert np.array_equal(tv.view('u4'),np.asarray(base[target]).view('u4'))
        max_norm_error=0.
        for lo in range(0,20000,512):
            original=np.asarray(train[lo:lo+512],dtype='f8');norm=np.sqrt(np.sum(original*original,axis=1));expected=original/norm[:,None];err=float(np.max(np.abs(qv[lo:lo+512].astype('f8')-expected)));max_norm_error=max(max_norm_error,err);assert err<4e-8
        hids=np.fromfile(c['anchor']['ids'],'<i4');hubmap=np.fromfile(c['hub_mapping'],'<i4');hv=np.asarray(base[hids],dtype='f8');hnorm=np.linalg.norm(hv,axis=1);mapping_ambiguous=0
        for lo in range(0,20000,256):
            v=np.asarray(base[target[lo:lo+256]],dtype='f8');score=(v@hv.T)/np.linalg.norm(v,axis=1)[:,None]/hnorm[None,:];best=score.argmax(1);chosen=np.array([int(np.flatnonzero(hids==x)[0]) for x in hubmap[lo:lo+len(v)]])
            for i in np.flatnonzero(chosen!=best):
                assert abs(score[i,chosen[i]]-score[i,best[i]])<1e-12;direct=(hv/hnorm[:,None])@(v[i]/np.linalg.norm(v[i]));assert int(np.argmax(direct))==int(chosen[i]);mapping_ambiguous+=1
        gt=np.fromfile(c['GT'],'<i4').reshape(n,100);hits=np.zeros((n,6,2),dtype='i8');hitsets={};entries={};slots={};walls=read(root/'timings.json');qpss={}
        for ki,pt in enumerate(c['points']):
            K,L=pt['K'],pt['L'];ap=ar['points'][str(K)];point=root/f'k{K}_L{L}';assert read(point/'complete.json')['status']=='PASS';gtlookup=[{int(v):True for v in row[:K]} for row in gt];hitsets[ki]={};qpss[ki]={}
            for mi,name in enumerate(C['methods']):
                loc=point/name;ids=np.fromfile(loc/'ids.i32','<i4').reshape(n,K);dist=np.fromfile(loc/'distances.f32','<f4').reshape(n,K);assert np.isfinite(dist).all();valid=[]
                for i in range(n):
                    assert len(set(map(int,ids[i])))==K;row={int(v) for v in ids[i] if int(v) in gtlookup[i]};valid.append(row);hits[i,mi,ki]=len(row)
                hitsets[ki][name]=valid;return_rows+=n;ent=np.fromfile(loc/'entry_ids.i32','<i4').reshape(n,3);s=np.fromfile(loc/'route_slots.i32','<i4');assert len(s)==n
                if ki==0:entries[name]=ent;slots[name]=s
                else:assert np.array_equal(ent,entries[name]) and np.array_equal(s,slots[name])
                if mi<2:assert np.all(s==-1)
                else:
                    assert np.all((s>=0)&(s<20000));mapping=hubmap if mi==3 else target[perm] if mi==5 else target;assert np.array_equal(ent[:,0],mapping[s]) and np.all(ent[:,1:]==-1)
                if mi==0:
                    old=Path(c['old_results'])/f'k{K}'/f'{c["anchor"]["name"]}_L{L}'
                    for file in ('ids.i32','distances.f32','entry_ids.i32','graph_ndc.u64','route_ndc.u64'):assert (loc/file).read_bytes()==(old/file).read_bytes()
                secs=[x['seconds'] for x in sorted([x for x in walls if x['K']==K and x['method']==name],key=lambda x:x['repeat'])];assert len(secs)==3;pool=3*n/math.fsum(secs);qpss[ki][name]=pool;recall=sum(map(len,valid))*100/(n*K);m=ap['methods'][name];assert abs(recall-m['recall_pct'])<1e-12 and m['total_hits']==sum(map(len,valid)) and abs(pool-m['qps_pooled'])<1e-9
                for field in ('graph_ndc','route_ndc'):
                    counts=np.fromfile(loc/(field+'.u64'),'<u8');assert len(counts)==n and np.all(counts>0);assert abs(sum(map(int,counts))/n-m[field+'_mean'])<1e-12
            default=hitsets[ki]['Default3']
            for mi,name in enumerate(C['methods']):
                sets=hitsets[ki][name];added=sum(len(a-b) for a,b in zip(sets,default));lost=sum(len(b-a) for a,b in zip(sets,default));m=ap['methods'][name];diff=hits[:,mi,ki]-hits[:,0,ki]
                assert (added,lost)==(m['true_member_added'],m['true_member_lost']) and added-lost==diff.sum();assert m['rescued_queries']==sum(int(x>0) for x in diff) and m['damaged_queries']==sum(int(x<0) for x in diff)
            for name,m in ap['main_vs_controls'].items():
                mi=C['methods'].index(name);diff=hits[:,2,ki]-hits[:,mi,ki];assert abs(diff.sum()*100/(n*K)-m['main_minus_control_recall_pp'])<1e-12
                assert m['true_member_added']==sum(len(a-b) for a,b in zip(hitsets[ki]['QueryTarget1'],hitsets[ki][name])) and m['true_member_lost']==sum(len(b-a) for a,b in zip(hitsets[ki]['QueryTarget1'],hitsets[ki][name]))
                assert abs((qpss[ki]['QueryTarget1']/qpss[ki][name]-1)*100-m['main_relative_QPS_pct'])<1e-10
        assert np.array_equal(hits,np.load(root/'score_arrays.npz')['hits']);assert np.array_equal(slots['QueryTarget1'],slots['QueryHub1']) and np.array_equal(slots['QueryTarget1'],slots['ShuffledQueryTarget1'])
        assert all(int(x) in row for x,row in zip(entries['DefaultRank1'][:,0],entries['Default3']))
        w=np.fromfile(c['anchor']['W'],'<f4').reshape(c['H'],d);hpos={int(x):i for i,x in enumerate(hids)}
        for i in range(n):
            e=entries['Default3'][i];score=np.asarray(w[[hpos[int(x)] for x in e]],dtype='f8')@q[i].astype('f8');chosen=int(np.flatnonzero(e==entries['DefaultRank1'][i,0])[0]);assert score.max()-score[chosen]<2e-6
        integer_delta=(hits-hits[:,:1,:]).reshape(n,12);boot=np.empty((C['bootstrap_reps'],12),dtype='i8')
        for lo in range(0,len(boot),128):
            m=min(128,len(boot)-lo);ix=rng.integers(0,n,size=(m,n))
            for j in range(m):boot[lo+j]=np.bincount(ix[j],minlength=n).astype('i8')@integer_delta
        boot=boot.reshape(-1,6,2)
        for ki,pt in enumerate(c['points']):
            K=pt['K'];ap=ar['points'][str(K)]
            for mi,name in enumerate(C['methods']):
                ci=np.quantile(boot[:,mi,ki],[.025,.975])*100/(n*K);want=ap['methods'][name]['delta_recall_95pct_descriptive_interval_pp'];err=float(np.max(np.abs(ci-want)));max_ci_error=max(max_ci_error,err);assert err<1e-11
                if mi!=2:
                    ci=np.quantile(boot[:,2,ki]-boot[:,mi,ki],[.025,.975])*100/(n*K);err=float(np.max(np.abs(ci-ap['main_vs_controls'][name]['interval_pp'])));max_ci_error=max(max_ci_error,err);assert err<1e-11
        audit[ds]={'all_return_rows_independently_scored':n*12,'train_GT1_and_permutation':True,'all_20000_hub_mappings_checked':True,'floating_near_ties_rechecked':mapping_ambiguous,'query_graph':qmeta,'target_graph':tmeta,'max_query_normalization_abs_error':max_norm_error,'all_native_graph_vectors_bit_checked':True,'all_Default3_historical_fields_equal':True,'same_query_slots_across_controls_and_K':True,'bootstrap_integer_weight_reimplementation':True}
    put(R/'reviews/independent_audit.json',{'status':'PASS','datasets':audit,'complete_return_rows':return_rows,'max_bootstrap_interval_abs_error_pp':max_ci_error,'all_sources_inputs_models_unchanged':True,'independence_scope':'same agent separate parser and arithmetic; not independent personnel; original GT source provenance reused','seconds':time.perf_counter()-start});print('INDEPENDENT_AUDIT_PASS',return_rows,max_ci_error,flush=True)
if __name__=='__main__':main()
