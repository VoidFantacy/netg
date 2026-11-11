from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=list(csv.DictReader((R/'analysis/points.csv').open()));methods=['GT10','OPT-B32','ONEHOP96','DIST96','DIST384','NOVEL96','NOVEL384','REP384'];colors=plt.get_cmap('tab10').colors
for ds in DS:
 ks=sorted(set(int(p['K'])for p in P if p['dataset']==ds));fig,axes=plt.subplots(len(ks),2,figsize=(12,4*len(ks)),squeeze=False,constrained_layout=True)
 for i,K in enumerate(ks):
  for j,w in enumerate(['A','B']):
   ax=axes[i,j]
   for k,m in enumerate(methods):
    a=sorted([p for p in P if p['dataset']==ds and p['window']==w and int(p['K'])==K and p['method']==m],key=lambda p:float(p['recall_pct']))
    if not a:continue
    ax.plot([float(p['recall_pct'])for p in a],[float(p['qps'])for p in a],label=m,marker='.'if k<2 else 'o',markersize=3,color=colors[k],linewidth=1)
   ax.set_title(f'{ds} / {w} / K={K}');ax.set_xlabel('Strict GT-ID recall (%)');ax.set_ylabel('Complete T1 QPS');ax.grid(alpha=.2)
 h,l=axes[0,0].get_legend_handles_labels();fig.legend(h,l,loc='outside lower center',ncol=4,fontsize=8);fig.savefig(R/f'analysis/{ds}_recall_qps.svg')
 if ds=='coco':fig.savefig(R/'analysis/preview.png',dpi=110)
 plt.close(fig)
print('PLOTS_WRITTEN',flush=True)
