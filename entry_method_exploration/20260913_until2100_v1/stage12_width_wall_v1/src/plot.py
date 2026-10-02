from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
points=list(csv.DictReader((O/'results/points.csv').open()));paired=list(csv.DictReader((O/'results/paired.csv').open()));interp=list(csv.DictReader((O/'results/frontier_interpolation.csv').open()));cost=read(O/'results/cost.json')
selection=read(O/'results/frozen_selection.json')['datasets'];(O/'figures').mkdir(exist_ok=True)
colors={'nsg':'#697386','fast30k':'#1673b8','gt10_hard':'#e39125','baseline_soft':'#30946e','best_new':'#ac3c85','p30':'#627fbe','mode10':'#8752b3'}
base_labels={'nsg':'NSG','fast30k':'Fast30K (GT1)','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft (matched)','p30':'GT10 matched ef30','mode10':'Multi-profile ef10','best_new':'Multi-profile ef30'}
def pp(ds,name):return sorted([p for p in points if p['dataset']==ds and p['model']==name],key=lambda x:int(x['L']))
def names(ds):return ['nsg','fast30k','gt10_hard']+(['baseline_soft'] if ds==DS[0] else [])+['p30','mode10','best_new']
def label(ds,name):return base_labels.get(name,'New: '+selection[ds]['best_new'])
def export(fig,name):
    for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'{name}.{ext}',dpi=180)
    plt.close(fig)
foot='Historical development 2,048 queries already used for selection • CPU15 / 1 thread • Five full batch walls • Not final validation'
for key,xlabel,file in [('recall_pct','Recall@10 (%)','recall_qps'),('failure_rate_pct','GT10 zero-hit failure rate (%)','failure_qps')]:
    fig,axes=plt.subplots(1,2,figsize=(13,5.5))
    for ax,ds,title in zip(axes,DS,['WebVid','Yandex']):
        for name in names(ds):
            ps=pp(ds,name);x=[float(p[key]) for p in ps];q=np.array([float(p['QPS']) for p in ps]);low=np.array([float(p['QPS_min']) for p in ps]);high=np.array([float(p['QPS_max']) for p in ps])
            ax.plot(x,q,'o-',label=label(ds,name),color=colors[name],markersize=4,lw=1.4);ax.fill_between(x,low,high,color=colors[name],alpha=.13)
        ax.set(title=title,xlabel=xlabel,ylabel='QPS (median; shade = five-run range)');ax.set_yscale('log');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('E71 — '+('Recall–QPS' if key=='recall_pct' else 'Failure rate–QPS'),fontsize=15);fig.text(.5,.014,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.05,1,.94));export(fig,file)
fig,axes=plt.subplots(2,3,figsize=(14,8))
for row,(ds,title) in enumerate(zip(DS,['WebVid','Yandex'])):
    for name in names(ds):
        ps=pp(ds,name);x=np.arange(5)
        for col,(key,ylabel) in enumerate([('recall_pct','Recall@10 (%)'),('QPS','QPS (median)'),('failure_rate_pct','Zero-hit failures (%)')]):
            ax=axes[row,col];ax.plot(x,[float(p[key]) for p in ps],'o-',color=colors[name],label=label(ds,name),markersize=4,lw=1.3);ax.set_xticks(x,[64,128,256,400,800]);ax.set(xlabel='Search L',ylabel=ylabel,title=title+' — '+ylabel);ax.grid(alpha=.2)
            if col==1:ax.set_yscale('log')
    axes[row,0].legend(fontsize=8)
fig.suptitle('E71 — all three measured metrics by L',fontsize=15);fig.text(.5,.01,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,.94));export(fig,'three_metrics_by_L')
fig,axes=plt.subplots(2,2,figsize=(12,7))
for row,(ds,title) in enumerate(zip(DS,['WebVid','Yandex'])):
    comparator='baseline_soft' if ds==DS[0] else 'gt10_hard'
    vals=sorted([p for p in paired if p['dataset']==ds and p['comparator']==comparator],key=lambda p:int(p['L']));x=np.arange(5)
    recall=np.array([float(p['delta_recall_pp']) for p in vals]);qps=np.array([float(p['QPS_change_pct']) for p in vals])
    axes[row,0].plot(x,recall,'o-',color='#ac3c85');axes[row,0].fill_between(x,[float(p['descriptive_query_bootstrap_low_pp']) for p in vals],[float(p['descriptive_query_bootstrap_high_pp']) for p in vals],color='#ac3c85',alpha=.12)
    axes[row,1].plot(x,qps,'o-',color='#ac3c85');axes[row,1].fill_between(x,[float(p['all_range_low_pct']) for p in vals],[float(p['all_range_high_pct']) for p in vals],color='#ac3c85',alpha=.12)
    for col,yl in enumerate(['Recall change (pp)','QPS change (%)']):
        ax=axes[row,col];ax.axhline(0,color='gray',lw=.8);ax.set_xticks(x,[64,128,256,400,800]);ax.set(title=title+' new vs matched GT10',xlabel='Search L',ylabel=yl);ax.grid(alpha=.2)
fig.suptitle('E71 — paired changes; bands: query bootstrap / timing ranges',fontsize=15);fig.text(.5,.01,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,.94));export(fig,'paired_deltas')
