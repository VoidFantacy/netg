"""Verify existing research artifacts without rerunning LP or retrieval."""
from pathlib import Path
import hashlib
import json
import re
import datetime
import numpy as np

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    protected=json.loads((OUT/'reviews/protected_before.json').read_text())
    for x in protected:
        p=ROOT/x['path']
        assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'], p
    snapshots=json.loads((OUT/'source_before/manifest.json').read_text())
    for x in snapshots:
        assert sha(OUT/'source_before'/x['path'])==x['sha256'], x['path']
    data=json.loads((OUT/'results/representation.json').read_text())
    for x in data['inputs']+[data['source']]:
        assert sha(ROOT/x['path'])==x['sha256'], x['path']
    assert data['protocol']==json.loads((OUT/'reviews/geometry_lock.json').read_text())
    witnesses=np.load(OUT/'results/geometry_witnesses.npz', allow_pickle=False)
    count=0
    for ds in data['datasets']:
        profile=next(x for x in data['inputs'] if f"models/{ds['dataset']}/" in x['path'])
        p=np.fromfile(ROOT/profile['path'],dtype='float32').reshape(ds['hub_count'],ds['dim']).astype('float64')
        for rec in ds['records']:
            assert rec['solver_status']==0
            z=witnesses[f"{ds['dataset']}_{rec['row']}"]
            scores=p@z
            selected=np.array(rec['teacher_slots'])
            others=np.setdiff1d(np.arange(len(p)),selected)
            gap=float(scores[selected].min()-scores[others].max())
            assert gap>=data['protocol']['margin']-1e-7
            assert abs(gap-rec['witness_min_margin'])<1e-12
            assert set(np.argsort(-scores)[:3])==set(selected)
            count+=1
    files=[OUT/'report.md',OUT/'protocol.md',ROOT/'experiment_history/97_query_representation_research.md',
           *[ROOT/x for x in ['spec.md','summary.md','s-target.md','s-experiment.md','experiment_history/README.md']]]
    broken=[]; links=0
    audit=OUT/'reviews/completion_audit.json'
    for p in files:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('https://','http://','#','mailto:')):
                continue
            target=target.split('#',1)[0]
            if not target:continue
            path=(p.parent/target).resolve()
            links+=1
            if not path.exists() and path!=audit:
                broken.append(dict(source=str(p),target=target))
    assert not broken, broken
    scope=json.loads((OUT/'scope.json').read_text())
    for key in ['new_training_runs','ann_calls','gt_calls','graph_builds','qps_rounds']:
        assert scope[key]==0 and data['protocol'][key]==0
    assert not scope['evaluation_payload_access']
    result=dict(status='PASS',time=datetime.datetime.now().astimezone().isoformat(),
                protected_selected_files_unchanged=len(protected),
                root_before_snapshots_verified=len(snapshots),input_files_verified=len(data['inputs']),
                geometry_witnesses_independently_recomputed=count,local_links_checked=links,
                missing_local_links=broken,pilot_status='DESIGN_ONLY',
                new_training_runs=0,ann_calls=0,gt_calls=0,graph_builds=0,qps_rounds=0,
                evaluation_payload_access=False,
                limitation='Protection checks cover the listed files, not a fresh hash of all large data/index assets.',
                delivered=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in files])
    audit.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('delivered','limitation')}))


if __name__=='__main__':
    main()
