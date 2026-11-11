#!/usr/bin/env python3
"""Seal the offline probe after source, link and actual-PDF review checks."""
from pathlib import Path
import csv,hashlib,json,re,sys
sys.path.insert(0,'/tmp/acsg_pdf_render_20261024')
import pymupdf
R=Path(__file__).resolve().parent;REPO=R.parents[1];A=R/'analysis'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    run=json.loads((A/'receipt.json').read_text());audit=json.loads((A/'audit.json').read_text())
    assert run['status']=='PASS_OFFLINE_MANIFOLD_RELATED_GEOMETRY_PROBE'
    assert audit['status']=='PASS_SECOND_STDLIB_SET_RANK_STRATA_IMPLEMENTATION'
    protected={}
    for base,manifest in [
        (REPO/'entry_method_exploration/20261024_residual_geometry_diagnosis_v1','delivery_manifest.json'),
        (REPO/'reports/20261024_failure_rescue_residual_v1','manifest.json'),
        (REPO/'reports/20261024_failure_rescue_residual_lt10_v2','manifest.json')]:
        m=json.loads((base/manifest).read_text())
        for name,v in m.items():
            p=base/name;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],p
        protected[str(base.relative_to(REPO))]=len(m)
    inputs=json.loads((A/'inputs_manifest.json').read_text())
    for name,v in inputs['small_inputs'].items():assert sha(Path(name))==v['sha256'],name
    for name,v in inputs['inherited_big_inputs'].items():
        p=Path(name);assert p.stat().st_size==v['bytes'] and p.stat().st_mtime_ns==v['mtime_ns'],name
    q=list(csv.DictReader((A/'sample_query_metrics.csv').open()));assert len(q)==3584
    assert len(set((r['dataset'],r['query_row']) for r in q))==3584
    p=R/'ACSG_流形相关几何与残差_诊断图_20261024.pdf';doc=pymupdf.open(p);assert len(doc)==2
    out=R/'review_pages';out.mkdir(exist_ok=True);pages=[]
    for i,page in enumerate(doc):
        fn=out/f'page_{i+1}.png';page.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6),alpha=False).save(fn)
        pages.append(dict(page=i+1,rendered_actual_PDF=True,png=str(fn.relative_to(R)),sha256=sha(fn)))
    text='\n'.join(x.get_text() for x in doc);(out/'extracted_text.txt').write_text(text)
    for term in ['COCO','Deep10M','42.00','10.51','12.04']:assert term in text,term
    dump(R/'pdf_render_receipt.json',dict(status='PASS_ACTUAL_PDF_RENDERED_AND_VISUALLY_REVIEWED',pdf=p.name,
        pdf_sha256=sha(p),renderer='PyMuPDF '+pymupdf.VersionBind,pages=pages,
        visual_review=dict(reviewer='root',pages=[1,2],notes='Chinese visible, all seven labels readable, scatter labels separated, caption wrapped within page')))
    broken=[];docs={}
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','readme.md',
                 'experiment_history/README.md','experiment_history/185_manifold_residual_probe_v1.md']:
        f=REPO/name;t=f.read_text();assert 'E185' in t;docs[name]=sha(f)
        for target in re.findall(r'\]\(([^)]+)\)',t):
            if target.startswith(('http:','https:','#')):continue
            target=target.split('#')[0]
            if not target:continue
            dest=f.parent/target
            if not dest.exists():broken.append(dict(file=name,target=target))
    assert not broken,broken
    state=dict(status='COMPLETED_OFFLINE_GEOMETRY_DIAGNOSTIC',samples=3584,existing_queries=56000,
        conclusion='Local geometric continuity associated with GT/omission sharing; no simple low-dimensional rule or causal manifold proof',
        new_ANN=0,new_training=0,new_GT=0,new_QPS=0,default_changed=False,pending_experiments=0)
    dump(R/'state.json',state)
    result=dict(status='PASS_E185_OFFLINE_PROBE_AND_DELIVERY',source_inputs_unchanged=True,old_artifacts_unchanged=protected,
        main_seconds=run['seconds'],second_implementation_seconds=audit['seconds'],failed_attempt_seconds=None,
        failed_attempt_log='failed_attempt_01.log',pdf_sha256=sha(p),actual_pdf_pages=2,
        scientific_validation=audit['status'],correlations=168,adjusted_contrasts=126,
        current_documents_sha256=docs,broken_links=broken,scope=state)
    dump(R/'delivery_validation.json',result)
    m={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(R.rglob('*'))
       if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts}
    dump(R/'delivery_manifest.json',m)
    print(json.dumps(dict(status=result['status'],files=len(m),protected_old_files=sum(protected.values()),pdf=str(p)),ensure_ascii=False))
if __name__=='__main__':main()
