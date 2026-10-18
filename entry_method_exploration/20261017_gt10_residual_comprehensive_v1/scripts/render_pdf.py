#!/usr/bin/env python3
"""Package an existing Chinese report and curve image; never analyze ANN data.

Uses matplotlib's PDF backend and the system Noto CJK font only. Text wraps by
actual font widths, tables repeat headers across pages, and individual dataset
curve images occupy separate pages. E181's verified Type 3 CJK rendering is retained.
Existing output files are preserved; no CSV or scientific arrays are accessed.
"""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT/'analysis/final_v1/NETG_E183_GT10与残差_七数据集及失败查询_20261017.pdf'
DEFAULT_FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
E181_TYPE3_SOURCE_SHA = '680fbc584174a004929b5ec22a630d773a2ad8297cda81f4a00dd3c180a17a5f'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def identity(path):
    s = Path(path).stat()
    result = dict(sha256=sha(path), bytes=s.st_size, mtime_ns=s.st_mtime_ns)
    t = Path(path).stat()
    require((s.st_size, s.st_mtime_ns) == (t.st_size, t.st_mtime_ns), 'input changed while hashing')
    return result


def plain(text):
    """Remove presentation markers, retaining words, numbers and link targets."""
    def link(match):
        label, target = match.group(1), match.group(2)
        return label if target == label else label+' ('+target+')'
    text = re.sub(r'!?\[([^\]]*)\]\(([^)]+)\)', link, text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.replace('**', '').replace('__', '').replace('<br>', '\n').replace('<br/>', '\n')


def table_cells(line):
    protected = line.strip().replace(r'\|', '\x00')
    if protected.startswith('|'):
        protected = protected[1:]
    if protected.endswith('|'):
        protected = protected[:-1]
    return [plain(cell.strip().replace('\x00', '|')) for cell in protected.split('|')]


def table_separator(line):
    cells = table_cells(line)
    return len(cells) >= 2 and all(re.fullmatch(r':?-{3,}:?', c) for c in cells)


def parse_markdown(text):
    lines = text.splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith('```'):
            i += 1
            code = []
            while i < len(lines) and not lines[i].lstrip().startswith('```'):
                code.append(lines[i].expandtabs(4))
                i += 1
            require(i < len(lines), 'unclosed Markdown code block')
            blocks.append(dict(kind='code', text='\n'.join(code)))
            i += 1
            continue
        heading = re.match(r'^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
        if heading:
            blocks.append(dict(kind='heading', level=len(heading.group(1)), text=plain(heading.group(2))))
            i += 1
            continue
        if i+1 < len(lines) and '|' in line and table_separator(lines[i+1]):
            header = table_cells(line)
            separator = table_cells(lines[i+1])
            require(len(header) == len(separator), 'table header/separator width mismatch')
            rows = []
            i += 2
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                row = table_cells(lines[i])
                require(len(row) == len(header), 'table row/header width mismatch: '+lines[i])
                rows.append(row)
                i += 1
            alignments = ['center' if c.startswith(':') and c.endswith(':') else
                          'right' if c.endswith(':') else 'left' for c in separator]
            blocks.append(dict(kind='table', header=header, rows=rows, alignments=alignments))
            continue
        if re.fullmatch(r'\s*(?:-{3,}|\*{3,}|_{3,})\s*', line):
            blocks.append(dict(kind='rule'))
            i += 1
            continue
        if re.fullmatch(r'\s*!\[[^\]]*\]\([^)]*\)\s*', line):
            # The requested curve image is attached once, at readable full-page size.
            blocks.append(dict(kind='paragraph', text='图表见文末独立图页。'))
            i += 1
            continue
        bullet = re.match(r'^\s*(?:[-+*]\s+|\d+[.)]\s+)', line)
        if bullet:
            match = re.match(r'^\s*(\d+[.)])\s+', line)
            prefix = match.group(1)+' ' if match else '• '
            value = line[bullet.end():]
            i += 1
            while i < len(lines) and re.match(r'^\s{2,}\S', lines[i]) and not re.match(r'^\s*[-+*]\s+', lines[i]):
                value += ' '+lines[i].strip()
                i += 1
            blocks.append(dict(kind='list', text=prefix+plain(value)))
            continue
        paragraph = [line.strip().lstrip('>').strip()]
        i += 1
        while i < len(lines) and lines[i].strip():
            next_line = lines[i]
            if re.match(r'^\s*(?:#{1,6}\s|```|[-+*]\s|\d+[.)]\s)', next_line):
                break
            if i+1 < len(lines) and '|' in next_line and table_separator(lines[i+1]):
                break
            if re.fullmatch(r'\s*(?:-{3,}|\*{3,}|_{3,})\s*', next_line):
                break
            paragraph.append(next_line.strip().lstrip('>').strip())
            i += 1
        blocks.append(dict(kind='paragraph', text=plain(' '.join(paragraph))))
    return blocks


class Document:
    """Coordinates and wrapping are in typographic points, not pixel guesses."""
    PORTRAIT = (595.276, 841.890)
    LANDSCAPE = (841.890, 595.276)

    def __init__(self, pdf, font, pyplot, font_properties, text_to_path):
        self.pdf = pdf
        self.plt = pyplot
        self.font = font
        self.FontProperties = font_properties
        self.text_path = text_to_path
        self.figure = None
        self.pages = []
        self.orientation = 'portrait'
        self.margin = 43.
        self.bottom = 47.
        self.body_size = 11.
        self.default_leading = 17.
        self.new_page()

    def props(self, size):
        return self.FontProperties(fname=str(self.font), size=size)

    @lru_cache(maxsize=32768)
    def width(self, text, size):
        return self.text_path.get_text_width_height_descent(text, self.props(size), ismath=False)[0]

    def wrap(self, text, size, width):
        require(width > size, 'positive usable text width')
        output = []
        for paragraph in text.split('\n'):
            # Keep ordinary Latin words and numbers intact where possible; Chinese
            # characters can break between glyphs. Overlong paths split explicitly.
            tokens = re.findall(r'[A-Za-z0-9_./:@%+\-=,()]+|\s+|[^\x00-\x7f]|.', paragraph)
            line = ''
            for token in tokens:
                if not line and token.isspace():
                    continue
                if self.width(line+token, size) <= width:
                    line += token
                    continue
                if line:
                    output.append(line.rstrip())
                    line = ''
                token = token.lstrip()
                if self.width(token, size) <= width:
                    line = token
                else:
                    for char in token:
                        if line and self.width(line+char, size) > width:
                            output.append(line)
                            line = ''
                        line += char
            output.append(line.rstrip())
        return output or ['']

    def text(self, x, y, value, size, *, color='#263238', align='left'):
        return self.figure.text(x/self.w, y/self.h, value, fontproperties=self.props(size),
                                ha=align, va='top', color=color, parse_math=False)

    def line(self, x0, y0, x1, y1, color='#cfd8dc', width=.6):
        from matplotlib.lines import Line2D
        self.figure.add_artist(Line2D([x0/self.w, x1/self.w], [y0/self.h, y1/self.h],
                                     transform=self.figure.transFigure, color=color, linewidth=width))

    def rectangle(self, x, y, width, height, color):
        from matplotlib.patches import Rectangle
        self.figure.add_artist(Rectangle((x/self.w, y/self.h), width/self.w, height/self.h,
                                         transform=self.figure.transFigure, facecolor=color,
                                         edgecolor='none', zorder=-1))

    def new_page(self, orientation='portrait', kind='text'):
        if self.figure is not None:
            self.flush()
        self.orientation = orientation
        self.w, self.h = self.LANDSCAPE if orientation == 'landscape' else self.PORTRAIT
        self.figure = self.plt.figure(figsize=(self.w/72., self.h/72.))
        self.figure.patch.set_facecolor('white')
        self.page_info = dict(number=len(self.pages)+1, orientation=orientation, kind=kind, text_lines=0, table_rows=0)
        self.text(self.margin, self.h-20, 'NETG · E183 · GT10 与残差：跨数据集和失败查询', 8.2, color='#607d8b')
        self.line(self.margin, self.h-34, self.w-self.margin, self.h-34)
        self.y = self.h-49

    def flush(self):
        if self.figure is None:
            return
        self.line(self.margin, 32, self.w-self.margin, 32)
        self.text(self.margin, 24, '完整单线程三轮计时 · 测点连线不代表额外等 Recall 测量', 7.5, color='#78909c')
        self.text(self.w-self.margin, 24, str(len(self.pages)+1), 8, align='right', color='#607d8b')
        self.pdf.savefig(self.figure, dpi=180)
        self.plt.close(self.figure)
        self.figure = None
        self.pages.append(self.page_info)

    def room(self, height, orientation=None):
        orientation = orientation or self.orientation
        if self.orientation != orientation or self.y-height < self.bottom:
            self.new_page(orientation)

    def paragraph(self, value, *, size=None, leading=None, before=0., after=8., indent=0., color='#263238'):
        size = self.body_size if size is None else size
        leading = self.default_leading if leading is None else leading
        self.room(before+leading, 'portrait')
        self.y -= before
        lines = self.wrap(value, size, self.w-2*self.margin-indent)
        for index, line in enumerate(lines):
            # Avoid leaving a lone final paragraph line on a fresh page.
            need = 2*leading if len(lines)-index == 2 else leading
            self.room(need, 'portrait')
            self.text(self.margin+indent, self.y, line, size, color=color)
            self.y -= leading
            self.page_info['text_lines'] += 1
        self.y -= after

    def heading(self, value, level):
        size = 20. if level == 1 else 15. if level == 2 else 12.5
        leading = size*1.42
        lines = self.wrap(value, size, self.PORTRAIT[0]-2*self.margin)
        self.room(len(lines)*leading+2*self.default_leading+14, 'portrait')
        self.y -= 9 if self.page_info['text_lines'] else 0
        for line in lines:
            self.text(self.margin, self.y, line, size, color='#123b5d')
            self.y -= leading
            self.page_info['text_lines'] += 1
        self.y -= 6

    def table(self, block):
        header, rows = block['header'], block['rows']
        columns = len(header)
        size, leading, pad = 9.2, 13.6, 6.
        intrinsic = [max(self.width(str(row[c]), size) for row in [header, *rows]) + 2*pad for c in range(columns)]
        orientation = 'landscape' if columns >= 7 or sum(min(w, 180.) for w in intrinsic) > 680 else 'portrait'
        page_w = (self.LANDSCAPE if orientation == 'landscape' else self.PORTRAIT)[0]
        available = page_w-2*self.margin
        require(columns <= 16, 'table exceeds readable column count; split it in the Markdown report')
        # Long descriptive columns receive more room, without allowing one path to
        # consume the whole page. Every value wraps; no table content is truncated.
        weights = [max(44., min(w, 200.)) for w in intrinsic]
        widths = [available*w/sum(weights) for w in weights]
        require(min(widths) > 2*pad+size, 'table columns too narrow; split table in source Markdown')

        def wrapped(row):
            return [self.wrap(cell, size, width-2*pad) for cell, width in zip(row, widths)]

        header_lines = wrapped(header)
        header_height = max(map(len, header_lines))*leading+2*pad

        def draw_cells(cells, height, is_header=False, shade=False):
            if is_header or shade:
                self.rectangle(self.margin, self.y-height, available, height, '#e8eff5' if is_header else '#f6f8fa')
            x = self.margin
            for c, lines in enumerate(cells):
                for j, value in enumerate(lines):
                    align = block['alignments'][c]
                    tx = x+widths[c]/2 if align == 'center' else x+widths[c]-pad if align == 'right' else x+pad
                    self.text(tx, self.y-pad-j*leading, value, size,
                              align=align, color='#123b5d' if is_header else '#263238')
                    self.page_info['text_lines'] += 1
                x += widths[c]
            self.y -= height
            self.line(self.margin, self.y, self.w-self.margin, self.y, width=.45)

        self.room(header_height+leading+2*pad+10, orientation)
        self.y -= 5
        draw_cells(header_lines, header_height, is_header=True)
        for ordinal, row in enumerate(rows):
            cells = wrapped(row)
            remaining = max(map(len, cells))
            offset = 0
            while remaining:
                capacity = math.floor((self.y-self.bottom-2*pad)/leading)
                if capacity < 1:
                    self.new_page(orientation, 'table')
                    draw_cells(header_lines, header_height, is_header=True)
                    capacity = math.floor((self.y-self.bottom-2*pad)/leading)
                # Keep an ordinary row intact. Split only a row taller than an
                # otherwise empty page, and repeat the table header after a break.
                full_page_capacity = math.floor((self.h-49-self.bottom-header_height-2*pad)/leading)
                if remaining > capacity and remaining <= full_page_capacity:
                    self.new_page(orientation, 'table')
                    draw_cells(header_lines, header_height, is_header=True)
                    capacity = math.floor((self.y-self.bottom-2*pad)/leading)
                take = min(remaining, capacity)
                require(take > 0, 'table header leaves no row space')
                part = [cell[offset:offset+take] for cell in cells]
                draw_cells(part, take*leading+2*pad, shade=ordinal % 2 == 1)
                self.page_info['table_rows'] += 1
                remaining -= take
                offset += take
        self.y -= 12

    def curves(self, path, title='Recall–QPS 曲线（既有原图）', kind='curves'):
        picture = self.plt.imread(path)
        height, width = picture.shape[:2]
        # Tall multi-panel charts fit a portrait page; wide charts remain landscape.
        self.new_page('portrait' if height > width*1.1 else 'landscape', kind)
        for line in self.wrap(title, 16, self.w-2*self.margin):
            self.text(self.margin, self.y, line, 16, color='#123b5d')
            self.y -= 23
        self.y -= 12
        box_w, box_h = self.w-2*self.margin, self.y-self.bottom-18
        factor = min(box_w/width, box_h/height)
        image_w, image_h = width*factor, height*factor
        x, y = (self.w-image_w)/2, self.bottom+18+(box_h-image_h)/2
        ax = self.figure.add_axes((x/self.w, y/self.h, image_w/self.w, image_h/self.h))
        ax.imshow(picture, interpolation='none')
        ax.set_axis_off()
        self.text(self.margin, self.bottom+4, '原始 PNG 随报告保留；本页仅等比例放置图像，没有重新计算或修改数据。', 8, color='#607d8b')
        self.page_info['source_image_pixels'] = [width, height]
        self.page_info['source_image'] = str(Path(path).resolve())
        self.page_info['figure_title'] = title


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT/'analysis/final_v1/report_zh.md')
    parser.add_argument('--curves', type=Path, default=None,
                        help='Optional first figure; default reads figure list from summary.json beside report.')
    parser.add_argument('--extra-figure', action='append', type=Path, default=[],
                        help='Append an existing mechanism/diagnostic PNG; repeat for multiple pages.')
    parser.add_argument('--output', type=Path, default=DEFAULT_PDF)
    parser.add_argument('--receipt', type=Path, default=ROOT/'analysis/final_v1/pdf_render_receipt.json')
    parser.add_argument('--font', type=Path, default=DEFAULT_FONT)
    args = parser.parse_args()
    if 14 in os.sched_getaffinity(0):
        os.sched_setaffinity(0, {14})
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    started = time.monotonic()
    output, receipt = args.output.resolve(), args.receipt.resolve()
    require(not output.exists() and not receipt.exists(), 'preserve existing PDF and rendering receipt')
    require(output.is_relative_to(ROOT/'analysis') and receipt.is_relative_to(ROOT/'analysis'), 'output stays in new campaign analysis')
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    record = dict(status='FAIL_E183_PDF_RENDER', pdf=str(output), inputs={}, elapsed_seconds=None,
                  source=str(Path(__file__).resolve()), source_sha256=sha(__file__),
                  numeric_analysis_executed=False, ANN_or_GT_executed=False, visual_review_pending=True,
                  e181_verified_type3_source_sha256=E181_TYPE3_SOURCE_SHA,
                  pdf_fonttype=3, ps_fonttype=3,
                  font_history='E181 Noto CJK TTC/CFF under Type42 produced blank Chinese and corrupted ASCII; final Type3 was visually verified. Type42 is not used here.')
    try:
        figures = []
        summary_path = args.report.parent/'summary.json'
        if args.curves:
            figures.append({'path': str(args.curves.resolve()), 'title': '完整 Recall–QPS 曲线'})
        elif summary_path.exists():
            record['inputs'][str(summary_path.resolve())] = identity(summary_path)
            figures.extend(json.loads(summary_path.read_text())['figures'])
        figures.extend({'path': str(p.resolve()), 'title': '补充图 · '+p.stem} for p in args.extra_figure)
        for path in (args.report.resolve(), args.font.resolve(),
                     *[Path(f['path']).resolve() for f in figures]):
            require(path.is_file(), 'required rendering input missing: '+str(path))
            record['inputs'][str(path)] = identity(path)
        blocks = parse_markdown(args.report.read_text(encoding='utf-8'))
        require(bool(blocks), 'report has no renderable content')
        import matplotlib
        matplotlib.use('Agg')
        matplotlib.rcParams.update({'pdf.fonttype': 3, 'ps.fonttype': 3, 'axes.unicode_minus': False,
                                   'text.usetex': False, 'savefig.facecolor': 'white'})
        require(matplotlib.rcParams['pdf.fonttype']==3 and matplotlib.rcParams['ps.fonttype']==3,
                'retain verified Type3 CJK glyph rendering')
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.font_manager import FontProperties
        from matplotlib.textpath import TextToPath
        with output.open('xb') as handle:
            with PdfPages(handle, metadata={'Title': 'NETG E183 GT10与残差：七数据集及失败查询',
                                           'Author': 'NETG', 'Subject': 'GT10独立贡献、残差增量、失败救回和完整Recall-QPS'}) as pdf:
                document = Document(pdf, args.font, plt, FontProperties, TextToPath())
                for block in blocks:
                    kind = block['kind']
                    if kind == 'heading':
                        document.heading(block['text'], block['level'])
                    elif kind == 'table':
                        document.table(block)
                    elif kind == 'code':
                        document.paragraph(block['text'], size=9.4, leading=14., indent=10., after=10., color='#455a64')
                    elif kind == 'rule':
                        document.room(18, 'portrait')
                        document.line(document.margin, document.y-4, document.w-document.margin, document.y-4)
                        document.y -= 18
                    else:
                        document.paragraph(block['text'], indent=8. if kind == 'list' else 0., after=5. if kind == 'list' else 8.)
                for figure in figures:
                    document.curves(figure['path'], title=figure['title'], kind='dataset_figure')
                document.flush()
                record['pages'] = document.pages
        for path, value in record['inputs'].items():
            require(identity(path) == value, 'rendering input changed: '+path)
        require(sha(__file__) == record['source_sha256'], 'render source changed')
        record.update(status='PASS_E183_PDF_RENDER', pdf_sha256=sha(output), pdf_bytes=output.stat().st_size,
                      page_count=len(record['pages']), markdown_block_counts=dict(Counter(b['kind'] for b in blocks)),
                      output_policy='New exclusive output, existing files never overwritten',
                      scientific_scope='Formatting only: existing Markdown, PNG and figure-path list from summary; no CSV/ANN result arrays opened')
    except BaseException as exc:
        record['exception'] = repr(exc)
        record['partial_output_preserved'] = output.exists()
    record['elapsed_seconds'] = time.monotonic()-started
    with receipt.open('x', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: record.get(k) for k in ('status', 'pdf', 'pdf_sha256', 'page_count', 'elapsed_seconds')}))
    return 0 if record['status'] == 'PASS_E183_PDF_RENDER' else 2


if __name__ == '__main__':
    raise SystemExit(main())
