from common import *
import shutil,subprocess,datetime

storage=Path('/root/acsg-e194-storage')
assert not (R/'selection_freeze.json').exists(),'input preparation already frozen'
storage.mkdir(exist_ok=True)
if not (R/'storage').exists():(R/'storage').symlink_to(storage,target_is_directory=True)
for sub in ['inputs','results','qualification']:(storage/sub).mkdir(exist_ok=True)
for sub in ['source_before','configs','reviews','analysis']:(R/sub).mkdir(exist_ok=True)
root_names=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md']
for name in root_names:
    if not (R/'source_before'/name).exists():shutil.copy2(REPO/name,R/'source_before'/name)
shutil.copy2(REPO/'experiment_history/README.md',R/'source_before/experiment_history_README.md')

prev=R.parent/'20261029_adaptive_completion_gate_v1'
seal=read(prev/'delivery_manifest.json');bridges=[];failures=[]
for a in seal['files']:
    p=Path(a['path'])
    if p.is_file() and p.stat().st_size==a['bytes'] and sha(p)==a['sha256']:continue
    candidates=[REPO/'experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/source_before'/p.relative_to(REPO)]
    match=next((x for x in candidates if x.is_file() and sha(x)==a['sha256']),None)
    if (p.parent==REPO or p==REPO/'experiment_history/README.md') and match:bridges.append(dict(old=a,snapshot=str(match),current=ident(p)))
    else:failures.append(str(p))
receipt=R/'reviews/E193_seal_before.json'
if receipt.exists():shutil.copy2(receipt,R/'reviews/E193_seal_before.attempt1.json')
dump(receipt,dict(status='PASS_SCIENTIFIC_FILES_AND_ROOT_SNAPSHOT_BRIDGES' if not failures else 'FAIL',files=len(seal['files']),root_bridges=bridges,failures=failures))
assert not failures,failures

assets=[];input_roles=[]
for ds in DS:
    c=read(OLD/f'configs/{ds}.json');s=storage/'inputs'/ds;s.mkdir()
    public_ids=np.sort(np.random.default_rng(19420261030).choice(c['queries']['n'],2048,replace=False)).astype('<i4')
    public=np.asarray(view(c['queries'])[public_ids],dtype='<f4');public.tofile(s/'public.f32')
    np.asarray(gt(c['test_gt'])[public_ids],dtype='<i4').tofile(s/'public.gt.i32');public_ids.tofile(s/'public_source_rows.i32')
    excluded=set()
    def exclude(q):
        for row in q:excluded.add(hashlib.sha256(np.asarray(row,dtype='<f4').tobytes()).digest())
    exclude(view(c['queries']));exclude(view(c['train_queries']))
    rng=np.random.default_rng(19420261031)
    if ds=='coco':
        origin=R.parent/'20261016_m5_multimodal_transfer_v1/inputs/coco'
        records=[json.loads(x) for x in (origin/'prepared/row_assignment.jsonl').open()]
        eligible=[x['original_row'] for x in records if x['query_decision']=='unused_unique_query_candidate' and x['group_query_role'] is None]
        for role in ['qgt','profile','residual','test']:
            exclude(np.memmap(origin/f'prepared/{role}.f32','<f4','r').reshape(-1,512))
        text=np.load(origin/'text.npy',mmap_mode='r');selected=[];rows=[]
        for ix in rng.permutation(eligible):
            q=np.asarray(text[ix],dtype='<f4');h=hashlib.sha256(q.tobytes()).digest()
            if h in excluded:continue
            excluded.add(h);selected.append(int(ix));rows.append(q)
            if len(rows)==2048:break
        source=dict(path=str(origin/'text.npy'),format='npy',role='unused_identity_groups',assignment=ident(origin/'prepared/row_assignment.jsonl'))
    else:
        folder=REPO/'benches/datasets/WebVid2.5M_light_v1'
        for name in ['query.aco_train.seed20260826.fvecs','query.router_train.seed20260826.fvecs','query.validation.seed20260826.fvecs']:
            p=folder/name;exclude(view(dict(path=str(p),format='fvecs',n=p.stat().st_size//(513*4),d=512)))
        for role in ['fit','cal','audit','validation','recovery']:
            p=R.parent/f'20260910_gt_topk_profiles_v1/inputs/{ds}/{role}/queries.f32'
            if p.exists():exclude(np.memmap(p,'<f4','r').reshape(-1,512))
        p=folder/'source/webvid.query.train.2.5M.fbin';header=np.fromfile(p,'<i4',count=2);assert header[1]==512
        sourceq=np.memmap(p,'<f4','r',offset=8,shape=tuple(header));selected=[];rows=[]
        for ix in rng.permutation(int(header[0])):
            q=np.asarray(sourceq[ix],dtype='<f4');h=hashlib.sha256(q.tobytes()).digest()
            if h in excluded:continue
            excluded.add(h);selected.append(int(ix));rows.append(q.copy())
            if len(rows)==2048:break
        source=dict(path=str(p),format='fbin',role='new_sample_excluded_registered_roles',source_stat=ident(p,False),historical_global_nonexposure_proven=False)
    assert len(rows)==2048
    conf=np.asarray(rows,dtype='<f4');assert np.isfinite(conf).all();conf.tofile(s/'confirmation.f32');np.asarray(selected,dtype='<i4').tofile(s/'confirmation_source_rows.i32')
    dump(s/'roles.json',dict(dataset=ds,source=source,n=2048,public_seed=19420261030,confirmation_seed=19420261031,duplicate_against_registered_roles=0,query_sha256=[hashlib.sha256(x.tobytes()).hexdigest() for x in conf],normalization='none',semantic_independence_claimed=False))
    for window in ['public','confirmation']:
        cc=dict(c);cc.update(window=window,queries=dict(path=str(s/f'{window}.f32'),format='raw_f32',n=2048,d=512),test_gt=dict(path=str(s/f'{window}.gt.i32'),format='raw_i32',n=2048,k=100),output_dir=str(storage/f'results/{ds}/{window}'),Ls=LS,opt_B32_L=[100,200,400,800],sq_L=[100,200,400] if ds=='coco' else [200,400,800])
        dump(R/f'configs/{ds}.{window}.json',cc)
        if window=='public':
            qq=dict(cc);qq['queries']=dict(cc['queries'],n=128);qq['test_gt']=dict(cc['test_gt'],n=128);qq.update(output_dir=str(storage/f'qualification/{ds}'),window='qualification',Ls=[200],opt_B32_L=[200],sq_L=[200]);dump(R/f'configs/{ds}.qualification.json',qq)
    assets += [ident(c['base']['path'],False),ident(c['index'],False)]
    paths=[c['table'],*c['router'].values()]
    model=read(Path(c['models'])/'model.json');paths += [str(Path(c['models'])/'model.json'),*model['files'].values()]
    assets += [ident(p) for p in paths if isinstance(p,str) and Path(p).is_file()]
dump(R/'inherited_assets.json',assets)
dump(R/'selection_freeze.json',dict(status='FROZEN_INPUT_SELECTION_AND_ALGORITHM_BEFORE_NEW_GT_OR_ANN',time=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol=ident(R/'protocol.md'),native=ident(R/'src/benchmark.cpp'),inputs=[ident(p) for p in sorted((storage/'inputs').rglob('*')) if p.is_file()],configs=[ident(p) for p in sorted((R/'configs').glob('*.json'))]))
print('E194_SELECTION_FROZEN',flush=True)
