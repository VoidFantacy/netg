#!/usr/bin/env python3
"""A separate stdlib verification of the numbers used by the six-page PDF."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import re

H=Path(__file__).resolve().parent
REPO=H.parents[1]
E184=REPO/'entry_method_exploration/20261024_residual_geometry_diagnosis_v1'
E183=REPO/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
def rows(p):return list(csv.DictReader(p.open()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def num(r,k):return float(r[k])
def eq(a,b):assert abs(float(a)-float(b))<1e-9,(a,b)

def main():
    charts=rows(H/'chart_data.csv');source=rows(E184/'analysis/dataset_summary.csv');old=rows(E183/'analysis/final_v1/same_L_deltas.csv')
    assert len(charts)==len(source)==7
    for c,s in zip(charts,source):
        assert c['dataset']==s['dataset'];n=int(s['n']);ds=s['dataset']
        gs=next(r for r in old if r['dataset']==ds and r['method']==c['GT10_method'] and r['K']=='1' and r['L']=='200')
        rs=next(r for r in old if r['dataset']==ds and r['method']==c['B32_method'] and r['K']=='1' and r['L']=='200')
        g100=next(r for r in old if r['dataset']==ds and r['method']==c['GT10_method'] and r['K']=='100' and r['L']=='200')
        r100=next(r for r in old if r['dataset']==ds and r['method']==c['B32_method'] and r['K']=='100' and r['L']=='200')
        eq(c['NSG_K1_failure_pct'],100*int(gs['reference_missing_members'])/n)
        eq(c['GT_K1_failure_pct'],100*int(rs['reference_missing_members'])/n)
        eq(c['B32_K1_failure_pct'],100*(n-int(rs['actual_full_success_queries']))/n)
        eq(c['NSG_K100_incomplete_pct'],100*int(g100['reference_incomplete_queries'])/n)
        eq(c['GT_K100_incomplete_pct'],100*int(r100['reference_incomplete_queries'])/n)
        eq(c['B32_K100_incomplete_pct'],100*(n-int(r100['actual_full_success_queries']))/n)
        eq(c['GT10_K1_rescue_pct'],100*int(gs['rescued_members'])/int(gs['reference_missing_members']))
        eq(c['B32_K1_rescue_pct'],100*int(rs['rescued_members'])/int(rs['reference_missing_members']))
        eq(c['K100_improved_pct'],100*int(r100['net_improved_queries'])/int(r100['reference_incomplete_queries']))
        eq(c['K100_full_repair_pct'],100*int(r100['failed_queries_become_full_success'])/int(r100['reference_incomplete_queries']))
        eq(c['K100_member_repair_pct'],100*int(r100['rescued_members'])/int(r100['reference_missing_members']))
        eq(c['recall_gain_pp'],100*(int(r100['rescued_members'])-int(r100['damaged_members']))/(n*100))
        eq(c['qps_delta_pct'],100*(num(c,'B32_qps')/num(c,'GT_qps')-1))
        assert int(rs['damaged_members'])==int(r100['damaged_members'])==0
    curve=rows(H/'K100_measured_curves.csv');allpoints=rows(E183/'analysis/final_v1/points.csv')
    original={(r['dataset'],r['method'],r['K'],r['L']):r for r in allpoints}
    assert len(curve)==147
    for r in curve:assert r==original[(r['dataset'],r['method'],r['K'],r['L'])]
    for path,v in json.loads((H/'inputs_manifest.json').read_text()).items():assert sha(Path(path))==v['sha256'],path
    # Every file in the original E184 delivery still has its original scientific bytes.
    legacy=json.loads((E184/'delivery_manifest.json').read_text())
    for path,v in legacy.items():assert sha(E184/path)==v['sha256'],path
    render=json.loads((H/'pdf_render_receipt.json').read_text());build=json.loads((H/'build_checks.json').read_text())
    assert len(render['pages'])==6 and len(build['pages'])==6
    pdf=H/build['pdf'];assert sha(pdf)==build['pdf_sha256']==render['pdf_sha256']
    text=(H/'review_pages/extracted_text.txt').read_text();clean=re.sub(r'\s+','',text)
    for expected in ['19.44%','16.37%','448/2237','307/1944','73.20%','16.43%','29.459%',
                     '1934.02','1867.56','2690.89','2522.93','0.964','8.17/11.50']:
        assert expected in clean,expected
    for p in H.glob('*.py'):ast.parse(p.read_text())
    for p in render['pages']:
        q=H/p['png'];assert sha(q)==p['png_sha256']
    doc_names=['summary.md','spec.md','s-experiment.md','readme.md','LOCAL_CODEX_START.md','experiment_history/184_residual_geometry_diagnosis_v1.md']
    broken=[]
    for p in [H/'README.md']+[REPO/n for n in doc_names]:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://' in link or link.startswith('#'):continue
            target=(p.parent/link.split('#')[0]).resolve()
            if target in [H/'delivery_validation.json',H/'manifest.json']:continue
            if not target.exists():broken.append((str(p),link))
    assert not broken,broken
    check={'status':'PASS_SIX_PAGE_PDF_NUMERIC_AND_ACTUAL_RENDER_REVIEW','pdf':pdf.name,'pdf_sha256':sha(pdf),
        'pages':6,'datasets':7,'source_queries':56000,'source_K100_curve_points':147,'L200_source_comparisons':28,
        'numeric_review':'stdlib arithmetic independent of plotter; all seven datasets and all 147 copied curve points',
        'visual_review':{'reviewer':'root','actual_PDF_pages_rendered':list(range(1,7)),
            'contact_sheet_viewed':True,'full_pages_viewed':[2,3,4,5,6],
            'checks':['Chinese renders correctly','all dataset labels readable','denominators stated',
                      'legends and captions separated','table columns and actual point labels legible','no clipping observed']},
        'old_E184_delivered_files_unchanged':len(legacy),'scientific_inputs_unchanged':True,
        'new_experiments':0,'default_changed':False,'broken_current_links':broken,
        'current_document_sha256':{n:sha(REPO/n) for n in doc_names},
        'review_limits':'same executor; no new GT, bootstrap, independent reviewer, timing or causal inference'}
    (H/'delivery_validation.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
    manifest={str(p.relative_to(H)):{'bytes':p.stat().st_size,'sha256':sha(p)}
        for p in H.rglob('*') if p.is_file() and p.name!='manifest.json'}
    (H/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':check['status'],'pdf':str(pdf),'pages':6,'manifest_files':len(manifest)},ensure_ascii=False))

if __name__=='__main__':main()
