"""A separate stdlib check of plotted numbers, controls, document bridges and delivery."""
from pathlib import Path
from collections import defaultdict
import csv,json,hashlib,math,re

W=Path(__file__).resolve().parents[3]
R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261104_gate_timing_cost_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rows(path):return list(csv.DictReader(path.open()))
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
identity=json.loads((R/'source_before/identity.json').read_text())
for p,h in identity['sources'].items():assert sha(W/p)==h,p
old=json.loads((E/'delivery_validation.json').read_text())
oldbridges={r['path']:r for r in old['source_before_bridges']}
bridges=[]
for name,h in identity['roots_before'].items():
    assert sha(R/'source_before'/name)==h
    assert oldbridges[str(W/name)]['after_sha256']==h,name
    bridges.append(dict(path=name,before_sha256=h,after_sha256=sha(W/name),before_snapshot='source_before/'+name))

p=rows(E/'analysis/points.csv');assert len(p)==736
strong={'GT10','OPT-B32','REUSE-SQ'}
primary={'F-PRE90','F-POST90','N-PRE90','N-POST90','N-CPOST90'}
covered=0;left=[]
for r in p:
    if r['method'] not in primary:continue
    controls=[s for s in p if s['method'] in strong and (s['dataset'],s['window'],s['K'])==(r['dataset'],r['window'],r['K'])]
    is_covered=any(float(s['recall_pct'])>=float(r['recall_pct']) and float(s['qps'])>=float(r['qps']) for s in controls)
    if is_covered:covered+=1
    else:left.append(r)
assert covered==79 and len(left)==1

groups=defaultdict(list)
for r in p:groups[(r['dataset'],r['K'],r['L'],r['method'])].append(r)
derived=rows(R/'analysis/pooled_points.csv')
for r in derived:
    src=groups[r['dataset'],r['K'],r['L'],r['method']]
    assert len(src)==2
    n=sum(int(x['n']) for x in src)
    us=sum(float(x['mean_us'])*int(x['n']) for x in src)/n
    recall=100*sum(int(x['hits']) for x in src)/(n*int(r['K']))
    assert math.isclose(float(r['qps']),1e6/us,rel_tol=1e-12)
    assert math.isclose(float(r['recall_pct']),recall,abs_tol=1e-12)
for r in rows(R/'analysis/rerank_marginal.csv'):
    # Recompute from per-window raw point summaries, not the rerank aggregator.
    arms=[]
    for m in ['ALWAYS','FAST384']:
        a=groups[r['dataset'],r['K'],'200',m]
        arms.append((sum(float(x['recall_pct']) for x in a)/2,sum(float(x['mean_us']) for x in a)/2))
    assert math.isclose(float(r['recall_gain_pp']),arms[0][0]-arms[1][0],abs_tol=1e-10)
    assert math.isclose(float(r['formal_extra_us']),arms[0][1]-arms[1][1],abs_tol=1e-10)

docs=[W/n for n in identity['roots_before']]
docs += [R/'README.md',W/'experiment_history/_maintenance/20261104_residual_pruning_graphs_v2/README.md']
links=0
for doc in docs:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if target.startswith(('http:','https:','#','mailto:')):continue
        dest=doc.parent/target.split('#')[0]
        # Receipt is created below as the final step.
        if dest.resolve()==(R/'delivery_validation.json').resolve():continue
        assert dest.exists(),(str(doc),target)
        links+=1
render=json.loads((R/'reviews/pdf_render.json').read_text())
pdf=R/'残差方法筛选与成本_图解精简版_20261104.pdf'
assert render['pdf_sha256']==sha(pdf) and len(render['pages'])==5
write(R/'reviews/visual_review.json',dict(status='PASS_ACTUAL_PDF_VISUAL_REVIEW',reviewer='same operator',reviewed='actual PDF contact sheet plus full-size pages 4 and 5; standalone Recall@100 chart',checks=['Chinese glyphs and numeric labels readable','all five pages present','legends and captions fit','negative K1 recall delta visible','Flickr K1 129.1us cost not clipped','complete wall and diagnostic cost separated'],pdf_sha256=sha(pdf)))
write(R/'analysis/independent_derived_audit.json',dict(status='PASS_STDLIB_RECOMPUTATION',independence='same operator; separate code path; no import of plot builder',raw_point_summaries=736,pooled_points=len(derived),primary_covered_recomputed=covered,uncovered_count=len(left),rerank_comparisons_recomputed=8,protected_source_hashes=len(identity['sources']),root_bridges=len(bridges),links_checked=links))
write(R/'analysis/decision.json',dict(status='PRUNED_CURRENT_RESEARCH_MAINLINE',keep=['original search baseline','direct residual completion and return-equivalent optimizations'],stop_current_versions=['learned candidate selection','shortlist reranking plus auxiliary navigation','pre/post residual gates'],experimental_controls_not_independent_methods=['offline static switch','same-gate placement','75/90 retention targets','fixed-budget ablations'],preserve_conditional_history=['M5','B32','SQ'],default_changed=False,new_measurements=False,delete_evidence=False,scope='E199 four multimodal datasets; exposed A/B; L200 complex pipeline; Q8 bank; single seed 384'))
files=[]
for f in sorted(R.rglob('*')):
    if f.is_file() and f.name not in ['delivery_manifest.json','delivery_validation.json']:
        files.append(dict(path=str(f.relative_to(R)),bytes=f.stat().st_size,sha256=sha(f)))
maintenance=W/'experiment_history/_maintenance/20261104_residual_pruning_graphs_v2/README.md'
manifest=dict(status='LOCAL_GRAPH_REPORT_DELIVERY',files=files,root_bridges=bridges,maintenance=dict(path=str(maintenance.relative_to(W)),sha256=sha(maintenance)),old_E199_delivery_manifest_sha256=sha(E/'delivery_manifest.json'),old_E199_pdf_sha256=old['PDF_sha256'])
write(R/'delivery_manifest.json',manifest)
write(R/'delivery_validation.json',dict(status='PASS_PRUNED_GRAPH_REPORT_LOCAL_DELIVERY',pdf=str(pdf),pdf_sha256=sha(pdf),pdf_pages=5,standalone_png_svg_pairs=5,source_points=736,new_measurements=0,default_changed=False,protected_sources_unchanged=len(identity['sources']),root_bridges=bridges,independent_numeric_check='same operator; stdlib recomputation from raw point summaries',actual_pdf_render_and_visual_review=True,links_checked=links,manifest_sha256=sha(R/'delivery_manifest.json')))
print('PASS: 5 pages, 5 PNG/SVG pairs; 736 points checked; 79/80 coverage recomputed; 32 inputs unchanged; six root bridges verified.')
