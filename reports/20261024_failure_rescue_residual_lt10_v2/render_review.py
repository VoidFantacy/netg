#!/usr/bin/env python3
"""Render the actual five-page PDF, keeping review receipts separate from inputs."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'/tmp/acsg_pdf_render_20261024')
import pymupdf
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent
P=R/'ACSG_低于10%召回的查询比例_全L修正版_20261024.pdf'

def main():
    out=R/'review_pages';out.mkdir(exist_ok=True);doc=pymupdf.open(P);assert len(doc)==5
    alltext=[];pages=[];thumbs=[]
    for i,page in enumerate(doc):
        fn=out/f'page_{i+1:02d}_actual.png'
        page.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6),alpha=False).save(fn)
        txt=page.get_text();assert len(txt)>100;alltext.append(f'PAGE {i+1}\n{txt}')
        im=Image.open(fn).convert('RGB');im.thumbnail((841,595))
        canvas=Image.new('RGB',(861,635),'#eaf0f5');canvas.paste(im,((861-im.width)//2,30))
        ImageDraw.Draw(canvas).text((12,10),f'PDF page {i+1}',fill='#172f40');thumbs.append(canvas)
        pages.append(dict(page=i+1,png=str(fn.relative_to(R)),sha256=hashlib.sha256(fn.read_bytes()).hexdigest()))
    sheet=Image.new('RGB',(1722,1905),'white')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%2)*861,(i//2)*635))
    sheet.save(out/'contact_sheet.png');full='\n'.join(alltext);(out/'extracted_text.txt').write_text(full)
    # Type3 CJK/non-ASCII glyphs render correctly but are not all extractable as Unicode.
    # The strict numeric formula remains extractable; the 0-9/CJK text is visually reviewed.
    for term in ['Deep10M','SIFT10M','GIST1M','WebVid','Yandex','COCO','Flickr30k',
                 'Recall@100 < 10%','9 / 100 = 9%','10 / 100 = 10%','1.92%','0.53%','0.14%']:assert term in full,term
    (R/'pdf_render_receipt.json').write_text(json.dumps(dict(status='ACTUAL_PDF_RENDERED_AWAITING_VISUAL_REVIEW',
        pages=pages,renderer='PyMuPDF',version=pymupdf.VersionBind,pdf_sha256=hashlib.sha256(P.read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
    print('PASS actual PDF rendered, five pages')
if __name__=='__main__':main()
