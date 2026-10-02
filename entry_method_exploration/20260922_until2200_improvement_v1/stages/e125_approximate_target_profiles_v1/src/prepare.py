import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import json,hashlib,shutil,difflib,datetime
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];P=R.parent.parent;ROOT=P.parents[1];OLD=ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1';E118=ROOT/'entry_method_exploration/20260921_comparison_direction_pilot_v1';C=json.loads((P/'stages/e124_semantic_service_ridge_v1/config.locked.json').read_text());I={}
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):assert not p.exists(),p;p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
for name in ['reviews','logs','bin','models','results','inputs']:(R/name).mkdir(exist_ok=True)
dump(R/'reviews/prepare_frozen.json',{'files':{str(p):ident(p) for p in [R/'protocol.md',R/'theory.md',Path(__file__)]}})
shutil.copytree(OLD/'src/common',R/'src/common');shutil.copy2(OLD/'src/kernels.hpp',R/'src/kernels.hpp');shutil.copy2(E118/'src/base_engine.hpp',R/'src/base_engine.hpp')
for p in list((OLD/'src/common').rglob('*'))+[OLD/'src/kernels.hpp',OLD/'src/evaluate.cpp',E118/'src/base_engine.hpp']:
    if p.is_file():I[str(p)]=ident(p)
src=(OLD/'src/evaluate.cpp').read_text();new=src.replace('names[1]=="WFree"','names[1]=="ApproxTarget10"').replace('if(m==1||c.value("normalize_anchor",false))','if(c.value("normalize_anchor",false))')
needle='   write_json(out/key(m)/"complete.json",'
extra='''   if(m==0){auto old=fs::path(c["baseline_reference"].get<std::string>())/key(m);require(b.ids==read_raw<int32_t>(old/"ids.i32")&&b.entries==read_raw<int32_t>(old/"entry_ids.i32"),"all old baseline ids/entries");auto od=read_raw<float>(old/"distances.f32");require(od.size()==b.dist.size()&&!memcmp(od.data(),b.dist.data(),od.size()*4),"all old baseline distance bits");require(b.graph_ndc==read_raw<uint64_t>(old/"graph_ndc.u64")&&b.route_ndc==read_raw<uint64_t>(old/"route_ndc.u64"),"all old baseline NDC");}
   std::vector<acsg::Neighbor> legacy;legacy.reserve(1501);idx->acsg.search_L=L;std::array<float,100>sd;std::array<faiss::idx_t,100>si;
   for(size_t i=0;i<16;++i){ep.clear();for(int j=0;j<3;++j)ep.emplace_back(b.entries[i*3+j],1);vt.advance();counter.set_query(q.data()+i*d);idx->acsg.search_new(counter,K,si.data(),sd.data(),vt,2,ep,&legacy);for(int j=0;j<K;++j)require(si[j]==b.ids[i*K+j]&&!memcmp(&sd[j],&b.dist[i*K+j],4),"linked E99 actual return bits");require(counter.count==b.graph_ndc[i],"linked E99 NDC");++calls;}
'''
assert src.count(needle)==1;new=new.replace(needle,extra+needle).replace('calls==n*2*c["points"].size()*(reps+2)','calls==(n*2*(reps+2)+32)*c["points"].size()')
(R/'src/evaluate.cpp').write_text(new);(R/'reviews/evaluator.diff').write_text(''.join(difflib.unified_diff(src.splitlines(True),new.splitlines(True),fromfile=str(OLD/'src/evaluate.cpp'),tofile='E125/evaluate.cpp')))
deadline=datetime.datetime.fromisoformat('2026-09-22T13:30:00+00:00').timestamp();settings={};rolecheck={}
for i,(ds,dc) in enumerate(C['datasets'].items()):
    d=dc['dimension'];ip=OLD/'inputs'/ds;mp=R/'models'/ds;mp.mkdir();op=R/'inputs'/ds;op.mkdir();points=[{'K':k,'L':L} for k,ls in ([(1,[800,1000,1250]),(100,[1120,1250,1400])] if ds.startswith('web') else [(1,[96,128,160]),(100,[200,256,320])])]
    queries=Path(dc['fit_source']['queries_file']);evalq=ip/'queries.f32';fit=np.fromfile(queries,'<f4').reshape(20000,d);eq=np.fromfile(evalq,'<f4').reshape(4096,d);overlap=len(set(map(bytes,fit))&set(map(bytes,eq)));assert overlap==0
    rolecheck[ds]={'fit_rows':20000,'evaluation_rows':4096,'query_byte_overlap':overlap,'evaluation_historically_exposed':True}
    for p in [queries,Path(dc['fit_source']['gt_file']),evalq,ip/'gt.i32',ip/'source_rows.i64',Path(dc['anchor']['W']),Path(dc['anchor']['ids']),Path(dc['anchor']['graph']),ip/'manifest.json',ip/'gt_manifest.json']:
        I[str(p)]=ident(p)
    for point in points:
        old=OLD/'results'/ds/f'k{point["K"]}'/f'{dc["anchor"]["name"]}_L{point["L"]}'
        for p in old.iterdir():
            if p.is_file():I[str(p)]=ident(p)
    cand={'name':'ApproxTarget10','ids':dc['anchor']['ids'],'W':str(mp/'W.f32'),'graph':str(mp/'router.hnsw')}
    label={k:dc[k] for k in ['base','base_n','dimension','index','anchor']};label.update(n=20000,queries=str(queries),L=1250 if ds.startswith('web') else 256,deadline_unix=deadline)
    evaluate={k:dc[k] for k in ['base','base_n','dimension','index']};evaluate.update(dataset=ds,n=4096,queries=str(evalq),gt=str(ip/'gt.i32'),formal=False,threads=1,repeats=3,normalize_anchor=False,dataset_order=i,points=points,methods=[dc['anchor'],cand],baseline_reference=str(OLD/'results'/ds),max_search_calls=260000,seconds_cap=2700)
    dump(op/'labels.json',label);dump(op/'evaluate.json',evaluate);settings[ds]={'original':dc,'labels':label,'evaluate':evaluate,'candidate':cand,'primary_L':{'1':1000 if ds.startswith('web') else 128,'100':1250 if ds.startswith('web') else 256}}
for p,v in I.items():assert ident(Path(p))==v,p
dump(R/'config.locked.json',{'experiment':'E125','datasets':settings,'deadline_unix':deadline,'bootstrap_seed':2026092229,'bootstrap_reps':20000,'max_new_NSG':550000,'candidate':'ApproxTarget10','gate':{'label_process_vs_exact20k_search_max_ratio':.5,'all_point_mean_delta_recall_min_pp':-.1,'primary_98_75_lower_min_pp':-.25,'all_point_QPS_ratio_min':.97},'new_source_payloads':0,'heldout':False})
dump(R/'reviews/prepare_inputs.json',I);dump(R/'reviews/roles.json',rolecheck);dump(R/'reviews/prepare_complete.json',{'status':'PASS','protected_files':len(I),'new_searches':0,'new_fits':0})
print('PASS',len(I))
