#!/usr/bin/env python3
"""Render a reviewed methods Markdown document only. No ANN or result access.

Run with system Python; dependencies live only in this directory's .deps.
All browser children inherit CPU14 affinity and single-thread library settings.
"""
import argparse,asyncio,hashlib,html,json,os,re,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
CHROME=Path('/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome')
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[name]='1'
if hasattr(os,'sched_setaffinity'):os.sched_setaffinity(0,{14})
sys.path.insert(0,str(HERE/'.deps'))
import fitz
import markdown
from playwright.async_api import async_playwright

CSS=r'''
@font-face{font-family:ReportCJK;src:url('file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');font-weight:400;font-style:normal}
@font-face{font-family:ReportCJK;src:url('file:///usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc');font-weight:700;font-style:normal}
@page{size:A4;margin:16mm 14mm 18mm}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:white}
body{color:#253446;font-family:ReportCJK,'Noto Sans CJK SC',sans-serif;font-size:11pt;line-height:1.66;font-weight:400;-webkit-print-color-adjust:exact;print-color-adjust:exact}
main.report{width:182mm;margin:0 auto}
h1{font-size:23pt;line-height:1.32;letter-spacing:-.4pt;color:#15334c;margin:0 0 13pt;font-weight:700;break-after:avoid}
h2{font-size:15pt;line-height:1.45;color:#183e56;margin:19pt 0 9pt;padding-bottom:5pt;border-bottom:1px solid #ccdae3;break-after:avoid}
h3{font-size:12pt;line-height:1.5;color:#21485f;margin:13pt 0 6pt;break-after:avoid}
h4{font-size:11pt;line-height:1.5;margin:10pt 0 4pt;break-after:avoid}
p{margin:6pt 0;orphans:3;widows:3}
strong{font-weight:700;color:#1b3449}
a{color:#195d92;text-decoration:underline;text-decoration-thickness:.6pt;text-underline-offset:2pt;overflow-wrap:anywhere}
ul,ol{padding-left:18pt;margin:6pt 0 9pt}
li{margin:3.5pt 0;orphans:2;widows:2}
li p{margin:3pt 0}
table{width:100%;border-collapse:collapse;margin:10pt 0 12pt;font-size:10.5pt;line-height:1.55;table-layout:fixed;break-inside:auto}
thead{display:table-header-group}
tfoot{display:table-footer-group}
tr{break-inside:avoid;page-break-inside:avoid}
th,td{text-align:left;vertical-align:top;padding:6pt 6.5pt;border-bottom:1px solid #dbe3ea;overflow-wrap:anywhere}
th{font-weight:700;color:#18425a;background:#eaf1f6}
tbody tr:nth-child(even){background:#f7f9fb}
table p{margin:0}
blockquote{border-left:3pt solid #6b9bb8;background:#f1f6f9;margin:10pt 0;padding:5pt 10pt;break-inside:avoid}
blockquote p{margin:3pt 0}
code{font-family:'DejaVu Sans Mono',ReportCJK,monospace;font-size:10.5pt;color:#1f4860;white-space:pre-wrap;overflow-wrap:anywhere}
pre{font-size:10.5pt;line-height:1.5;padding:9pt;background:#f3f6f8;border:1px solid #e0e7ed;border-radius:4pt;white-space:pre-wrap;overflow-wrap:anywhere;break-inside:auto}
pre code{background:none;padding:0}
.math,.formula{font-family:'DejaVu Serif',ReportCJK,serif;font-size:10.5pt;line-height:1.75;color:#20475c;overflow-wrap:anywhere}
div.math,div.formula{padding:5pt 9pt;margin:8pt 0;background:#f5f8fa;border-left:2pt solid #82a6bb;break-inside:avoid}
sub,sup{font-size:72%;line-height:0}
figure,.diagram{margin:12pt 0;break-inside:avoid;page-break-inside:avoid}
svg,img{display:block;max-width:100%;height:auto;margin:8pt auto;break-inside:avoid;page-break-inside:avoid}
svg{width:100%;max-height:105mm}
svg text{font-family:ReportCJK,'Noto Sans CJK SC',sans-serif}
figcaption,.caption{font-size:10.5pt;line-height:1.55;color:#526579;margin:5pt 0 0;text-align:left}
.subtitle,.metadata{color:#617589;font-size:10.5pt;line-height:1.55;margin:0 0 12pt}
.note{color:#51697b;font-size:10.5pt}
.references{font-size:10.5pt;line-height:1.5}
.references li{margin:2pt 0}
.page-break{break-before:page;page-break-before:always}
hr{border:0;border-top:1px solid #d6e1e8;margin:13pt 0}
@media screen{html{background:#e9eef2}body{padding:24px 0}main.report{background:white;box-shadow:0 3px 25px #16364a20;padding:16mm 14mm;box-sizing:content-box}}
'''

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(ok,message):
    if not ok:raise RuntimeError(message)

def inline_svg_images(rendered,source_dir):
    """Keep local SVG assets as vector DOM, while retaining caption alt text."""
    assets=[]
    def replace(match):
        tag=match.group(0);src=re.search(r'\bsrc=["\']([^"\']+)["\']',tag)
        if not src:return tag
        name=html.unescape(src.group(1))
        if not name.lower().endswith('.svg') or re.match(r'https?://|data:',name):return tag
        candidate=(source_dir/name).resolve() if not Path(name).is_absolute() else Path(name)
        require(candidate.is_file(),f'missing SVG asset: {candidate}')
        svg=candidate.read_text();start=svg.find('<svg');require(start>=0,'SVG root missing')
        svg=svg[start:];alt=re.search(r'\balt=["\']([^"\']*)["\']',tag)
        if alt:svg=re.sub(r'<svg\b',f'<svg role="img" aria-label="{html.escape(html.unescape(alt.group(1)),quote=True)}"',svg,count=1)
        assets.append({'path':str(candidate),'sha256':sha(candidate),'embedded_as_vector_svg':True})
        return '<figure class="diagram">'+svg+'</figure>'
    return re.sub(r'<img\b[^>]*>',replace,rendered),assets

async def print_pdf(html_path,pdf_path):
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=str(CHROME),headless=True,args=['--no-sandbox','--allow-file-access-from-files','--disable-dev-shm-usage','--disable-background-networking'])
        page=await browser.new_page(viewport={'width':1100,'height':1400});errors=[];failed=[]
        page.on('pageerror',lambda x:errors.append(str(x)))
        page.on('requestfailed',lambda x:failed.append({'url':x.url,'failure':x.failure}))
        await page.goto(html_path.as_uri(),wait_until='load');await page.emulate_media(media='print');await page.evaluate('document.fonts.ready')
        measures=await page.evaluate('''() => {
          const root=document.querySelector('main.report'), rr=root.getBoundingClientRect();
          const nodes=Array.from(root.querySelectorAll('p,h1,h2,h3,h4,table,pre,blockquote,figure,img,svg')).filter(x=>!x.closest('svg')||x.tagName.toLowerCase()==='svg');
          const bad=nodes.map(x=>({tag:x.tagName,text:(x.textContent||'').trim().slice(0,90),r:x.getBoundingClientRect()})).filter(x=>x.r.width>rr.width+1||x.r.left<rr.left-1||x.r.right>rr.right+1).map(x=>({tag:x.tag,text:x.text,left:x.r.left,right:x.r.right,width:x.r.width}));
          return {content_width_px:rr.width,content_height_px:rr.height,horizontal_overflow:bad,font_status:document.fonts.status,headings:Array.from(root.querySelectorAll('h1,h2,h3')).map(x=>({tag:x.tagName,text:x.textContent.trim()})),svg_count:root.querySelectorAll('svg').length,image_count:root.querySelectorAll('img').length,body_font_px:getComputedStyle(document.body).fontSize};
        }''')
        require(not errors,f'browser page errors: {errors}');require(not failed,f'failed document assets: {failed}')
        require(not measures['horizontal_overflow'],f'horizontal document overflow: {measures["horizontal_overflow"]}')
        require(measures['font_status']=='loaded','Chinese fonts not ready')
        footer='<div style="font-family:Arial,sans-serif;font-size:8.5pt;color:#607487;width:100%;padding:0 14mm;display:flex;justify-content:space-between;"><span>ACSG | GT10 + M5</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'
        await page.pdf(path=str(pdf_path),prefer_css_page_size=True,print_background=True,display_header_footer=True,header_template='<div></div>',footer_template=footer)
        await browser.close();return measures

def font_embedding_record(doc,item):
    xref,ext,font_type,name,resource,*rest=item
    record={'xref':xref,'name':name,'type':font_type,'embedded':False,'embedded_kind':None}
    # Chromium writes CFF CJK subsets as self-contained Type3 glyph programs,
    # whose empty BaseFont and absent extract_font buffer do not mean fallback.
    if font_type=='Type3':
        desc_kind,desc_value=doc.xref_get_key(xref,'FontDescriptor')
        require(desc_kind=='xref',f'Type3 FontDescriptor absent: {xref}')
        descriptor_xref=int(desc_value.split()[0])
        name_kind,font_name=doc.xref_get_key(descriptor_xref,'FontName')
        family_kind,font_family=doc.xref_get_key(descriptor_xref,'FontFamily')
        require(name_kind=='name' and bool(font_name.strip('/')),f'Type3 descriptor FontName absent: {xref}')
        record['name']=font_name.lstrip('/');record['font_family']=font_family
        record['font_descriptor_xref']=descriptor_xref
        procs_kind,procs_value=doc.xref_get_key(xref,'CharProcs')
        if procs_kind=='xref':procs_value=doc.xref_object(int(procs_value.split()[0]))
        else:require(procs_kind=='dict',f'Type3 CharProcs absent: {xref}')
        glyph_refs=re.findall(r'/([^\s/<>{}\[\]]+)\s+(\d+)\s+\d+\s+R',procs_value)
        require(bool(glyph_refs),f'Type3 glyph programs absent: {xref}')
        glyphs=[]
        for glyph,glyph_xref_string in glyph_refs:
            glyph_xref=int(glyph_xref_string)
            require(doc.xref_is_stream(glyph_xref),f'Type3 glyph is not an embedded stream: {xref}/{glyph}')
            stream=doc.xref_stream(glyph_xref)
            require(bool(stream),f'Type3 empty embedded glyph stream: {xref}/{glyph}')
            glyphs.append({'name':glyph,'xref':glyph_xref,'decoded_bytes':len(stream),'sha256':hashlib.sha256(stream).hexdigest()})
        unicode_kind,unicode_value=doc.xref_get_key(xref,'ToUnicode')
        require(unicode_kind=='xref',f'Type3 ToUnicode mapping absent: {xref}')
        unicode_xref=int(unicode_value.split()[0]);require(doc.xref_is_stream(unicode_xref),f'Type3 ToUnicode is not embedded: {xref}')
        cmap=doc.xref_stream(unicode_xref)
        require(bool(cmap) and b'begincmap' in cmap and (b'beginbfchar' in cmap or b'beginbfrange' in cmap),f'Type3 ToUnicode has no character mapping: {xref}')
        record.update({'embedded':True,'embedded_kind':'vector_glyph_programs','embedded_font_file':False,
            'glyph_program_count':len(glyphs),'glyph_programs':glyphs,'ToUnicode_xref':unicode_xref,
            'ToUnicode_bytes':len(cmap),'ToUnicode_sha256':hashlib.sha256(cmap).hexdigest(),
            'self_contained_glyph_streams_checked':True,'unicode_mapping_checked':True})
    else:
        try:buffer=doc.extract_font(xref)[3]
        except Exception:buffer=b''
        record['embedded']=bool(buffer)
        if buffer:record.update({'embedded_kind':'font_file','embedded_font_file':True,'embedded_font_bytes':len(buffer)})
    return record

def check_pdf(pdf,output_dir,source_text,measures,assets):
    doc=fitz.open(pdf);require(len(doc)>0,'empty PDF');pages=[];all_text=[];boundary=[];fonts={};blank=[];font_sizes=[];links=0
    previews=output_dir/'pages';previews.mkdir(exist_ok=True)
    for i,page in enumerate(doc):
        require(abs(page.rect.width-595.276)<1 and abs(page.rect.height-841.890)<1,'PDF page is not portrait A4')
        text=page.get_text();all_text.append(text);links+=len(page.get_links())
        if len(re.sub(r'\s','',text))<25:blank.append(i+1)
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line.get('spans',[]):
                    if not span['text'].strip():continue
                    box=fitz.Rect(span['bbox']);font_sizes.append(float(span['size']))
                    if box.x0<-.5 or box.y0<-.5 or box.x1>page.rect.width+.5 or box.y1>page.rect.height+.5:boundary.append({'page':i+1,'text':span['text'],'bbox':list(box)})
        for item in page.get_fonts(full=True):
            xref=item[0]
            if xref not in fonts:
                fonts[xref]=font_embedding_record(doc,item)
        page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(previews/f'page-{i+1:02d}.png')
        pages.append({'page':i+1,'width_pt':float(page.rect.width),'height_pt':float(page.rect.height),'text_characters':len(text),'links':len(page.get_links()),'preview':str(previews/f'page-{i+1:02d}.png')})
    combined='\n\n'.join(all_text);require('\ufffd' not in combined,'replacement glyph in extracted text');require(not boundary,f'text crosses page boundary: {boundary}');require(not blank,f'nearly blank pages: {blank}')
    cjk_fonts=[v for v in fonts.values() if re.search(r'CJK|NotoSans|SourceHan|ReportCJK',v['name'],re.I)]
    require(cjk_fonts and all(v['embedded'] for v in cjk_fonts),'Chinese PDF font not embedded')
    # A heading must occur in extractable PDF text (spaces normalize only).
    normalize=lambda value:re.sub(r'\s','',value)
    for heading in measures['headings']:require(normalize(heading['text']) in normalize(combined),f'heading absent from PDF: {heading["text"]}')
    record={'pdf':str(pdf),'pdf_sha256':sha(pdf),'source_sha256':hashlib.sha256(source_text.encode()).hexdigest(),'page_count':len(doc),'pages':pages,'layout':measures,
        'font_faces':list(fonts.values()),'Chinese_fonts_embedded':True,'body_font_pt':11,'table_and_math_font_pt':10.5,'observed_font_sizes_pt':sorted(set(round(x,2) for x in font_sizes)),
        'page_boundary_violations':boundary,'nearly_blank_pages':blank,'replacement_character_present':False,'clickable_links':links,'svg_assets':assets,'new_searches':0,'new_training':0,
        'cpu_affinity':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,'scope':'document render/font/text/page bounds checks only; scientific claims require the reviewed source document'}
    (output_dir/'extracted_text.txt').write_text(combined)
    (output_dir/'document_checks.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');doc.close();return record

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=HERE/'method_report.md');parser.add_argument('--out',type=Path,default=HERE);args=parser.parse_args()
    args.source=args.source.resolve();args.out=args.out.resolve()
    started=time.monotonic();require(args.source.is_file(),f'waiting for reviewed document: {args.source}');require(CHROME.is_file(),'Chromium binary absent')
    text=args.source.read_text();require(text.strip(),'empty Markdown');args.out.mkdir(parents=True,exist_ok=True)
    rendered=markdown.markdown(text,extensions=['extra','sane_lists'],output_format='html5');rendered,assets=inline_svg_images(rendered,args.source.parent)
    title_match=re.search(r'^#\s+(.+)$',text,re.M);title=title_match.group(1) if title_match else 'GT与M5方法说明'
    document='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>'+html.escape(title)+'</title><base href="'+html.escape(args.source.parent.as_uri()+'/',quote=True)+'"><style>'+CSS+'</style></head><body><main class="report">'+rendered+'</main></body></html>'
    html_path=args.out/'report.html';pdf_path=args.out/'GT与M5方法说明.pdf';html_path.write_text(document)
    measures=asyncio.run(print_pdf(html_path,pdf_path));record=check_pdf(pdf_path,args.out,text,measures,assets)
    print(json.dumps({'pdf':str(pdf_path),'pages':record['page_count'],'bytes':pdf_path.stat().st_size,'seconds':time.monotonic()-started,'document_checks':str(args.out/'document_checks.json')},ensure_ascii=False))

if __name__=='__main__':main()
