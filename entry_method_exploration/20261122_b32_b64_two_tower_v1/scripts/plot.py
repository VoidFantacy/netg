"""Plot the two requested pairwise comparisons from independently scored formal rows."""
import csv
from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib import ticker
from matplotlib.font_manager import FontProperties
import numpy as np

from run import DATASETS, ROOT

ANALYSIS = ROOT/'analysis'
FONT = Path('/usr/share/fonts/opentype/noto')
CJK = FontProperties(fname=FONT/'NotoSansCJK-Regular.ttc')
BOLD = FontProperties(fname=FONT/'NotoSansCJK-Bold.ttc')
DATASET_NAMES = ('COCO', 'WebVid 2.5M')
INK = '#182b43'
MUTED = '#5c6a7a'
BASE = '#20708b'
TOWER = '#bd4c34'


with (ANALYSIS/'points.csv').open() as f:
    points=list(csv.DictReader(f))
fig, panes = plt.subplots(2,2,figsize=(12,8),facecolor='#f4f7fa')
fig.subplots_adjust(left=.092, right=.97, bottom=.11, top=.843, hspace=.48, wspace=.265)
fig.text(.092,.945,'双塔补点的 Recall–QPS 实测曲线',fontproperties=BOLD,fontsize=25,color=INK)
fig.text(.092,.894,'真实 K100  ·  每集 3,072 条查询  ·  CPU15 单线程完整计时  ·  每点两遍均值',
         fontproperties=CJK,fontsize=11.5,color=MUTED)
fig.text(.092,.043,'散点为实际 L 测点，连线用于读图。越靠右上，召回与吞吐的组合越好。',
         fontproperties=CJK,fontsize=9.5,color=MUTED)
for i,(ds,title) in enumerate(zip(DATASETS,DATASET_NAMES)):
    data = [p for p in points if p['dataset']==ds and p['method'] in ('B32','TT-B32','TT-B64')]
    xs = np.array([float(p['qps']) for p in data])
    ys = np.array([100*float(p['recall']) for p in data])
    dx,dy=np.ptp(xs)*.07,np.ptp(ys)*.11
    for j,width in enumerate((32,64)):
        pane = panes[i,j]
        pane.set_title(f'{title}   /   B{width} 候选池',loc='left',fontproperties=BOLD,fontsize=13,
                       color=INK,pad=9)
        pane.set(xlim=(xs.min()-dx,xs.max()+dx),ylim=(ys.min()-dy,ys.max()+dy))
        pane.set_axisbelow(True)
        pane.grid(color='#dbe4ed',linewidth=.8)
        pane.tick_params(colors=MUTED,labelsize=9,length=0,pad=6)
        for edge in pane.spines.values():
            edge.set_color('#ced9e5')
        pane.xaxis.set_major_locator(ticker.MaxNLocator(5))
        pane.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        pane.yaxis.set_major_locator(ticker.MaxNLocator(5))
        pane.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.2f}'))
        for method,name,color,marker in (('B32','GT10+B32',BASE,'o'),
                (f'TT-B{width}',f'GT10+双塔 B{width}',TOWER,'D')):
            use=sorted([p for p in data if p['method']==method],key=lambda p:int(p['L']))
            pane.plot([float(p['qps']) for p in use],[100*float(p['recall']) for p in use],
                      label=name,color=color,linewidth=2.05,marker=marker,markersize=4.4,
                      markeredgecolor='white',markeredgewidth=.65,zorder=4)
        pane.legend(loc='lower left',prop=FontProperties(fname=CJK.get_file(),size=8.5),
                    labelcolor=INK,facecolor='white',edgecolor='#dce4ed',frameon=True,framealpha=.97)
        pane.set_xlabel('完整吞吐量（QPS）',fontproperties=CJK,fontsize=10,color=INK,labelpad=5)
        pane.set_ylabel('Recall@100（%）',fontproperties=CJK,fontsize=10,color=INK,labelpad=6)
fig.savefig(ANALYSIS/'recall_qps.png',dpi=210,facecolor=fig.get_facecolor())
