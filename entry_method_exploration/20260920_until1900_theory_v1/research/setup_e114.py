from pathlib import Path
import json,time,hashlib,shutil,csv
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1]
OLD=ROOT/'entry_method_exploration/20260920_until1600_theory_v1'
E107=OLD/'stages/e107_initialization_factorial';R=TB/'stages/e114_terminal_peaks'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not R.exists();R.mkdir()
for d in ['src','reviews','logs','results']:(R/d).mkdir()
before=[]
for rel in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
    p=ROOT/rel;dest=R/'reviews/source_before'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dest);before.append(dict(**ident(p),snapshot=str(dest)))
dump(R/'reviews/source_before.json',before)
(R/'protocol.md').write_text((TB/'research/e114_protocol.md').read_text().replace('(terminal_search_sets.md)','(research.md)'))
(R/'research.md').write_text((TB/'research/terminal_search_sets.md').read_text().replace('(../../20260920_until1600_theory_v1/','(../../../20260920_until1600_theory_v1/'))
shutil.copy2(TB/'research/analyze_e114.py',R/'src/analyze.py')
shutil.copy2(TB/'research/run_e114.py',R/'src/run.py')
old=read(E107/'config.locked.json');datasets={};sources=[E107/'config.locked.json',E107/'results/metrics.csv']
for ds,c in old['datasets'].items():
    p=E107/'results'/('main_'+ds);native=read(p/'config.json');sources.append(p/'config.json')
    methods=[]
    for m in old['methods'][ds]:
        base=p/m['name']/'k1_L128';paths={key:str(base/suffix) for key,suffix in [('ids','ids.i32'),('distances','distances.f32')]}
        assert Path(paths['ids']).stat().st_size==4096*4 and Path(paths['distances']).stat().st_size==4096*4
        methods.append(dict(name=m['name'],**paths));sources.extend(Path(s) for s in paths.values());sources.append(base/'complete.json')
    datasets[ds]=dict(dataset=ds,n=4096,dimension=c['dimension'],base_n=c['base_n'],index=c['index'],
                     index_stat=c['index_stat'],queries=native['queries'],GT=native['GT'],methods=methods)
    sources.extend([Path(native['queries']),Path(native['GT'])])
fields=next(csv.reader((E107/'results/metrics.csv').open()));assert all(x in fields for x in ['recall','failed','K','L'])
cfg=dict(version='E114_terminal_peaks_v1',created_unix=time.time(),datasets=datasets,
         original_metrics=str(E107/'results/metrics.csv'),recall_column='recall',recall_multiplier=100,failed_column='failed',
         independent_query_positions=list(range(0,4096,256)),threads=1,cpu=15,deadline_unix=1789901400,
         wall_timeout_seconds=600,max_new_bytes=32*2**20,max_combined_bytes=2*2**30,min_free_gib=4,max_rss_gib=40,
         expected_NSG_calls=0,new_ANN=0,new_GT=0,new_graphs=0,new_training=0,
         data_role='All exposed E105 development queries reused through E107 results; no held-out',
         purpose='Necessary terminal-local-optimum property and finite preset-policy convergence; no learner branch')
dump(R/'config.locked.json',cfg);dump(R/'reviews/input_sources.json',dict(files=[ident(p) for p in dict.fromkeys(sources)]))
protected=[OLD/'complete.json',OLD/'report.md',E107/'complete.json',E107/'report.md',
           TB/'stages/e112_one_hop_hub_design/complete.json',TB/'stages/e113_comparison_support/complete.json',
           E107/'src/kernels.hpp',ROOT/'ACSG/detail/CandidatePool.h']
dump(R/'reviews/protected_before.json',[ident(p) for p in protected])
dump(R/'reviews/source_freeze.json',dict(files=[ident(R/p) for p in ['protocol.md','research.md','config.locked.json','src/analyze.py','src/run.py']]))
dump(R/'state.json',dict(status='READY_FROZEN',pending=['one serial read-only audit','interpretation and closeout']))
state=read(TB/'state.json');state['stage']='E114 frozen terminal local-optimum audit; zero new searches';dump(TB/'state.json',state)
print(json.dumps(dict(status='READY_FROZEN',NSG_calls=0,source_files=len(sources)),indent=2))
