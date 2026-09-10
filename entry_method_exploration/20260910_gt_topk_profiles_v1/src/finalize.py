"""Delivery check only: no training, searching, validation refresh or upstream mutation."""
import json
import re
import shutil
import time
from pathlib import Path
from urllib.parse import unquote
from common import DATASETS, ROOT, RUN, check_lock, dump, identity, read, sha

lock=check_lock()
status='EXPLORATORY_LOCAL_FRONTIER_SIGNAL_NO_FORMAL_GO'
summary=read(RUN/'results/summary.json');verification=read(RUN/'reviews/result_verification.json')
assert summary['completed_validation']
assert verification['status']=='PASS' and verification['points']==116
assert verification['independently_rescored_outputs']==169408 and verification['E23_baseline_regression_outputs']==60000
assert sum(x['stage']=='validation' for x in summary['metrics'])==60
integrity=read(RUN/'reviews/immutable_integrity.json');assert integrity['status']=='PASS'
# No new large hash sweep after documentation-only edits. Stat check follows the completed full sweep.
for item in integrity['upstream']:
    if item['role']!='unchanged upstream source or artifact':continue
    st=Path(item['path']).stat()
    assert st.st_size==item['bytes'] and st.st_mtime_ns==item['mtime_ns'],item['path']
for name in ['frozen_before_cal.json','frozen_before_audit.json','frozen_before_validation.json']:
    for item in read(RUN/'models'/name)['files']:
        assert sha(item['path'])==item['sha256'],item['path']
jobs=read(RUN/'reviews/search_jobs.json')
assert len(jobs)==8 and all(x['status']=='COMPLETE' and x['exit_code']==0 for x in jobs)
assert sum(x['actual_calls'] for x in jobs)==543296 and not any(x['repair'] for x in jobs)
assert all(x['max_observed_process_threads']==1 and x['cpu']==15 for x in jobs)
assert max(x['max_observed_rss_bytes'] for x in jobs)<lock['rss_limit_bytes']
active=[]
for x in jobs:
    cmdline=Path(f"/proc/{x['pid']}/cmdline")
    if cmdline.exists() and str(RUN/'bin/evaluate').encode() in cmdline.read_bytes():active.append(x['pid'])
assert not active,'owned evaluator still active'
cal=read(RUN/'reviews/cal_gate.json');assert cal['status']=='PASS'
state={'status':status,'execution_status':'COMPLETE_CLOSED','completed_unix':time.time(),
       'P0':'IDENTITY_AND_PROTOCOL_PASS','P1':'RECOVERY_AND_BUILD_PASS','P2':'CAL_GATE_PASS_AUDIT_REPORTED',
       'P3':'ALL_60_POINTS_COMPLETE','physical_real_search_calls':543296,'repair_calls_used':0,
       'synthetic_calls':1500,'independently_rescored_outputs':169408,'E23_baseline_bitwise_outputs':60000,
       'formal_performance_GO':False,'new_training_labels':0,'single_or_triple_training_labels_used':False,
       'validation_opened':True,'validation_scope':'historically used first 2000 only, after freeze',
       'heldout_opened':False,'active_job':None,'remaining_protocol_stages':[],
       'primary_models':{ds:read(RUN/'models'/ds/'selection.json')['primary']['name'] for ds in DATASETS},
       'next_direction':'2A fixed-H actual finite-L utility grouping is a recommendation only; not started',
       'other_branches_started':False,'protocol_sha256':lock['protocol_sha256']}
dump(RUN/'state.json',state)
costs=read(RUN/'results/costs.json')
costs['GT1_recovery_full_process_wall']={'seconds':None,'reason':'core recovery/control timings saved; complete startup and support-artifact serialization were not separately timed'}
costs['candidate_build_stage_time_boundary']='sum of dataset stages, excludes common Python import/self-test startup; includes per-dataset inputs, all remaining candidates and support/artifact writes'
costs['no_double_counting']='router construction/load and query wall are included in corresponding process wall; separate phase totals are not additive with those process totals'
dump(RUN/'results/costs.json',costs)
docs=[ROOT/p for p in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md',
    'experiment_history/README.md','experiment_history/13_gt_topk_profiles.md']]
docs += [RUN/p for p in ['README.md','report.md','protocol.md','commands.md','results/tables.md']]
links=[];broken=[]
for doc in docs:
    content=doc.read_text()
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',content):
        target=target.strip().strip('<>')
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
        target=unquote(target.split('#',1)[0])
        path=(doc.parent/target).resolve()
        record={'document':str(doc.relative_to(ROOT)),'target':target,'exists':path.exists()}
        links.append(record)
        if not path.exists():broken.append(record)
assert not broken,broken
for doc in [ROOT/'summary.md',ROOT/'s-target.md',ROOT/'s-experiment.md',ROOT/'experiment_history/13_gt_topk_profiles.md',RUN/'report.md']:
    assert status in doc.read_text()
required=['report.md','results/metrics.csv','results/comparisons.csv','results/profile_support.csv',
          'results/ann_diagnostics.csv','results/frontier_points.csv','results/frontier_interpolation.csv',
          'results/costs.json','figures/recall_qps.png','figures/recall_qps.svg','figures/deltas.png','figures/deltas.svg']
assert all((RUN/p).is_file() and (RUN/p).stat().st_size>0 for p in required)
artifact_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
assert artifact_bytes<lock['output_limit_bytes'] and shutil.disk_usage(ROOT).free>lock['min_free_bytes']
dump(RUN/'reviews/final_audit.json',{'status':'PASS','scope':'authorized first direction complete, not formal performance GO',
    'completed_unix':time.time(),'execution':state,'active_processes':active,'checked_documents':len(docs),
    'checked_local_links':len(links),'broken_links':broken,'links':links,
    'document_identities':[identity(p) for p in docs], 'artifact_bytes_before_final_manifest':artifact_bytes,
    'visual_checks':['recall_qps.png: both datasets, six methods, all five points, labels readable',
                     'deltas.png: both datasets and both metrics, all negative points preserved',
                     'cal_recall_qps.png: label overlap corrected by plot-only rerender'],
    'upstream_integrity':identity(RUN/'reviews/immutable_integrity.json'),
    'no_new_search_after_completed_matrix':True,'memory_files_modified':False})
dump(RUN/'reviews/delivery_manifest.json',{'status':status,'files':[identity(RUN/p) for p in required],
    'state':identity(RUN/'state.json'),'final_audit':identity(RUN/'reviews/final_audit.json')})
print('FINAL_DELIVERY_PASS',len(links),'local links',artifact_bytes,'artifact bytes',flush=True)
