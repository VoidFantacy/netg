import pathlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
D=pathlib.Path(__file__).resolve().parent.parent;s=json.loads((D/'results/summary.json').read_text());rows=s['metrics'];pairs=s['paired_speedups']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
colors={'Faiss-native':'#64748b','NSG-current':'#94a3b8','GT10-current':'#2563eb','GT10-span':'#16a34a','GT10-batch4':'#ea580c','GT10-span-batch4':'#dc2626','HNSW':'#9333ea'}
labels={'Faiss-native':'Faiss 1.9.0 native (same graph)','NSG-current':'Project NSG, fixed entry','GT10-current':'GT10 + current E99 kernel','GT10-span':'GT10 + span','GT10-batch4':'GT10 + batch4','GT10-span-batch4':'GT10 + span + batch4','HNSW':'Full HNSW'}
fig,axs=plt.subplots(1,2,figsize=(13,5.6))
for ax,k in zip(axs,[1,100]):
 for v,color in colors.items():
  a=sorted([x for x in rows if x['variant']==v and x['K']==k],key=lambda x:x['recall']);x=[r['recall']*100 for r in a];y=[r['qps_mean'] for r in a]
  ax.errorbar(x,y,yerr=[[r['qps_mean']-r['qps_min'] for r in a],[r['qps_max']-r['qps_mean'] for r in a]],label=labels[v],color=color,marker='o',linestyle='--',capsize=3,alpha=.9)
 ax.set_xlabel(f'Recall@{k} (%)');ax.set_ylabel('End-to-end QPS (1 thread)');ax.set_yscale('log');ax.set_title(f'WebVid Recall@{k}',fontweight='bold');ax.grid(alpha=.15)
handles,lab=axs[0].get_legend_handles_labels();fig.legend(handles,lab,loc='lower center',bbox_to_anchor=(.5,.055),ncol=3,frameon=False)
fig.suptitle('Native library and targeted search controls on the same frozen graph',fontsize=14)
fig.text(.5,.01,'Four preselected points only; dashed segments are not a measured continuous frontier. Bars show 3-run range.\nGT10 controls are implementation comparisons; the other NSG entry methods have not been rebenchmarked with these changes.',ha='center',fontsize=8.5)
fig.tight_layout(rect=(0,.25,1,.94))
for ext in ['png','pdf']:fig.savefig(D/f'figures/recall_qps.{ext}',dpi=180)
plt.close(fig)
variants=['GT10-minimal','GT10-core','GT10-span','GT10-prefetch-filter','GT10-batch4','GT10-span-batch4'];short=['Minimal\nadapter','Core\ncontrol','Skip tail\npadding','Filter visited\nprefetch','Batch4','Span +\nbatch4'];points=[(1,96),(100,100),(1,800),(100,1250)];pal=['#93c5fd','#3b82f6','#fb923c','#dc2626']
fig,ax=plt.subplots(figsize=(13,5.5));x=np.arange(len(variants));width=.19
for i,((k,L),col) in enumerate(zip(points,pal)):
 a=[next(p for p in pairs if p['variant']==v and p['baseline']=='GT10-current' and p['K']==k and p['L']==L) for v in variants];y=[p['speedup_percent'] for p in a]
 ax.bar(x+(i-1.5)*width,y,width,color=col,label=f'K{k}, L{L}')
 for xi,yi in zip(x+(i-1.5)*width,y):ax.text(xi,yi+(1 if yi>=0 else -1),f'{yi:+.1f}',ha='center',va='bottom' if yi>=0 else 'top',fontsize=8)
ax.axhline(0,color='#475569',linewidth=.8);ax.set_xticks(x,short);ax.set_ylabel('QPS change vs current GT10 (%)');ax.set_title('Which implementation changes help with identical results?',fontweight='bold');ax.legend(ncol=4,frameon=False,loc='upper left');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.margins(y=.22)
fig.text(.5,.015,'All GT10 controls must preserve IDs, float bits, entries and per-query NDC. Three repeats; full ranges are in paired_speedup.csv.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.05,1,1))
for ext in ['png','pdf']:fig.savefig(D/f'figures/optimization_controls.{ext}',dpi=180)
plt.close(fig)
