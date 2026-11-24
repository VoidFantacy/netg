"""Draw only the two complete-wall methods for each dataset."""
import csv
from pathlib import Path
from matplotlib import pyplot as plt, ticker
from matplotlib.font_manager import FontProperties

from drive import DATASETS,ROOT

font=Path('/usr/share/fonts/opentype/noto')
reg=FontProperties(fname=font/'NotoSansCJK-Regular.ttc')
bold=FontProperties(fname=font/'NotoSansCJK-Bold.ttc')
legend=FontProperties(fname=reg.get_file(),size=9)
ink='#182b43'; muted='#546e83'
with (ROOT/'analysis/points.csv').open() as fp:
    rows=list(csv.DictReader(fp))
fig,axs=plt.subplots(1,2,figsize=(11.5,5.15),facecolor='#f4f7fa')
fig.subplots_adjust(left=.091,right=.977,bottom=.19,top=.73,wspace=.27)
fig.text(.091,.918,'B64 全精算补点的异窗复测',fontproperties=bold,fontsize=23,color=ink)
fig.text(.091,.83,'真实 K100  ·  每集 3,072 条查询  ·  CPU15 单线程完整计时  ·  每点两遍均值',
         fontproperties=reg,fontsize=11,color=muted)
fig.text(.091,.053,'每个散点是一档实测 L。L 从 168 到 244，步长为 4。',fontproperties=reg,fontsize=9,color=muted)
for ax,ds,text in zip(axs,DATASETS,('COCO','WebVid 2.5M')):
    ax.set_title(text,loc='left',fontproperties=bold,fontsize=14,color=ink,pad=8)
    ax.set_axisbelow(True)
    ax.grid(color='#dae5ee',linewidth=.8)
    ax.tick_params(colors=muted,labelsize=9,length=0,pad=5)
    for edge in ax.spines.values(): edge.set_color('#ccd9e6')
    ax.xaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.2f}'))
    for method,name,color,mark in [('B32','GT10+B32','#16748a','o'),('B64','GT10+B64 全精算','#ba4b36','D')]:
        points=sorted((p for p in rows if p['dataset']==ds and p['method']==method),key=lambda p:int(p['L']))
        ax.plot([float(p['qps']) for p in points],[float(p['recall'])*100 for p in points],label=name,
                color=color,marker=mark,linewidth=1.8,markersize=4,markeredgecolor='white',markeredgewidth=.55,zorder=3)
    ax.set_xlabel('完整吞吐量（QPS）',fontproperties=reg,fontsize=10,color=ink,labelpad=6)
    ax.set_ylabel('Recall@100（%）',fontproperties=reg,fontsize=10,color=ink,labelpad=6)
    ax.legend(loc='lower left',prop=legend,labelcolor=ink,framealpha=.97,edgecolor='#dce5ed')
fig.savefig(ROOT/'analysis/recall_qps.png',dpi=210,facecolor=fig.get_facecolor())
