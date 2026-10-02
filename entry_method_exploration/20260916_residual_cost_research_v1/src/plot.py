import pathlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=pathlib.Path(__file__).resolve().parent.parent;s=json.loads((D/'results/summary.json').read_text());methods=['GT10-soft-t1','HNSW'];cols=['#2563eb','#9333ea'];labels=['GT10-soft + optimized NSG','Full HNSW']
a=[next(x for x in s['formal_e99'] if x['method']==m and x['K']==100 and x['L']==1250) for m in methods]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,3,figsize=(13.5,4.6))
for ax,key,title,unit in zip(axs,['total_ndc','amortized_ns_per_ndc','mean_ms'],['Fewer distance evaluations','Higher amortized cost','Slightly longer total latency'],['Distance calls / query','Total wall / distance count (ns)','Mean query wall (ms)']):
 vals=[r[key] for r in a];bars=ax.bar(range(2),vals,color=cols,width=.6)
 for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v,f'{v:,.0f}' if key=='total_ndc' else f'{v:.2f}',ha='center',va='bottom',fontweight='bold')
 ax.set_xticks([0,1],['GT10-soft','HNSW']);ax.set_ylabel(unit);ax.set_title(title,fontweight='bold');ax.set_ylim(0,max(vals)*1.18);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.suptitle('Why fewer distance calls do not guarantee lower latency',fontsize=15,y=.98)
fig.text(.5,.03,'E99 formal measurements: WebVid, K=100, L/ef=1250, 10K queries, 1 thread. Amortized cost includes all search work.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.07,1,.92));(D/'figures').mkdir(exist_ok=True)
for ext in ['png','pdf']:fig.savefig(D/f'figures/count_vs_time.{ext}',dpi=180)
plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5));cats=['distance_kernel_including_memory_stalls','candidate_queue','libc_memcpy_memmove','graph_loop_visited_bounds_and_other','hnsw_other','other_libc','other'];catlabels=['Distance code + memory stalls','Candidate management','libc copy','Graph / visited / bounds','HNSW other','Other libc','Other'];pal=['#2563eb','#f59e0b','#fb7185','#64748b','#a78bfa','#a3a3a3','#d1d5db'];left=[0.,0.]
for cat,label,col in zip(cats,catlabels,pal):
 vals=[s['profile_categories'][m]['percent'].get(cat,0) for m in methods]
 if max(vals)==0:continue
 ax.barh(range(2),vals,left=left,color=col,label=label)
 for i,v in enumerate(vals):
  if v>=4:ax.text(left[i]+v/2,i,f'{v:.1f}%',ha='center',va='center',fontsize=10,color='white' if cat in [cats[0],cats[3]] else 'black')
 left=[x+y for x,y in zip(left,vals)]
ax.set_yticks(range(2),labels);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('SIGPROF instruction samples (%)');ax.set_title('E100: hotspots after the E99 optimization',fontweight='bold');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.15),ncol=3,frameon=False)
fig.text(.5,.015,'Separate diagnostic runs; sampled CPU locations include memory stalls. These are not hardware cache-miss measurements.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.13,1,1))
for ext in ['png','pdf']:fig.savefig(D/f'figures/optimized_hotspots.{ext}',dpi=180)
plt.close(fig)
