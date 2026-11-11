from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=list(csv.DictReader((R/'analysis/points.csv').open()))
methods=['GT10','B32','OPT-B32','REUSE-SQ',*NAV];colors=plt.get_cmap('tab10').colors
for ds in DS:
    fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    for i,K in enumerate([1,100]):
        for j,w in enumerate(['A','B']):
            ax=axes[i,j]
            for z,m in enumerate(methods):
                x=sorted([r for r in rows if r['dataset']==ds and r['window']==w and int(r['K'])==K and r['method']==m],key=lambda a:float(a['recall_pct']))
                ax.plot([float(a['recall_pct']) for a in x],[float(a['qps']) for a in x],label=m,color=colors[z],marker='o' if z<4 else '.',markersize=4,linewidth=1.2)
            ax.set_title(f'{ds} / {w} / K={K}');ax.set_xlabel('Strict GT-ID recall (%)');ax.set_ylabel('Complete T1 QPS');ax.grid(alpha=.2)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=5,fontsize=8)
    fig.savefig(R/f'analysis/{ds}_recall_qps.svg');plt.close(fig)
print('PLOTS_WRITTEN',flush=True)
