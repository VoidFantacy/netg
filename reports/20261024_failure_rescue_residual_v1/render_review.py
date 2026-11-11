#!/usr/bin/env python3
"""Render the actual PDF for review, not a substitute figure export."""
import sys
from pathlib import Path
import hashlib
import json
sys.path.insert(0,'/tmp/acsg_pdf_render_20261024')
import pymupdf as fitz
from PIL import Image, ImageDraw

R=Path(__file__).resolve().parent
P=R/'ACSG_失败率_救回率与残差作用_20261024.pdf'

def main():
    out=R/'review_pages';out.mkdir(exist_ok=True)
    doc=fitz.open(P);assert len(doc)==6
    text=[];pages=[]
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
        file=out/f'page_{i+1:02d}_actual.png';pix.save(file)
        s=page.get_text();assert len(s)>100
        text.append(f'PAGE {i+1}\n{s}')
        pages.append({'page':i+1,'width_pt':page.rect.width,'height_pt':page.rect.height,
            'png':str(file.relative_to(R)),'png_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'extracted_text_chars':len(s)})
    full='\n'.join(text);(out/'extracted_text.txt').write_text(full)
    for term in ['Deep10M','SIFT10M','GIST1M','WebVid','Yandex','COCO','Flickr30k']:
        assert term in full,term
    thumbs=[]
    for p in pages:
        im=Image.open(R/p['png']).convert('RGB');im.thumbnail((841,595))
        canvas=Image.new('RGB',(861,635),'#eaf0f5');canvas.paste(im,((861-im.width)//2,30))
        ImageDraw.Draw(canvas).text((12,10),f"PDF page {p['page']}",fill='#172f40');thumbs.append(canvas)
    sheet=Image.new('RGB',(1722,1905),'white')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%2)*861,(i//2)*635))
    sheet.save(out/'contact_sheet.png')
    receipt={'status':'ACTUAL_PDF_RENDERED_PENDING_HUMAN_VISUAL_REVIEW','pdf':str(P),'pdf_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),
        'pages':pages,'renderer':'PyMuPDF','renderer_version':fitz.VersionBind,'contact_sheet':'review_pages/contact_sheet.png',
        'rendered_actual_pdf_not_matplotlib_preview':True}
    (R/'pdf_render_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pages':len(doc),'text_chars':len(full),'contact_sheet':str(out/'contact_sheet.png')}))

if __name__=='__main__':main()
