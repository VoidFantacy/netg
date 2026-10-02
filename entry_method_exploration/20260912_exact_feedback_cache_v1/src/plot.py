from shared import *
threads(8)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
cost=read(O/'results_v2/cost.json');fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
for i,(ds,name) in enumerate(zip(DS,['WebVid','Yandex'])):
 r=read(O/'results_v2'/ds/'query_complete.json');ax=axes[i]
 ax.bar([0,1,2],[327680,r['normal_new_NSG'],40960+r['normal_new_NSG']],color=['#64748b','#059669','#d97706'])
 ax.set(xticks=[0,1,2],xticklabels=['Full candidate\nNSG reference','New candidate\nNSG calls','If all 10 C seeds\nwere recomputed'],yscale='log',ylabel='NSG calls (log scale)',title=f'{name}: exact feedback reuse')
 for x,v in enumerate([327680,r['normal_new_NSG'],40960+r['normal_new_NSG']]):ax.text(x,v*1.12,f'{v:,}',ha='center',fontsize=10)
 ax.set_ylim(100,800000);ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
fig.suptitle('All HNSW routes are still executed; seed feedback and parity charged separately\nCall reduction is not an online QPS claim',fontsize=12)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'exact_feedback_cache.{ext}',dpi=160)
plt.close(fig);print('E46 plots written')
