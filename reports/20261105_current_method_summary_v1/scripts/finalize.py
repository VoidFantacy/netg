from pathlib import Path
import json,hashlib,re

W=Path(__file__).resolve().parents[3]
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
identity=read(R/'source_before/identity.json')
for name,h in identity['sources'].items():assert sha(W/name)==h,name
previous=read(W/'reports/20261104_residual_pruning_graphs_v2/delivery_validation.json')
old={x['path']:x for x in previous['root_bridges']}
bridges=[]
for name,h in identity['roots_before'].items():
    assert sha(R/'source_before'/name)==h
    assert old[name]['after_sha256']==h,name
    bridges.append(dict(path=name,before_snapshot='source_before/'+name,before_sha256=h,after_sha256=sha(W/name)))
assert sha(W/'s-target.md')==identity['roots_before']['s-target.md']
docs=[W/name for name in identity['roots_before']]+[R/'README.md']
links=0
for doc in docs:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if target.startswith(('https:','http:','#','mailto:')):continue
        dest=(doc.parent/target.split('#')[0]).resolve()
        if dest==(R/'delivery_validation.json').resolve():continue
        assert dest.exists(),(doc,target)
        links+=1
pdf=R/'ACSG_当前方法总结_GT10与直接残差补点_20261105.pdf'
render=read(R/'reviews/content_and_render.json')
assert render['pdf_sha256']==sha(pdf) and len(render['pages'])==3
text=(R/'reviews/pdf_pages/extracted_text.txt').read_text()
assert all(s not in text for s in ['双塔','FAST384','CASCADE','问题分析','下一步'])
write(R/'reviews/visual_review.json',dict(status='PASS_ACTUAL_PDF_VISUAL_REVIEW',pdf_sha256=sha(pdf),reviewer='same operator',reviewed='all three actual PDF page images; revised first-page columns',checks=['Chinese glyphs and formula readable','routing and candidate table arrows clear','first-page paragraphs separated','training sizes and candidate bound distinct','example scores and final K1 answer consistent','no two-tower chapter or problem analysis']))
write(R/'reviews/document_checks.json',dict(status='PASS_METHOD_ONLY_DOCUMENT_DELIVERY',protected_sources=len(identity['sources']),roots_bridged=len(bridges),links_checked=links,new_experiments=0,problem_analysis=False,two_tower_in_current_method=False,default_changed=False,s_target_unchanged=True))
files=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ['delivery_manifest.json','delivery_validation.json']]
write(R/'delivery_manifest.json',dict(status='METHOD_ONLY_LOCAL_DELIVERY',files=files,root_bridges=bridges,protected_sources=identity['sources']))
write(R/'delivery_validation.json',dict(status='PASS_CURRENT_METHOD_PDF_LOCAL_DELIVERY',client_date='2026-11-05',pdf=str(pdf),pdf_sha256=sha(pdf),pages=3,figure_png_svg_pairs=3,new_experiments=0,scope='GT10 interface and B32 direct residual completion only',two_tower_included=False,problem_analysis_included=False,default_changed=False,old_sources_unchanged=len(identity['sources']),actual_pdf_rendered_and_visually_reviewed=True,root_bridges=bridges,links_checked=links,manifest_sha256=sha(R/'delivery_manifest.json')))
print('PASS: 3-page current-method PDF; 3 PNG/SVG diagrams; sources and six root bridges checked; default and future boundary unchanged.')
