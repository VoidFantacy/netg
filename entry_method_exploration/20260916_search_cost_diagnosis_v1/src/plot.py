import pathlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
D=pathlib.Path(__file__).resolve().parent.parent
s=json.loads((D/'results/summary.json').read_text());rows=s['timing'];fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
colors={'GT10-soft-t1':'#2563eb','HNSW':'#ea580c'}
for name in colors:
 r=sorted([r for r in rows if r['variant']=='original' and r['method']==name and r['K']==100],key=lambda r:r['L']);axes[0,0].plot([r['L'] for r in r],[r['mean_qps'] for r in r],'-o',label=name,color=colors[name])
axes[0,0].set(xlabel='Search budget L / ef (Recall@100)',ylabel='Queries / second',title='A. Baseline cost increases with budget');axes[0,0].legend();axes[0,0].grid(alpha=.2)
labels=['GT10-soft-t1','HNSW'];stage=[json.loads((D/f'results/original/{n}.stages.json').read_text()) for n in labels];bottom=np.zeros(2)
for key,label,color in [('route_seconds','Route','#14b8a6'),('setup_seconds','Setup','#94a3b8'),('graph_seconds','Graph search','#6366f1'),('output_seconds','Output','#f59e0b')]:
 vals=np.array([r[key]*1e6/10000 for r in stage]);axes[0,1].bar(labels,vals,bottom=bottom,label=label,color=color);bottom+=vals
axes[0,1].set(ylabel='Microseconds / query',title='B. Staged timers (separate from plain QPS)');axes[0,1].legend(fontsize=8);axes[0,1].text(.98,.96,'GT10 route: 21.6 us (0.47%)',transform=axes[0,1].transAxes,ha='right',va='top',fontsize=9)
cat=s['profile_categories'];keys=['distance_kernel_including_memory_stalls','candidate_queue','libc_memcpy_memmove','graph_loop_visited_bounds_and_other','hnsw_other','other_libc','other'];clabels=['Distance + memory stalls','Candidate queues','Copy / move','Graph loop / visited / bounds','Other HNSW','Other libc','Other'];bottom=np.zeros(2)
for key,label in zip(keys,clabels):
 vals=np.array([sum(x['percent'] for x in cat[n] if x['category']==key) for n in labels]);axes[1,0].barh(labels,vals,left=bottom,label=label);bottom+=vals
axes[1,0].set(xlabel='Instruction-pointer samples (%)',title='C. CPU sampling; not hardware cache counters',xlim=(0,100));axes[1,0].legend(loc='upper center',bbox_to_anchor=(.5,-.18),ncol=2,fontsize=7)
sel=[]
for v in ['original_only','prefetch','active_pool','combined']:
 r=next((r for r in rows if r['variant']==v and r['method']=='GT10-soft-t1' and r['K']==100 and r['L']==1250),None)
 if r:sel.append(r)
if sel:
 means=np.array([r['mean_qps'] for r in sel]);err=np.array([[r['mean_qps']-r['qps_min'] for r in sel],[r['qps_max']-r['mean_qps'] for r in sel]])
 axes[1,1].bar(range(len(sel)),means,yerr=err,capsize=4,color=['#2563eb','#14b8a6','#8b5cf6','#059669'][:len(sel)])
 axes[1,1].set_xticks(range(len(sel)),['Matched base','Prefetch','Active pool','Combined'][:len(sel)],rotation=12)
 for i,v in enumerate(means):axes[1,1].text(i,v+3,f'{v:.1f}',ha='center',fontsize=9)
h=next(r for r in rows if r['variant']=='original' and r['method']=='HNSW' and r['K']==100 and r['L']==1250);axes[1,1].axhline(h['mean_qps'],color='#ea580c',linestyle='--',label=f'HNSW reference {h["mean_qps"]:.1f}');axes[1,1].legend(fontsize=8);axes[1,1].set(ylabel='Queries / second',title='D. Local controls, K=100 / L=1250',ylim=(0,290))
fig.suptitle('WebVid implementation diagnosis: fixed outputs, CPU 15, one thread',fontsize=14)
(D/'figures').mkdir(exist_ok=True)
for ext in ['png','pdf']:fig.savefig(D/f'figures/cost_diagnosis.{ext}',dpi=180)
