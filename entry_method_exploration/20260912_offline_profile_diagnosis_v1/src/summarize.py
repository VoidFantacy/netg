from common import *
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

assert not (O/'results/group_summary.csv').exists()
s=pd.read_csv(O/'results/steps.csv');q=pd.read_csv(O/'results/query_exposure.csv');c=pd.read_csv(O/'results/centers.csv');mq=pd.read_csv(O/'results/matched_queries.csv');mg=pd.read_csv(O/'results/matched_groups.csv');r=pd.read_csv(O/'results/runs.csv')
groups=[];matched_stats=[];endpointstats=[];windows=[]
for (ds,arm),v in s.groupby(['dataset','arm'],sort=False):
 rr=r[(r.dataset==ds)&(r.arm==arm)];qq=q[(q.dataset==ds)&(q.arm==arm)]
 groups.append(dict(dataset=ds,arm=arm,steps=len(v),median_discriminating_queries=float(v.discriminating_queries.median()),entry_change_pct=float(v.entry_changed_observations.sum()/(len(v)*1024)*100),hit_change_pct=float(v.hit_changed_observations.sum()/(len(v)*1024)*100),discriminating_query_pct=float(v.discriminating_queries.sum()/(len(v)*128)*100),
  split_query_cosine_median=float(v.split_query_cosine.median()),negative_split_cosine_pct=float((v.split_query_cosine<0).mean()*100),conditional_query_snr_median=float(v.conditional_query_snr_estimate.median()),largest_query_gradient_share_median=float(v.largest_query_hit_gradient_share.median()),
  top1pct_query_gradient_share_min=float(rr.top1pct_query_gradient_share.min()),top1pct_query_gradient_share_max=float(rr.top1pct_query_gradient_share.max()),
  no_discrimination_steps=int((v.discriminating_queries==0).sum()),at_most_one_discriminating_pct=float((v.discriminating_queries<=1).mean()*100),
  hit_gradient_norm_median=float(v.hit_gradient_norm.median()),cost_gradient_norm_median=float(v.cost_gradient_norm.median()),failure_gradient_norm_median=float(v.failure_gradient_norm.median()),drift_gradient_norm_median=float(v.drift_gradient_norm.median()),
  cos_total_hits_median=float(v.cos_total_hits.median()),auxiliary_dominates_hits_pct=float(v.auxiliary_dominates_hits.mean()*100),drop_big_query_cosine_median=float(v.cos_after_drop_largest_query.median()),clipped_steps=int(v.gradient_clipped.sum()),mu_at_bound=int(v.mu_at_bound_count.sum()),max_mu_abs=float(v.mu_max_abs.max())))
for (ds,arm,seed),v in mg.groupby(['dataset','arm','seed'],sort=False):
 rows=mq[(mq.dataset==ds)&(mq.arm==arm)&(mq.seed==seed)];rng=np.random.default_rng(20260912);i=rng.integers(0,len(v),size=(5000,len(v)));boot=v.gap_sum_pp.to_numpy()[i].sum(1)/v.queries.to_numpy()[i].sum(1);lo,hi=np.percentile(boot,[2.5,97.5]);top=int(np.argmax(np.abs(rows.delta_recall_pp.to_numpy())))
 matched_stats.append(dict(dataset=ds,arm=arm,seed=int(seed),groups=len(v),query_records=len(rows),unique_queries=int(rows.query_row.nunique()),changed_records=int((rows.delta_recall_pp!=0).sum()),gap_pp=float(rows.delta_recall_pp.mean()),block_bootstrap_low_pp=float(lo),block_bootstrap_high_pp=float(hi),without_largest_abs_record_gap_pp=float(rows.drop(rows.index[top]).delta_recall_pp.mean()),reward_gap=float(rows.reward_gap.mean()),interpretation='descriptive dependent checkpoint-block bootstrap; not a population causal effect'))
for (ds,arm,seed),v in c.groupby(['dataset','arm','seed'],sort=False):
 for tag in ['selected','last']:
  x=v[v[tag]]
  for row in x.to_dict('records'):endpointstats.append(dict(endpoint=tag,**row))
for key,v in s.groupby(['dataset','arm','seed','block'],sort=False):windows.append(dict(dataset=key[0],arm=key[1],seed=int(key[2]),block=int(key[3]),sample_delta_recall_pp=float(v.mean_hit_delta.mean()*10),sample_reward=float(v.mean_reward.mean()),query_sampling_noise_is_not_a_fixed_center_curve=True))
for name,rows in [('group_summary',groups),('matched_summary',matched_stats),('endpoint_summary',endpointstats),('window_summary',windows)]:pd.DataFrame(rows).to_csv(O/'results'/f'{name}.csv',index=False)
dump(O/'results/summary.json',dict(groups=groups,matched=matched_stats,endpoints=endpointstats,windows=windows))

plt.rcParams.update({'font.size':10,'figure.dpi':120,'savefig.dpi':180});colors={'rl':'#bc4939','es':'#256e9e'}
def save(fig,name):
 fig.tight_layout()
 for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'{name}.{ext}',bbox_inches='tight')
 plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(12,7))
for col,ds in enumerate(DS):
 v=s[s.dataset==ds]
 for arm in ARMS:
  vv=v[v.arm==arm];x=np.sort(vv.discriminating_queries);axes[0,col].step(x,np.arange(1,len(x)+1)/len(x),where='post',label=arm.upper(),color=colors[arm])
  for seed,style in zip(SEEDS,['-','--']):
   x=q[(q.dataset==ds)&(q.arm==arm)&(q.seed==seed)].sort_values('gradient_norm_sum',ascending=False);y=x.gradient_norm_sum.cumsum()/x.gradient_norm_sum.sum();axes[1,col].plot(np.arange(1,4097)/4096*100,y,label=f'{arm.upper()} seed{seed%100}',color=colors[arm],linestyle=style)
 axes[0,col].set_title('WebVid' if col==0 else 'Yandex-IP');axes[0,col].set(xlabel='Queries with different hits across 8 actions (of 128)',ylabel='Fraction of optimizer steps')
 axes[1,col].set(xlabel='Queries ranked by sampled gradient contribution (%)',ylabel='Cumulative sum of per-query gradient norms',xlim=(0,20),ylim=(0,1.02));axes[1,col].axvline(1,color='grey',linewidth=.7)
 for row in range(2):axes[row,col].legend(fontsize=8);axes[row,col].grid(alpha=.2)
save(fig,'feedback_sparsity')
fig,axes=plt.subplots(1,2,figsize=(12,4.6))
labels=[];data=[]
for ds in DS:
 for arm in ARMS:
  v=s[(s.dataset==ds)&(s.arm==arm)];labels.append(('WebVid' if ds==DS[0] else 'Yandex')+' '+arm.upper());data.append(v.split_query_cosine.dropna())
axes[0].boxplot(data,tick_labels=labels,showfliers=False);axes[0].axhline(0,color='grey',linewidth=.8);axes[0].set(ylabel='Cosine of gradients from two query halves',title='Same perturbation directions; 64 vs 64 queries');axes[0].tick_params(axis='x',rotation=20)
x=np.arange(4);width=.18
for i,name in enumerate(['hit','cost','failure','drift']):axes[1].bar(x+(i-1.5)*width,[g[name+'_gradient_norm_median'] for g in groups],width,label=name)
axes[1].set(xticks=x,xticklabels=labels,yscale='log',ylabel='Median gradient norm',title='Reward components before clipping and Adam');axes[1].tick_params(axis='x',rotation=20);axes[1].legend();axes[1].grid(axis='y',alpha=.2);save(fig,'gradient_diagnosis')
fig,axes=plt.subplots(1,2,figsize=(12,4.6))
for col,ds in enumerate(DS):
 vv=[x for x in matched_stats if x['dataset']==ds]
 for i,x in enumerate(vv):
  axes[col].errorbar(i,x['gap_pp'],yerr=[[x['gap_pp']-x['block_bootstrap_low_pp']],[x['block_bootstrap_high_pp']-x['gap_pp']]],fmt='o',color=colors[x['arm']],capsize=4)
 axes[col].axhline(0,color='grey',linewidth=.8);axes[col].set(xticks=range(len(vv)),xticklabels=[x['arm'].upper()+f" seed{x['seed']%100}" for x in vv],ylabel='Sample mean - deterministic center recall (pp)',title=('WebVid' if col==0 else 'Yandex-IP')+'; same means and query rows');axes[col].tick_params(axis='x',rotation=20);axes[col].grid(alpha=.2)
fig.suptitle('Limited matched records; descriptive checkpoint-block intervals',fontsize=11);save(fig,'sample_center_gap')
print('SUMMARY_AND_FIGURES_COMPLETE',flush=True)
