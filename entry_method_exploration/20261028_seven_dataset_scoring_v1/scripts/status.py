"""Small read-only progress view; does not import numerical libraries."""
import json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=json.loads((R/'state.json').read_text());ds=s.get('dataset');stage=s['status']
folder='dense_controls' if stage=='RUNNING_DENSE_CONTROLS' else 'results'
v=[];expected=192
if ds:
    p=R/'storage'/folder/ds/'progress.json'
    if p.exists():v=json.loads(p.read_text())
    if folder=='dense_controls':
        c=json.loads((R/f'configs/{ds}.dense.json').read_text());expected=3*(sum(map(len,c['K_L'].values()))+4*sum(map(len,c['completion_L'].values())))
done=[p.name for p in (R/'analysis').iterdir() if p.is_dir() and (R/f'reviews/results_audit_{p.name}.json').exists()]
print(json.dumps(dict(stage=stage,dataset=ds,batches_completed=len(v),batches_planned=expected,last=v[-1] if v else None,primary_datasets_audited=len(done),root_free_GiB=round(shutil.disk_usage('/').free/2**30,3),primary_complete=(R/'primary_complete.json').exists(),dense_complete=(R/'dense_complete.json').exists(),report_ready=(R/'reviews/report_build.json').exists(),PDF_authorized=(R/'delivery_authorization_update.json').exists()),ensure_ascii=False))
