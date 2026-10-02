from setup import *
import numpy as np,itertools,csv
records=[];model_rows=[]
for ds in DS:
 c=json.loads((O/'inputs'/ds/'fit/config.json').read_text());n=c['num_queries'];h=c['hub_count'];d=c['dim'];dest=O/'labels'/ds
 candidates=np.fromfile(O/'inputs'/ds/'proposals/candidates.i32',np.int32).reshape(n,8);ts=np.fromfile(O/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
 bs=np.fromfile(O/'inputs'/ds/'proposals/baseline_triples.i32',np.int32).reshape(n,2,3)[:,1];targets=np.fromfile(dest/'teacher.i32',np.int32).reshape(n,3);slots=np.fromfile(dest/'teacher_slot.i32',np.int32)
 hits=np.fromfile(dest/'hits.u8',np.uint8).reshape(n,56);ndc=np.fromfile(dest/'graph_ndc.u32',np.uint32).reshape(n,56);base_slots=(ts==bs[:,None,:]).all(2).argmax(1);ri=np.arange(n)
 bh=hits[ri,base_slots].astype(int);th=hits[ri,slots].astype(int);bn=ndc[ri,base_slots];tn=ndc[ri,slots];headroom=th>bh;changed=(targets!=bs).any(1);ties=(hits==th[:,None]).sum(1)
 for group,mask in [('all',np.ones(n,dtype=bool)),('recall_headroom',headroom),('no_recall_headroom',~headroom)]:
  records.append(dict(dataset=ds,group=group,queries=int(mask.sum()),fraction=float(mask.mean()),teacher_entry_set_change_fraction=float(changed[mask].mean()),mean_max_hit_ties=float(ties[mask].mean()),median_max_hit_ties=float(np.median(ties[mask])),mean_hit_gain=float((th-bh)[mask].mean()),mean_graph_ndc_gain_pct=float(((bn.astype(float)-tn)/bn)[mask].mean()*100),baseline_full_recall_fraction=float((bh[mask]==10).mean())))
 q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(np.float64);q/=np.linalg.norm(q,axis=1,keepdims=True)
 lookup=np.full((8,8,8),-1,int)
 for i,comb in enumerate(itertools.combinations(range(8),3)):lookup[comb]=i
 models=json.loads((O/'models'/ds/'selection.json').read_text())['selected']
 for m in models:
  w=np.fromfile(m['W'],np.float32).reshape(h,d).astype(np.float64);chosen=np.argsort(-(q@w.T),axis=1,kind='stable')[:,:3];match=chosen[:,:,None]==candidates[:,None,:];known=match.any(2).all(1);positions=np.sort(match.argmax(2),axis=1);label_slots=lookup[positions[:,0],positions[:,1],positions[:,2]];assert (label_slots[known]>=0).all()
  mh=np.full(n,-1,int);mh[known]=hits[ri[known],label_slots[known]]
  for group,gmask in [('all',np.ones(n,dtype=bool)),('recall_headroom',headroom),('no_recall_headroom',~headroom)]:
   mask=gmask&known;diff=mh[mask]-bh[mask]
   model_rows.append(dict(dataset=ds,method=m['model_name'],group=group,group_queries=int(gmask.sum()),known_queries=int(mask.sum()),known_fraction=float(mask.sum()/gmask.sum()),delta_recall_pp_on_known=float(diff.mean()*10),improved_queries_on_known=int((diff>0).sum()),harmed_queries_on_known=int((diff<0).sum()),gained_hits_on_known=int(diff[diff>0].sum()),lost_hits_on_known=int(-diff[diff<0].sum()),scope='exact float64 static scores; only predicted sets inside labeled C8; selection-biased subset; no new NSG calls'))
dump(O/'results/teacher_diagnostics.json',dict(groups=records,model_labeled_subset=model_rows,physical_search_calls=0,posthoc_after_training_and_development=True,caveat='C8 membership conditions on predictions; subset results do not estimate all-fit or HNSW performance'))
for name,rows in [('teacher_groups',records),('fit_labeled_subset',model_rows)]:
 with (O/'results'/f'{name}.csv').open('w') as f:
  writer=csv.DictWriter(f,rows[0].keys());writer.writeheader();writer.writerows(rows)
print(json.dumps(dict(groups=records,physical_search_calls=0)))
