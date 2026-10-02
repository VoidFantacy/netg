import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import hashlib,json,shutil,time,zipfile
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3]
E118=ROOT/'entry_method_exploration/20260921_comparison_direction_pilot_v1'
E117=ROOT/'entry_method_exploration/20260920_entry_set_pilot_v1'
E121=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e121_router_state_table_v1'
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
    with Path(p).open('x') as f:f.write(v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def size(p):return sum(q.stat().st_size for q in p.rglob('*') if q.is_file())
def main():
    assert not (R/'config.locked.json').exists()
    assert shutil.disk_usage(R).free>=6*2**30
    names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
    before={n:(ROOT/n).read_text() for n in names}
    with zipfile.ZipFile(R/'root_docs_before_prepare.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(ROOT/n,n)
        z.write(CAMP/'state.json','campaign_state.json')
    with zipfile.ZipFile(R/'root_docs_before_prepare.zip') as z:
        for n in names:assert z.read(n)==(ROOT/n).read_bytes()
    put(R/'resource_amendment.json',{'unix':time.time(),'reason':'User priority is complete online Recall/QPS; preserve existing artifacts and add one frozen rank/state experiment.',
        'original_campaign_bytes_cap':2**30,'new_campaign_bytes_cap':2**30+64*2**20,'this_stage_bytes_cap':64*2**20,
        'campaign_current_bytes':size(CAMP),'minimum_free_bytes':6*2**30,'old_protocols_unchanged':True,'user_imposed_limit':False,
        'new_NSG_cap':620000,'new_ANN_cap':680000,'new_GT_profiles_graphs':0,'search_job_seconds_cap_total':1800})
    for name in ('src','bin','inputs','models','results','reviews','logs'):(R/name).mkdir()
    shutil.copytree(E118/'src/common',R/'src/common')
    for name in ('base_engine.hpp','kernels.hpp'):shutil.copy2(E118/'src'/name,R/'src'/name)
    original=(E118/'src/common/hnswlib/hnswalg.h').read_text()
    observed=(E121/'src/hnswlib/hnswalg.h').read_text()
    marker='    std::priority_queue<std::pair<dist_t, labeltype >>\n'
    lo=observed.rfind(marker,0,observed.index('    searchKnnObserved('))
    hi=observed.rfind(marker,0,observed.index('    searchKnn(const void'))
    assert observed[:lo]+observed[hi:]==original,'Only observed method is added'
    shutil.copy2(E121/'src/hnswlib/hnswalg.h',R/'src/common/hnswlib/hnswalg.h')
    sources={str(p):ident(p) for p in [E118/'src/base_engine.hpp',E118/'src/kernels.hpp',E121/'src/hnswlib/hnswalg.h']}
    inputs={};big={};datasets={};checks={}
    for ds in read(E121/'config.locked.json')['datasets']:
        e18=E118/'inputs'/ds/'fit';e17=E117/'inputs'/ds/'fit'
        c=read(e18/'config.json');d=c['dimension'];n=c['n'];assert n==4096
        q=np.fromfile(c['queries'],'<f4').reshape(n,d);gt=np.fromfile(c['gt'],'<i8').reshape(n,100)
        rows=np.fromfile(e18/'row_ids.i64','<i8');q17=np.fromfile(e17/'queries.f32','<f4').reshape(10000,d)
        gt17=np.fromfile(e17/'gt.i64','<i8').reshape(10000,100);rows17=np.fromfile(e17/'row_ids.i64','<i8')
        assert np.array_equal(rows,rows17[2048:6144]) and np.array_equal(q.view('u4'),q17[2048:6144].view('u4')) and np.array_equal(gt,gt17[2048:6144])
        raw=E117/'results'/ds/'labels';ranked=np.fromfile(raw/'ranked_entries.i32','<i4').reshape(10000,3)[2048:6144]
        features=np.fromfile(raw/'features.f64','<f8').reshape(10000,6)[2048:6144]
        scores=np.fromfile(raw/'profile_scores.f32','<f4').reshape(10000,3)[2048:6144]
        reference=np.fromfile(E121/'results'/ds/'entries.i32','<i4').reshape(n,3)
        states=np.fromfile(E121/'results'/ds/'upper_states.i32','<i4');hubs=np.fromfile(c['anchor']['ids'],'<i4')
        assert np.array_equal(np.sort(ranked,axis=1),reference) and np.isfinite(features).all() and np.isfinite(scores).all()
        assert np.isin(ranked,hubs).all() and len(states)==n and len(np.unique(hubs))==len(hubs)
        roles=np.load(E121/'models'/ds/'roles.npz');folds=roles['folds'];assert np.bincount(folds).tolist()==[1024]*4
        for f in range(4):
            train=np.flatnonzero(folds!=f);outer=np.flatnonzero(folds==f)
            assert set(roles['train_shuffle'][f])==set(train) and set(roles['outer_shuffle'][f])==set(outer)
        inp=R/'inputs'/ds;inp.mkdir();(R/'models'/ds).mkdir()
        for name,a,dt in [('ranked_entries.i32',ranked,'<i4'),('features.f64',features,'<f8'),('profile_scores.f32',scores,'<f4'),('folds.i32',folds,'<i4')]:np.asarray(a,dtype=dt).tofile(inp/name)
        c.update({'n':n,'threads':1,'cpu':15,'ranked_reference':str(inp/'ranked_entries.i32'),'feature_reference':str(inp/'features.f64'),
                  'profile_reference':str(inp/'profile_scores.f32'),'state_reference':str(E121/'results'/ds/'upper_states.i32'),
                  'canonical_reference':str(E121/'results'/ds/'entries.i32'),'folds':str(inp/'folds.i32'),
                  'old_roles':str(E121/'models'/ds/'roles.npz'),'old_labels_root':str(E118/'results'/ds/'labels'),
                  'points':[{'K':1,'L':1000 if ds.startswith('web') else 128},{'K':100,'L':1250 if ds.startswith('web') else 256}],
                  'repeats':3,'warm_n':128,'label_block':128,'max_search_calls':310000,'seconds_cap':1800,'root':str(R),
                  'min_free_bytes':6*2**30,'maxrss_bytes':32*2**30,'H':len(hubs)})
        datasets[ds]=c;put(inp/'native.json',c)
        consumed=[e18/'config.json',e18/'identity.json',e18/'queries.f32',e18/'gt.i64',e18/'row_ids.i64',
                  e17/'config.json',e17/'queries.f32',e17/'gt.i64',e17/'row_ids.i64',raw/'ranked_entries.i32',raw/'features.f64',raw/'profile_scores.f32',
                  E121/'results'/ds/'upper_states.i32',E121/'results'/ds/'entries.i32',E121/'models'/ds/'roles.npz',
                  *[Path(c['anchor'][k]) for k in ('W','graph','ids')]]
        for p in consumed:inputs[str(p)]=ident(p)
        for k in ('base','index'):
            p=Path(c[k]);s=p.stat();big[str(p)]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
        checks[ds]={'query_GT_row_bit_alignment':True,'rank_membership_E121_exact':True,'source_positions':[2048,6144],
                    'n':n,'states':len(np.unique(states)),'old_rank_query_rows':10000,'folds':[1024]*4,
                    'new_response_values_read':False,'historical_exposure':True,'heldout':False}
    put(R/'config.locked.json',{'experiment':'router_rank_pareto_v1','datasets':datasets,'N':4096,'folds':4,'models':['StatePareto','GlobalPareto','ShufflePareto','FeaturePareto'],
        'methods':['Default','ForcedDefault','StatePareto','GlobalPareto','ShufflePareto','FeaturePareto'],'training_rule':'min_full_query_time_subject_to_integer_recall_delta_ge_0_and_strict_time_saving_per_cell',
        'tree_depth':2,'min_leaf':512,'split_quantiles':[i/10 for i in range(1,10)],'bootstrap_seed':2026093025,'bootstrap_reps':10000,
        'max_new_NSG':620000,'max_new_ANN':680000,'max_stage_bytes':64*2**20,'max_campaign_bytes':2**30+64*2**20,
        'min_free_bytes':6*2**30,'search_job_seconds_cap_total':1800,'deadline_unix':1790771400,
        'new_source_access':False,'default_change_allowed':False,'labels_are_instrumented_proxy_not_QPS':True})
    put(R/'reviews/source_provenance.json',sources);put(R/'reviews/consumed_inputs.json',inputs)
    put(R/'reviews/large_inputs_stat.json',{'stat_only':big,'not_full_rehash':True,'native_embedded_vector_byte_check_n':16})
    put(R/'reviews/cache_inventory.json',{'status':'PASS_INPUT_ALIGNMENT','datasets':checks,'missing':'Matched 4096-query four-action target-budget complete response/time; existing 256 subset is insufficient.',
        'E121_action_family':'default dynamic3 or one static real hub in full H','this_action_family':'default dynamic3 or this query actual rank1/rank2/rank3',
        'old_shuffle_outer_not_used':True,'new_NSG':0,'new_ANN':0,'new_GT':0})
    put(R/'reviews/prepared.json',{'status':'PASS','unix':time.time(),'campaign_bytes':size(CAMP),'stage_bytes':size(R),'no_new_responses_or_fits':True})
    target=before['s-target.md'].replace('当前只审查原协议、完整缓存键与在线费用；不重跑旧runner、扩大候选/深度/阈值或追加测试直到通过。',
        '缓存审计后已冻结[状态到相对rank的目标预算证伪](entry_method_exploration/20260930_theory_until2200_v1/research/router_rank_pareto_v1/protocol.md)：两集各4096历史query、四动作、原四折，经验召回约束下选更快动作，与固定/训练状态置换/原六特征浅树同监督比较，并对所有冻结规则测真实完整wall。当前处于准备阶段，尚无新结果。不扩动作/深度/状态/阈值或追加测试直到通过。',1)
    target=target.replace('当前全日1GiB新增/空余6GiB预算继续检查','为本次在线目标小验证，执行前将全日自定新增上限由1GiB增加64MiB（原阶段协议保持），空余6GiB预算继续检查',1)
    (ROOT/'s-target.md').write_text(target)
    s=before['summary.md'];title='# ACSG 当前结果摘要\n\n';assert title in s
    (ROOT/'summary.md').write_text(s.replace(title,title+'已准备[状态/rank目标预算证伪](entry_method_exploration/20260930_theory_until2200_v1/research/router_rank_pareto_v1/protocol.md)，检验原路由状态对查询相对入口动作的增量及完整费用；尚未运行搜索或拟合，无新性能结论。\n\n',1))
    state=read(CAMP/'state.json');state.update(stage='router_rank_pareto_prepared',active_process=None,last_updated_unix=time.time(),campaign_new_bytes_cap=2**30+64*2**20)
    (CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    assert size(CAMP)<2**30+64*2**20 and size(R)<64*2**20
    print(json.dumps({'status':'PREPARED','checks':checks,'stage_bytes':size(R),'campaign_bytes':size(CAMP)},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
