"""Presentation-only E183 report; read sealed CSVs, never run ANN."""
from pathlib import Path
import csv
import hashlib
import json
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator, FuncFormatter, LogLocator, NullFormatter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'analysis/final_v1'
OUT = ROOT / 'analysis/concise_v1'
OUT.mkdir(exist_ok=True)
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font_manager.fontManager.addfont(FONT)
plt.rcParams.update({
    'font.family': font_manager.FontProperties(fname=FONT).get_name(),
    'pdf.fonttype': 3, 'ps.fonttype': 3, 'axes.unicode_minus': False,
    'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.labelcolor': '#344453', 'text.color': '#182d40',
    'axes.edgecolor': '#aab5bf', 'xtick.color': '#485968', 'ytick.color': '#485968',
})
DATA = [
    ('deep10m_l2_v1', 'Deep10M', 'soft', '10M × 96；L2；10K 查询'),
    ('sift10m_bigann_l2_v1', 'SIFT10M', 'soft', '10M × 128；L2；10K 查询'),
    ('gist1m_l2_v1', 'GIST1M', 'hard', '1M × 960；L2；1K 查询'),
    ('webvid2_5m_light_v1', 'WebVid', 'soft', '2.505M × 512；IP；10K 查询'),
    ('yandex_t2i_official10M_ip_v1', 'Yandex', 'hard', '10M × 200；IP；10K 查询'),
    ('coco', 'COCO', 'hard', '118,272 × 512；IP；10K 查询'),
    ('flickr30k', 'Flickr30k', 'hard', '31,782 × 512；IP；5K 查询'),
]
POINTS = list(csv.DictReader((SRC / 'points.csv').open()))
DELTAS = list(csv.DictReader((SRC / 'same_L_deltas.csv').open()))
assert len(POINTS) == 645
def methods(fam):
    return ['NSG', 'GT10-soft-t1' if fam == 'soft' else 'GT10-hard', fam + '-JOINT32']
def delta(ds, method, k):
    rr = [r for r in DELTAS if r['dataset'] == ds and r['method'] == method
          and int(r['K']) == k and int(r['L']) == 200]
    assert len(rr) == 1
    return rr[0]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def write_csv(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

selected = []
comparisons = []
table = []
table_raw = []
for ds, label, fam, _ in DATA:
    mm = methods(fam)
    subset = [r for r in POINTS if r['dataset'] == ds and r['method'] in mm]
    assert len(subset) == 45
    for method in mm:
        for k, expected in [(1, [16,32,64,100,200,400,800,1200]),
                            (100, [100,128,200,400,800,1000,1200])]:
            rr = sorted([r for r in subset if r['method'] == method and int(r['K']) == k], key=lambda r:int(r['L']))
            assert [int(r['L']) for r in rr] == expected
            assert all(int(r['timing_repeats']) == 3 for r in rr)
            selected.extend(rr)
    g1, r1, g100, r100 = [delta(ds, m, k) for m,k in [(mm[1],1),(mm[2],1),(mm[1],100),(mm[2],100)]]
    comparisons.extend([g1,r1,g100,r100])
    assert all(r['reference_method'] == mm[1] for r in (r1,r100))
    for k, g, r in [(1,g1,r1),(100,g100,r100)]:
        lookup = {(p['method'],int(p['K']),int(p['L'])):p for p in subset}
        for v, reference in [(g,'NSG'),(r,mm[1])]:
            assert int(v['hits']) == int(lookup[(v['method'],k,200)]['hits'])
            assert int(v['reference_hits']) == int(lookup[(reference,k,200)]['hits'])
            assert int(v['net_members']) == int(v['rescued_members'])-int(v['damaged_members'])
    table.append([
        label,
        f"{g1['rescued_members']}/{g1['reference_missing_members']}；{g1['damaged_members']}",
        f"{r1['rescued_members']}/{r1['reference_missing_members']}；{r1['damaged_members']}",
        f"{float(g100['recall_delta_pp']):+.4f}",
        f"{100*float(r100['rescue_rate_on_missing']):.3f}%",
        f"{float(r100['recall_delta_pp']):+.4f}",
        f"{float(r100['qps_pct']):+.2f}%",
    ])
    table_raw.append({
        'dataset':ds, 'label':label, 'GT10_method':mm[1], 'residual_method':mm[2], 'L':200,
        'GT10_K1_rescued_queries':int(g1['rescued_members']),
        'NSG_K1_failed_queries':int(g1['reference_missing_members']),
        'GT10_K1_damaged_queries':int(g1['damaged_members']),
        'residual_K1_rescued_queries':int(r1['rescued_members']),
        'GT10_K1_failed_queries':int(r1['reference_missing_members']),
        'residual_K1_damaged_queries':int(r1['damaged_members']),
        'GT10_K100_recall_delta_pp':float(g100['recall_delta_pp']),
        'residual_K100_rescued_members':int(r100['rescued_members']),
        'GT10_K100_missing_members':int(r100['reference_missing_members']),
        'residual_K100_damaged_members':int(r100['damaged_members']),
        'residual_K100_missing_repair_pct':100*float(r100['rescue_rate_on_missing']),
        'residual_K100_recall_delta_pp':float(r100['recall_delta_pp']),
        'residual_K100_qps_delta_pct':float(r100['qps_pct']),
    })
assert len(selected) == 315 and len(comparisons) == 28
write_csv(OUT/'selected_points.csv', selected)
write_csv(OUT/'selected_L200_comparisons.csv', comparisons)
write_csv(OUT/'failure_queries_L200.csv', table_raw)

CONCLUSIONS = [
    ('GT10：非多模态可迁移', 'Deep 的效率收益较清楚；SIFT 的 K100 有收益，K1 高召回端混合；GIST 表现较弱、部分区间交叉。'),
    ('残差：非多模态增益有限', 'Deep / SIFT 新增召回很小，K100 曲线低于 GT10；GIST 仅部分 K100 区间有小幅收益。'),
    ('多模态：按数据集判断', 'WebVid / COCO 的 K1、K100 曲线受益；Flickr30k 存在交叉，Yandex 的 K100 曲线较低。'),
]
HEADERS = ['数据集','GT10 K1\n救回/原失败；损伤','残差 K1\n救回/原失败；损伤',
           'GT10 K100\nΔRecall (pp)','残差 K100\n遗漏修复率','残差 K100\nΔRecall (pp)','残差 K100\nΔQPS']
def txt(fig,x,y,s,size=10,**kw):
    return fig.text(x,y,s,fontsize=size,va='top',**kw)
def wrapped(s,width=49):
    return '\n'.join(textwrap.wrap(s,width=width,break_long_words=True,break_on_hyphens=False))
def chrome(fig,title,page,subtitle=None):
    txt(fig,.06,.957,title,18,weight='bold')
    if subtitle: txt(fig,.06,.921,subtitle,9,color='#617381')
    fig.add_artist(plt.Line2D([.06,.94],[.902,.902],transform=fig.transFigure,color='#dbe3e9',lw=1))
    txt(fig,.06,.029,'E183 · 既有结果简版 · 单线程完整端到端 QPS',8,color='#617381')
    txt(fig,.94,.029,f'{page} / 4',8,ha='right',color='#617381')

pdf_path = OUT/'NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf'
with PdfPages(pdf_path, metadata={'Title':'E183 | NSG、GT10 与 GT10＋残差',
              'Author':'ACSG','Subject':'七数据集 Recall–QPS 与失败查询；仅重排既有结果'}) as pdf:
    fig = plt.figure(figsize=(8.27,11.69))
    chrome(fig,'NSG、GT10 与 GT10＋残差',1,'七数据集结果简报  |  原实验 2026-10-17  ·  简版 2026-10-18')
    y = .877
    for title,body in CONCLUSIONS:
        txt(fig,.065,y,title,12,weight='bold',color='#176a97')
        txt(fig,.065,y-.029,wrapped(body,48),10)
        y -= .102
    txt(fig,.065,.561,'失败查询与遗漏修复（统一 L = 200）',12,weight='bold')
    ax=fig.add_axes([.052,.310,.896,.219]); ax.axis('off')
    tab=ax.table(cellText=table,colLabels=HEADERS,cellLoc='center',colLoc='center',
                 colWidths=[.123,.175,.175,.137,.125,.14,.125],bbox=[0,0,1,1])
    tab.auto_set_font_size(False); tab.set_fontsize(7.7)
    for (r,c),cell in tab.get_celld().items():
        cell.set_linewidth(.5); cell.set_edgecolor('#d5dfe6')
        cell.set_facecolor('#eaf1f6' if r==0 else ('#f6f8fa' if r%2==0 else 'white'))
        if r==0: cell.set_text_props(weight='bold'); cell.set_height(cell.get_height()*1.4)
    notes=[
        'K1：GT10 对比 NSG；残差对比自身 GT10。每格为“救回数 / 原失败数；新损伤数”。',
        'K100：GT10 ΔRecall 对比 NSG；残差三列均对比 GT10。遗漏修复率以原遗漏成员为分母，',
        '不表示整条查询已完全解决；pp 为百分点。本表残差 K100 新损伤均为 0。',
        '固定展示：Deep / SIFT / WebVid 用 soft-t1，其余用 hard；残差均为同一版本的 B32。',
        '每个数据集全 L 固定同一版本，没有按测点切换赢家。',
    ]
    for i,note in enumerate(notes): txt(fig,.065,.286-i*.023,note,8.4,color='#526775')
    txt(fig,.065,.149,'读图与证据范围',10,weight='bold')
    txt(fig,.065,.124,'点为既有实测，线段仅连接相邻 L；QPS 为三轮中位数，同召回下越高越好。\n'
        '复用 645 点中的 315 点，无新增实验；单图 / 单模型 / 已曝光查询，不作盲泛化结论。\n'
        '当前 E99 GT10 默认保持；原始结果与详细报告均保留。',8.7,linespacing=1.7)
    pdf.savefig(fig); fig.savefig(OUT/'page_1.png',dpi=150); plt.close(fig)

    colors=['#6f7a84','#187caf','#e37c25']; markers=['o','^','s']
    labels=['NSG','GT10','GT10＋残差']
    groups=[(DATA[:3],'非多模态数据：原始 L2',2),
            (DATA[3:5],'多模态数据：WebVid 与 Yandex',3),
            (DATA[5:],'多模态数据：COCO 与 Flickr30k',4)]
    for datasets,title,page in groups:
        fig,axes=plt.subplots(len(datasets),2,figsize=(8.27,11.69),squeeze=False)
        chrome(fig,title,page,'每图仅三条线：NSG / GT10 / GT10＋残差（B32）')
        fig.subplots_adjust(left=.10,right=.955,bottom=.115,top=.835,hspace=.49 if len(datasets)==3 else .36,wspace=.30)
        handles=[]
        for i,(ds,label,fam,info) in enumerate(datasets):
            for j,k in enumerate([1,100]):
                ax=axes[i,j]
                for method,color,marker,display in zip(methods(fam),colors,markers,labels):
                    rr=sorted([r for r in selected if r['dataset']==ds and r['method']==method and int(r['K'])==k],key=lambda r:int(r['L']))
                    assert len(rr)==(8 if k==1 else 7)
                    line,=ax.plot([float(r['recall_pct']) for r in rr],[float(r['qps']) for r in rr],
                                  color=color,marker=marker,ms=3.7,lw=1.5,label=display)
                    if i==0 and j==0: handles.append(line)
                assert len(ax.lines)==3
                ax.set_title(f'{label} · Recall@{k}',fontsize=11,pad=8,loc='left')
                ax.set_xlabel(f'Recall@{k} (%)',fontsize=9); ax.set_ylabel('QPS（对数）',fontsize=9)
                ax.set_yscale('log'); ax.yaxis.set_major_locator(LogLocator(base=10,subs=(1,2,5),numticks=6))
                ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:,.0f}'))
                ax.yaxis.set_minor_formatter(NullFormatter())
                ax.xaxis.set_major_locator(MaxNLocator(nbins=4,min_n_ticks=3))
                ax.tick_params(axis='both',labelsize=8); ax.grid(True,which='major',alpha=.19)
                ax.text(0,.99,info,transform=ax.transAxes,va='top',fontsize=7.1,color='#617381')
                ax.margins(x=.045,y=.15)
        fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.52,.889),ncol=3,frameon=False,fontsize=10)
        txt(fig,.075,.078,'单线程完整端到端 QPS，三轮中位数；仅连接实测点。K1：8 档 L；K100：7 档 L。',8)
        txt(fig,.075,.057,'Deep / SIFT / WebVid 固定 soft-t1，其余固定 hard；残差为对应 GT10 的 B32 补全。',8)
        pdf.savefig(fig); fig.savefig(OUT/f'page_{page}.png',dpi=150); plt.close(fig)

md=['# NSG、GT10 与 GT10＋残差：简版报告','',
    '2026-10-18。只重排 E183 既有结果，无新增实验。完整图表见同目录四页 PDF。','']
for title,body in CONCLUSIONS: md.extend([f'**{title}**：{body}',''])
md.extend(['统一 L200 的失败查询表：','',
           '| '+' | '.join(h.replace('\n',' ') for h in HEADERS)+' |',
           '|'+'---|'*len(HEADERS)])
md.extend('| '+' | '.join(row)+' |' for row in table)
md.extend(['',*notes,'',
    '曲线为单线程完整端到端 QPS 三轮中位数，点为实测、线段只连接相邻 L；七集各固定一个版本。',
    '315 个图示点来自完整 645 点。单图、单模型、已曝光查询；当前 E99 GT10 默认不变。',
    '数据：selected_points.csv；失败表：failure_queries_L200.csv；原始比较：selected_L200_comparisons.csv。',''])
(OUT/'report_zh.md').write_text('\n'.join(md))
manifest={
    'status':'PASS_CONCISE_REPORT_DATA_CHECKS',
    'scope':'Presentation only; no new measurements, no default change; detailed reports preserved',
    'source_points':645,'selected_points':315,'panels':14,'lines_per_panel':3,'pages':4,
    'fixed_L200_comparisons':28,'failure_table_rows':7,
    'method_selection':{ds:methods(fam) for ds,_,fam,_ in DATA},
    'selection_policy':'Same whole-L hard/soft examples as detailed delivery_v2; fixed B32, no per-point selection',
    'sources':{str(p.relative_to(ROOT)):digest(p) for p in [SRC/'points.csv',SRC/'same_L_deltas.csv',ROOT/'analysis/delivery_v2/report_zh.md']},
    'artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['manifest.json','pdf_visual_review.json']},
}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pdf':str(pdf_path),'pages':4,'points':315,'table_rows':7,'bytes':pdf_path.stat().st_size},ensure_ascii=False))
