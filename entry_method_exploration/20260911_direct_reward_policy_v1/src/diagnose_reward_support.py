from common import *
import numpy as np,csv

rows=[]
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json');n=c['num_queries'];rr=np.arange(n)
    hits=np.fromfile(E28/'labels'/ds/'hits.u8',np.uint8).reshape(n,56).astype(int)
    flat=hits.max(1)==hits.min(1);headroom=np.fromfile(O/'inputs'/ds/'teachers/headroom.u8',np.uint8).astype(bool)
    outputs={m:np.load(O/'results'/ds/(m+'.npz')) for m in ['anchor','teacher','reward']}
    for name,mask in [('constant_action_hits',flat),('varying_action_hits',~flat),('old_headroom',headroom),('no_old_headroom',~headroom)]:
        a,t,r=[outputs[m] for m in ['anchor','teacher','reward']]
        if name=='constant_action_hits':
            assert np.max(np.abs(r['regret'][mask]))==0
            assert np.array_equal(a['hits'][mask],r['hits'][mask]) and np.array_equal(t['hits'][mask],r['hits'][mask])
        rows.append(dict(dataset=ds,group=name,queries=int(mask.sum()),fraction=float(mask.mean()),
            initial_teacher_loss_mean=float(a['teacher_loss'][mask].mean()),initial_teacher_positive_loss_fraction=float((a['teacher_loss'][mask]>1e-10).mean()),
            initial_teacher_loss_mass_fraction=float(a['teacher_loss'][mask].sum()/a['teacher_loss'].sum()),
            teacher_selected_loss_mean=float(t['teacher_loss'][mask].mean()),reward_selected_teacher_loss_mean=float(r['teacher_loss'][mask].mean()),
            reward_delta_anchor_pp=float((r['hits'][mask]-a['hits'][mask]).mean()*10),reward_delta_teacher_pp=float((r['hits'][mask]-t['hits'][mask]).mean()*10),
            reward_gained_hits_vs_teacher=int(np.maximum(r['hits'][mask]-t['hits'][mask],0).sum()),reward_lost_hits_vs_teacher=int(np.maximum(t['hits'][mask]-r['hits'][mask],0).sum())))
with (O/'results/reward_support.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
dump(O/'results/reward_support.json',rows)
dump(O/'reviews/reward_support.json',dict(status='PASS',posthoc_read_only=True,optimizer_updates=0,new_search_calls=0,models_changed=False,
    statement='For queries with identical hits across all 56 actions, direct Recall data gradient is exactly zero; teacher can still optimize NDC tie choice. Group gradient norms are not inferred from loss shares.'))
print(json.dumps(rows,indent=2),flush=True)
