#!/usr/bin/env python3
import json,sys,time
from pathlib import Path
sys.path.insert(0,'/tmp/acsg_e187_pdf_tool')
import fitz
from PIL import Image,ImageOps,ImageDraw
R=Path(__file__).resolve().parents[1]
def main():
    t=time.perf_counter();path=R/'ACSG_自适应残差补全_实验对比_20261028.pdf';doc=fitz.open(path);assert len(doc)==6
    out=R/'reviews/pdf_render';out.mkdir(exist_ok=True);pages=[];receipt=[];outside=[]
    for i,page in enumerate(doc):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False);pix.save(out/f'page{i+1}.png')
        text=page.get_text();assert len(text)>200
        for b in page.get_text('blocks'):
            if b[0]<-1 or b[1]<-1 or b[2]>page.rect.width+1 or b[3]>page.rect.height+1:outside.append(dict(page=i+1,bbox=list(b[:4])))
        receipt.append(dict(page=i+1,width=page.rect.width,height=page.rect.height,text_chars=len(text)))
        im=Image.open(out/f'page{i+1}.png').convert('RGB');im.thumbnail((850,610));pages.append(im)
    assert not outside,outside
    sheet=Image.new('RGB',(1740,1890),'#dde4ea')
    for i,im in enumerate(pages):sheet.paste(im,(15+(i%2)*870,15+(i//2)*630))
    sheet.save(out/'contact_sheet.png')
    (R/'reviews/pdf_validation.json').write_text(json.dumps(dict(status='PASS_SIX_PAGE_PDF',pages=receipt,outside_page_text_blocks=outside,renderer='PyMuPDF, task-local /tmp package',contact_sheet=str(out/'contact_sheet.png'),seconds=time.perf_counter()-t),indent=2)+'\n')
    print('PASS six-page PDF render and page bounds')
if __name__=='__main__':main()
