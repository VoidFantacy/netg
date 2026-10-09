#!/usr/bin/env python3
"""Assemble explicit completed-publication files; never push or run ANN."""
from pathlib import Path
import base64, hashlib, json, re, shutil, subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

EXP=Path(__file__).resolve().parents[1]
ROOT=EXP.parents[1]
PUB=Path('/data/netg/ACSG-publish-20261009')
REL=EXP.relative_to(ROOT).as_posix()
SNAP='research_snapshots/20261009_nsg_gt_m5'
plan=json.loads((EXP/'publication_plan.json').read_text())
for f in ['final_result_review.json','final_document_review.json']:
    assert (EXP/f).exists(),f
    review=json.loads((EXP/f).read_text())
    assert str(review.get('status','')).startswith('PASS'),review
state=json.loads((EXP/'run_state_v2.json').read_text())
metrics=json.loads((EXP/'analysis_v2/metrics.json').read_text())
assert all(j['status']=='COMPLETED' for j in state['jobs']) and len(metrics['points'])==60
final={'status':'COMPLETED_TEST_MATRIX','completed_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
       'M5_status':'正在研究','default_replacement':False,'default':{'WebVid':'GT10-soft-t1','Yandex':'GT10-hard'},
       'points':60,'formal_timing_batches':180,'repeats_per_point':3,'queries_per_point':10000,
       'L':[200,400,800,1000,1200],'K':[1,100],'methods':['NSG','GT','M5'],'new_training':False,
       'checks':{'native_full_matrix':'PASS','full_10K_return_domain_and_recall':'PASS','full_10K_M5_linear_merge':'PASS',
                 'fixed_256_query_plain_count_parity':'PASS','final_result_independent_review':'PASS','final_document_review':'PASS',
                 'curves_visual_inspection':'PASS','input_stats_match_preflight':state['input_stats_still_match_preflight']},
       'public_test_historical_exposure':True,'count_NDC_scope':'fixed uniform 256, not complete 10000',
       'raw_native_driver_receipt':'run_state_v2.json remains NATIVE_COMPLETED_PENDING_EVALUATION as an immutable native-stage receipt',
       'publication_status':'READY_PENDING_REMOTE_UPDATE',
       'conclusion':'M5/GT same-L: 20 Recall gains, no truth-member damage, 20 median QPS decreases; two discrete WebVid K1 cross-L joint gains; Yandex gains small'}
(EXP/'final_status.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n')
paths={x['path'] for x in plan['explicit_experiment_files']}
paths.update(x['destination'] for x in plan['planned_exact_byte_copies_after_native_complete'])
paths.update([REL+'/frozen_m5_source/README.md'])
extras=['run_state_v2.json','final_status.json','final_result_review.json','final_document_review.json',
        'delivery_costs.json','observed_cross_L_comparisons.json','src/finalize_delivery.py','src/prepare_publication.py']
paths.update(REL+'/'+f for f in extras)
paths.update(['readme.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md',
              'experiment_history/173_nsg_gt_m5_public_test_retest.md',SNAP+'/README.md',SNAP+'/publication.md'])
# Root documents in PUB preserve the prior published historical body; E173 artifacts are exact active bytes.
for f in sorted(paths):
    src=ROOT/f;dst=PUB/f
    assert src.exists() and dst.parent, f
    if f.startswith(REL+'/'):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    assert dst.is_file() and dst.stat().st_size<=1048576,f
records=[]
for f in sorted(paths):
    b=(PUB/f).read_bytes()
    records.append({'path':f,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),
                    'git_blob_sha':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()})
manifest={'schema':'acsg.e173.final_publication.v1','status':'COMPLETE_FILE_INVENTORY',
          'repository':'VoidFantacy/netg','branch':'research/state-20261002',
          'parent_commit':'9026dc60ca4f29983792e0f5dcfb33d7ef9335b5',
          'active_local_head':'96cf05d5410cf51272048cd1f90b4bb194e23c62',
          'files':records,'file_count_excluding_manifest':len(records),
          'manifest_self_excluded':True,'new_training':False,'M5_status':'正在研究'}
mf=SNAP+'/manifest.json'
for root in [ROOT,PUB]:(root/mf).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
paths.add(mf)
# Check newly authored browser-navigation links, not historical local-data/source path prose.
check_files=[SNAP+'/README.md',SNAP+'/publication.md','experiment_history/173_nsg_gt_m5_public_test_retest.md',
             REL+'/m5_method_explanation.md',REL+'/frozen_m5_source/README.md',REL+'/analysis_v2/report.md',
             REL+'/advisor_report/concise_v1/method_report.md']
broken=[];checked=0
for f in check_files:
    p=PUB/f
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('https:','http:','#','app:')):continue
        target=target.split('#',1)[0];checked+=1
        if not (p.parent/target).exists():broken.append({'file':f,'target':target})
assert not broken,broken
for f in ['summary.md','spec.md','s-target.md','s-experiment.md']:
    t=(PUB/f).read_text();assert 'M5' in t and 'E173_CURRENT_BEGIN' in t
selected=sorted(paths)
subprocess.run(['git','add','--',*selected],cwd=PUB,check=True)
actual=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=PUB).decode().split('\0')
actual=[p for p in actual if p];assert set(actual)==set(selected),(set(actual)-set(selected),set(selected)-set(actual))
tree=subprocess.check_output(['git','write-tree'],cwd=PUB).decode().strip()
index_modes={}
for row in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=PUB).decode().split('\0'):
    if row:
        meta,name=row.split('\t',1);index_modes[name]=meta.split()[0]
payload=[]
for f in selected:
    b=(PUB/f).read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    try:
        content=b.decode('utf-8');encoding='utf-8'
    except UnicodeDecodeError:
        content=base64.b64encode(b).decode('ascii');encoding='base64'
    payload.append({'path':f,'mode':index_modes[f],'type':'blob','encoding':encoding,'content':content,'expected_blob_sha':blob})
(EXP/'git_api_payload.json').write_text(json.dumps(payload,ensure_ascii=False))
receipt={'status':'PASS_EXPLICIT_PUBLICATION_TREE','files':len(selected),'total_bytes':sum((PUB/f).stat().st_size for f in selected),
         'local_tree_sha':tree,'remote_parent':manifest['parent_commit'],'navigation_links_checked':checked,'broken_new_links':broken,
         'binary_files':sum(x['encoding']=='base64' for x in payload),'paths':selected}
(EXP/'publication_preflight.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='paths'},ensure_ascii=False))
