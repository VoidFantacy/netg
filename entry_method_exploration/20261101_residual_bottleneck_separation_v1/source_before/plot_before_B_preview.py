from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=list(csv.DictReader((R/'analysis/points.csv').open()))
room=list(csv.DictReader((R/'analysis/bottlenecks.csv').open()))
out=R/'analysis/figures';out.mkdir(exist_ok=True)
labels=dict(zip(DS,['COCO','Flickr','WebVid','Yandex','Deep10M','SIFT10M','GIST']))
fig,axes=plt.subplots(3,3,figsize=(14,10));palette=['#547aa5','#3d9c75','#a9a9a9','#d5a64c']
for ax,ds in zip(axes.flat,DS):
    r=next(x for x in room if x['dataset']==ds and x['K']=='100' and x['bank']=='FULL')
    scale=100/(int(r['queries'])*100)
    values=[float(r[k])*scale for k in ['distance_single_gain','model_gain','C_full_gain','shared_pool_gain']]
    bars=ax.bar(range(4),values,color=palette)
    ax.set_xticks(range(4),['Distance1','Model1','Oracle C','Oracle shared'],rotation=12,fontsize=8)
    ax.set_title(labels[ds]);ax.set_ylabel('Additional Recall@100 (pp)');ax.axhline(0,color='#555',lw=.6)
    ax.grid(axis='y',alpha=.2)
    for b,v in zip(bars,values):ax.annotate(f'{v:.3f}',(b.get_x()+b.get_width()/2,v),ha='center',va='bottom',fontsize=8)
for ax in list(axes.flat)[7:]:ax.axis('off')
fig.suptitle('One-seed quality above full B32: L200 / cap384 / exposed A+B\nOracle bars use GT; shared oracle adds scored-unexpanded candidates. These bars exclude selection cost.',fontsize=12)
fig.tight_layout(rect=[0,0,.99,.93]);fig.savefig(out/'quality_headroom.svg');fig.savefig(out/'quality_headroom.png',dpi=140);plt.close(fig)
display={'MODEL-FULL':('o','#24895c'),'MODEL-GATE-FULL':('s','#77aa52'),
         'DIST1-FULL':('x','#6e4c9b'),'CBRIDGE384-FULL':('D','#d3922b'),
         'SHARED384-FULL':('^','#c7524b'),'EARLY-MIX-FULL':('P','#a36d53')}
for window in ['A','B']:
    fig,axes=plt.subplots(3,3,figsize=(15,10))
    for ax,ds in zip(axes.flat,DS):
        data=[r for r in rows if r['dataset']==ds and r['window']==window and r['K']=='100']
        for method,color in [('GT10','#3179b2'),('OPT-B32','#ed7d31'),('REUSE-SQ','#9272ba')]:
            p=sorted([r for r in data if r['method']==method],key=lambda r:int(r['L']))
            ax.plot([float(r['recall_pct']) for r in p],[float(r['qps']) for r in p],'.-',color=color,lw=.8,ms=3,label=method)
        for method,(marker,color) in display.items():
            r=next(r for r in data if r['method']==method and r['L']=='200')
            ax.scatter(float(r['recall_pct']),float(r['qps']),marker=marker,c=color,s=36,label=method,zorder=4)
        ax.set_title(labels[ds]);ax.set_xlabel('Recall@100 (%)');ax.set_ylabel('Complete T1 QPS');ax.grid(alpha=.18)
    handles,names=axes.flat[0].get_legend_handles_labels()
    for ax in list(axes.flat)[7:]:ax.axis('off')
    fig.legend(handles,names,loc='lower right',bbox_to_anchor=(.98,.04),fontsize=8,ncol=1)
    fig.suptitle(f'E197 / K100 / window {window}: full-table L200 candidates and measured strong controls\nControl lines connect actual L points; no interpolation or exact-equal-Recall speed claim.',fontsize=12)
    fig.tight_layout(rect=[0,0,.99,.93]);fig.savefig(out/f'complete_wall_{window}.svg')
    if window=='A':fig.savefig(out/'complete_wall_A.png',dpi=140)
    plt.close(fig)
dump(out/'plot_receipt.json',dict(status='PLOTS_FROM_ACTUAL_MEASURED_ROWS_ONLY',figures=3,new_performance_measurements=False))
print('PLOTS_WRITTEN',flush=True)
