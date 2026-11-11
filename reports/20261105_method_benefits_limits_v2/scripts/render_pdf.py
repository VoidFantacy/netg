from pathlib import Path
import json,sys,hashlib
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261104_gate_timing_cost_v1'
sys.path.insert(0,str(E/'storage/pdf_renderer'))
import pymupdf
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'ACSG_当前方法_残差收益_低召回修复与局限_20261105.pdf'
doc=pymupdf.open(p);assert len(doc)==8
dest=R/'reviews/pdf_pages';dest.mkdir(exist_ok=True);texts=[];records=[];tiles=[]
for i,page in enumerate(doc):
    d=dest/f'page_{i+1:02}.png';page.get_pixmap(matrix=pymupdf.Matrix(1.8,1.8),alpha=False).save(d)
    s=page.get_text();assert len(s)>180 and '\ufffd' not in s;texts.append(s)
    records.append(dict(page=i+1,chars=len(s),render_sha256=sha(d)))
    im=Image.open(d).convert('RGB');im.thumbnail((620,445));tile=Image.new('RGB',(640,475),'#ECF2F6');tile.paste(im,((640-im.width)//2,24));ImageDraw.Draw(tile).text((10,7),f'Actual PDF page {i+1}',fill='#23394a');tiles.append(tile)
alltext='\n\n'.join(texts);(dest/'extracted_text.txt').write_text(alltext)
for term in ['GT10','B32','Recall@1','Recall@100','113','128','142','53','46','174','86','85','1.3715','0.37%','局限一','局限二','工程','创新性','E199','E183']:
    assert term in alltext,term
for term in ['FAST384','CASCADE384','POLICY384']:
    assert term not in alltext,term
original=pymupdf.open(W/'reports/20261105_current_method_summary_v1/ACSG_当前方法总结_GT10与直接残差补点_20261105.pdf')
for i in range(3):assert texts[i]==original[i].get_text()
sheet=Image.new('RGB',(2560,950),'white')
for i,tile in enumerate(tiles):sheet.paste(tile,((i%4)*640,(i//4)*475))
sheet.save(dest/'contact_sheet.png')
(R/'reviews/pdf_render.json').write_text(json.dumps(dict(status='RENDER_AND_CONTENT_CHECKS_PASS_PENDING_VISUAL_REVIEW',actual_pdf=True,pdf_sha256=sha(p),renderer='PyMuPDF '+pymupdf.VersionBind,pages=records,original_first_three_pages_text_identical=True,methods_exclude_failed_two_tower_branch=True,limitations_qualified_as_research_judgment=True),ensure_ascii=False,indent=2)+'\n')
print('Rendered all 8 actual PDF pages; content and first-three-page identity checked.')
