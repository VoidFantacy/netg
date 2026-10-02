import json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
D=pathlib.Path(__file__).resolve().parent.parent;s=json.loads((D/'results/summary.json').read_text());rows=s['metrics']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors={'NSG':'#64748b','GT10-hard':'#2563eb','GT10-soft-t1':'#dc2626','GATE':'#16a34a','HNSW':'#9333ea'}
labels={'NSG':'Project NSG (fixed entry)','GT10-hard':'GT10-hard','GT10-soft-t1':'GT10-soft','GATE':'GATE','HNSW':'Full HNSW (reference)'}
fig,axs=plt.subplots(1,2,figsize=(12,5.3))
for ax,k in zip(axs,[1,100]):
 for m,col in colors.items():
  a=sorted([r for r in rows if r['K']==k and r['method']==m and r['kernel']!='current'],key=lambda x:x['recall'])
  ax.errorbar([x['recall']*100 for x in a],[x['qps_mean'] for x in a],yerr=[[x['qps_mean']-x['qps_min'] for x in a],[x['qps_max']-x['qps_mean'] for x in a]],label=labels[m],color=col,marker='o',linestyle='--',capsize=3)
 ax.set_title(f'WebVid Recall@{k}',fontweight='bold');ax.set_xlabel(f'Recall@{k} (%)');ax.set_ylabel('End-to-end QPS (1 thread)');ax.set_yscale('log');ax.grid(alpha=.15)
handles,names=axs[0].get_legend_handles_labels();fig.legend(handles,names,loc='lower center',bbox_to_anchor=(.5,.05),ncol=3,frameon=False)
fig.suptitle('NSG, GT10 and GATE with the same span + batch4 search kernel',fontsize=13)
fig.text(.5,.015,'Two measured budgets per K; dashed lines are guides, not a measured continuous frontier. Error bars: 3-run range.',ha='center',fontsize=8.5)
fig.tight_layout(rect=(0,.22,1,.94))
for ext in ['png','pdf']:fig.savefig(D/f'figures/shared_kernel_recall_qps.{ext}',dpi=180)
plt.close(fig)
methods=['NSG','GT10-hard','GT10-soft-t1','GATE'];points=[(1,96),(100,100),(1,800),(100,1250)];pal=['#93c5fd','#2563eb','#fb923c','#dc2626'];x=np.arange(4);width=.19
fig,ax=plt.subplots(figsize=(11,5.2))
for i,((k,L),col) in enumerate(zip(points,pal)):
 a=[next(v for v in s['speedups'] if (v['method'],v['K'],v['L'])==(m,k,L)) for m in methods];ys=[v['speedup_percent'] for v in a]
 ax.bar(x+(i-1.5)*width,ys,width,color=col,label=f'K{k}, L{L}')
 for xi,yi in zip(x+(i-1.5)*width,ys):ax.text(xi,yi+(0.7 if yi>=0 else -.7),f'{yi:+.1f}%',ha='center',va='bottom' if yi>=0 else 'top',fontsize=8)
ax.axhline(0,color='#475569',linewidth=.8);ax.set_xticks(x,[labels[m] for m in methods]);ax.set_ylabel('QPS change vs the same method with E99 kernel (%)');ax.set_title('Shared implementation speedup, with identical results and NDC',fontweight='bold');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.margins(y=.28);ax.legend(ncol=4,frameon=False,loc='upper left')
fig.text(.5,.015,'All methods measured in the same serial, single-thread run. Bars use 3-run means; full ranges are in results/metrics.csv.',ha='center',fontsize=8.5);fig.tight_layout(rect=(0,.05,1,1))
for ext in ['png','pdf']:fig.savefig(D/f'figures/shared_speedup.{ext}',dpi=180)
plt.close(fig)
