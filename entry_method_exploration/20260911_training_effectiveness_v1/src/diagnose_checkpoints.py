from common import *
import numpy as np
import csv

assert read(O/'state.json')['status']=='CACHE_ANALYSIS_COMPLETE'
tables=read(O/'results/analysis_tables.json');rows=[]
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json');n,d,h=c['num_queries'],c['dim'],c['hub_count'];rr=np.arange(n)
    q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(float);q/=np.linalg.norm(q,axis=1,keepdims=True)
    ts=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
    hits=np.fromfile(E28/'labels'/ds/'hits.u8',np.uint8).reshape(n,56).astype(int)
    for cell in CELLS:
        dest=O/'models'/ds/cell;r=read(dest/'model.json')
        ws=np.fromfile(dest/'W.f32',np.float32).reshape(h,d).astype(float);wl=np.fromfile(dest/'last_W.f32',np.float32).reshape(h,d).astype(float)
        selected=np.load(O/'results'/ds/('new_'+cell+'.npz'));slots=[];known=[]
        for b in range(0,n,512):
            z=q[b:b+512]@wl.T/.05;s=np.take_along_axis(z[:,None,:],ts[b:b+512],axis=2).sum(2)
            slots.extend(s.argmax(1));pred=np.sort(np.argsort(-z,axis=1,kind='stable')[:,:3],axis=1)
            known.extend((ts[b:b+512]==pred[:,None,:]).all(2).any(1))
        slots=np.array(slots);hh=hits[rr,slots];delta=hh-selected['candidate_hits']
        oldpoint=[x for x in tables['alignment_curve'] if x['dataset']==ds and x['cell']==cell and x['experiment']=='E31' and x['group']=='all' and x['teacher']=='multi']
        base=oldpoint[0]['candidate_recall_pct']
        rows.append(dict(dataset=ds,cell=cell,selected_epoch=r['selected_epoch'],last_epoch=r['updates'],
            objective_last_minus_selected=r['last']['objective']-r['selected']['objective'],
            last_candidate_recall_pct=float(hh.mean()*10),selected_candidate_recall_pct=float(selected['candidate_hits'].mean()*10),
            last_minus_selected_recall_pp=float(delta.mean()*10),candidate_changed_queries=int((slots!=selected['slot']).sum()),
            max_hub_W_displacement=float(np.linalg.norm(wl-ws,axis=1).max()),last_known_fraction=float(np.mean(known)),
            largest_recorded_float64_cache_gain_pp=max(x['candidate_recall_pct']-base for x in oldpoint),
            selection_changed=False,scope='read-only sensitivity diagnostic; no new checkpoint selection or optimizer updates'))
tables['checkpoint_sensitivity']=rows;dump(O/'results/analysis_tables.json',tables)
with (O/'results/checkpoint_sensitivity.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
dump(O/'reviews/checkpoint_diagnostics.json',dict(status='PASS',rows=rows,optimizer_steps=0,NSG_calls=0,selection_changed=False))
print(json.dumps(rows,indent=2),flush=True)
