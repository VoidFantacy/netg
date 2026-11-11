from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[3]
R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261104_gate_timing_cost_v1'
sys.path.insert(0,str(E/'storage/pdf_renderer'))
import pymupdf
pdf=R/'残差方法筛选与成本_图解精简版_20261104.pdf'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=pymupdf.open(pdf); assert len(doc)==5
dest=R/'reviews/pdf_pages';dest.mkdir(exist_ok=True)
texts=[];records=[];thumbs=[]
for i,page in enumerate(doc):
    p=dest/f'page_{i+1:02}.png'
    page.get_pixmap(matrix=pymupdf.Matrix(1.8,1.8),alpha=False).save(p)
    s=page.get_text();assert len(s)>300 and '\ufffd' not in s
    texts.append(s);records.append(dict(page=i+1,chars=len(s),render_sha256=sha(p)))
    im=Image.open(p).convert('RGB');im.thumbnail((700,500))
    tile=Image.new('RGB',(720,530),'#edf2f6');tile.paste(im,((720-im.width)//2,25));ImageDraw.Draw(tile).text((10,8),f'Actual PDF page {i+1}',fill='#21394a');thumbs.append(tile)
alltext='\n\n'.join(texts)
for term in ['Recall@100','Recall@1','COCO','Flickr','WebVid','Yandex','79','80','0.025','129','0.098','停止','直接补点']:
    assert term in alltext,term
(dest/'extracted_text.txt').write_text(alltext)
sheet=Image.new('RGB',(2160,1060),'white')
for i,im in enumerate(thumbs):sheet.paste(im,((i%3)*720,(i//3)*530))
sheet.save(dest/'contact_sheet.png')
(R/'reviews/pdf_render.json').write_text(json.dumps(dict(status='RENDERED_PENDING_VISUAL_REVIEW',actual_pdf=True,renderer='PyMuPDF '+pymupdf.VersionBind,pdf_sha256=sha(pdf),pages=records,text_chars=len(alltext)),indent=2)+'\n')
print('Rendered 5 actual PDF pages; text checks passed')
