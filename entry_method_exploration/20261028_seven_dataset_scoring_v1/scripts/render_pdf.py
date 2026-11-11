"""Render every authorized PDF page and verify embedded evidence byte-for-byte."""
import hashlib, json, math, sys, time
from pathlib import Path
sys.path.insert(0,'/tmp/acsg_e187_pdf_tool')
import fitz
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    t=time.perf_counter();build=json.loads((R/'reviews/pdf_build.json').read_text());path=Path(build['path']);assert sha(path.read_bytes())==build['pdf_sha256']
    pdf=fitz.open(path);assert len(pdf)==build['pages'] and len(pdf)>=18
    out=R/'reviews/pdf_render';out.mkdir(exist_ok=True);receipts=[];outside=[];pages=[];texts=[]
    for i,page in enumerate(pdf):
        pix=page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False);png=out/f'page{i+1:02d}.png';pix.save(png);text=page.get_text();assert len(text)>80,(i,len(text));texts.append(text)
        for b in page.get_text('blocks'):
            if b[0]<-1 or b[1]<-1 or b[2]>page.rect.width+1 or b[3]>page.rect.height+1:outside.append(dict(page=i+1,bbox=list(b[:4])))
        receipts.append(dict(page=i+1,title=build['page_titles'][i],text_chars=len(text),png=str(png),png_sha256=sha(png.read_bytes())))
        im=Image.open(png).convert('RGB');im.thumbnail((840,595));pages.append(im)
    assert not outside,outside
    full=''.join(texts)
    for word in ['E191','Deep10M','SIFT10M','GIST1M','COCO','Flickr30k','WebVid','Yandex','GT10','REUSE-SQ','MAIN-SQ','448','1344']:assert word in full,word
    for x in build['attachments']:
        p=R/x['path'];assert sha(p.read_bytes())==x['sha256'];assert sha(pdf.embfile_get(p.name))==x['sha256'],p.name
    assert pdf.embfile_count()==len(build['attachments'])
    sheets=[]
    for start in range(0,len(pages),8):
        ims=pages[start:start+8];sheet=Image.new('RGB',(1720,math.ceil(len(ims)/2)*625),'#e2e8f0');draw=ImageDraw.Draw(sheet)
        for j,im in enumerate(ims):
            x,y=10+(j%2)*860,20+(j//2)*625;sheet.paste(im,(x,y));draw.text((x,y-15),f'Page {start+j+1}',fill='#0f172a')
        p=out/f'contact_sheet_{start//8+1:02d}.png';sheet.save(p);sheets.append(str(p))
    (out/'extracted_text.txt').write_text('\n\n'.join(texts))
    v=dict(status='PASS_E191_ALL_PAGE_PDF_AND_ATTACHMENTS',pages=receipts,embedded_files=build['attachments'],outside_page_text_blocks=outside,contact_sheets=sheets,pdf_sha256=build['pdf_sha256'],seconds=time.perf_counter()-t,scope='rasterized every page; bounds, text keys and attachment bytes checked; human-style visual inspection recorded separately')
    (R/'reviews/pdf_validation.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(status=v['status'],pages=len(pdf),attachments=pdf.embfile_count(),contact_sheets=sheets)),flush=True)
if __name__=='__main__':main()
