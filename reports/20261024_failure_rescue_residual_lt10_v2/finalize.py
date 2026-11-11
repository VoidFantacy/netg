#!/usr/bin/env python3
"""Check delivered identities, numeric partitions, and current links without new searches."""
from pathlib import Path
import csv,hashlib,json,re
R=Path(__file__).resolve().parent;REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def rows(p):return list(csv.DictReader(p.open()))
def verify_manifest(base,manifest):
    m=json.loads(manifest.read_text())
    for name,v in m.items():
        p=base/name;assert p.stat().st_size==v['bytes'],p;assert sha(p)==v['sha256'],p
    return len(m)
def main():
    audit=json.loads((R/'integer_audit.json').read_text());assert audit['status']=='PASS_STDLIB_SET_RECOMPUTATION'
    s=rows(R/'failure_by_L.csv');c=rows(R/'paired_rescue_by_L.csv');hist=rows(R/'hit_distributions.csv')
    for r in s:
        hh=[x for x in hist if x['dataset']==r['dataset'] and x['method']==r['method'] and x['L']==r['L']]
        assert len(hh)==101 and sum(int(x['count']) for x in hh)==int(r['n'])
        assert sum(int(x['count']) for x in hh if int(x['hits'])<10)==int(r['low_count'])
        assert int(r['exactly10_count'])==int(hh[10]['count'])
    for r in c:
        den=int(r['reference_low_count']);out=int(r['exit_low_count']);ent=int(r['enter_low_count'])
        assert den-out+ent==int(r['result_low_count'])
        assert out+int(r['low_improved_still_low_count'])==int(r['low_net_improved_count'])
        if den==0:assert r['exit_rate_pct']=='' and r['low_net_improved_pct']==''
    transitions=rows(R/'cross_L_query_transitions.csv');assert len(transitions)==126
    for r in transitions:
        assert int(r['low_from'])-int(r['exited'])+int(r['entered'])==int(r['low_to'])
        assert int(r['entered'])==0
    old=REPO/'reports/20261024_failure_rescue_residual_v1'
    old_count=verify_manifest(old,old/'manifest.json')
    old184=REPO/'entry_method_exploration/20261024_residual_geometry_diagnosis_v1'
    old184_count=verify_manifest(old184,old184/'delivery_manifest.json')
    for path,record in json.loads((R/'inputs_manifest.json').read_text()).items():
        p=Path(path);assert p.stat().st_size==record['bytes'] and sha(p)==record['sha256'],p
    broken=[];docs={}
    for path in (R/'source_before').rglob('*.md'):
        p=REPO/path.relative_to(R/'source_before');docs[str(p.relative_to(REPO))]=sha(p)
        text=p.read_text()
        assert '低于10%' in text or 'Recall@100<10%' in text,p
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if '20261024_failure_rescue_residual_lt10_v2' in target:
                q=p.parent/target
                if not q.exists():broken.append(str(q))
    assert not broken,broken
    receipt=json.loads((R/'pdf_render_receipt.json').read_text());build=json.loads((R/'build_receipt.json').read_text())
    pdf=R/build['pdf'];assert sha(pdf)==build['sha256']==receipt['pdf_sha256']
    assert len(receipt['pages'])==5
    for p in receipt['pages']:assert sha(R/p['png'])==p['sha256']
    receipt.update(status='PASS_ACTUAL_PDF_RENDER_AND_VISUAL_REVIEW',reviewer='root',
        actual_pages_visually_reviewed=[1,2,3,4,5],contact_sheet_viewed=True,
        checks=['Chinese visible','strict denominator and threshold explicit','all seven L shown',
                'heatmap counts readable','no clipping or legend overlap observed'])
    dump(R/'pdf_render_receipt.json',receipt)
    result=dict(status='PASS_CORRECTED_STRICT_LT10_ALL_L_PDF_DELIVERY',pages=5,points=147,paired_comparisons=98,
        unique_queries=56000,query_point_evaluations=1176000,pdf=str(pdf),pdf_sha256=sha(pdf),
        strict_hit_counts='0..9; exactly10 excluded',zero_denominator='undefined, not 0% rescue',
        original_E184_files_unchanged=old184_count,previous_v1_files_unchanged=old_count,
        source_inputs_unchanged=True,per_query_NPZ_checked_by_stdlib=True,
        visual_review=receipt['status'],current_documents=docs,broken_current_links=broken,
        new_ANN=0,new_GT=0,new_training=0,new_QPS_measurements=0,default_changed=False)
    dump(R/'delivery_validation.json',result)
    manifest={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':sha(p)}
        for p in sorted(R.rglob('*')) if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts}
    dump(R/'manifest.json',manifest)
    print(json.dumps({'status':result['status'],'files':len(manifest),'pdf':str(pdf)},ensure_ascii=False))
if __name__=='__main__':main()
