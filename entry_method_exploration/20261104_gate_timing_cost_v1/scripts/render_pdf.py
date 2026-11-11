from common import *
sys.path.insert(0,str(R/'storage/pdf_renderer'))
import pymupdf
from PIL import Image,ImageDraw
p=R/'E199_残差门控时机与精排成本_20261104.pdf';doc=pymupdf.open(p);assert len(doc)==16;root=R/'reviews/pdf_pages';root.mkdir(exist_ok=True);records=[];texts=[];thumbs=[]
for i,page in enumerate(doc):
    image=page.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6),alpha=False);dest=root/f'page_{i+1:02d}.png';image.save(dest);s=page.get_text();assert len(s)>120;assert '\ufffd' not in s;texts.append(s)
    records.append(dict(page=i+1,text_chars=len(s),png=str(dest.relative_to(R)),png_sha256=sha(dest),size_pt=[page.rect.width,page.rect.height]))
    im=Image.open(dest).convert('RGB');im.thumbnail((600,425));tile=Image.new('RGB',(620,455),'#eaf0f4');tile.paste(im,((620-im.width)//2,25));ImageDraw.Draw(tile).text((10,8),f'Actual PDF page {i+1}',fill='#19364a');thumbs.append(tile)
full='\n\n'.join(texts)
for term in ['E199','COCO','Flickr','WebVid','Yandex','PRE','POST','精排','736','2208']:assert term in full,term
(root/'extracted_text.txt').write_text(full);sheet=Image.new('RGB',(2480,1820),'white')
for i,tile in enumerate(thumbs):sheet.paste(tile,((i%4)*620,(i//4)*455))
sheet.save(root/'contact_sheet.png');dump(R/'reviews/pdf_render.json',dict(status='ACTUAL_PDF_RENDERED_PENDING_VISUAL_REVIEW',pdf=str(p),pdf_sha256=sha(p),renderer='PyMuPDF '+pymupdf.VersionBind,pages=records,contact_sheet=str(root/'contact_sheet.png'),text_chars=len(full),source_actual_pdf=True))
print('RENDERED_ACTUAL_PDF',len(doc),'pages',flush=True)
