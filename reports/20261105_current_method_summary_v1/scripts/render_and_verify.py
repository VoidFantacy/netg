from pathlib import Path
import sys,json,hashlib,re
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[3]
R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261104_gate_timing_cost_v1'
sys.path.insert(0,str(E/'storage/pdf_renderer'))
import pymupdf
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pdf=R/'ACSG_当前方法总结_GT10与直接残差补点_20261105.pdf'
doc=pymupdf.open(pdf);assert len(doc)==3
out=R/'reviews/pdf_pages';out.mkdir(exist_ok=True)
texts=[];records=[];tiles=[]
for i,page in enumerate(doc):
    dest=out/f'page_{i+1:02}.png'
    page.get_pixmap(matrix=pymupdf.Matrix(1.9,1.9),alpha=False).save(dest)
    s=page.get_text();assert len(s)>300 and '\ufffd' not in s
    texts.append(s);records.append(dict(page=i+1,chars=len(s),png_sha256=sha(dest)))
    im=Image.open(dest).convert('RGB');im.thumbnail((720,510))
    tile=Image.new('RGB',(740,540),'#edf3f7');tile.paste(im,((740-im.width)//2,25));ImageDraw.Draw(tile).text((10,8),f'Actual PDF page {i+1}',fill='#21394a');tiles.append(tile)
alltext='\n\n'.join(texts);(out/'extracted_text.txt').write_text(alltext)
for term in ['GT10','B32','16,000','8,000','96','K100 / L200','覆盖','严格替换','0.91','最终K1返回 c','学习排序器']:
    assert term in alltext,term
for term in ['双塔','CASCADE','FAST384','精排导航','问题分析','下一步','QPS优势']:
    assert term not in alltext,term
sheet=Image.new('RGB',(2220,540),'white')
for i,tile in enumerate(tiles):sheet.paste(tile,(i*740,0))
sheet.save(out/'contact_sheet.png')
identity=json.loads((R/'source_before/identity.json').read_text())
for p,h in identity['sources'].items():assert sha(W/p)==h,p
compiler=(W/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/src/residual_tools.cpp').read_text()
runtime=(W/'entry_method_exploration/20261030_residual_optimization_stability_v1/src/benchmark.cpp').read_text()
for snippet in ['teacher_K") ==100','for(int cap:{8,16,32})']:
    if snippet.startswith('teacher'):assert 'teacher_K")==100' in compiler
    else:assert snippet in compiler
assert 'nc<96' in runtime and 'fast_plan(p,route,I,K)' in runtime and 'dc(p.candidate[j])' in runtime
# Check only the explanatory toy arithmetic; no ANN/model execution.
toy_rows=[['a','c'],['c','d'],['b','d']];scores={'a':.8,'b':.76,'c':.91,'d':.83}
candidate=set().union(*map(set,toy_rows))-{'a'}
assert candidate=={'b','c','d'} and max(candidate|{'a'},key=scores.get)=='c'
receipt=dict(status='ACTUAL_PDF_RENDER_AND_CONTENT_CHECKS_PASS_PENDING_VISUAL_REVIEW',pdf_sha256=sha(pdf),renderer='PyMuPDF '+pymupdf.VersionBind,pages=records,protected_sources_unchanged=len(identity['sources']),toy_only_not_experiment=True,current_method_excludes_two_tower=True,problem_analysis_excluded=True)
(R/'reviews/content_and_render.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('PASS: 3 rendered pages; current-method scope, source hashes and explanatory arithmetic verified')
