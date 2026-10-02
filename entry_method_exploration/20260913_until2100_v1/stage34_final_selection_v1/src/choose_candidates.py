from pathlib import Path
import sys,copy,time
import numpy as np
O=Path(__file__).resolve().parents[1];C=O.parent
sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import *
from scoring_v3 import raw,scores
from contracts_v3 import BINARY_SHA
# Imported common O refers to tooling; restore this independent run location.
O=Path(__file__).resolve().parents[1]
threads();assert not (O/'selection.json').exists()
old=read(C/'candidate_inventory_v11.json');inventory=copy.deepcopy(old);newmodel=read(C/'stage33_composed_repair_v1/models/model.json')
extra=dict(dataset=DS[0],name='E92_composed10',kind='new_method',selectable_for_final=True,zero_update_alias_of=None,configuration=newmodel,evaluator=identity(E73/'bin/evaluate'),development_configuration=identity(C/'stage33_composed_repair_v1/inputs/aux.json'),aligned_aux_raw=str(C/'stage33_composed_repair_v1/results/aux/composed10_L128'),source_protocol=identity(C/'stage33_composed_repair_v1/protocol.md'),historical_auxiliary_feedback_is_training=True,final_validation_access=False)
inventory['candidates'].append(extra);inventory['prior_inventory']=identity(C/'candidate_inventory_v11.json');inventory['final_selection']=False
assert inventory['candidates'][:76]==old['candidates'];dump(C/'candidate_inventory_v12.json',inventory)
prepared=[];excluded=[];paths=[O/'protocol.md',Path(__file__),C/'candidate_inventory_v12.json']+list((C/'stage32_final_tooling_v1/src').glob('*.py'))
for index,x in enumerate(inventory['candidates']):
 ds,name=x['dataset'],x['name']
 if name=='E62_C':reason='Matched P anchor; scored as baseline'
 elif x.get('zero_update_alias_of'):reason='Excluded: zero-update alias of '+x['zero_update_alias_of']
 elif x['kind'] not in ['new_method','candidate','width_candidate']:reason='Excluded: '+x['kind']+' is not a static main candidate'
 elif x.get('selectable_for_final') is False:reason='Excluded: catalog explicitly nonselectable; native deployment absent or control'
 else:reason='Eligible nonzero static main candidate with common full auxiliary response'
 if reason.startswith('Excluded'):
  excluded.append(dict(dataset=ds,name=name,catalog_index=index,eligible=False,reason=reason));continue
 if name.startswith('E62_') or name=='E63_zero_mass2':
  cp=C/'stage5_frozen_pool_aux_v1/inputs'/ds/'config.json';model={'E62_C':'baseline','E62_A':'E61_missing','E62_S':'E62_score','E62_T':'E62_topology','E63_zero_mass2':'E63_zero_mass'}[name];cfg=read(cp);m=next(m for m in cfg['methods'] if m['model_name']==model);rp=C/'stage5_frozen_pool_aux_v1/results'/ds/m['name']
 elif name=='E66_mode3P':
  cp=C/'stage7_multimode_index_v1/inputs'/ds/'aux.json';cfg=read(cp);m=next(m for m in cfg['methods'] if m['model_name']=='mode3P');rp=C/'stage7_multimode_index_v1/results'/ds/'aux'/m['name']
 elif name=='E70_mode3P30':
  cp=C/'stage11_width_control_v1/inputs'/ds/'aux.json';cfg=read(cp);m=next(m for m in cfg['methods'] if m['model_name']=='mode3P30');rp=C/'stage11_width_control_v1/results'/ds/'aux'/m['name']
 else:
  cp=Path(x['development_configuration']['path']);cfg=read(cp);m=x['configuration'];rp=Path(x.get('aligned_aux_raw') or str(cp.parents[2]/'results'/ds/'aux'/m['name']))
 assert cfg['num_queries']==7952 and cfg['gt_k']==100 and cfg['threads']==1 and cfg['query_cpu']==15 and m['L']==128
 assert rp.exists(),str(rp)
 prepared.append(dict(item=x,index=index,config=cfg,method=m,config_path=str(cp),raw_path=str(rp),anchor=name=='E62_C'))
 excluded.append(dict(dataset=ds,name=name,catalog_index=index,eligible=True,reason=reason))
 paths += [cp]+list(rp.glob('*'))+[Path(cfg[k]) for k in ['queries_file','gt_file','row_ids']]+[Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
freeze(O/'reviews/prescore_freeze.json',[p for p in paths if p.is_file()])
table(O/'results/eligibility.csv',excluded)
scored=[];selected={};nscore=0;configs={};basearrays={}
for ds in DS:
 group=[p for p in prepared if p['item']['dataset']==ds];base=next(p for p in group if p['anchor']);cfg=base['config'];baseids={k:sha(cfg[k]) for k in ['queries_file','gt_file','row_ids']};gt=np.fromfile(cfg['gt_file'],np.int64).reshape(7952,100);rows=np.fromfile(cfg['row_ids'],np.int64);assert np.array_equal(rows,np.arange(2048,10000));b=raw(base['raw_path']);scores(b,gt,cfg['base_count']);basearrays[ds]=b
 for p in group:
  x=p['item'];a=raw(p['raw_path']);assert all(sha(p['config'][k])==baseids[k] for k in baseids);assert p['config']['index_path']==cfg['index_path'];h=scores(a,gt,cfg['base_count']);nscore+=7952
  d=h.astype(int)-b['hits'];net=int(d.sum());half=[int(z.sum()) for z in np.split(d,2)];fail=int((h==0).sum());ndc=float((a['route_ndc'].astype(float)+a['graph_ndc']).mean());relative=ndc/float((b['route_ndc'].astype(float)+b['graph_ndc']).mean())-1
  gate=bool(net>0 and min(half)>=0 and fail<=int((b['hits']==0).sum()) and relative<=.01)
  rec=dict(dataset=ds,name=x['name'],catalog_index=p['index'],anchor=p['anchor'],net_hits=net,half1=half[0],half2=half[1],failure_count=fail,failure_delta=fail-int((b['hits']==0).sum()),total_NDC=ndc,total_NDC_relative=relative,development_gate_pass=gate,raw_path=p['raw_path'],config_path=p['config_path']);scored.append(rec);configs[ds,x['name']]=p['method']
 choices=[p for p in scored if p['dataset']==ds and not p['anchor']];passing=[p for p in choices if p['development_gate_pass']];ranking=sorted(passing or choices,key=lambda p:(-p['net_hits'],p['failure_count'],p['total_NDC'],p['catalog_index']));winner=ranking[0]
 for rank,p in enumerate(sorted(choices,key=lambda p:(-p['net_hits'],p['failure_count'],p['total_NDC'],p['catalog_index']))):p['overall_quality_rank']=rank+1
 selected[ds]=dict(best_new_inventory=winner['name'],best_all_inventory=winner['name'] if passing else 'E62_C',passing_count=len(passing),fallback_without_gate=not bool(passing),selection_score=winner,ranking_names=[p['name'] for p in ranking],tie_rule='net_hits descending; failure_count ascending; total_NDC ascending; original catalog index ascending')
 for p in choices:print(ds[:3],p['name'],p['net_hits'],p['failure_delta'],p['development_gate_pass'])
# All rows have uniform CSV keys.
for p in scored:p.setdefault('overall_quality_rank',0)
table(O/'results/candidate_score_table.csv',scored);dump(O/'results/selected.json',selected)
final_inventory=[]
for p in prepared:
 x=copy.deepcopy(p['item']);m=dict(p['method']);m.update(reference_graph=True);m.setdefault('ef_search',10);x['configuration']=m
 if x['name'] in ['E92_composed10','E73_compact10']:
  assert x['evaluator']['sha256']==BINARY_SHA
 # Other old binaries are kept explicitly; an actual selected mismatch stops below.
 final_inventory.append(x)
for ds,z in selected.items():
 chosen=next(x for x in final_inventory if x['dataset']==ds and x['name']==z['best_new_inventory']);assert chosen.get('evaluator',{}).get('sha256')==BINARY_SHA,('Compatibility audit required for selected candidate',ds,chosen['name'])
dump(O/'results/final_inventory.json',dict(status='ACTUAL_ELIGIBLE_CATALOG_WITH_ORIGINAL_BINARY_IDENTITIES',candidates=final_inventory,original_inventory=str(C/'candidate_inventory_v12.json')))
dump(O/'reviews/selection_verification.json',dict(status='PASS',independent_set_mask_rows=nscore,eligible_rows=len(scored),catalog_records=len(inventory['candidates']),excluded_records=len(excluded)-len(scored),final_payload_access=False,new_ANN=0,method_selection_feedback_role='historically exposed auxiliary training',selected=selected))
freeze(O/'reviews/selection_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file()]+[C/'candidate_inventory_v12.json'])
print('E93_SELECTED',selected)
