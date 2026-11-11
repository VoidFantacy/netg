#!/usr/bin/env python3
"""Remove only source-rebuildable, untracked caches with no textual name reference."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import time

H=Path(__file__).resolve().parent
REPO=H.parents[2]

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not (H/'cleanup_plan.json').exists(),'one-shot cleanup: preserve existing plan/receipt; use a new version for new cleanup'
    start=time.time();candidates=[]
    for root in [REPO/'entry_method_exploration',REPO/'benches/run']:
        for parent,dirs,files in os.walk(root):
            if '__pycache__' not in dirs:continue
            cache=Path(parent)/'__pycache__';dirs.remove('__pycache__')
            for p in cache.iterdir():
                if p.is_file() and p.suffix=='.pyc' and not p.is_symlink():
                    source=Path(parent)/(p.name.split('.cpython-')[0]+'.py')
                    st=p.stat()
                    if source.is_file() and st.st_nlink==1:
                        candidates.append({'path':str(p.relative_to(REPO)),'basename':p.name,'source':str(source.relative_to(REPO)),
                            'bytes':st.st_size,'sha256':digest(p)})
    names=sorted({c['basename'] for c in candidates});patterns=H/'cache_names.txt';patterns.write_text('\n'.join(names)+'\n')
    tracked_run=subprocess.run(['git','ls-files','-z','--cached','--','*.pyc','*__pycache__*','GATE/.DS_Store'],cwd=REPO,capture_output=True,check=True)
    tracked=set(tracked_run.stdout.decode().split('\0'))
    argv=['rg','--json','-F','-f',str(patterns)]
    for glob in ['*.json','*.jsonl','*.md','*.py','*.txt','*.yaml','*.yml','*.toml','*.sh','*.lock','*.csv']:
        argv+=['--glob',glob]
    for glob in ['!**/.git/**','!**/.venv_cpu/**','!**/.agents/**','!**/build/**','!indices/**','!benches/datasets/**',
                 '!acpg/**','!jing/**','!faiss/**','!gate_baseline_artifacts/**',
                 '!experiment_history/_maintenance/20261024_current_state_cleanup_v1/**']:
        argv+=['--glob',glob]
    argv+=['.']
    scan=subprocess.run(argv,cwd=REPO,capture_output=True,text=True)
    assert scan.returncode in (0,1),scan.stderr
    referenced=set();evidence=[]
    for line in scan.stdout.splitlines():
        item=json.loads(line)
        if item['type']!='match':continue
        text=item['data']['lines']['text'];found=[n for n in names if n in text]
        referenced.update(found)
        if found:evidence.append({'file':item['data']['path']['text'],'line':item['data']['line_number'],'cache_basenames':found})
    (H/'cache_reference_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    plan={'scope':'only entry_method_exploration/**/__pycache__ and benches/run/__pycache__; environment, build, data and assets excluded',
        'reference_policy':'preserve every matching cache basename anywhere in scanned source/document/metadata text, even if another directory',
        'reference_scan_argv':argv,'eligible_cache_files':len(candidates),'removed':[],'preserved':[],'other_removed':[]}
    for c in candidates:
        if c['basename'] in referenced or c['path'] in tracked:
            plan['preserved'].append(c|{'reason':'referenced basename or Git tracked'})
        else:plan['removed'].append(c)
    other=REPO/'GATE/.DS_Store'
    if other.is_file() and 'GATE/.DS_Store' not in tracked:
        # Confirm Finder metadata, and keep exact deletion identity.
        raw=other.read_bytes()
        if raw[4:8]==b'Bud1':plan['other_removed'].append({'path':'GATE/.DS_Store','bytes':len(raw),'sha256':digest(other)})
    # This empty failed directory has no file in the sealed E184 delivery manifest; failure log stays.
    empty=REPO/'entry_method_exploration/20261024_residual_geometry_diagnosis_v1/failed_empty_analysis_v1'
    plan['empty_directory_removed']=str(empty.relative_to(REPO)) if empty.is_dir() and not any(empty.iterdir()) else None
    # A concrete inventory precedes every unlink. Recheck byte identity just before removing.
    (H/'cleanup_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    for c in plan['removed']+plan['other_removed']:
        p=REPO/c['path'];assert p.stat().st_size==c['bytes'] and digest(p)==c['sha256'];p.unlink()
    removed_dirs=[]
    for p in sorted({(REPO/c['path']).parent for c in plan['removed']},key=str):
        if not any(p.iterdir()):p.rmdir();removed_dirs.append(str(p.relative_to(REPO)))
    if plan['empty_directory_removed']:empty.rmdir()
    receipt={'status':'PASS','removed_cache_files':len(plan['removed']),'preserved_cache_files':len(plan['preserved']),
        'removed_other_metadata_files':len(plan['other_removed']),'removed_empty_cache_directories':removed_dirs,
        'removed_empty_failed_directory':plan['empty_directory_removed'],
        'reclaimed_file_bytes':sum(c['bytes'] for c in plan['removed']+plan['other_removed']),
        'elapsed_seconds':time.time()-start,'models_data_graphs_logs_results_deleted':False}
    (H/'cleanup_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='removed_empty_cache_directories'},ensure_ascii=False))

if __name__=='__main__':main()
