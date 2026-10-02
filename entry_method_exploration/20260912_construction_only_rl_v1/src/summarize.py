from shared import *
threads(8);resources();assert read(O/'reviews/training_verification.json')['status']=='PASS'
r=read(O/'results/training_analysis.json');models=[];checkpoints=[]
for ds in DS:
 for seed in SEEDS:
  folder=O/'models'/ds/f'graph_rl_{seed}';m=read(folder/'model.json');old=read(E53/'models'/ds/f'rl_ls_{seed}'/'model.json');chosen=m['selected'];last=m['last'];curve=read(folder/'training_curve.json')
  row=dict(dataset=ds,seed=seed,selected_step=m['selected_step'],train512_delta_recall_pp=chosen['train']['delta_recall_pp'],full_train_delta_recall_pp=chosen['full_train']['delta_recall_pp'],
   monitor_delta_recall_pp=chosen['monitor']['delta_recall_pp'],last_full_train_delta_recall_pp=last['full_train']['delta_recall_pp'],last_monitor_delta_recall_pp=last['monitor']['delta_recall_pp'],
   monitor_gain_hits=chosen['monitor']['gain_hits'],monitor_loss_hits=chosen['monitor']['loss_hits'],monitor_failure_queries=chosen['monitor']['failure_queries'],monitor_graph_NDC_change_pct=chosen['monitor']['graph_NDC_change_pct'],
   feasible=m['monitor_gate_feasible'],accepted_updates=m['accepted_updates'],quality_changing_updates=sum(x['accepted_gain_hits']+x['accepted_loss_hits']>0 for x in curve),
   positive_quality_updates=sum(x['accepted_net_hits']>0 for x in curve),negative_quality_updates=sum(x['accepted_net_hits']<0 for x in curve),step_quarter=sum(x['choice']==0 for x in curve),step_half=sum(x['choice']==1 for x in curve),step_full=sum(x['choice']==2 for x in curve),
   E53_joint_RL_selected_monitor_delta_recall_pp=old['selected']['monitor']['delta_recall_pp'],E53_joint_RL_selected_full_train_delta_recall_pp=old['selected']['full_train']['delta_recall_pp'],
   NSG_calls=m['NSG_calls'],candidate_new_NSG=m['candidate_new_NSG'],deterministic_new_NSG=m['deterministic_new_NSG'],HNSW_calls=m['HNSW_calls'],builds=m['builds'],seconds=m['seconds'])
  models.append(row)
  for x in read(folder/'checkpoints.json'):checkpoints.append(dict(dataset=ds,seed=seed,step=x['step'],full_train_delta_recall_pp=x['full_train']['delta_recall_pp'],monitor_delta_recall_pp=x['monitor']['delta_recall_pp'],monitor_U=x['monitor']['mean_U'],monitor_graph_NDC_change_pct=x['monitor']['graph_NDC_change_pct'],drift=x['drift']))
for name,rows in [('models',models),('checkpoints',checkpoints),('steps',r['steps'])]:
 with (O/'results'/f'{name}.csv').open('w',newline='') as f:z=csv.DictWriter(f,fieldnames=list(rows[0]));z.writeheader();z.writerows(rows)
datasets=[dict(dataset=ds,positive_feasible_seeds=sum(x['feasible'] and x['monitor_delta_recall_pp']>0 for x in models if x['dataset']==ds)) for ds in DS]
gate=dict(status='PASS_DUAL_LOCAL_CONSTRUCTION_RL_SIGNAL' if all(x['positive_feasible_seeds']>0 for x in datasets) else 'NO_DUAL_LOCAL_CONSTRUCTION_RL_SIGNAL',datasets=datasets,scope='Selected historical monitor signal, not independent generalization or performance GO')
cost=dict(NSG_calls=sum(x['NSG_calls'] for x in models),candidate_new_NSG=sum(x['candidate_new_NSG'] for x in models),deterministic_new_NSG=sum(x['deterministic_new_NSG'] for x in models),fixed_NSG=62976,HNSW_calls=sum(x['HNSW_calls'] for x in models),builds=sum(x['builds'] for x in models),
 decision_steps=800,gradient_updates=800,accepted_updates=sum(x['accepted_updates'] for x in models),logical_candidate_rows=26214400,logical_deterministic_rows=9830400,mean_update_queries=9830400,
 training_process_seconds=sum(read(O/'results'/ds/'training_complete.json')['seconds'] for ds in DS),new_GT=0,new_cal_audit_queries=0,QPS_points=0)
assert cost['NSG_calls']==62976+cost['candidate_new_NSG']+cost['deterministic_new_NSG'] and cost['HNSW_calls']==36107264 and cost['builds']==19224
dump(O/'results/gate.json',gate);dump(O/'results/cost.json',cost);dump(O/'results/summary.json',dict(models=models,gate=gate,cost=cost))
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(11.5,7));colors=['#277f9c','#c26e37']
for col,ds in enumerate(DS):
 for seed,color in zip(SEEDS,colors):
  current=[x for x in checkpoints if x['dataset']==ds and x['seed']==seed];old=read(E53/'models'/ds/f'rl_ls_{seed}'/'checkpoints.json')
  for row,(key,phase) in enumerate([('full_train_delta_recall_pp','full_train'),('monitor_delta_recall_pp','monitor')]):
   axes[row,col].plot([x['step'] for x in current],[x[key] for x in current],'-o',markersize=3,color=color,label=f'Construction-only RL seed{seed%100}')
   axes[row,col].plot([x['step'] for x in old],[x[phase]['delta_recall_pp'] for x in old],'--',color=color,label=f'E53 joint RL seed{seed%100}')
 for row in range(2):axes[row,col].axhline(0,color='grey',lw=.7);axes[row,col].grid(alpha=.2);axes[row,col].set_xlabel('Decision steps');axes[row,col].legend(fontsize=8)
 axes[0,col].set_title('WebVid' if col==0 else 'Yandex-IP');axes[0,col].set_ylabel('Full train4096 recall change (pp)');axes[1,col].set_ylabel('Monitor1024 recall change (pp)')
fig.suptitle('Construction-only RL versus joint profile and topology RL\nSame initial profiles, Gaussian streams and schedules; states diverge',fontsize=11);fig.tight_layout()
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'construction_learning.{ext}',dpi=170)
plt.close(fig);print(json.dumps(read(O/'results/summary.json'),ensure_ascii=False,indent=2),flush=True)
