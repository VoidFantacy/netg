"""Render reviewed prose and existing plots only. No model or search calls."""
import base64,hashlib,html,json,re,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/tmp/acsg_gt10_review_document_tools')
import markdown
import pymupdf
from playwright.sync_api import sync_playwright

R=Path(__file__).resolve().parents[1]
sources=[R/'report.md',R/'directions.md',R/'literature/review.md']
parts=[]
for i,p in enumerate(sources):
    body=markdown.markdown(p.read_text(),extensions=['tables','sane_lists'])
    def img(m):
        fp=(p.parent/m[1]).resolve()
        assert fp.is_file()
        return 'src="data:image/png;base64,'+base64.b64encode(fp.read_bytes()).decode()+'"'
    body=re.sub(r'src="([^"]+)"',img,body)
    def link(m):
        target=m[1]
        if target.startswith(('https:','http:','#')):return m[0]
        fp=(p.parent/target).resolve()
        for j,s in enumerate(sources):
            if fp==s:return f'href="#part{j}"'
        return 'href="'+html.escape(fp.as_uri(),quote=True)+'"'
    body=re.sub(r'href="([^"]+)"',link,body)
    parts.append(f'<article id="part{i}">{body}</article>')
css='''
@font-face {font-family: ReportCJK; src:url('file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); font-weight:400;}
@font-face {font-family: ReportCJK; src:url('file:///usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'); font-weight:700;}
@page {size:A4; margin:15mm 13mm 16mm;}
*{box-sizing:border-box} body{font-family:ReportCJK,'Noto Sans CJK SC',sans-serif;color:#233044;font-size:10pt;line-height:1.6;margin:0}
h1{font-size:20pt;line-height:1.4;color:#173656;margin:0 0 12pt} h2{font-size:14pt;color:#173656;margin:17pt 0 8pt;border-bottom:1px solid #d9e1ea;padding-bottom:4pt;break-after:avoid}
h3{font-size:11.5pt;color:#2855a6;margin:12pt 0 7pt;break-after:avoid}
p{margin:6pt 0;orphans:3;widows:3} a{color:#2855a6;text-decoration:none;overflow-wrap:anywhere} strong{color:#142d48}
table{border-collapse:collapse;width:100%;font-size:8.8pt;line-height:1.5;margin:9pt 0;table-layout:auto} thead{display:table-header-group}
th,td{border-bottom:1px solid #dde4ec;padding:5pt 5pt;text-align:left;vertical-align:top;overflow-wrap:anywhere} th{background:#eef3fa;color:#173656}tr{break-inside:avoid}tr:nth-child(even)td{background:#fafbfd}
img{width:100%;height:auto;max-height:240mm;object-fit:contain;display:block;margin:12pt auto;break-inside:avoid} code{font-family:'DejaVu Sans Mono',ReportCJK,monospace;font-size:9pt;overflow-wrap:anywhere;background:#f1f4f8}
article+article{break-before:page}ul,ol{padding-left:20pt}li{margin:5pt 0;orphans:2;widows:2}
nav{padding:12pt;background:#eef3fa;margin-bottom:18pt}nav a{margin-right:12pt} .note{color:#63758a;font-size:9pt}
@media screen{body{max-width:1060px;margin:32px auto;padding:30px 40px;background:white}html{background:#e9eef4}article{margin-bottom:60px}nav{position:sticky;top:0} }
@media print{nav{display:none}}
'''
doc='<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><title>GT10现状、机制与改进方向</title><style>'+css+'</style></head><body><nav><a href="#part0">研究报告</a><a href="#part1">改进方向</a><a href="#part2">一手文献</a></nav>'+''.join(parts)+'</body></html>'
output=R/'report.html';assert not output.exists();output.write_text(doc)
pdf=R/'GT10现状与改进方向.pdf';assert not pdf.exists()
start=time.perf_counter()
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome',headless=True,timeout=20000,args=['--no-sandbox','--allow-file-access-from-files','--disable-background-networking'])
    page=browser.new_page()
    page.goto(output.as_uri(),wait_until='load',timeout=20000)
    page.evaluate('document.fonts.ready')
    page.pdf(path=str(pdf),format='A4',print_background=True,prefer_css_page_size=True)
    browser.close()
book=pymupdf.open(pdf);texts=[p.get_text() for p in book]
joined='\n'.join(texts)
for key in ['17.8223','21.23','27.30','31.55','2.5007','1.4648','0.8125','实施GO仍为0']:
    assert key in joined,key
bad=[];empty=[]
for i,p in enumerate(book):
    if len(texts[i].strip())<10 and not p.get_images():empty.append(i+1)
    for b in p.get_text('dict')['blocks']:
        if b['type']!=0:continue
        for line in b['lines']:
            for s in line['spans']:
                x0,y0,x1,y1=s['bbox']
                if x0<5 or y0<5 or x1>p.rect.width-5 or y1>p.rect.height-5:bad.append([i+1,s['text'],s['bbox']])
assert not bad,bad[:5]
assert not empty,empty
(R/'reviews/pdf_text.txt').write_text(joined)
preview=R/'reviews/pdf_preview';preview.mkdir()
for i,p in enumerate(book):p.get_pixmap(matrix=pymupdf.Matrix(.7,.7)).save(preview/f'page_{i+1:02}.png')
record={'status':'PASS','pages':len(book),'text_characters':len(joined),'empty_pages':empty,'outside_page_text_spans':bad,
        'seconds':time.perf_counter()-start,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
        'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'renderer':'Local Chromium; independent PDF parse/rasterization with PyMuPDF',
        'new_performance_runs':0}
(R/'reviews/pdf_verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False,indent=2))
