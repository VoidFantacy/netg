#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path
from common import DATASETS, ROOT, RUN, dump, identity, read, sha

assert read(RUN/'state.json')['status']=='RESULTS_VERIFIED_REPORT_PENDING'
assert read(RUN/'reviews/immutable_integrity.json')['status']=='PASS'
assert read(RUN/'reviews/result_verification.json')['status']=='PASS'
assert read(RUN/'reviews/v2_metadata_tie_check.json')['status']=='PASS'
cfg=read(RUN/'config.locked.json');assert cfg['protocol_sha256']==sha(RUN/'protocol.md')
data=read(RUN/'results/summary.json');assert len(data['metrics'])==50 and len(data['comparisons'])==60
assert read(RUN/'results/costs.json')['new_actual_dataset_search_calls']['total']==1325344
status='EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN'
for ds in DATASETS:
    for sp in ['fit_probe','cal','audit']:
        result=read(RUN/'diagnostics'/ds/sp/'results.json')
        assert result['status']=='COMPLETE' and result['threads']==1
        assert all(x['qps'] is None for x in result['methods'])
    result=read(RUN/'results'/ds/'results.json')
    assert result['status']=='COMPLETE' and result['queries']==2000
    assert {x['L'] for x in result['methods']}=={64,128,256,400,800}
    assert all(x['configuration']['k']==3 for x in result['methods'] if x['family']!='nsg_medoid')
    assert len(read(RUN/'models'/ds/'complete.json')['models'])==6
# No controller, trainer, labeler, or evaluator from this version may still be active.
processes=subprocess.check_output(['ps','-eo','pid=,args='],text=True)
active=[]
for line in processes.splitlines():
    if str(RUN) not in line:continue
    if any(name in line for name in ['/bin/evaluate','/bin/label_triples','/src/run_training.py','/src/train.py','/src/run_labels.py','/src/run_diagnostics.py','/src/run_validation.py']):
        active.append(line.strip())
assert not active,active
decision={'status':status,'execution_complete':True,'performance_go':False,'scope':'one build, 2K validation per dataset, five L, one timing run',
    'reason':'small Recall gains; no clear overall QPS improvement; Full optimizes the surrogate better but does not consistently beat rank8 in search',
    'models_selected_using':'cal only','additional_experiments_started':False,'original_E22_status_unchanged':True}
dump(RUN/'results/decision.json',decision)
docs=[ROOT/x for x in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/12_three_entry_rank_exploration.md']]
docs += [RUN/x for x in ['README.md','report.md','protocol.md','commands.md','results/tables.md']]
links=[]
for doc in docs:
    text=doc.read_text();assert '\x00' not in text
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
        if re.match(r'^[a-z]+://',target) or target.startswith('#'):continue
        path=(doc.parent/target.split('#')[0]).resolve()
        if path==RUN/'reviews/final_audit.json':continue
        assert path.exists(),(str(doc),target)
        links.append({'document':str(doc.relative_to(ROOT)),'target':target})
for doc in [ROOT/'summary.md',ROOT/'s-target.md',ROOT/'s-experiment.md',ROOT/'experiment_history/12_three_entry_rank_exploration.md',RUN/'report.md']:
    assert status in doc.read_text(),doc
    assert '训练运行中' not in doc.read_text() and '模型正在训练' not in doc.read_text(),doc
audit={'status':'PASS','scope':'complete authorized experiment, raw outputs, preservation and delivery; not a performance GO',
    'requirements':{'fixed_unique_three_real_entries':'all 50 points checked, k3 except NSG medoid',
      'actual_joint_search_supervision':'960000 labels independently scored; 880000 physical calls plus parity',
      'full_and_rank8_same_objective':'12 fixed candidates; full objective optimized; independent gradient/folding tests passed',
      'cal_only_selection_and_frozen_validation':'selection independently recomputed; frozen file hashes verified',
      'one_model_five_L_single_thread':'100000 outputs verified; serialized router graph and entries identical across L',
      'real_end_to_end_and_costs':'one plain wall per point, full count outside timer; complete costs.json with reused-label dependency',
      'original_artifacts_preserved':'immutable_integrity.json verifies original base/graphs, source/libs, inputs and frozen weights',
      'evidence_and_handoff':'report, plot visually inspected, 50-row raw table, 60 comparisons, four root docs and E23 history synchronized'},
    'metadata_correction':'v1 diagnostic warmup-count display only, retained and corrected in v2 before audit/validation',
    'local_links_checked':len(links),'local_links':links,'active_experiment_processes':active,
    'document_identities':[identity(x) for x in docs]}
dump(RUN/'reviews/final_audit.json',audit)
dump(RUN/'state.json',{'status':status,'execution_status':'COMPLETE','final_audit':'reviews/final_audit.json',
    'report':'report.md','decision':'results/decision.json','protocol_sha256':cfg['protocol_sha256'],
    'validation_points':50,'verified_validation_query_outputs':100000,'performance_go':False,'running_processes':[]})
# A delivery manifest binds generated small artifacts and result files; old large datasets stay referenced.
files=[p for p in sorted(RUN.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
dump(RUN/'delivery_manifest.json',{'status':'COMPLETE','files':[identity(p) for p in files],
    'root_documents':[identity(p) for p in docs if not p.is_relative_to(RUN)]})
print('FINAL_AUDIT_PASS',len(links),'local links',len(files),'delivery files',flush=True)
