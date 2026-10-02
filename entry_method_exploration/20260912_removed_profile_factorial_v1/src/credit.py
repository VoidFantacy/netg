from shared import *
threads(8);resources();check(O/'reviews/prequery_freeze.json')
diagnosis=read(O/'results/diagnosis.json');records=[];summaries=[]
for ds in DS:
 d=dict(np.load(O/'results'/ds/'derived.npz'));h=d['hits'].astype(float);u=d['U'];rows=d['rows']
 drift=np.array([next(m['drift'] for m in diagnosis['metrics'] if m['dataset']==ds and m['cell']==cell) for cell in CELLS])
 j=u-drift[:,None];outputs={}
 for label,value in [('hits',h),('utility',u),('reward',j)]:
  c,f,s,r=value
  alone=s-c;conditional=f-r;rest_alone=r-c;rest_conditional=f-s
  target=(alone+conditional)/2;rest=(rest_alone+rest_conditional)/2
  np.testing.assert_allclose(target+rest,f-c,atol=1e-12,rtol=1e-12)
  outputs[label]=dict(alone=alone,conditional=conditional,target=target,rest=rest,interaction=f-s-r+c)
 for i,row in enumerate(rows):
  rec=dict(dataset=ds,row=int(row))
  for label,values in outputs.items():
   for key,value in values.items():rec[label+'_'+key]=float(value[i])
  records.append(rec)
 ca=case(ds);negative=next(x for x in ca['observations'] if int(x['delta_hits'])<0);ni=int(negative['qi'])
 result=dict(dataset=ds,target_hub=ca['hub'],negative_row=int(negative['row']),
    negative={label:{key:float(v[ni]) for key,v in values.items()} for label,values in outputs.items()},
    all_query={label:{key:float(v.mean()) for key,v in values.items()} for label,values in outputs.items()},
    nonzero_hit_interactions=[int(row) for row,iv in zip(rows,outputs['hits']['interaction']) if iv!=0])
 summaries.append(result)
writecsv('credit.csv',records)
dump(O/'results/credit.json',dict(status='COMPUTED_TWO_BLOCK_CONDITIONAL_CREDIT',datasets=summaries,
 interpretation='Two-background average is an accounting convention. Do not add credits across different partitions.',new_search=0,optimizer_updates=0))
# Independently check all exported rows by scalar arithmetic on the raw-scored arrays.
count=0
for rec in records:
 ds=rec['dataset'];d=dict(np.load(O/'results'/ds/'derived.npz')) if count%1024==0 else d
 i=int(np.flatnonzero(d['rows']==rec['row'])[0]);hc,hf,hs,hr=map(int,d['hits'][:,i])
 assert rec['hits_alone']==hs-hc and rec['hits_conditional']==hf-hr
 assert 2*rec['hits_target']==hs-hc+hf-hr and 2*rec['hits_rest']==hr-hc+hf-hs
 assert rec['hits_target']+rec['hits_rest']==hf-hc
 count+=1
assert count==2048
dump(O/'reviews/credit_verification.json',dict(status='PASS',queries=count,identities=['conditional_marginals','two_block_sum'],new_search=0))
print(json.dumps(summaries,ensure_ascii=False,indent=2))
