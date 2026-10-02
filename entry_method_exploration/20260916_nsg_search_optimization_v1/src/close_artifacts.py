import pathlib,json,hashlib,datetime
D=pathlib.Path(__file__).resolve().parent.parent
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(D/'reviews/results_audit.json')['status']=='PASS'
assert read(D/'reviews/figures_render_check.json')['status']=='PASS'
for p,h in read(D/'reviews/frozen_code.json').items():assert sha(pathlib.Path(p))==h,p
size=sum(p.stat().st_size for p in D.rglob('*') if p.is_file());assert size<1024**3,size
files=['report.md','results/metrics.csv','results/paired_speedup.csv','results/wall_rounds.csv','results/dataset_audit.csv','source_changes.patch']
x={'status':'COMPLETE_RESULTS_REPORT_PLOTS','completed_at':datetime.datetime.now().isoformat(),
   'measurement_search_calls':2296000,'timed_rounds':108,'disk_bytes':size,'disk_cap_bytes':1024**3,
   'manual_visual_review':False,'rendered_file_integrity':'PASS','report_hashes':{n:sha(D/n) for n in files},
   'git_backup':'2739b09a67f3ca0b6f145d43690d36345df3182c','production_library':'bin/libACSG.optimized.a',
   'default_entry_models_changed':False,'original_build_library_changed':False}
(D/'complete.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x,indent=2))
