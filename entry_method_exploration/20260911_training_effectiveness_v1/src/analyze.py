from common import *
import numpy as np
import csv

def unit(x):return x/np.linalg.norm(x,axis=1,keepdims=True)
def records_csv(name,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with (O/'results'/(name+'.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def ci(delta):
    values,count=np.unique(delta,return_counts=True)
    rng=np.random.default_rng(SEED)
    boot=rng.multinomial(len(delta),count/len(delta),size=2000)@values/len(delta)*10
    return [float(x) for x in np.quantile(boot,[.025,.975])]
def scoring(q,w,ts,good):
    out={k:[] for k in ['slot','full_slot','known','single_loss','multi_loss']}
    for b in range(0,len(q),512):
        z=q[b:b+512]@w.T/.05;s=np.take_along_axis(z[:,None,:],ts[b:b+512],axis=2).sum(2)
        pred=np.sort(np.argsort(-z,axis=1,kind='stable')[:,:3],axis=1)
        match=(ts[b:b+512]==pred[:,None,:]).all(2)
        out['slot'].extend(s.argmax(1));out['full_slot'].extend(match.argmax(1));out['known'].extend(match.any(1))
        for cell in CELLS:
            a=good[cell][b:b+512]
            out[cell+'_loss'].extend(np.max(s+.1*(~a),axis=1)-np.max(np.where(a,s,-np.inf),axis=1))
    return {k:np.array(v) for k,v in out.items()}

assert read(O/'state.json')['status']=='TRAINING_COMPLETE_VERIFICATION_PENDING'
assert read(O/'logs/training_process.json')['status']=='PASS'
check_freeze(O/'models/frozen_after_training.json');check_freeze(O/'reviews/frozen_before_training.json')
models=[];metrics=[];paired=[];training=[];alignment=[];audit=[];gates=[]
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json');n,d,h=c['num_queries'],c['dim'],c['hub_count'];rr=np.arange(n)
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(float)
    q=unit(np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(float))
    ts=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
    good={k:np.fromfile(O/'inputs'/ds/'teachers'/(k+'.u8'),np.uint8).reshape(n,56).astype(bool) for k in CELLS}
    hits=np.fromfile(E28/'labels'/ds/'hits.u8',np.uint8).reshape(n,56).astype(int)
    ndc=np.fromfile(E28/'labels'/ds/'graph_ndc.u32',np.uint32).reshape(n,56).astype(float)
    headroom=np.fromfile(O/'inputs'/ds/'teachers/headroom.u8',np.uint8).astype(bool)
    groups={'all':np.ones(n,bool),'headroom':headroom,'no_headroom':~headroom}
    # Reconstruct the teacher definition independently from the preserved real labels.
    besthit=hits.max(1);bestcost=np.where(hits==besthit[:,None],ndc,np.inf).min(1)
    assert np.array_equal(good['multi'],(hits==besthit[:,None])&(ndc==bestcost[:,None]))
    assert np.all(good['single'].sum(1)==1) and np.all(~good['single']|good['multi'])
    for cell in CELLS:
        dest=O/'models'/ds/cell;r=read(dest/'model.json');curve=read(dest/'training_curve.json')
        assert len(curve)==1201 and r['updates']==1200
        assert r['selected_epoch']==min(range(len(curve)),key=lambda i:curve[i]['objective'])
        for which,prefix,key in [('selected','','selected'),('last','last_','last')]:
            a=np.fromfile(dest/(prefix+'A.f64'),np.float64).reshape(d,d);w=unit(p+p@a.T)
            exported=np.fromfile(dest/(prefix+'W.f32'),np.float32).reshape(h,d)
            assert np.allclose(w,exported,atol=2e-8,rtol=1e-7)
            assert np.max(np.abs(np.linalg.norm(exported.astype(float),axis=1)-1))<1e-7
            out=scoring(q,w,ts,good);loss=float(out[cell+'_loss'].mean());drift=float(np.square(w-p).sum(1).mean())
            ref=r[key];assert abs(loss-ref['data_loss'])<1e-8 and abs(drift-ref['drift'])<1e-10
            assert abs(loss+100*drift-ref['objective'])<1e-8
            if which=='selected':
                for m in read(dest/'selected_alignment.json'):
                    mask=groups[m['group']];a_good=good[m['teacher']]
                    assert abs(a_good[rr,out['slot']][mask].mean()-m['candidate_acceptance'])<1e-12
                    assert abs(hits[rr,out['slot']][mask].mean()*10-m['candidate_recall_pct'])<1e-12
                    assert abs(ndc[rr,out['slot']][mask].mean()-m['candidate_graph_ndc'])<1e-8
                    assert abs(out['known'][mask].mean()-m['full_exact_known_fraction'])<1e-12
            audit.append(dict(dataset=ds,cell=cell,checkpoint=which,status='PASS',objective=loss+100*drift))
        old=read(E30/'models'/ds/cell/'model.json')
        oldcurve=read(E30/'models'/ds/cell/'training_curve.json')
        models.append(dict(dataset=ds,cell=cell,selected_epoch=r['selected_epoch'],new_objective=r['selected']['objective'],
            old_objective=old['last']['objective'],objective_change_pct=(r['selected']['objective']/old['last']['objective']-1)*100,
            new_data_loss=r['selected']['data_loss'],old_data_loss=old['last']['data_loss'],new_drift=r['selected']['drift'],old_drift=old['last']['drift'],
            new_first_step_objective=curve[1]['objective'],old_first_step_objective=oldcurve[1]['objective'],
            best_improvement_last100_pct=(curve[1100]['best_objective']-curve[-1]['best_objective'])/curve[1100]['best_objective']*100,
            training_seconds=r['training_seconds'],gradient_norm=r['selected']['gradient_norm']))
        for experiment,path in [('E30',E30),('E31',O)]:
            for row in read(path/'models'/ds/cell/'training_curve.json'):training.append(dict(dataset=ds,cell=cell,experiment=experiment,**row))
            for arow in read(path/'models'/ds/cell/'alignment_curve.json'):
                for m in arow['metrics']:alignment.append(dict(dataset=ds,cell=cell,experiment=experiment,epoch=arow['epoch'],**m))
    paths={'anchor':E24/'models'/ds/'gt10_hard/W.f32'}
    for cell in CELLS:
        paths['old_'+cell]=E30/'models'/ds/cell/'W.f32';paths['new_'+cell]=O/'models'/ds/cell/'W.f32'
    outs={};point={}
    for name,path in paths.items():
        w=np.fromfile(path,np.float32).reshape(h,d).astype(float);out=scoring(q,w,ts,good)
        out['candidate_hits']=hits[rr,out['slot']];out['candidate_ndc']=ndc[rr,out['slot']]
        out['known_hits']=np.where(out['known'],hits[rr,out['full_slot']],0)
        out['known_ndc']=np.where(out['known'],ndc[rr,out['full_slot']],np.nan)
        outs[name]=out
        dest=O/'results'/ds;dest.mkdir(exist_ok=True);np.savez_compressed(dest/(name+'.npz'),**out)
        for group,mask in groups.items():
            k=out['known'][mask];num=int(mask.sum());unknown=int((~k).sum())
            row=dict(dataset=ds,method=name,group=group,queries=num,candidate_recall_pct=float(out['candidate_hits'][mask].mean()*10),
                candidate_graph_ndc=float(out['candidate_ndc'][mask].mean()),candidate_G_acceptance=float(good['multi'][rr,out['slot']][mask].mean()),
                full_exact_known_fraction=float(k.mean()),unknown_queries=unknown,
                full_exact_recall_lower_pct=float(out['known_hits'][mask].sum()*10/num),
                full_exact_recall_upper_pct=float((out['known_hits'][mask].sum()+unknown*10)*10/num),
                full_exact_known_recall_pct=float(out['known_hits'][mask].sum()*10/k.sum()),
                full_exact_known_graph_ndc=float(np.nanmean(out['known_ndc'][mask])))
            metrics.append(row)
            if group=='all':point[name]=row
    for name,ref in [('old_single','anchor'),('old_multi','anchor'),('new_single','anchor'),('new_multi','anchor'),('new_single','old_single'),('new_multi','old_multi'),('new_multi','new_single')]:
        for group,mask in groups.items():
            delta=outs[name]['candidate_hits'][mask]-outs[ref]['candidate_hits'][mask]
            low,high=ci(delta)
            paired.append(dict(dataset=ds,method=name,reference=ref,group=group,queries=int(mask.sum()),
                candidate_delta_recall_pp=float(delta.mean()*10),ci95_low_pp=low,ci95_high_pp=high,
                improved_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),
                gained_hits=int(delta[delta>0].sum()),lost_hits=int(-delta[delta<0].sum()),
                graph_ndc_change_pct=(float(outs[name]['candidate_ndc'][mask].mean()/outs[ref]['candidate_ndc'][mask].mean())-1)*100))
    for cell in CELLS:
        cur,old,base=point['new_'+cell],point['old_'+cell],point['anchor']
        dr=cur['candidate_recall_pct']-base['candidate_recall_pct'];oldgain=cur['candidate_recall_pct']-old['candidate_recall_pct']
        cost=cur['candidate_graph_ndc']/base['candidate_graph_ndc']-1
        lower=cur['full_exact_recall_lower_pct']-base['full_exact_recall_upper_pct']
        conditions=dict(candidate_gain_ge_point20=dr>=.2-1e-10,improves_old_cell=oldgain>1e-10,candidate_cost_le_1pct=cost<=.01,
            full_exact_known_ge_995=cur['full_exact_known_fraction']>=.995,full_exact_worst_delta_ge_point20=lower>=.2-1e-10)
        gates.append(dict(dataset=ds,cell=cell,candidate_gain_pp=dr,old_cell_gain_pp=oldgain,graph_ndc_change_pct=cost*100,
            full_exact_worst_delta_pp=lower,known_fraction=cur['full_exact_known_fraction'],conditions=conditions,passed=all(conditions.values())))
passing=[cell for cell in CELLS if all(x['passed'] for x in gates if x['cell']==cell)]
gate=dict(status='PASS_REAL_DEVELOPMENT_ALLOWED' if passing else 'STOP_CACHE_UTILITY_GATE',passing_cells=passing,by_dataset=gates,
    gate_scope='fit-only cached real L128 labels and exact known-coverage bounds; no HNSW/QPS',new_labels=0,real_search_calls=0)
dump(O/'results/cache_gate.json',gate)
tables=dict(model_comparison=models,training_curve=training,alignment_curve=alignment,cache_metrics=metrics,paired_cache=paired)
for name,rows in tables.items():records_csv(name,rows)
dump(O/'results/analysis_tables.json',tables)
dump(O/'reviews/model_and_cache_verification.json',dict(status='PASS',models=audit,original_objective_unchanged=True,teacher_definition_reconstructed=True,
    exported_models_scored=10,fit_queries_per_dataset=20000,logical_labels_reused=2240000,new_labels=0,NSG_calls=0,optimizer_steps=0))
dump(O/'state.json',dict(status='CACHE_ANALYSIS_COMPLETE',gate=gate['status'],real_search_calls=0,heldout_access=False))
print(json.dumps(dict(models=models,gate=gate),ensure_ascii=False,indent=2),flush=True)
