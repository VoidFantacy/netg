"""Plot only completed E99 measurements; no interpolation between budgets."""
import csv,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
D=pathlib.Path(__file__).resolve().parent.parent
assert json.loads((D/'reviews/results_audit.json').read_text())['status']=='PASS'
with (D/'results/metrics.csv').open() as f: rows=[x for x in csv.DictReader(f) if x['qps_mean']]
with (D/'results/paired_speedup.csv').open() as f: pairs=list(csv.DictReader(f))
methods=['NSG','GT10-hard','GT10-soft-t1','GATE','HNSW']
colors=dict(zip(methods,['#64748b','#dc2626','#2563eb','#059669','#9333ea']))
method_markers=dict(zip(methods,['s','^','o','v','D']))
method_sizes=dict(zip(methods,[7,9,6,8,7]))
points=[(1,96),(100,100),(1,800),(100,1250)]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,2,figsize=(13,9))
for ax,(k,L) in zip(axs.flat,points):
    view=[x for x in rows if int(x['K'])==k and int(x['L'])==L]
    for m in methods:
        by={x['kernel']:x for x in view if x['method']==m}
        for kernel,x in by.items():
            q=float(x['qps_mean']);rec=100*float(x['recall']);marker=method_markers[m]
            ax.errorbar(rec,q,yerr=[[q-float(x['qps_min'])],[float(x['qps_max'])-q]],fmt=marker,
                        markersize=method_sizes[m],mfc='white' if kernel=='legacy' else colors[m],mec=colors[m],ecolor=colors[m],capsize=3,zorder=3)
        if 'legacy' in by:
            a,b=by['legacy'],by['optimized']
            ax.plot([100*float(a['recall'])]*2,[float(a['qps_mean']),float(b['qps_mean'])],c=colors[m],lw=1.5,alpha=.55)
    ax.set_title(f'Recall@{k} | L/ef = {L}',fontweight='bold')
    ax.set_xlabel(f'Recall@{k} (%)');ax.set_ylabel('End-to-end QPS');ax.grid(alpha=.2);ax.margins(x=.12,y=.15)
fig.suptitle('WebVid: shared NSG optimization at four fixed budgets',fontsize=16,y=.985)
legend=[Line2D([0],[0],color=colors[m],marker=method_markers[m],ls='',label=m.replace('-t1','')) for m in methods]
legend += [Line2D([0],[0],color='black',marker='o',mfc='white',ls='',label='Legacy'),Line2D([0],[0],color='black',marker='o',ls='',label='Optimized')]
fig.legend(handles=legend,loc='lower center',ncol=7,bbox_to_anchor=(.5,.035),frameon=False)
fig.text(.5,.012,'10,000 queries; CPU 15; one thread; 3 repetitions. Bars = observed min/max, not confidence intervals. Outputs and NDC unchanged.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.08,1,.96));(D/'figures').mkdir(exist_ok=True)
for ext in ['png','pdf']:fig.savefig(D/f'figures/webvid_recall_qps.{ext}',dpi=180)
plt.close(fig)
fig,ax=plt.subplots(figsize=(11,5.8));markers=['o','s','^','D']
for j,m in enumerate(methods[:-1]):
    xs=[];ys=[];lo=[];hi=[]
    for i,(k,L) in enumerate(points):
        p=next(x for x in pairs if x['method']==m and int(x['K'])==k and int(x['L'])==L)
        y=float(p['speedup_percent']);xs.append(i+(j-1.5)*.16);ys.append(y)
        lo.append(max(0,y-float(p['paired_min_percent'])));hi.append(max(0,float(p['paired_max_percent'])-y))
    ax.errorbar(xs,ys,yerr=[lo,hi],fmt=markers[j],color=colors[m],capsize=4,markersize=7,label=m.replace('-t1',''))
ax.axhline(0,c='#334155',ls='--',lw=1);ax.set_xticks(range(4),[f'R@{k}\nL={L}' for k,L in points])
ax.set_ylabel('QPS gain over legacy kernel (%)');ax.set_title('WebVid: speedup at identical outputs and distance counts',fontweight='bold')
ax.legend(ncol=4,loc='upper center',bbox_to_anchor=(.5,1.0),frameon=False);ax.grid(axis='y',alpha=.2)
low,high=ax.get_ylim();ax.set_ylim(min(-1,low),high+(high-low)*.2)
fig.text(.5,.02,'Dots = ratio of mean QPS. Bars = range of 3 matched-repetition ratios (descriptive only). Complete routing + search wall.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.045,1,1))
for ext in ['png','pdf']:fig.savefig(D/f'figures/webvid_speedup.{ext}',dpi=180)
plt.close(fig)
print('PLOTS_WRITTEN')
