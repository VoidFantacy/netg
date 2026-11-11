"""Check derived chart/table numbers, immutable inputs, PDF and document bridges."""
from pathlib import Path
from collections import defaultdict
import csv,json,hashlib,math,re
W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def rows(p):return list(csv.DictReader(p.open()))
def write(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
identity=read(R/'source_before/identity.json')
for n,h in identity['sources'].items():assert sha(W/n)==h,n
for name,h in identity['prior_delivery_files'].items():assert sha(W/name)==h,name
old=read(W/identity['prior_delivery'])
before={x['path']:x for x in old['root_bridges']};bridges=[]
for n,h in identity['roots_before'].items():
    assert sha(R/'source_before'/n)==h and before[n]['after_sha256']==h,n
    bridges.append(dict(path=n,before_snapshot='source_before/'+n,before_sha256=h,after_sha256=sha(W/n)))
raw=rows(W/'entry_method_exploration/20261104_gate_timing_cost_v1/analysis/points.csv')
group=defaultdict(list)
for r in raw:
    if r['method'] in ['GT10','OPT-B32']:group[r['dataset'],r['K'],r['L'],r['method']].append(r)
curves=rows(R/'analysis/E199_two_family_curves.csv');assert len(curves)==len(group)==208
for name in ['E199_two_family_curves.csv','E183_L200_benefits_and_costs.csv']:
    assert (R/'analysis'/name).read_bytes()==(W/'reports/20261105_method_benefits_limits_v2/analysis'/name).read_bytes(),name
for r in curves:
    src=group[r['dataset'],r['K'],r['L'],r['method']];n=sum(int(x['n']) for x in src)
    total_us=sum(float(x['mean_us'])*int(x['n']) for x in src)
    recall=100*sum(int(x['hits']) for x in src)/(n*int(r['K']))
    assert math.isclose(float(r['recall_pct']),recall,abs_tol=1e-10)
    assert math.isclose(float(r['qps']),1e6*n/total_us,rel_tol=1e-12)
source=rows(W/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv')
lookup={(x['dataset'],x['K'],x['L'],x['method']):x for x in source}
costs=rows(R/'analysis/E183_L200_benefits_and_costs.csv');assert len(costs)==8
tail=rows(W/'reports/20261105_low_recall_stage_attribution_v1/analysis/stage_attribution_four_multimodal.csv')
for r in costs:
    fam='soft' if r['dataset'].startswith('webvid') else 'hard'
    a=lookup[r['dataset'],r['K'],'200','GT10-soft-t1' if fam=='soft' else 'GT10-hard']
    b=lookup[r['dataset'],r['K'],'200',fam+'-JOINT32']
    assert math.isclose(float(r['recall_gain_pp']),float(b['recall_pct'])-float(a['recall_pct']),abs_tol=1e-10)
    assert math.isclose(float(r['qps_change_pct']),100*(float(b['qps'])-float(a['qps']))/float(a['qps']),abs_tol=1e-10)
    assert math.isclose(float(r['extra_us']),1e6/float(b['qps'])-1e6/float(a['qps']),abs_tol=1e-10)
    if r['K']=='100':
        t=next(x for x in tail if x['dataset']==r['dataset'] and x['L']=='200')
        assert r['B32_extra_low_recall_rescues']==t['B32_rescued']
    else:assert r['B32_extra_low_recall_rescues']==''
pdf=R/'ACSG_当前方法_残差收益_低召回修复与局限_20261105.pdf'
render=read(R/'reviews/pdf_render.json');assert render['pdf_sha256']==sha(pdf) and len(render['pages'])==8
assert render['original_first_three_pages_text_identical']
text=(R/'reviews/pdf_pages/extracted_text.txt').read_text()
assert '工程' in text and '创新性' in text and '残差收益不全面' in text
assert 'FAST384' not in text and 'CASCADE384' not in text
assert '仅展示合并曲线' in text and '浅线' not in text and '逐窗' not in text
assert 'GT10较NSG新增1条' in text and 'B32未新增，也未救回' in text
audit=read(R/'reviews/coco_raw_audit.json')
assert audit['status']=='PASS_COCO_RAW_GT_AND_21_TIMED_PACKETS' and audit['points']==21
assert audit['L200_query_4815_hits']==[97,3,3] and audit['B32_new_low_all_L']==0
docs=[W/n for n in identity['roots_before']]+[R/'README.md'];links=0
for doc in docs:
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if link.startswith(('https:','http:','#','mailto:')):continue
        dest=(doc.parent/link.split('#')[0]).resolve()
        if dest==(R/'delivery_validation.json').resolve():continue
        assert dest.exists(),(doc,link)
        links+=1
visual=read(R/'reviews/visual_review.json')
assert visual['status']=='PASS_ACTUAL_EIGHT_PAGE_PDF_VISUAL_REVIEW' and visual['pdf_sha256']==sha(pdf)
write(R/'reviews/numeric_and_document_checks.json',dict(status='PASS_DERIVED_NUMBERS_AND_DOCUMENTS',curve_points_recomputed=208,L200_cost_rows_recomputed=8,pooled_curve_and_cost_CSV_bytes_unchanged=True,COCO_raw_points_reaudited=21,COCO_query_point_evaluations=210000,source_hashes_unchanged=len(identity['sources']),prior_delivery_files_unchanged=len(identity['prior_delivery_files']),root_bridges=len(bridges),links_checked=links,new_experiments=0,default_changed=False))
files=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ['delivery_manifest.json','delivery_validation.json']]
write(R/'delivery_manifest.json',dict(status='LOCAL_METHOD_BENEFITS_LIMITS_PDF_DELIVERY',files=files,root_bridges=bridges,protected_sources=identity['sources']))
write(R/'delivery_validation.json',dict(status='PASS_POOLED_CURVES_ONLY_AND_COCO_FAILURE_ATTRIBUTION',client_date='2026-11-05',pdf=str(pdf),pdf_sha256=sha(pdf),pages=8,original_method_pages_retained=3,standalone_png_svg_pairs=5,performance_curve_source='E199 original two public batches pooled, 1024 queries per dataset; GT10 and full16K OPT-B32',performance_subwindow_lines_removed=True,tail_and_L200_table_source='E183 full windows; preserved original B32 implementation',curve_points_checked=208,cost_rows_checked=8,COCO_raw_points_reaudited=21,COCO_query_point_evaluations=210000,COCO_L200_low_counts=[0,1,1],COCO_L200_query4815_hits=[97,3,3],protected_sources_unchanged=len(identity['sources']),prior_delivery_files_unchanged=len(identity['prior_delivery_files']),actual_pdf_rendered_and_visually_reviewed=True,new_ANN=0,new_GT=0,new_training=0,new_timing=0,default_changed=False,root_bridges=bridges,links_checked=links,manifest_sha256=sha(R/'delivery_manifest.json')))
print('PASS: pooled curves only; 208 points unchanged; COCO 21 raw packets audited; prior delivery unchanged.')
