from shared import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads(8);assert read(O/'reviews/training_verification.json')['status']=='PASS'
analysis=read(O/'results/training_analysis.json');models=analysis['models']
with (O/'results/steps.csv').open() as f:steps=list(csv.DictReader(f))
rows=[];feedback=[]
for model in models:
 ds,arm,seed=model['dataset'],model['arm'],model['seed'];dest=O/'models'/ds/f'{arm}_{seed}'
 for tag in ['selected','last']:
  for split in ['train','monitor']:
   met=model[tag+'_'+split];rows.append(dict(dataset=ds,arm=arm,seed=seed,checkpoint=tag,split=split,**met))
 st=[x for x in steps if x['dataset']==ds and x['arm']==arm and int(x['seed'])==seed]
 assert len(st)==200
 feedback.append(dict(dataset=ds,arm=arm,seed=seed,active_hubs=model['active_hubs'],median_active_updates=model['median_active_updates'],
  max_active_updates=model['max_active_updates'],steps_with_hit_feedback=model['steps_with_hit_feedback'],
  candidates_with_hit_feedback=model['candidates_with_hit_feedback'],steps_with_hit_gradient=model['steps_with_hit_gradient'],
  positive_net_candidates=sum(int(x['positive_net_candidates']) for x in st),negative_net_candidates=sum(int(x['negative_net_candidates']) for x in st),
  mean_candidate_distance=float(np.mean([float(x['candidate_mean_distance']) for x in st])),
  mean_update_distance=float(np.mean([float(x['current_next_row_distance']) for x in st]))))
for name,data in [('quality.csv',rows),('feedback.csv',feedback)]:
 with (O/'results'/name).open('x') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
gates=[]
for ds in DS:
 eligible={arm:[m['seed'] for m in models if m['dataset']==ds and m['arm']==arm and m['selected_monitor']['delta_recall_pp']>0 and m['selected_monitor']['mean_U']>0 and m['selected_monitor']['graph_NDC_change_pct']<=1] for arm in ARMS}
 gates.append(dict(dataset=ds,eligible_seeds=eligible,pass_monitor_gate=all(eligible.values())))
gate=dict(status='GO_FREEZE_DEVELOPMENT_PROTOCOL' if all(x['pass_monitor_gate'] for x in gates) else 'STOP_THIS_PARAMETERIZATION_BUDGET_EXPANSION',datasets=gates,
 formal_performance_GO=False,new_development_queries=0,reason='Prelocked monitor gate only; no cal/audit decision made')
dump(O/'results/method_gate.json',gate)
jobs=read(O/'logs/jobs.json');assert len(jobs)==10 and all(j['status']=='COMPLETE' for j in jobs)
cost=dict(NSG=sum(j['actual'] for j in jobs),reserved_NSG=sum(j['reserved'] for j in jobs),
 HNSW=sum(j['native']['HNSW_calls'] for j in jobs),builds=sum(j['native']['builds'] for j in jobs),optimizer_updates=1600,
 data=[dict(dataset=ds,**read(O/'results'/ds/'training_complete.json')) for ds in DS])
assert cost['NSG']==1992256 and cost['builds']==14510
dump(O/'results/cost.json',cost)
fig,axes=plt.subplots(2,2,figsize=(12,7),layout='constrained')
colors={'rl':'#2166ac','es':'#b2182b'}
for di,ds in enumerate(DS):
 for si,split in enumerate(['train','monitor']):
  ax=axes[di,si]
  for arm in ARMS:
   for seed in SEEDS:
    cp=read(O/'models'/ds/f'{arm}_{seed}'/'checkpoints.json')
    ax.plot([x['step'] for x in cp],[x[split]['delta_recall_pp'] for x in cp],color=colors[arm],ls='-' if seed==SEEDS[0] else '--',label=arm.upper()+' seed'+str(seed)[-2:])
  ax.axhline(0,color='gray',lw=.6);ax.set(xlabel='Updates (one hub per update)',ylabel='Recall change from anchor (pp)',title=('WebVid' if di==0 else 'Yandex')+' / '+split)
axes[0,0].legend(fontsize=8);fig.suptitle('E43: deterministic local-profile means; fixed training budget')
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('learning_curves.'+ext),dpi=170)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(12,4.3),layout='constrained')
labels=[('W' if x['dataset']==DS[0] else 'Y')+' '+x['arm'].upper()+str(x['seed'])[-2:] for x in feedback]
axes[0].bar(range(8),[x['steps_with_hit_feedback']/2 for x in feedback],color=[colors[x['arm']] for x in feedback]);axes[0].set(xticks=range(8),xticklabels=labels,ylabel='Steps with any hit change (%)',title='Sampled reward exposure')
axes[1].bar(range(8),[x['active_hubs'] for x in feedback],color=[colors[x['arm']] for x in feedback]);axes[1].set(xticks=range(8),xticklabels=labels,ylabel='Unique updated hubs',title='200 updates distributed over hubs')
for ax in axes:ax.tick_params(axis='x',labelrotation=35)
fig.suptitle('Feedback and update coverage; counts do not prove generalization')
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('feedback_coverage.'+ext),dpi=170)
plt.close(fig)
print(json.dumps(gate,ensure_ascii=False,indent=2));print(json.dumps(feedback,ensure_ascii=False))
