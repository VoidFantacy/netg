#!/usr/bin/env python3
"""Check the theory-only delivery and protect prior scientific artifacts."""
from pathlib import Path
import hashlib,json,re
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    state=json.loads((R/'state.json').read_text());assert state['status']=='THEORY_ONLY_UNIMPLEMENTED_UNTESTED'
    assert not state['execution_started'] and not state['default_changed']
    for k in ['new_ANN','new_GT','new_training','new_QPS']:assert state[k]==0
    protected={}
    for base,name in [
        (REPO/'entry_method_exploration/20261024_residual_geometry_diagnosis_v1','delivery_manifest.json'),
        (REPO/'entry_method_exploration/20261024_manifold_residual_probe_v1','delivery_manifest.json'),
        (REPO/'reports/20261024_failure_rescue_residual_v1','manifest.json'),
        (REPO/'reports/20261024_failure_rescue_residual_lt10_v2','manifest.json')]:
        m=json.loads((base/name).read_text())
        for rel,v in m.items():
            p=base/rel;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],p
        protected[str(base.relative_to(REPO))]=len(m)
    files=[REPO/n for n in ['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','readme.md',
        'experiment_history/README.md','experiment_history/186_adaptive_completion_design_v1.md']]+[R/'design_zh.md',R/'README.md']
    broken=[]
    for p in files:
        t=p.read_text()
        for target in re.findall(r'\]\(([^)]+)\)',t):
            if target.startswith(('https:','http:','#')):continue
            target=target.split('#')[0]
            if target and not (p.parent/target).exists():broken.append(dict(file=str(p),target=target))
    assert not broken,broken
    design=(R/'design_zh.md').read_text()
    for term in ['THEORY_ONLY_UNIMPLEMENTED_UNTESTED','区域级标签','同后端','E174/E175','E176','不补全','主结果','全base','独立校准']:
        assert term in design,term
    for p in files[:8]:assert 'E186' in p.read_text(),p
    dump(R/'delivery_validation.json',dict(status='PASS_THEORY_ONLY_DESIGN_AND_DOCUMENT_SYNC',state=state,
        previous_scientific_files_unchanged=protected,protected_file_count=sum(protected.values()),
        current_document_sha256={str(p.relative_to(REPO)):sha(p) for p in files},broken_links=broken,
        new_algorithm_implemented=False,new_experiments=False,new_measured_conclusion=False,
        current_default='GT10; Web soft-t1 / Yandex hard; E99 shared kernel unchanged'))
    m={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(R.rglob('*'))
        if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts}
    dump(R/'manifest.json',m)
    print(json.dumps(dict(status='PASS_THEORY_ONLY_DESIGN_AND_DOCUMENT_SYNC',protected_files=sum(protected.values()),delivery_files=len(m)),ensure_ascii=False))
if __name__=='__main__':main()
