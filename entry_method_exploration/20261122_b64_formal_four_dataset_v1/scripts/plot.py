"""Plot the two requested curves in four panels for each real return width."""
import csv
from pathlib import Path

from matplotlib import pyplot as plt, ticker
from matplotlib.font_manager import FontProperties

from drive import DATASETS,NAMES,ROOT

font=Path('/usr/share/fonts/opentype/noto')
regular=FontProperties(fname=font/'NotoSansCJK-Regular.ttc')
bold=FontProperties(fname=font/'NotoSansCJK-Bold.ttc')
legend=FontProperties(fname=regular.get_file(),size=8.8)
ink='#182b43'; muted='#536a81'
with (ROOT/'analysis/points.csv').open() as fp:
    rows=list(csv.DictReader(fp))
for k in (1,100):
    fig,axes=plt.subplots(2,2,figsize=(12,8.4),facecolor='#f4f7fa')
    fig.subplots_adjust(left=.09,right=.974,bottom=.105,top=.828,hspace=.48,wspace=.27)
    fig.text(.09,.941,f'四集全精算 B64 正式比较  /  K{k}',fontproperties=bold,fontsize=23,color=ink)
    fig.text(.09,.888,'每集 3,072 条真实查询  ·  CPU15 单线程完整计时  ·  每点两遍均值',
             fontproperties=regular,fontsize=11,color=muted)
    fig.text(.09,.036,'散点为实测 L。每个面板只比较原版 B32 和全精算 B64。',fontproperties=regular,fontsize=9,color=muted)
    for ax,ds in zip(axes.ravel(),DATASETS):
        ax.set_title(NAMES[ds],loc='left',fontproperties=bold,fontsize=13,color=ink,pad=8)
        ax.grid(color='#d9e4ed',linewidth=.8)
        ax.set_axisbelow(True)
        ax.tick_params(colors=muted,labelsize=9,length=0,pad=6)
        for edge in ax.spines.values(): edge.set_color('#ccd9e5')
        ax.xaxis.set_major_locator(ticker.MaxNLocator(5))
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:.2f}'))
        for method,label,color,marker in [('B32','GT10+B32','#16748a','o'),('B64','GT10+B64 全精算','#bd4d34','D')]:
            pts=sorted((p for p in rows if p['dataset']==ds and int(p['K'])==k and p['method']==method),key=lambda p:int(p['L']))
            ax.plot([float(p['qps']) for p in pts],[float(p['recall_pct']) for p in pts],label=label,color=color,
                marker=marker,linewidth=1.85,markersize=4.2,markeredgecolor='white',markeredgewidth=.6,zorder=4)
        ax.set_xlabel('完整吞吐量（QPS）',fontsize=10,fontproperties=regular,color=ink,labelpad=6)
        ax.set_ylabel(f'Recall@{k}（%）',fontsize=10,fontproperties=regular,color=ink,labelpad=7)
        ax.legend(loc='lower left',prop=legend,labelcolor=ink,framealpha=.97,edgecolor='#dae5ed')
    fig.savefig(ROOT/f'analysis/recall_qps_k{k}.png',dpi=200,facecolor=fig.get_facecolor())
    plt.close(fig)
