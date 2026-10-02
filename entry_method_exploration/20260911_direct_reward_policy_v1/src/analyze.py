from common import *
import numpy as np
import csv

def unit(x):return x/np.linalg.norm(x,axis=1,keepdims=True)
def score(q,w,ts,g,hits,ndc):
    rows={k:[] for k in ['slot','teacher_loss','regret','expected_hits','expected_ndc','entropy','max_probability']}
    for b in range(0,len(q),512):
        sl=slice(b,b+512);z=q[sl]@w.T/.05
        s=np.take_along_axis(z[:,None,:],ts[sl],axis=2).sum(2)
        pi=np.exp(s-s.max(1)[:,None]);pi/=pi.sum(1)[:,None]
        rows['slot'].extend(s.argmax(1))
        rows['teacher_loss'].extend((s+.1*(~g[sl])).max(1)-np.where(g[sl],s,-np.inf).max(1))
        rows['regret'].extend((pi*(hits[sl].max(1)[:,None]-hits[sl])/10).sum(1))
        rows['expected_hits'].extend((pi*hits[sl]).sum(1));rows['expected_ndc'].extend((pi*ndc[sl]).sum(1))
        rows['entropy'].extend(-(pi*np.log(np.maximum(pi,1e-300))).sum(1));rows['max_probability'].extend(pi.max(1))
    out={k:np.array(v) for k,v in rows.items()};rr=np.arange(len(q))
    out['hits']=hits[rr,out['slot']];out['ndc']=ndc[rr,out['slot']]
    return out

def independent_initial_gradient(q,p,ts,g,hits,cell):
    w=unit(p);gw=np.zeros_like(p);n=len(q)
    for b in range(0,n,512):
        sl=slice(b,b+512);z=q[sl]@w.T/.05;s=np.take_along_axis(z[:,None,:],ts[sl],axis=2).sum(2)
        if cell=='teacher':
            gs=np.zeros_like(s);rr=np.arange(len(s));gs[rr,(s+.1*(~g[sl])).argmax(1)]+=1/n;gs[rr,np.where(g[sl],s,-np.inf).argmax(1)]-=1/n
        else:
            pi=np.exp(s-s.max(1)[:,None]);pi/=pi.sum(1)[:,None]
            regret=(hits[sl].max(1)[:,None]-hits[sl])/10
            gs=pi*(regret-(pi*regret).sum(1)[:,None])/n
        gz=np.zeros_like(z)
        np.add.at(gz,(np.arange(len(s))[:,None,None],ts[sl]),np.repeat(gs[:,:,None],3,axis=2))
        gw+=gz.T@q[sl]/.05
    gu=(gw-(gw*w).sum(1)[:,None]*w)/np.linalg.norm(p,axis=1)[:,None]
    return gu.T@p

def ci(delta):
    v,c=np.unique(delta,return_counts=True);rng=np.random.default_rng(SEED)
    samples=rng.multinomial(len(delta),c/len(delta),size=2000)@v/len(delta)*10
    return list(map(float,np.quantile(samples,[.025,.975])))

assert read(O/'state.json')['status']=='TRAINING_COMPLETE_VERIFICATION_PENDING'
check_freeze(O/'reviews/frozen_protocol_before_scale.json');check_freeze(O/'reviews/frozen_before_training.json');check_freeze(O/'models/frozen_after_training.json')
metrics=[];pairs=[];curves=[];models=[];verification=[];gates=[];scale_checks=[]
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json');n,d,h=c['num_queries'],c['dim'],c['hub_count'];rr=np.arange(n)
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(float)
    q=unit(np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(float))
    ts=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
    g=np.fromfile(O/'inputs'/ds/'teachers/multi.u8',np.uint8).reshape(n,56).astype(bool)
    hits=np.fromfile(E28/'labels'/ds/'hits.u8',np.uint8).reshape(n,56).astype(int)
    ndc=np.fromfile(E28/'labels'/ds/'graph_ndc.u32',np.uint32).reshape(n,56).astype(float)
    scales=read(O/'reviews/reward_scales.json')[ds];beta=scales['beta']
    grads={cell:independent_initial_gradient(q,p,ts,g,hits,cell) for cell in CELLS}
    for cell,key in [('teacher','teacher_data_gradient_norm'),('reward','unscaled_reward_gradient_norm')]:
        norm=np.linalg.norm(grads[cell]);assert abs(norm/scales[key]-1)<1e-10
        scale_checks.append(dict(dataset=ds,cell=cell,numpy_initial_gradient_norm=float(norm),status='PASS'))
    for cell in CELLS:
        dest=O/'models'/ds/cell;r=read(dest/'model.json');curve=read(dest/'training_curve.json')
        assert len(curve)==1201 and r['updates']==1200
        feasible=[x for x in curve if x['expected_graph_ndc']<=curve[0]['expected_graph_ndc']*1.01 and x['greedy_graph_ndc']<=curve[0]['greedy_graph_ndc']*1.01]
        selected=min(feasible,key=lambda x:x['objective']);assert selected['epoch']==r['selected_epoch']
        for key,prefix in [('selected',''),('last','last_')]:
            a=np.fromfile(dest/(prefix+'A.f64'),float).reshape(d,d);w=unit(p+p@a.T)
            export=np.fromfile(dest/(prefix+'W.f32'),np.float32).reshape(h,d)
            assert np.allclose(w,export,rtol=1e-7,atol=2e-8)
            out=score(q,w,ts,g,hits,ndc);loss=out['teacher_loss'].mean() if cell=='teacher' else beta*out['regret'].mean()
            drift=np.square(w-p).sum(1).mean();ref=r[key]
            values=dict(data_loss=loss,drift=drift,objective=loss+100*drift,expected_recall_pct=out['expected_hits'].mean()*10,
                greedy_recall_pct=out['hits'].mean()*10,expected_graph_ndc=out['expected_ndc'].mean(),greedy_graph_ndc=out['ndc'].mean())
            for k,v in values.items():assert abs(v-ref[k])<1e-7,(ds,cell,key,k,v,ref[k])
            verification.append(dict(dataset=ds,cell=cell,checkpoint=key,status='PASS',objective=float(values['objective'])))
        recovery=None
        if cell=='teacher':
            recovery=all(sha(dest/f)==sha(E31/'models'/ds/'multi'/f) for f in ['A.f64','W.f32','last_A.f64','last_W.f32'])
            assert recovery,'Teacher unexpectedly differs from E31; review before any gate'
        models.append(dict(dataset=ds,cell=cell,selected_epoch=r['selected_epoch'],initial_objective=r['first']['objective'],selected_objective=r['selected']['objective'],
            objective_change_pct=(r['selected']['objective']/r['first']['objective']-1)*100,selected_gradient_norm=r['selected']['gradient_norm'],
            beta=beta,selected_drift=r['selected']['drift'],training_seconds=r['training_seconds'],feasible_points=len(feasible),
            best_improvement_last100=float(curve[1100]['best_objective']-curve[-1]['best_objective']),teacher_E31_four_files_bit_equal=recovery))
        curves.extend(dict(dataset=ds,cell=cell,**row) for row in curve)
    paths={'anchor':E24/'models'/ds/'gt10_hard/W.f32',**{cell:O/'models'/ds/cell/'W.f32' for cell in CELLS}}
    outs={};point={};headroom=np.fromfile(O/'inputs'/ds/'teachers/headroom.u8',np.uint8).astype(bool)
    groups={'all':np.ones(n,bool),'headroom':headroom,'no_headroom':~headroom}
    for name,path in paths.items():
        w=np.fromfile(path,np.float32).reshape(h,d).astype(float);out=score(q,w,ts,g,hits,ndc);outs[name]=out
        od=O/'results'/ds;od.mkdir(exist_ok=True)
        np.savez_compressed(od/(name+'.npz'),row_ids=np.fromfile(c['row_ids'],np.int64),selected_triples=ts[rr,out['slot']],**out)
        for group,mask in groups.items():
            row=dict(dataset=ds,method=name,group=group,queries=int(mask.sum()),greedy_recall_pct=float(out['hits'][mask].mean()*10),
                expected_recall_pct=float(out['expected_hits'][mask].mean()*10),greedy_graph_ndc=float(out['ndc'][mask].mean()),
                expected_graph_ndc=float(out['expected_ndc'][mask].mean()),entropy=float(out['entropy'][mask].mean()),
                max_probability=float(out['max_probability'][mask].mean()),teacher_loss=float(out['teacher_loss'][mask].mean()),
                expected_regret=float(out['regret'][mask].mean()),zero_hit_queries=int((out['hits'][mask]==0).sum()))
            metrics.append(row)
            if group=='all':point[name]=row
    for name,reference in [('teacher','anchor'),('reward','anchor'),('reward','teacher')]:
        for group,mask in groups.items():
            a,b=outs[name],outs[reference];delta=a['hits'][mask]-b['hits'][mask];low,high=ci(delta)
            pairs.append(dict(dataset=ds,method=name,reference=reference,group=group,queries=int(mask.sum()),greedy_delta_recall_pp=float(delta.mean()*10),
                ci95_low_pp=low,ci95_high_pp=high,expected_delta_recall_pp=float((a['expected_hits'][mask]-b['expected_hits'][mask]).mean()*10),
                greedy_graph_ndc_change_pct=float((a['ndc'][mask].mean()/b['ndc'][mask].mean()-1)*100),
                expected_graph_ndc_change_pct=float((a['expected_ndc'][mask].mean()/b['expected_ndc'][mask].mean()-1)*100),
                gained_hits=int(delta[delta>0].sum()),lost_hits=int(-delta[delta<0].sum()),improved_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),
                rescued_zero_hit=int(((b['hits'][mask]==0)&(a['hits'][mask]>0)).sum()),new_zero_hit=int(((b['hits'][mask]>0)&(a['hits'][mask]==0)).sum())))
    a,t,r=point['anchor'],point['teacher'],point['reward']
    conditions=dict(greedy_gain_anchor_ge_point20=r['greedy_recall_pct']-a['greedy_recall_pct']>=.2-1e-10,
        greedy_gain_teacher_ge_point05=r['greedy_recall_pct']-t['greedy_recall_pct']>=.05-1e-10,
        greedy_cost_le_1pct=r['greedy_graph_ndc']<=a['greedy_graph_ndc']*1.01,
        expected_cost_le_1pct=r['expected_graph_ndc']<=a['expected_graph_ndc']*1.01)
    gates.append(dict(dataset=ds,conditions=conditions,passed=all(conditions.values()),
        reward_gain_anchor_pp=r['greedy_recall_pct']-a['greedy_recall_pct'],reward_gain_teacher_pp=r['greedy_recall_pct']-t['greedy_recall_pct'],
        greedy_graph_ndc_change_pct=(r['greedy_graph_ndc']/a['greedy_graph_ndc']-1)*100,
        expected_graph_ndc_change_pct=(r['expected_graph_ndc']/a['expected_graph_ndc']-1)*100))
budget=read(O/'models/training_budget.json');passed=all(x['passed'] for x in gates) and budget['all_runs_complete'] and budget['status']=='PASS'
gate=dict(status='PASS_REAL_DEVELOPMENT_ALLOWED' if passed else 'STOP_CACHE_UTILITY_GATE',by_dataset=gates,
    prerequisites_passed=True,scope='fit-only complete C8 real-label cache; no online QPS',NSG_calls=0,new_labels=0,heldout_access=False)
dump(O/'results/cache_gate.json',gate)
tables=dict(model_comparison=models,training_curve=curves,cache_metrics=metrics,paired_cache=pairs)
for name,rows in tables.items():
    with (O/'results'/(name+'.csv')).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
dump(O/'results/analysis_tables.json',tables)
dump(O/'reviews/model_and_cache_verification.json',dict(status='PASS',models=verification,independent_scale_checks=scale_checks,
    teacher_E31_bit_recovery=True,scored_float32_exports=6,logical_labels_reused=2240000,new_labels=0,NSG_calls=0,optimizer_steps=0))
dump(O/'state.json',dict(status='CACHE_ANALYSIS_COMPLETE',gate=gate['status'],real_search_calls=0,heldout_access=False))
print(json.dumps(dict(models=models,metrics=[x for x in metrics if x['group']=='all'],gate=gate),indent=2),flush=True)
