#!/usr/bin/env python3
import hashlib,json,re,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
    t=time.perf_counter()
    audit=json.loads((R/'reviews/results_audit.json').read_text());score=json.loads((R/'reviews/score_binding_audit.json').read_text());pdf=json.loads((R/'reviews/pdf_validation.json').read_text())
    assert audit['status']=='PASS_E187_STDLIB_SECOND_IMPLEMENTATION' and score['status']=='PASS_E187_INDEPENDENT_FLOAT64_SCORE_BINDING' and pdf['status']=='PASS_SIX_PAGE_PDF'
    assert pdf.get('visual_review_passed') is True,'actual rendered glyph/layout review is required'
    checked=[];broken=[]
    files=[REPO/x for x in ['summary.md','spec.md','s-target.md','s-experiment.md','readme.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/187_adaptive_completion_pilot_v1.md']]+[R/'README.md',R/'report_zh.md']
    for p in files:
        for match in re.finditer(r'\[[^\]]*\]\(([^\)]+)\)',p.read_text()):
            target=match.group(1).split('#')[0]
            if not target or target.startswith(('http:','https:','mailto:')):continue
            path=p.parent/target
            if not path.exists():broken.append(dict(file=str(p),target=target))
        checked.append(dict(path=str(p),sha256=sha(p)))
    assert not broken,broken
    conclusion=json.loads((R/'analysis/conclusion.json').read_text())
    dump(R/'state.json',dict(status='COMPLETED_FROZEN_PILOT',date='2026-10-28',scope='COCO and Deep10M, actual K100 only',points=52,formal_batches=156,original_matrix_points=46,supplemental_GT_points=6,formal_queries_per_point=10000,
        default_changed=False,blind_confirmation=False,query_action_selector_implemented=False,remaining_formal_queue=False,conclusion=conclusion))
    ledger=[]
    for ds in ['coco','deep10m_l2_v1']:
        model=R/'models'/ds;s=json.loads((model/'backend.json').read_text());stages=dict(backend_offline_seconds=s['elapsed_seconds'],backend_threads=8)
        for mode in ['features','qualification','formal']:
            stages[mode+'_outer_seconds']=json.loads((R/f'reviews/{mode}_{ds}.receipt.json').read_text())['seconds']
        stages['ridge_seconds']=json.loads((model/'training.json').read_text())['seconds'];stages['dataset']=ds
        stages['controls_outer_seconds']=json.loads((R/f'controls_v1/results/{ds}/complete.json').read_text())['outer_seconds']
        stages['controls_internal_seconds']=sum(x['wall_seconds'] for p in json.loads((R/f'controls_v1/results/{ds}/complete.json').read_text())['results'] for x in p['rounds'])
        stages['formal_internal_seconds']=sum(x['wall_seconds'] for p in json.loads((R/f'results/{ds}/complete.json').read_text())['results'] for x in p['rounds'])
        ledger.append(stages)
    dump(R/'analysis/cost_ledger.json',dict(stages=ledger,formal_internal_nested_in_formal_outer=True,
        backend_components_nested_in_backend_elapsed=True,build_wall_seconds=None,historical_base_graph_B32_build_seconds=None,
        note='No parallel formal benchmark/training/labels; no sum of nested times. Historical cold-start costs unknown, not zero.'))
    dump(R/'delivery_validation.json',dict(status='PASS_E187_DELIVERY',point_count=52,formal_batches=156,quality_audit=audit['status'],score_binding=score['status'],pdf=pdf['status'],local_links_checked=True,broken_links=broken,current_document_files=checked,default_changed=False,seconds=time.perf_counter()-t))
    manifest=[]
    for p in sorted(R.rglob('*')):
        if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts:
            manifest.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=sha(p)))
    total=sum(x['bytes'] for x in manifest);assert total<1.2*2**30,total
    dump(R/'delivery_manifest.json',dict(status='SEALED_E187_LOCAL_DELIVERY',files=manifest,total_bytes=total,default_changed=False,old_scientific_artifacts_modified=False))
    print('PASS final delivery',len(manifest),'files',round(total/2**20,2),'MiB')
if __name__=='__main__':main()
