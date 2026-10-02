from common import *
import pandas as pd

assert not (O/'reviews/independent_verification.json').exists()
s=pd.read_csv(O/'results/steps.csv');q=pd.read_csv(O/'results/query_exposure.csv');groups=pd.read_csv(O/'results/matched_groups.csv');matched=pd.read_csv(O/'results/matched_queries.csv')
checked=0;raw=0;matched_count=0;extra=[]
def scalarhits(ids,gt):return np.array([len(set(map(int,x))&set(map(int,g[:10]))) for x,g in zip(ids,gt)],dtype=np.int16)
def direct_gradient(arm,reward,eps):
 if arm=='rl':return sum((reward[i]-sum(reward[j] for j in range(8) if j!=i)/7)*eps[i]/(8*.3) for i in range(8))
 return sum((reward[i]-reward[i+4])*eps[i]/(8*.3) for i in range(4))
for ds in DS:
 config=read(E/'inputs'/ds/'config.json');gt=np.fromfile(config['gt_file'],np.int64).reshape(5120,100);rowids=np.fromfile(config['row_ids'],np.int64);base=dict(np.load(E/'results'/ds/'baseline.npz'));bc=base['route_ndc'].astype(float)+base['graph_ndc']
 for arm in ARMS:
  for seed in SEEDS:
   model=E/'models'/ds/f'{arm}_{seed}';runq=q[(q.dataset==ds)&(q.arm==arm)&(q.seed==seed)];seen=runq[runq.batches>0];normalized=(seen.gradient_norm_sum/seen.batches).sort_values(ascending=False);runsteps=s[(s.dataset==ds)&(s.arm==arm)]
   extra.append(dict(dataset=ds,arm=arm,seed=seed,observed_queries=len(seen),exposure_normalized_top41_gradient_share=float(normalized.iloc[:41].sum()/normalized.sum()),unseen_train_rows=int((runq.batches==0).sum())))
   assert runq.observations.sum()==204800 and runq.batches.sum()==25600
   for step in [1,20,100,200]:
    a=dict(np.load(model/'trajectory'/f'{step:04}.npz'));rows=a['rows'];h=np.stack([scalarhits(x,gt[rows]) for x in a['ids']]);bh=scalarhits(base['ids'][rows],gt[rows]);raw+=h.size
    delta=h-bh;u=delta-.1*((a['route_ndc'].astype(float)+a['graph_ndc']-bc[rows])/bc[rows])-.1*((h==0).astype(float)-(bh==0).astype(float));reward=u.mean(1)-a['drift'];g=direct_gradient(arm,reward,a['eps']);assert np.max(np.abs(g-a['gradient']))<1e-12
    perq=np.stack([direct_gradient(arm,u[:,j],a['eps']) for j in range(128)],axis=1);mean=perq.mean(1);variance=sum(float(np.dot(perq[:,j]-mean,perq[:,j]-mean)) for j in range(128))/127/128*(1-128/4096)
    v=s[(s.dataset==ds)&(s.arm==arm)&(s.seed==seed)&(s.step==step)].iloc[0];assert abs(variance-v.query_gradient_variance)<1e-12
    assert int((h.max(0)>h.min(0)).sum())==v.discriminating_queries
    rng=np.random.default_rng(seed+step*10000);cos=[]
    for _ in range(16):
     inds=rng.permutation(128);g1=direct_gradient(arm,u[:,inds[:64]].mean(1),a['eps']);g2=direct_gradient(arm,u[:,inds[64:]].mean(1),a['eps']);cos.append(cosine(g1,g2))
    assert abs(median(cos)-v.split_query_cosine)<1e-10;checked+=1
   for centerstep in range(0,200,20):
    a=dict(np.load(model/'trajectory'/f'{centerstep+1:04}.npz'));cp=dict(np.load(model/'checkpoints'/f'{centerstep:04}.npz'));assert np.array_equal(a['mu_before'],cp['mu']);ii=np.flatnonzero(a['rows']<512);rr=a['rows'][ii]
    h=np.stack([scalarhits(x[ii],gt[rr]) for x in a['ids']]);ch=scalarhits(cp['ids'][rr],gt[rr]);gap=(h.mean(0)-ch)*10
    actual=matched[(matched.dataset==ds)&(matched.arm==arm)&(matched.seed==seed)&(matched.center_step==centerstep)];assert np.array_equal(actual.query_index,rr) and np.array_equal(actual.query_row,rowids[rr]);assert np.max(np.abs(actual.delta_recall_pp-gap))<1e-12
    group=groups[(groups.dataset==ds)&(groups.arm==arm)&(groups.seed==seed)&(groups.center_step==centerstep)].iloc[0];assert group.queries==len(ii) and abs(group.mean_recall_gap_pp-gap.mean())<1e-12;matched_count+=len(rr)
check(read(O/'reviews/analysis_inputs.json')['files'])
pd.DataFrame(extra).to_csv(O/'results/exposure_control.csv',index=False)
dump(O/'reviews/independent_verification.json',dict(status='PASS',independent_set_scored_action_outputs=raw,step_decompositions_checked=checked,conditional_variance_and_half_query_gradient_checked=checked,all_exact_mu_matched_query_records_checked=matched_count,all_run_exposure_totals_checked=True,analysis_sources_unchanged=True))
print('INDEPENDENT_VERIFICATION_PASS',checked,'steps',matched_count,'matched rows',flush=True)
