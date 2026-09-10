"""Label placement correction only; reuse measured metrics without new analysis/search."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import DATASETS, RUN, read
from analyze import SHORT, COLOR

rows=read(RUN/'results/summary.json')['metrics']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
for ax,ds in zip(axes,DATASETS):
    for m in [x for x in rows if x['dataset']==ds and x['stage']=='cal' and not x['exact']]:
        ax.scatter(m['recall_percent'],m['qps'],color=COLOR[m['family']],s=35)
        offset=(5,6);ha='left'
        if ds==DATASETS[0] and m['model_name']=='gt10_soft_t0':offset=(-8,13);ha='right'
        if ds==DATASETS[0] and m['model_name']=='gt10_soft_t1':offset=(7,-15)
        if ds==DATASETS[1] and m['model_name']=='gt1_hard':offset=(5,-14)
        ax.annotate(m['model_name'].replace('gt','GT').replace('_',' '),(m['recall_percent'],m['qps']),
                    xytext=offset,textcoords='offset points',fontsize=8,ha=ha)
    ax.margins(x=.17,y=.15)
    ax.set(title=SHORT[ds]+' | cal 1,024, L128',xlabel='Recall@10 (%)',ylabel='End-to-end QPS (1 thread)')
    ax.grid(alpha=.2)
fig.suptitle('Calibration candidates: HNSW direct3 (selection uses hits, not timing)',fontsize=12)
for ext in ['png','svg']:fig.savefig(RUN/f'figures/cal_recall_qps.{ext}',dpi=180)
