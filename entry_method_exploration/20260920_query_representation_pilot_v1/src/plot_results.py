from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows=read(RUN/'results/quality_metrics.json')
fig,axes=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
families=['QLinear','QMLP','WFree'];colors={'fit':'#b8c9e4','cal':'#355c8c'}
for i,ds in enumerate(DS):
    for j,K in enumerate([1,100]):
        ax=axes[i,j]
        for s,shift in [('fit',-.18),('cal',.18)]:
            selected=[next(x for x in rows if x['dataset']==ds and x['split']==s and x['K']==K and x['method']==f+'ANN') for f in families]
            values=np.array([x['delta_gt10_pp'] for x in selected]);low=np.array([x['ci95_low_pp'] for x in selected]);high=np.array([x['ci95_high_pp'] for x in selected])
            ax.bar(np.arange(3)+shift,values,width=.32,color=colors[s],label='Fit (2048)' if s=='fit' else 'Development (512)')
            ax.errorbar(np.arange(3)+shift,values,yerr=[values-low,high-values],fmt='none',ecolor='#263648',capsize=3,lw=1)
        ax.axhline(0,color='#333',lw=.8);ax.set_xticks(np.arange(3),families);ax.set_ylabel('Recall change vs GT10 (percentage points)')
        ax.set_title(('WebVid' if ds.startswith('webvid') else 'Yandex')+f' | Recall@{K}')
        ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axes[0,0].legend(frameon=False,fontsize=9)
fig.suptitle('E104: query representation pilot | L=128, actual Micro-HNSW routing\nDescriptive paired 95% bootstrap intervals; reused development data; no QPS claim',fontsize=12)
out=RUN/'figures';out.mkdir(exist_ok=True)
fig.savefig(out/'recall_changes.png',dpi=180);fig.savefig(out/'recall_changes.pdf');plt.close(fig)
dump(RUN/'reviews/figure_manifest.json',dict(source=identity(Path(__file__)),files=[identity(out/x) for x in ['recall_changes.png','recall_changes.pdf']]))
print(out/'recall_changes.png')
