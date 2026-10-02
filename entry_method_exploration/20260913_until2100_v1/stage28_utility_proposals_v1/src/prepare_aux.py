from common import *
threads();resources();assert read(O/'reviews/training_verification.json')['status']=='PASS';assert read(O/'reviews/proposals_independent.json')['status']=='PASS';check(O/'reviews/pretraining_freeze.json');paths=[Path(x['path']) for x in read(O/'reviews/pretraining_freeze.json')['files']]
for di,ds in enumerate(DS):
 old=read(E73/'inputs'/ds/'aux.json');geometric=read(E84/'models'/ds/'shortcut10/model.json');geometric.update(name='geometric10_L128',model_name='geometric10')
 previous=read(E86/'models'/ds/'utility10/model.json');previous.update(name='previous10_L128',model_name='previous10')
 models=[dict(m) for m in old['methods'] if m['model_name'] in ['baseline10','compact10']]+[geometric,previous]+[read(O/'models'/ds/m/'model.json') for m in ['utility10','neighbor10']];assert len(models)==6
 for split,n in [('preflight',128),('aux',7952)]:
  cfg=dict(old,methods=models,split='E87_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=6*(2*n+16),timing_repeats=0);dump(O/'inputs'/ds/(split+'.json'),cfg)
 for m in models:
  paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
 paths += [Path(old[k]) for k in ['queries_file','gt_file','row_ids']]
paths+=list((O/'models').rglob('*'))+list((O/'inputs').rglob('*.json'))+list((O/'results').rglob('*'))+list((O/'src').glob('*'))+[O/'reviews/training_verification.json',O/'reviews/proposal_verification.json',O/'reviews/proposals_independent.json']
freeze(O/'reviews/prequery_freeze.json',[p for p in paths if p.is_file()]);jobs=read(O/'logs/training_jobs.json');dump(O/'state.json',dict(status='TRAINING_VERIFIED_MODELS_FROZEN_AUX_PENDING',NSG=sum(j['actual_NSG'] for j in jobs),HNSW=sum(j['actual_HNSW'] for j in jobs),day_goal_complete=False));print('E87_FROZEN_READY_AUX')
