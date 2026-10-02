import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
os.sched_setaffinity(0,{0})
import hashlib,json,shutil,time,zipfile
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]
def read(p):return json.loads(Path(p).read_text())
def put(p,x):
    with Path(p).open('x') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def fvecs(p,d):
    x=np.memmap(p,dtype='<f4',mode='r');assert len(x)%(d+1)==0;x=x.reshape(-1,d+1);assert (x[:,0].view('<i4')==d).all();return x[:,1:]
def total(p):return sum(x.stat().st_size for x in Path(p).rglob('*') if x.is_file())
def main():
    start=time.perf_counter();assert not (R/'config.locked.json').exists();assert read(CAMP/'state.json')['active_process'] is None
    old=ROOT/'entry_method_exploration/20260921_comparison_direction_pilot_v1';copied={}
    for name in ('base_engine.hpp','kernels.hpp'):
        shutil.copy2(old/'src'/name,R/'src'/name);copied[name]=ident(R/'src'/name);assert ident(old/'src'/name)==copied[name]
    shutil.copytree(old/'src/common',R/'src/common')
    for p in (R/'src/common').rglob('*'):
        if p.is_file():rel=str(p.relative_to(R/'src'));copied[rel]=ident(p);assert ident(old/'src'/rel)==copied[rel]
    with zipfile.ZipFile(R/'reviews/root_docs_before_prepare.zip','x',zipfile.ZIP_DEFLATED) as z:
        for n in ('summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'):z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    with zipfile.ZipFile(R/'reviews/root_docs_before_prepare.zip') as z:assert z.testzip() is None
    previous_cap=read(CAMP/'state.json')['campaign_new_bytes_cap'];cap=previous_cap+192*2**20
    put(R/'resource_amendment.json',{'unix':time.time(),'scope':'before any new build or search','old_campaign_cap':previous_cap,'new_campaign_cap':cap,'new_stage_cap':192*2**20,'min_free_bytes':6*2**30,'reason':'bounded full online query-target information probe under user authorization; previous protocols and artifacts unchanged'})
    methods=['Default3','DefaultRank1','QueryTarget1','QueryHub1','TargetBank1','ShuffledQueryTarget1']
    config={'experiment':R.name,'methods':methods,'main_candidate':'QueryTarget1','datasets':{},'bootstrap_reps':10000,'bootstrap_seed':2026093026,'shuffle_seed':2026093026,'build_seed':20260828,'max_new_NSG':420000,'max_new_ANN':420000,'expected_NSG':397440,'expected_ANN':397056,'max_stage_bytes':192*2**20,'max_campaign_bytes':cap,'min_free_bytes':6*2**30,'search_seconds_cap':1800,'compile_and_build_seconds_cap':300,'deadline_unix':1790773200,'maxrss_bytes':32*2**30}
    prior=read(R.parent/'router_rank_pareto_v1/config.locked.json');rng=np.random.default_rng(2026093026);consumed={};large={};reviews={}
    for ds,orig in prior['datasets'].items():
        d=orig['dimension'];dest=R/'inputs'/ds;dest.mkdir();(R/'models'/ds).mkdir()
        prep=read(ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/inputs'/ds/'prepared.json')
        tq=Path(prep['source_train']['query_train']['path']);tg=Path(prep['source_train']['gt_train']['path'])
        assert ident(tq)['sha256']==prep['source_train']['query_train']['sha256'];assert ident(tg)['sha256']==prep['source_train']['gt_train']['sha256']
        train=fvecs(tq,d)[10000:30000];assert train.shape==(20000,d) and np.isfinite(train).all() and (np.linalg.norm(train,axis=1)>0).all()
        gt0=np.memmap(tg,dtype='<i4',mode='r').reshape(-1,101);assert gt0.shape[0]==30000 and (gt0[:,0]==100).all()
        target=np.asarray(gt0[10000:30000,1],dtype='<i4').copy();assert (target>=0).all() and (target<orig['base_n']).all()
        eroot=ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1/inputs'/ds;em=read(eroot/'manifest.json');gm=read(eroot/'gt_manifest.json')
        assert ident(eroot/'queries.f32')['sha256']==em['files']['queries.f32']==gm['query_sha256'];assert ident(eroot/'gt.i32')['sha256']==gm['GT_sha256']
        eq=np.fromfile(eroot/'queries.f32','<f4').reshape(4096,d);assert np.isfinite(eq).all()
        trainhash={hashlib.sha256(np.ascontiguousarray(x).tobytes()).digest() for x in train}
        evalhash={hashlib.sha256(x.tobytes()).digest() for x in eq};assert len(evalhash)==4096 and not trainhash.intersection(evalhash)
        target.tofile(dest/'target_ids.i32');perm=rng.permutation(20000).astype('<i4');perm.tofile(dest/'shuffle_rows.i32');target[perm].tofile(dest/'shuffled_target_ids.i32')
        base=fvecs(orig['base'],d);hids=np.fromfile(orig['hub_ids'],'<i4');assert len(hids)==orig['H'];bh=np.asarray(base[hids],dtype='f8');bh/=np.linalg.norm(bh,axis=1)[:,None]
        x=np.asarray(base[target],dtype='f8');x/=np.linalg.norm(x,axis=1)[:,None];scores=x@bh.T;hmap=hids[np.argmax(scores,axis=1)].astype('<i4');hmap.tofile(dest/'hub_ids.i32')
        del scores,x,bh
        c={k:orig[k] for k in ('dataset','dimension','base_n','base','index','anchor','points','H')}
        c.update(n=4096,threads=1,cpu=15,root=str(R),train_queries=str(tq),train_start=10000,train_n=20000,targets=str(dest/'target_ids.i32'),hub_mapping=str(dest/'hub_ids.i32'),shuffled_targets=str(dest/'shuffled_target_ids.i32'),shuffle_rows=str(dest/'shuffle_rows.i32'),queries=str(eroot/'queries.f32'),GT=str(eroot/'gt.i32'),source_rows=str(eroot/'source_rows.i64'),train_GT=str(tg),old_results=str(ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1/results'/ds),query_graph=str(R/'models'/ds/'query.hnsw'),target_graph=str(R/'models'/ds/'target.hnsw'),methods=methods,build_seed=20260828,M=16,efConstruction=200,ef=10,repeats=3,warm_n=128,max_search_calls=210000,seconds_cap=1800,maxrss_bytes=32*2**30,min_free_bytes=6*2**30)
        for p in c['points']:
            ref=Path(c['old_results'])/f'k{p["K"]}'/f'{c["anchor"]["name"]}_L{p["L"]}'
            for f in ('ids.i32','distances.f32','entry_ids.i32','graph_ndc.u64','route_ndc.u64'):assert (ref/f).is_file()
        put(dest/'native.json',c);config['datasets'][ds]=c
        for p in (tq,tg,eroot/'queries.f32',eroot/'gt.i32',eroot/'source_rows.i64',eroot/'manifest.json',eroot/'gt_manifest.json',Path(orig['anchor']['W']),Path(orig['anchor']['graph']),Path(orig['anchor']['ids'])):consumed[str(p)]=ident(p)
        for p in (orig['base'],orig['index']):
            st=Path(p).stat();large[p]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
        reviews[ds]={'train_n':20000,'train_unique_query_bytes':len(trainhash),'evaluation_n':4096,'overlap_query_bytes':0,'training_source_positions':[10000,30000],'unique_training_targets':int(len(np.unique(target))),'training_targets_in_H':int(np.isin(target,hids).sum()),'H':len(hids),'original_prepared':str(ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/inputs'/ds/'prepared.json'),'eval_original_manifest':str(eroot/'manifest.json'),'large_identity_scope':'original SHA provenance plus current stat and later native embedded-vector checks; no new full base/index hash'}
    put(R/'config.locked.json',config);put(R/'reviews/consumed_inputs.json',consumed);put(R/'reviews/large_inputs_stat.json',large);put(R/'reviews/input_roles.json',reviews);put(R/'reviews/copied_source.json',{'from':str(old),'files':copied})
    state=read(CAMP/'state.json');state['campaign_new_bytes_cap']=cap;state.update(stage='query_target_transfer_prepared',last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    assert total(R)<config['max_stage_bytes'] and total(CAMP)<cap and shutil.disk_usage(R).free>=6*2**30
    put(R/'reviews/prepared.json',{'status':'PASS','seconds':time.perf_counter()-start,'no_new_build_or_search':True,'no_evaluation_GT_used_for_model':True})
    print('PREPARED',reviews,flush=True)
if __name__=='__main__':main()
