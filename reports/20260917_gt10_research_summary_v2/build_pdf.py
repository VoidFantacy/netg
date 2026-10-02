"""Package the reviewed Markdown and existing E103 vector figures; no experiments."""
from pathlib import Path
import asyncio
import hashlib
import html
import json
import re

import pymupdf as fitz
import markdown
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / 'entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1'
SOURCE = HERE / 'draft.md'
CHROME = '/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome'

text = SOURCE.read_text()
first, remainder = text.split('**二、当前效果', 1)
figures_part, remainder = remainder.split('**三、GT10 之后做过的改进', 1)
second, remainder = ('**三、GT10 之后做过的改进' + remainder).split('**09-13｜', 1)
third = '**三、GT10 改进实验（续）**\n\n**09-13｜' + remainder

def render_md(value):
    out = markdown.markdown(value, extensions=['tables', 'sane_lists'])
    out = re.sub(r'<p><strong>([一二三四五]、[^<]+)</strong></p>',
                 r'<p class="section-heading"><strong>\1</strong></p>', out)
    out = re.sub(r'<p><strong>(09-[^<]+)</strong></p>',
                 r'<p class="date-heading"><strong>\1</strong></p>', out)
    expressions = {
        's_itj = unit(x_git) · unit(x_hj)':
            's<sub>itj</sub> = unit(x<sub>gᵢₜ</sub>) · unit(x<sub>hⱼ</sub>)',
        'b_itj = exp(s_itj/T) / Σ_l exp(s_itl/T)':
            'b<sub>itj</sub> = exp(s<sub>itj</sub>/T) / Σ<sub>ℓ</sub> exp(s<sub>itℓ</sub>/T)',
        'a_ij = (1/10) Σ_t b_itj':
            'a<sub>ij</sub> = (1/10) Σ<sub>t</sub> b<sub>itj</sub>',
        'p_j = unit(unit(x_hj) + Σ_i a_ij · unit(q_i))':
            'p<sub>j</sub> = unit(unit(x<sub>hⱼ</sub>) + Σ<sub>i</sub> a<sub>ij</sub> · unit(q<sub>i</sub>))',
    }
    for original, formatted in expressions.items():
        out = out.replace('<code>' + html.escape(original) + '</code>',
                          '<span class="math">' + formatted + '</span>')
    return out

charts = [
    ('recall_qps_k1', '图 1 · Recall@1 与 QPS',
     '完整重测 · 五个数据集 · 2026-09-17',
     '每条曲线包含全部 16 档实测预算，QPS 为三轮均值，阴影表示最小—最大范围。NSG、GT10 和 GATE 共用优化内核，完整 HNSW 同轮计时；所有方法均为单线程。'),
    ('recall_qps_k100', '图 2 · Recall@100 与 QPS',
     '完整重测 · 五个数据集 · 2026-09-17',
     '横轴为 Recall@100，纵轴为 QPS（对数轴）。计时包含路由与搜索；各方法均展示完整曲线。高召回区间的小幅速度差需结合三轮计时范围判断。'),
    ('failed_query_rate_k1', '图 3 · K=1 的失败查询率',
     '失败定义 · 未找到真实最近邻',
     '失败率为返回 top-1 未命中 exact GT top-1 的查询比例，即 1−Recall@1。横轴为搜索预算 L/ef（对数轴），纵轴越低越好；相同 L/ef 不表示不同方法工作量相同。'),
    ('failed_query_rate_k100', '图 4 · K=100 的失败查询率',
     '失败定义 · 返回的前百结果与真实前百近邻零交集',
     '失败率为返回 top-100 与 exact GT top-100 交集为空的查询比例。SIFT/GIST 本轮各预算均为零失败；这表示至少命中一个真实前百近邻，不代表 Recall@100 达到 100%。'),
]

CSS = '''
@font-face {font-family: ReportCJK; src: url('file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'); font-weight: 400;}
@font-face {font-family: ReportCJK; src: url('file:///usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'); font-weight: 700;}
@page {size: A4; margin: 13mm 14mm 14mm;}
@page narrative {size: A4; margin: 13mm 14mm 14mm;}
@page chart {size: A4 landscape; margin: 12mm;}
* {box-sizing: border-box;}
body {margin: 0; color: #243044; font-family: ReportCJK, 'Noto Sans CJK SC', sans-serif; font-size: 10pt; line-height: 1.56;}
.text-sheet {page: narrative; width: 182mm; break-before: page; break-after: page;}
h1 {font-size: 17.5pt; line-height: 1.35; margin: 0 0 9pt; color: #122d44; letter-spacing: -.3pt;}
p {margin: 5pt 0; orphans: 2; widows: 2;}
strong {font-weight: 700; color: #172d42;}
.section-heading {font-size: 11.5pt; line-height: 1.4; margin: 11pt 0 6pt; padding-bottom: 4pt; border-bottom: 1px solid #cad9e0; break-after: avoid;}
.date-heading {font-size: 10.2pt; margin: 8pt 0 3pt; break-after: avoid;}
table {width: 100%; border-collapse: collapse; margin: 7pt 0; font-size: 9pt; line-height: 1.45; break-inside: avoid;}
th {background: #eaf0f3; color: #14364a; font-weight: 700;}
th, td {text-align: left; padding: 4pt 5pt; border-bottom: 1px solid #dce3e8; vertical-align: middle;}
tr:nth-child(even) td {background: #f7f9fa;}
ul {margin: 3pt 0 7pt; padding-left: 14pt;}
li {margin: 3.2pt 0; orphans: 2; widows: 2;}
.math {font-family: 'DejaVu Serif', ReportCJK, serif; font-size: 9.6pt; color: #123e51; white-space: nowrap;}
sub {font-size: 70%;}
.chart-sheet {page: chart; break-before: page; width: 273mm;}
.chart-heading {margin: 0; font-size: 14pt; color: #12384d; line-height: 1.35;}
.chart-subtitle {font-size: 8.5pt; color: #667b8d; margin: 3pt 0 0;}
.plot-space {height: 153mm;}
.chart-caption {font-size: 9.5pt; line-height: 1.55; margin: 0; color: #374d60;}
@media screen {body {background: #e9edf0; padding: 24px;} .text-sheet,.chart-sheet {background: white; padding: 0; margin: 0 auto 28px;}}
'''
parts = [f'<section class="text-sheet" id="text-1">{render_md(first)}</section>']
for i, (stem, title, subtitle, caption) in enumerate(charts):
    section_title = '二、当前效果（2026-09-17，优化后五集重测）' if i == 0 else '二、当前效果（续）'
    parts.append(f'<section class="chart-sheet" data-figure="{stem}">'
                 f'<h2 class="chart-heading">{section_title}</h2>'
                 f'<p class="chart-subtitle">{title}</p>'
                 '<div class="plot-space"></div>'
                 '</section>')
for i, chunk in enumerate([second, third], start=2):
    parts.append(f'<section class="text-sheet" id="text-{i}">{render_md(chunk)}</section>')
document = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">' + \
    '<title>GT10：OOD 入口选择方法与实验总结</title><style>' + CSS + \
    '</style></head><body>' + ''.join(parts) + '</body></html>'
(HERE / 'report.html').write_text(document)

async def make_pdf():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME, headless=True,
                                           args=['--no-sandbox', '--allow-file-access-from-files'])
        page = await browser.new_page(viewport={'width': 1200, 'height': 1200})
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))
        await page.goto((HERE / 'report.html').as_uri(), wait_until='load')
        await page.emulate_media(media='print')
        await page.evaluate('document.fonts.ready')
        measures = await page.evaluate('''() => Array.from(document.querySelectorAll('.text-sheet')).map(x => ({id:x.id,height:x.getBoundingClientRect().height,width:x.getBoundingClientRect().width}))''')
        print('TEXT_LAYOUT', json.dumps(measures), flush=True)
        # A4 content height is 270 mm. Keep body text at 10 pt or above.
        max_height = max(x['height'] for x in measures)
        if max_height > 1019:
            await page.add_style_tag(content='body {line-height: 1.46;} p {margin:4pt 0;} li {margin:2.6pt 0;} .section-heading {margin-top:8pt;}')
            measures = await page.evaluate('''() => Array.from(document.querySelectorAll('.text-sheet')).map(x => ({id:x.id,height:x.getBoundingClientRect().height,width:x.getBoundingClientRect().width}))''')
            print('COMPACT_LAYOUT', json.dumps(measures), flush=True)
        assert max(x['height'] for x in measures) < 1019, measures
        assert not errors, errors
        await page.pdf(path=str(HERE / 'layout.pdf'), prefer_css_page_size=True,
                       print_background=True, display_header_footer=False)
        await browser.close()
    return measures

measures = asyncio.run(make_pdf())
doc = fitz.open(HERE / 'layout.pdf')
assert len(doc) == 7, [(i+1, p.rect, len(p.get_text())) for i,p in enumerate(doc)]
figure_metadata = []
for offset, (stem, title, subtitle, caption) in enumerate(charts, start=1):
    page = doc[offset]
    assert page.rect.width > page.rect.height
    source_path = RUN / 'figures' / (stem + '.pdf')
    source = fitz.open(source_path)
    assert len(source) == 1
    # Preserve the original vector plot without rasterizing it.
    rect = fitz.Rect(34.02, 69, page.rect.width-34.02, 505)
    page.show_pdf_page(rect, source, 0, keep_proportion=True, overlay=True)
    figure_metadata.append({'page': offset+1, 'path': str(source_path),
                            'sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
                            'vector_preserved': True})
    source.close()

for i, page in enumerate(doc):
    page.insert_text((page.rect.width-57, page.rect.height-16), f'{i+1} / {len(doc)}',
                     fontname='helv', fontsize=8, color=(.38,.44,.49))
doc.set_metadata({'title':'GT10：OOD 入口选择方法与实验总结',
                  'subject':'当前方法、改进实验、NSG实现优化及五集Recall@1/100与失败率重测',
                  'author':'ACSG', 'creator':'ACSG research report'})
doc.set_toc([[1,'当前 GT10 方法',1],[1,'当前效果：五集重测图',2],
             *[[2,x[1],i+2] for i,x in enumerate(charts)],
             [1,'GT10 之后做过的改进',6],
             [1,'后续改进实验、NSG 优化与总结',7]])
output = HERE / 'GT10研究总结.pdf'
doc.save(output, garbage=4, deflate=True)
doc.close()

verified = fitz.open(output)
text_all = '\n'.join(p.get_text() for p in verified)
for term in ['真实入口', '0.6/0.3/0.1', '71.82%', '10.51%', '27.28%', '失败查询率', '尚未找到', '阶段总结']:
    assert term in text_all, term
assert '希望老师和师兄指导的问题' not in text_all
assert 'GT10 实际 Recall' not in text_all
for i in range(1,5):
    assert verified[i].rect.width > verified[i].rect.height
    assert 'QPS 变化' not in verified[i].get_text()
assert '尚未找到' in verified[5].get_text()
assert '阶段总结' in verified[6].get_text()
assert '\ufffd' not in text_all
pages = []
for i, page in enumerate(verified):
    pix = page.get_pixmap(matrix=fitz.Matrix(1.3,1.3), alpha=False)
    pix.save(HERE / f'page-{i+1:02d}.png')
    pages.append({'page': i+1, 'width': page.rect.width, 'height': page.rect.height,
                  'text_length': len(page.get_text())})
(HERE / 'extracted_text.txt').write_text(text_all)
record = {'pdf': str(output), 'pages': pages, 'layout': measures,
          'source_lines': len(text.splitlines()), 'figures': figure_metadata,
          'metrics_sha256': hashlib.sha256((RUN/'results/metrics.csv').read_bytes()).hexdigest(),
          'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
          'pdf_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
          'retained_body_font_pt': 10, 'historical_recall_k10_kept_separate': True,
          'figures_from_e103_only': True, 'new_searches': 0,
          'section_order': ['method','figures','experiments','nsg_optimization','summary'],
          'results_section_contains_only_figures_and_titles': True}
(HERE / 'document_checks.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pdf':str(output),'pages':len(verified),'bytes':output.stat().st_size},ensure_ascii=False))
