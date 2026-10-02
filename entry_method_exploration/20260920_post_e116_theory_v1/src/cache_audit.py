from pathlib import Path
import json,time,hashlib,csv
import numpy as np
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1];OLD=ROOT/'entry_method_exploration/20260920_entry_id_pilot_v1'
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def quant(x):
 x=np.asarray(x,float)
 return dict(n=len(x),min=float(x.min()),q25=float(np.quantile(x,.25)),median=float(np.median(x)),q75=float(np.quantile(x,.75)),max=float(x.max())) if len(x) else dict(n=0)
def effects(d):return dict(n=len(d),positive=int((d>0).sum()),negative=int((d<0).sum()),nonzero=int((d!=0).sum()),net=float(d.sum()),mean=float(d.mean()) if len(d) else None)
started=time.time();summary=[];selected_rows=[];overlap_rows=[];assets=[]
for ds,cfg in read(OLD/'config.locked.json')['datasets'].items():
 p=OLD/'results'/ds/'labels';m=np.fromfile(p/'meta.i32',np.int32).reshape(-1,4);h=np.fromfile(p/'hits.u16',np.uint16).reshape(-1,2).astype(np.int64);t=np.fromfile(p/'seconds.f64',np.float64).reshape(-1,2);work=np.fromfile(p/'ndc.u64',np.uint64).astype(np.int64);b=np.flatnonzero(m[:,1]<0);n=len(b);bi=b[m[:,0]];delta=h-h[bi];dt=t-t[bi];dw=work-work[bi];baseentry=np.fromfile(OLD/'results'/ds/'route_fit/entries.i32',np.int32).reshape(n,3)
 records=read(OLD/'models'/ds/'selection_details.json');bykey={(x['old_id'],x['new_id']):x for x in records};models=read(OLD/'models'/ds/'models.json');result=dict(dataset=ds,fit_queries=n,candidates=len(records),all_candidates={},models={})
 support=[];respond1=[];respond100=[];k1_zero=0
 for key in bykey:
  ix=np.flatnonzero((m[:,1]==key[0])&(m[:,2]==key[1]));support.append(len(ix));respond1.append(int((delta[ix,0]!=0).sum()));respond100.append(int((delta[ix,1]!=0).sum()));k1_zero+=int(not np.any(delta[ix,0]))
 result['all_candidates']=dict(support=quant(support),nonzero_r1_events=quant(respond1),nonzero_r100_events=quant(respond100),no_r1_effect_candidates=k1_zero)
 # This is a finite measured-action oracle, not a new model or prediction.
 oracle=[]
 for k in [0,1]:
  best=np.maximum.reduceat(delta[:,k],b);oracle.append(effects(best))
 result['fit_measured_action_oracle']=oracle
 for model in models:
  name=model['name'];edits=model['edits'];modelrows=[];chosen_ids={x[0] for x in edits};nedit_fit=np.isin(baseentry,list(chosen_ids)).sum(1)
  audit=OLD/'results'/ds/'audit';base_a=np.fromfile(audit/'GT10_K1_L128/entry_ids.i32',np.int32).reshape(-1,3);edit_a=np.fromfile(audit/f'{name}_K1_L128/entry_ids.i32',np.int32).reshape(-1,3);nedit_a=np.isin(base_a,list(chosen_ids)).sum(1);N=len(base_a)
  stored=read(OLD/'results/hits.json')[ds];ar=np.column_stack([np.array(stored[f'{name}_K{k}'])-np.array(stored[f'GT10_K{k}']) for k in [1,100]])
  assert np.array_equal(nedit_a>0,np.any(base_a!=edit_a,axis=1))
  for ecount in [0,1,2,3]:
   ix=nedit_a==ecount
   row=dict(dataset=ds,method=name,edits_in_query=ecount,n=int(ix.sum()),k1=effects(ar[ix,0]),k100=effects(ar[ix,1]));overlap_rows.append(row)
  for old,new in edits:
   ix=np.flatnonzero((m[:,1]==old)&(m[:,2]==new));folds=[];time_replicate_signs=[]
   for f in [0,1]:
    jj=ix[m[ix,3]==f];tm=dt[jj].mean(0);mean_tm=float(tm.mean());time_replicate_signs.extend((tm<=0).tolist());folds.append(dict(n=len(jj),r1=effects(delta[jj,0]),r100=effects(delta[jj,1]),mean_dt_seconds=float(tm.mean()),replicate_dt_seconds=tm.tolist(),mean_ndc_delta=float(dw[jj].mean())))
   singlefit=ix[nedit_fit[m[ix,0]]==1];singleaudit=(nedit_a==1)&np.any(base_a==old,axis=1)
   rec=dict(dataset=ds,method=name,old_id=old,new_id=new,fit_support=len(ix),fit_r1=effects(delta[ix,0]),fit_r100=effects(delta[ix,1]),folds=folds,all_four_timing_signs_nonpositive=all(time_replicate_signs),single_fit_n=len(singlefit),single_fit_r1=effects(delta[singlefit,0]),single_fit_r100=effects(delta[singlefit,1]),single_audit_n=int(singleaudit.sum()),single_audit_r1=effects(ar[singleaudit,0]),single_audit_r100=effects(ar[singleaudit,1]))
   modelrows.append(rec);selected_rows.append(rec)
  result['models'][name]=dict(edits=len(edits),fit_support=quant([x['fit_support'] for x in modelrows]),fit_r1_response=quant([x['fit_r1']['nonzero'] for x in modelrows]),fit_r100_response=quant([x['fit_r100']['nonzero'] for x in modelrows]),k1_zero_response_edits=sum(x['fit_r1']['nonzero']==0 for x in modelrows),four_negative_timing_signs=sum(x['all_four_timing_signs_nonpositive'] for x in modelrows),single_audit_r1_positive_edits=sum(x['single_audit_r1']['net']>0 for x in modelrows),single_audit_r1_negative_edits=sum(x['single_audit_r1']['net']<0 for x in modelrows),single_audit_r100_positive_edits=sum(x['single_audit_r100']['net']>0 for x in modelrows),single_audit_r100_negative_edits=sum(x['single_audit_r100']['net']<0 for x in modelrows),fit_multi_edit_queries=int((nedit_fit>1).sum()),audit_multi_edit_queries=int((nedit_a>1).sum()))
 summary.append(result)
 for f in [p/'meta.i32',p/'hits.u16',p/'seconds.f64',p/'ndc.u64',OLD/'models'/ds/'models.json']:
  assets.append(dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
dump(RUN/'results/summary.json',summary);dump(RUN/'results/selected_edit_details.json',selected_rows);dump(RUN/'results/audit_overlap.json',overlap_rows);dump(RUN/'reviews/analysis_complete.json',dict(status='PASS',seconds=time.time()-started,new_search=0,new_training=0,new_gt=0,posthoc_descriptive_only=True,assets=assets))
print(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(overlap_rows,ensure_ascii=False,indent=2))
