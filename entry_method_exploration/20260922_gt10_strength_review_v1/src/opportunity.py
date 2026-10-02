"""Read-only, same-cohort decomposition of all-H versus actual routed candidates."""
from analyze import *

def run():
    start=time.perf_counter(); os.sched_setaffinity(0,{15})
    old=EXP/'20260921_comparison_direction_pilot_v1'
    cfg=read(old/'config.locked.json'); out=[]
    for ds,c in cfg['datasets'].items():
        root=old/'results'/ds/'labels'; done=read(root/'complete.json')
        H=done['A']-1; hubs=arr(c['anchor']['ids'],'<i4')
        assert len(set(hubs))==H
        lookup={int(h):i+1 for i,h in enumerate(hubs)}
        blocks=sorted(done['blocks'],key=lambda x:x['start'])
        es=np.concatenate([arr(root/f"block_{b['start']}"/'baseline_entries.i32','<i4').reshape(b['n'],3) for b in blocks])
        assert es.shape==(4096,3) and np.all(np.diff(es,axis=1)>0)
        ix=np.array([[lookup[int(h)] for h in row] for row in es])
        for K,name in [(1,'hits1.u8'),(100,'hits100.u8')]:
            h=np.concatenate([arr(root/f"block_{b['start']}"/name,'u1').reshape(b['n'],H+1) for b in blocks]).astype(np.int16)
            n=len(h); base=h[:,0]; singles=h[np.arange(n)[:,None],ix]
            small=np.maximum(base,singles.max(1)); full=h.max(1)
            dg=h[:,1:]-base[:,None]; pos=dg[dg>0]; neg=-dg[dg<0]
            full_gain=int((full-base).sum()); small_gain=int((small-base).sum())
            rec=dict(dataset=ds,K=K,L=128,n=n,H=H,
                default_recall_pct=float(base.mean()/K*100),
                all_H_oracle_gain_pp=full_gain/(n*K)*100,
                default_plus_actual_three_singles_oracle_gain_pp=small_gain/(n*K)*100,
                actual_three_captured_oracle_gain_fraction=small_gain/full_gain,
                additional_all_H_beyond_three_oracle_gain_pp=float((full-small).mean()/K*100),
                full_oracle_improvable_queries=int(np.count_nonzero(full>base)),
                three_oracle_improvable_queries=int(np.count_nonzero(small>base)),
                full_gain_absent_from_three_queries=int(np.count_nonzero((full>base)&(small==base))),
                full_strictly_better_than_three_queries=int(np.count_nonzero(full>small)),
                mean_positive_action_gain_in_recall_pp=float(pos.mean()/K*100),
                mean_negative_action_loss_in_recall_pp=float(neg.mean()/K*100),
                loss_gain_magnitude_ratio=float(neg.mean()/pos.mean()),
                positive_pairs=int(len(pos)),negative_pairs=int(len(neg)),
                net_uniform_change_check_pp=float((pos.sum()-neg.sum())/(n*H*K)*100))
            # Per-query success-action set overlap across nearby row IDs is NOT computed:
            # no query-space neighborhood is loaded, and row proximity is not semantic proximity.
            out.append(rec)
    dump(RUN/'results/same_cohort_candidate_coverage.json',out)
    # Paired K1 sensitivity illustrations use published counts, not a new test.
    examples=[('E105 Web K1',4096,125,126),('E105 Yandex K1',4096,63,63),
              ('E117 Web K1',4096,21,19),('E117 Yandex K1',4096,29,31)]
    precision=[]
    for label,n,rescue,damage in examples:
        delta=(rescue-damage)/n; var=(rescue+damage)/n-delta**2
        precision.append(dict(label=label,n=n,rescues=rescue,damages=damage,
            observed_delta_pp=delta*100,paired_standard_error_pp=float(np.sqrt(var/n)*100),
            rough_MDE_80pct_power_95pct_two_sided_pp=float(2.801585218*np.sqrt(var/n)*100),
            rough_n_for_0_2pp_at_same_discordance=int(np.ceil(2.801585218**2*var/.002**2)),
            caveat='Normal-approximation planning illustration; IID queries, fixed discordance, no multiplicity/selection/domain shift; not a new significance test or required sample size.'))
    dump(RUN/'results/paired_precision_illustration.json',precision)
    dump(RUN/'reviews/opportunity_inputs.json',consumed)
    dump(RUN/'reviews/opportunity_complete.json',dict(status='PASS',rows=len(out),seconds=time.perf_counter()-start,
        same_cohort=True,rank_policy_not_evaluated=True,new_searches=0,new_training=0))
    print(json.dumps({'same_cohort':out,'precision':precision},ensure_ascii=False,indent=2))

if __name__=='__main__':run()
