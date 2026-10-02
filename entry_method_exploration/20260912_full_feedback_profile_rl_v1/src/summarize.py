from shared import *
threads(8);resources();assert read(O/'reviews/training_verification.json')['status']=='PASS'
a=read(O/'results/training_analysis.json');models=[];feedback=[];quality=[]
def table(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for rec in a['runs']:
 ds=rec['dataset'];arm=rec['arm'];seed=rec['seed'];steps=[x for x in a['steps'] if x['dataset']==ds and x['arm']==arm and x['seed']==seed]
 old=read(E43/'models'/ds/f'{arm}_{seed}'/'model.json');sm=rec['selected']['monitor'];lm=rec['last']['monitor'];st=rec['selected']['train'];sf=rec['selected']['full_train']
 models.append(dict(dataset=ds,arm=arm,seed=seed,selected_step=rec['selected_step'],train_delta_recall_pp=st['delta_recall_pp'],full_train_delta_recall_pp=sf['delta_recall_pp'],
  monitor_delta_recall_pp=sm['delta_recall_pp'],monitor_U=sm['mean_U'],monitor_graph_NDC_change_pct=sm['graph_NDC_change_pct'],last_monitor_delta_recall_pp=lm['delta_recall_pp'],
  E43_selected_monitor_delta_recall_pp=old['selected']['monitor']['delta_recall_pp'],E43_last_monitor_delta_recall_pp=old['last']['monitor']['delta_recall_pp'],
  selected_vs_E43_monitor_delta_pp=sm['delta_recall_pp']-old['selected']['monitor']['delta_recall_pp'],seconds=rec['seconds'],NSG_calls=rec['NSG_calls'],
  candidate_new_NSG=rec['candidate_new_NSG'],mean_update_new_NSG=rec['mean_update_new_NSG']))
 feedback.append(dict(dataset=ds,arm=arm,seed=seed,hit_feedback_steps=sum(x['hit_candidates']>0 for x in steps),hit_candidates=sum(x['hit_candidates'] for x in steps),
  positive_candidates=sum(x['positive_candidates'] for x in steps),negative_candidates=sum(x['negative_candidates'] for x in steps),
  mean_quality_change_steps=sum(x['mean_gain_hits']+x['mean_loss_hits']>0 for x in steps),mean_positive_steps=sum(x['mean_net_hits']>0 for x in steps),mean_negative_steps=sum(x['mean_net_hits']<0 for x in steps),
  mean_gain_hits=sum(x['mean_gain_hits'] for x in steps),mean_loss_hits=sum(x['mean_loss_hits'] for x in steps),mean_net_hits=sum(x['mean_net_hits'] for x in steps),
  candidate_new_NSG=rec['candidate_new_NSG'],mean_new_NSG=rec['mean_update_new_NSG'],candidate_logical_rows=6553600,mean_logical_rows=819200,
  candidate_NSG_fraction=rec['candidate_new_NSG']/6553600,mean_NSG_fraction=rec['mean_update_new_NSG']/819200))
 for tag in ['selected','last']:
  for split in ['train','full_train','monitor']:quality.append(dict(dataset=ds,arm=arm,seed=seed,checkpoint=tag,step=rec[tag]['step'],split=split,**rec[tag][split]))
table(O/'results/models.csv',models);table(O/'results/feedback.csv',feedback);table(O/'results/quality.csv',quality);table(O/'results/steps.csv',a['steps'])
ds_gates=[]
for ds in DS:
 arms=[]
 for arm in ARMS:
  rr=[x for x in models if x['dataset']==ds and x['arm']==arm];ok=[x['seed'] for x in rr if x['monitor_delta_recall_pp']>0 and x['monitor_U']>0 and x['monitor_graph_NDC_change_pct']<=1]
  arms.append(dict(arm=arm,passing_seeds=ok,passed=bool(ok)))
 ds_gates.append(dict(dataset=ds,arms=arms,passed=all(x['passed'] for x in arms)))
passed=all(x['passed'] for x in ds_gates)
gate=dict(status='PASS_FULL_FEEDBACK_MONITOR_GATE' if passed else 'STOP_FULL_FEEDBACK_BUDGET_EXPANSION',datasets=ds_gates,scope='historically used train/monitor, checkpoint selection only; no development/QPS or default replacement')
dump(O/'results/method_gate.json',gate)
ds_cost=[read(O/'results'/ds/'training_complete.json') for ds in DS];jobs=read(O/'logs/jobs.json')
assert len(jobs)==8 and all(x['status']=='COMPLETE' for x in jobs)
cost=dict(NSG_calls=sum(x['NSG_calls'] for x in a['runs']),HNSW_calls=sum(x['HNSW_calls'] for x in a['runs']),builds=sum(x['builds'] for x in a['runs']),optimizer_updates=1600,
 reserved_NSG=sum(x['reserved'] for x in jobs),NSG_hard_cap=800000,fixed_actual_NSG=15744*8,candidate_new_NSG=sum(x['candidate_new_NSG'] for x in a['runs']),
 mean_update_new_NSG=sum(x['mean_update_new_NSG'] for x in a['runs']),logical_candidate_rows=6553600*8,logical_mean_rows=819200*8,cold_full_feedback_rows=4096*8,
 monitor_rows=1024*11*8,export_parity_NSG=64*3*2*8,train512_checkpoint_reuse_rows=512*11*8,datasets=ds_cost,new_GT=0,new_development_queries=0,QPS_points=0)
assert cost['HNSW_calls']==59107328 and cost['builds']==14424 and cost['NSG_calls']==cost['fixed_actual_NSG']+cost['candidate_new_NSG']+cost['mean_update_new_NSG']
dump(O/'results/cost.json',cost);dump(O/'results/summary.json',dict(models=models,feedback=feedback,gate=gate,cost=cost))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for row,ds in enumerate(DS):
 ax=axes[row,0]
 for arm in ARMS:
  for seed in SEEDS:
   cps=read(O/'models'/ds/f'{arm}_{seed}'/'checkpoints.json');ax.plot([x['step'] for x in cps],[x['monitor']['delta_recall_pp'] for x in cps],marker='o',ms=3,label=f'{arm.upper()} / {str(seed)[-2:]}')
 ax.set(xlabel='Optimizer step',ylabel='Monitor Recall@10 change (pp)',title=('WebVid' if row==0 else 'Yandex')+' full-feedback learning');ax.axhline(0,color='grey',lw=.7);ax.legend(fontsize=8)
 ax=axes[row,1];rr=[x for x in models if x['dataset']==ds];xx=np.arange(4)
 ax.bar(xx-.18,[x['E43_selected_monitor_delta_recall_pp'] for x in rr],.36,label='E43 batch feedback')
 ax.bar(xx+.18,[x['monitor_delta_recall_pp'] for x in rr],.36,label='E47 full feedback')
 ax.set(xticks=xx,xticklabels=[x['arm'].upper()+'/'+str(x['seed'])[-2:] for x in rr],ylabel='Selected monitor Recall@10 change (pp)',title='Same family, different feedback coverage/cost');ax.axhline(0,color='grey',lw=.7);ax.legend(fontsize=8)
 for ax in axes[row]:ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Complete feedback profile training: RL and ES, two fixed seeds\nMonitor selects checkpoints; this is not an independent performance frontier',fontsize=13)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'full_feedback_learning.{ext}',dpi=160)
plt.close(fig)
print(json.dumps(dict(gate=gate,models=models,feedback=feedback,cost={k:v for k,v in cost.items() if k!='datasets'}),indent=2),flush=True)
