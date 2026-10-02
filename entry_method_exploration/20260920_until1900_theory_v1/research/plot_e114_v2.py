from pathlib import Path
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.sched_setaffinity(0,{15})
import json,csv,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
TB=Path(__file__).resolve().parents[1];R=TB/'stages/e114_terminal_peaks'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
v=read(R/'reviews/numeric_verification.json');assert v['status']=='PASS'
summary=read(R/'results/summary.json');methods=list(csv.DictReader((R/'results/methods.csv').open()));pairs=list(csv.DictReader((R/'results/pairs.csv').open()))
cost=[]
for s in summary:
    rr=list(csv.DictReader((R/'results'/s['dataset']/'query_peaks.csv').open()))
    independent_peaks=sum(int(x['query']) in range(0,4096,256) for x in rr)
    cost.append(dict(dataset=s['dataset'],original_field_reference_inner_products=s['reference_inner_products'],
        original_semantics='Logical neighbor, peak and GT references per unique query/peak; GT term counted per peak',
        actual_primary_dot_products=s['out_edges_checked']+s['unique_query_peaks']+s['n'],
        cached_GT_duplicate_count=s['unique_query_peaks']-s['n'],
        independent_fsum_dot_products=s['independent_edges']+independent_peaks,
        interpretation='Main loop actually computes GT score once per query, not once per peak; no rerun or numerical result change'))

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(11.8,4.8));labels=['WebVid','Yandex'];y=np.arange(2)
same=np.array([s['all_eight_same_terminal_ID_pct'] for s in summary]);ax=axes[0]
ax.barh(y,same,color='#477caa',label='Same terminal ID');ax.barh(y,100-same,left=same,color='#d6dce3',label='Different terminal IDs')
for i,z in enumerate(same):ax.text(z/2,i,f'{z:.1f}%',ha='center',va='center',color='white',weight='bold')
ax.set_title('All queries: eight preset entry policies',loc='left',fontsize=11);ax.set_yticks(y,labels);ax.invert_yaxis();ax.legend(loc='upper left',bbox_to_anchor=(0,-.30),frameon=False,fontsize=9)
ax=axes[1];arr=[]
for s in summary:
    failed=s['default_failures'];rescued=s['any_preset_method_hits']-(s['n']-failed)
    arr.append([s['default_failed_all_eight_same_terminal_ID'],failed-s['default_failed_all_eight_same_terminal_ID']-rescued,rescued])
arr=np.asarray(arr);percent=arr/np.array([s['default_failures'] for s in summary])[:,None]*100
left=np.zeros(2)
for j,(name,color) in enumerate([('Same incorrect peak','#6f7d8d'),('Different peaks; all miss','#c5a070'),('Some preset policy hits','#4b9578')]):
    ax.barh(y,percent[:,j],left=left,label=name,color=color)
    for i in range(2):ax.text(left[i]+percent[i,j]/2,i,f'{percent[i,j]:.1f}%',ha='center',va='center',fontsize=9,color='white' if j!=1 else '#202020')
    left+=percent[:,j]
ax.set_title('Default failures: where the eight policies end',loc='left',fontsize=11);ax.set_yticks(y,[f'WebVid (n={summary[0]["default_failures"]})',f'Yandex (n={summary[1]["default_failures"]})']);ax.invert_yaxis();ax.legend(loc='upper left',bbox_to_anchor=(0,-.30),frameon=False,fontsize=9)
for ax in axes:
    ax.set_xlim(0,100);ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('Queries (%)');ax.spines[['top','right']].set_visible(False)
fig.suptitle('Existing true K1 / L128 results · 4096 queries per dataset',x=.08,ha='left',fontsize=13)
fig.subplots_adjust(left=.075,right=.985,top=.81,bottom=.40,wspace=.6)
fig.savefig(R/'figures/terminal_peaks.v2.png',dpi=180,bbox_inches='tight');fig.savefig(R/'figures/terminal_peaks.v2.pdf',bbox_inches='tight');plt.close(fig)
