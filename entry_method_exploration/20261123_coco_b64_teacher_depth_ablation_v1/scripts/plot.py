"""The three predeclared methods, with window roles labelled."""
import csv
from pathlib import Path
from matplotlib import pyplot as plt, ticker
from matplotlib.font_manager import FontProperties

from drive import ROOT

fonts=Path('/usr/share/fonts/opentype/noto')
regular=FontProperties(fname=fonts/'NotoSansCJK-Regular.ttc')
bold=FontProperties(fname=fonts/'NotoSansCJK-Bold.ttc')
legend=FontProperties(fname=regular.get_file(),size=9.3)
ink='#192c44'; muted='#557086'
with (ROOT/'analysis/points.csv').open() as src:
    rows=list(csv.DictReader(src))
fig,panels=plt.subplots(1,2,figsize=(12,5.25),facecolor='#f4f7fa')
fig.subplots_adjust(left=.084,right=.973,bottom=.183,top=.72,wspace=.24)
fig.text(.084,.922,'COCO K100 同样本监督深度消融',fontproperties=bold,fontsize=23,color=ink)
fig.text(.084,.836,'每组 3,072 条真实查询  ·  CPU15 单线程完整计时  ·  每点两遍均值',
         fontproperties=regular,fontsize=11,color=muted)
fig.text(.084,.047,'新 B64 为多档真遗漏监督，四个同样本单档对照见报告。',
         fontproperties=regular,fontsize=9.4,color=muted)
for (w,tag),ax in zip((("confirmation","确认窗"),("confirmation","97% 附近")),panels):
    ax.set_title(f'COCO  /  {tag}',loc='left',fontproperties=bold,fontsize=14,color=ink,pad=8)
    ax.set_axisbelow(True); ax.grid(color='#d9e5ed',linewidth=.85)
    ax.tick_params(colors=muted,labelsize=9,length=0,pad=6)
    for spine in ax.spines.values(): spine.set_color('#ccd9e6')
    ax.xaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.2f}'))
    for arm,name,colour,marker in [('B32','B32','#16718b','o'),('B64-old','老 B64','#bc5138','D'),('Mixed64','新 B64','#276e57','^')]:
        pts=sorted((p for p in rows if p['method']==arm and p['window']==w),key=lambda p:int(p['L']))
        ax.plot([float(p['qps']) for p in pts],[float(p['recall_pct']) for p in pts],label=name,color=colour,
                marker=marker,linewidth=1.8,markersize=4.5,markeredgecolor='white',markeredgewidth=.6,zorder=3)
    if tag=="97% 附近":
        ax.set_ylim(96.5,97.6)
        visible=[float(p['qps']) for p in rows if 96.45<=float(p['recall_pct'])<=97.65]
        ax.set_xlim(min(visible)-20,max(visible)+20)
    ax.set_xlabel('完整吞吐量（QPS）',fontproperties=regular,fontsize=10,color=ink,labelpad=6)
    ax.set_ylabel('Recall@100（%）',fontproperties=regular,fontsize=10,color=ink,labelpad=6)
    ax.legend(loc='lower left',prop=legend,labelcolor=ink,edgecolor='#dbe5ee',framealpha=.98)
fig.savefig(ROOT/'analysis/recall_qps.png',dpi=215,facecolor=fig.get_facecolor())
