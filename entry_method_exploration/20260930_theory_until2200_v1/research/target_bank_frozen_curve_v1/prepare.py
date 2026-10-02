import copy,hashlib,json,shutil,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent; CAMP=R.parents[1]; ROOT=R.parents[3]; PREV=R.parent/'query_target_transfer_v1'
def read(p):return json.loads(Path(p).read_text())
def put(p,x):
    with Path(p).open('x') as f:f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def main():
    assert read(PREV/'decision.json')['status']=='STOP_QUERY_TARGET_TRANSFER_V1'
    for name,v in read(PREV/'reviews/seal.json')['files'].items():assert ident(PREV/name)==v,name
    for n in ['src','inputs','logs','reviews','bin','results']:(R/n).mkdir(exist_ok=True)
    for n in ['base_engine.hpp','kernels.hpp']:shutil.copyfile(PREV/'src'/n,R/'src'/n)
    shutil.copytree(PREV/'src/common',R/'src/common')
    copied={str(p.relative_to(R/'src')):ident(p) for p in (R/'src').rglob('*') if p.is_file()}
    put(R/'reviews/copied_source.json',{'from':str(PREV/'src'),'files':copied})
    state=read(CAMP/'state.json');assert state['active_process'] is None
    with zipfile.ZipFile(R/'reviews/root_docs_before_prepare.zip','x',zipfile.ZIP_DEFLATED) as z:
        for n in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    oldcap=state['campaign_new_bytes_cap'];assert oldcap==1342177280
    newcap=oldcap+80*2**20
    put(R/'resource_amendment.json',{'unix':time.time(),'scope':'before any new search','old_campaign_cap':oldcap,'new_campaign_cap':newcap,'new_stage_cap':80*2**20,'reason':'one fixed adjacent-budget curve for positive TargetBank control; failed QueryTarget unchanged'})
    c=copy.deepcopy(read(PREV/'config.locked.json'));c.update(experiment=R.name,methods=['Default3','DefaultRank1','TargetBank1'],main_candidate='TargetBank1',bootstrap_seed=2026093027,max_stage_bytes=80*2**20,max_campaign_bytes=newcap,expected_NSG=596160,expected_ANN=595584,max_new_NSG=620000,max_new_ANN=620000,compile_seconds_cap=120,search_seconds_cap=1800,deadline_unix=1790771400)
    for k in ['shuffle_seed','build_seed','compile_and_build_seconds_cap']:c.pop(k,None)
    fixed={};large={}
    for ds,d in c['datasets'].items():
        grid={1:[800,1000,1250],100:[1120,1250,1400]} if ds.startswith('web') else {1:[96,128,160],100:[200,256,320]}
        for k in ['query_graph','train_queries','hub_mapping','shuffled_targets','shuffle_rows','train_GT','train_start','build_seed']:d.pop(k,None)
        d.update(root=str(R),methods=c['methods'],points=[{'K':k,'L':l} for k,ls in grid.items() for l in ls],max_search_calls=310000,previous_results=str(PREV/'results'/ds))
        (R/'inputs'/ds).mkdir()
        put(R/'inputs'/ds/'native.json',d)
        for k in ['queries','GT','source_rows','targets','target_graph']:fixed[d[k]]=ident(d[k])
        for k in ['W','ids','graph']:fixed[d['anchor'][k]]=ident(d['anchor'][k])
        for k in ['base','index']:
            s=Path(d[k]).stat();large[d[k]]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
        for p in d['points']:
            old=Path(d['old_results'])/f'k{p["K"]}'/f'{d["anchor"]["name"]}_L{p["L"]}'
            for name in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64']:assert (old/name).exists()
    put(R/'config.locked.json',c);put(R/'reviews/consumed_inputs.json',fixed);put(R/'reviews/large_inputs_stat.json',large)
    put(R/'reviews/input_roles.json',{'role':'historically exposed E105 development only','same_as_165':str(PREV/'reviews/input_roles.json'),'no_new_queries_GT_models_graphs':True,'models_frozen_before_previous_feedback':read(PREV/'reviews/models_frozen.json'),'all_165_seal_files_verified':True})
    state.update(stage='target_bank_frozen_curve_prepared',campaign_new_bytes_cap=newcap,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    put(R/'reviews/prepared.json',{'status':'PASS','unix':time.time(),'free_bytes':shutil.disk_usage(R).free})
    print('PREPARED_FIXED_3_METHOD_36_POINT_CURVE',flush=True)
if __name__=='__main__':main()
