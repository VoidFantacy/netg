from common import *
from analyze import SHORT,writecsv
import math
import numpy as np

assert read(O/'state.json')['status']=='ANALYSIS_COMPLETE_DIAGNOSTICS_PLOTS_PENDING'
anatomy=[];histogram=[];disagreement=[]
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json');n,h,d=c['num_queries'],c['hub_count'],c['dim'];rr=np.arange(n)
    ts=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
    hits=np.fromfile(E28/'labels'/ds/'hits.u8',np.uint8).reshape(n,56)
    ndc=np.fromfile(E28/'labels'/ds/'graph_ndc.u32',np.uint32).reshape(n,56)
    good=np.fromfile(O/'inputs'/ds/'teachers/multi.u8',np.uint8).reshape(n,56).astype(bool)
    single=np.fromfile(O/'inputs'/ds/'teachers/single.u8',np.uint8).reshape(n,56).astype(bool)
    gain=np.fromfile(O/'inputs'/ds/'teachers/headroom.u8',np.uint8).astype(bool)
    # Each of 8 candidates occurs in exactly C(7,2)=21 complete triples.
    sorted_members=np.sort(ts.reshape(n,-1),axis=1);candidates=sorted_members[:,::21]
    assert candidates.shape==(n,8) and (np.diff(candidates,axis=1)>0).all()
    assert np.array_equal(sorted_members,np.repeat(candidates,21,axis=1))
    incidence=(ts[:,:,:,None]==candidates[:,None,None,:]).any(2)
    freq=(incidence*good[:,:,None]).sum(1);counts=good.sum(1)
    union=(freq>0).sum(1);core=(freq==counts[:,None]).sum(1)
    envelope=np.array([math.comb(int(u-k),int(3-k)) for u,k in zip(union,core)])
    assert (envelope>=counts).all()
    frequency_order=np.argsort(-freq,axis=1,kind='stable')[:,:3]
    frequency_triple=np.sort(np.take_along_axis(candidates,frequency_order,axis=1),axis=1)
    match=(ts==frequency_triple[:,None,:]).all(2);assert (match.sum(1)==1).all();slot=match.argmax(1)
    top=hits==hits.max(1,keepdims=True);bestcost=np.where(top,ndc,np.iinfo(np.uint32).max).min(1)
    for group,mask in [('all',np.ones(n,bool)),('headroom',gain),('no_headroom',~gain)]:
        for count in range(1,57):
            histogram.append(dict(dataset=SHORT[ds],group=group,equivalent_sets=count,queries=int(((counts==count)&mask).sum()),fraction=float(((counts==count)&mask).sum()/mask.sum())))
        anatomy.append(dict(dataset=SHORT[ds],group=group,queries=int(mask.sum()),mean_mandatory_entries=float(core[mask].mean()),
            no_mandatory_entry_fraction=float((core[mask]==0).mean()),one_mandatory_entry_fraction=float((core[mask]==1).mean()),
            two_mandatory_entries_fraction=float((core[mask]==2).mean()),three_mandatory_entries_fraction=float((core[mask]==3).mean()),
            mean_union_entries=float(union[mask].mean()),core_union_closed_fraction=float((envelope[mask]==counts[mask]).mean()),
            teacher_member_frequency_top3_accepted_fraction=float(good[rr,slot][mask].mean()),
            frequency_top3_loss_recall_pp=float((hits.max(1).astype(float)-hits[rr,slot])[mask].mean()*10),
            frequency_top3_extra_graph_ndc=float((ndc[rr,slot].astype(float)-bestcost)[mask].mean()),
            scope='GT-dependent teacher anatomy only; no learner and no QPS'))
    q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(float);q/=np.linalg.norm(q,axis=1,keepdims=True)
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(float)
    checkpoints=[('initial',p/np.linalg.norm(p,axis=1,keepdims=True))]
    checkpoints += [(m['name'],np.fromfile(m['W']['path'],np.float32).reshape(h,d).astype(float)) for m in read(O/'models'/ds/'drift_match.json')['canonical_models']]
    for name,w in checkpoints:
        changed=[];loss_delta=[];single_zero=[];multi_zero=[];accepted_changed=[];augmented_changed=[]
        for b in range(0,n,512):
            z=q[b:b+512]@w.T/.05;t=ts[b:b+512];scores=np.take_along_axis(z[:,None,:],t,axis=2).sum(2)
            gradients=[];losses=[];accepted=[];competitors=[];nr=len(z);rows=np.repeat(np.arange(nr),3)
            for a in [single[b:b+512],good[b:b+512]]:
                positive=np.where(a,scores,-np.inf).argmax(1);augmented=(scores+.1*(~a)).argmax(1)
                accepted.append(positive);competitors.append(augmented)
                g=np.zeros((nr,h),np.int8)
                np.add.at(g,(rows,t[np.arange(nr),augmented].ravel()),1)
                np.add.at(g,(rows,t[np.arange(nr),positive].ravel()),-1)
                gradients.append(g)
                losses.append((scores+.1*(~a))[np.arange(nr),augmented]-scores[np.arange(nr),positive])
            changed.extend((gradients[0]!=gradients[1]).any(1));loss_delta.extend(losses[0]-losses[1])
            accepted_changed.extend(accepted[0]!=accepted[1]);augmented_changed.extend(competitors[0]!=competitors[1])
            single_zero.extend(losses[0]<1e-10);multi_zero.extend(losses[1]<1e-10)
        changed=np.array(changed);loss_delta=np.array(loss_delta);single_zero=np.array(single_zero);multi_zero=np.array(multi_zero)
        accepted_changed=np.array(accepted_changed);augmented_changed=np.array(augmented_changed)
        assert np.all(~changed|accepted_changed|augmented_changed)
        for group,mask in [('all',np.ones(n,bool)),('headroom',gain),('no_headroom',~gain)]:
            disagreement.append(dict(dataset=SHORT[ds],checkpoint=name,group=group,queries=int(mask.sum()),
                score_gradient_changed_fraction=float(changed[mask].mean()),single_minus_multi_loss=float(loss_delta[mask].mean()),
                accepted_winner_changed_fraction=float(accepted_changed[mask].mean()),loss_augmented_winner_changed_fraction=float(augmented_changed[mask].mean()),
                single_zero_loss_fraction=float(single_zero[mask].mean()),multi_zero_loss_fraction=float(multi_zero[mask].mean()),
                scope='same exported scores, per-query gradient with respect to hub logits; not parameter-gradient or performance causality'))
    print('SET_DIAGNOSTICS_COMPLETE',ds,flush=True)
tables=read(O/'results/analysis_tables.json')
for name,rows in [('set_anatomy',anatomy),('equivalence_histogram',histogram),('objective_disagreement',disagreement)]:
    tables[name]=rows;writecsv(name,rows)
dump(O/'results/analysis_tables.json',tables)
dump(O/'reviews/set_diagnostics.json',dict(status='PASS',teacher_anatomy_rows=len(anatomy),score_gradient_rows=len(disagreement),NSG_calls=0,optimizer_steps=0,
    posthoc_after_all_queries=True,scope='explanation of frozen objectives; no model or threshold selection'))
dump(O/'state.json',dict(status='DIAGNOSTICS_COMPLETE_PLOTS_PENDING',training_runs=4,real_search_calls=NORMAL_CAP,heldout_access=False))
