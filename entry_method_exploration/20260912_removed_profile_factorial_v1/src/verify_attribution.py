from shared import *
threads(8);resources()
diagnosis=read(O/'results/diagnosis.json');out=[];metrics_checked=0;credit_checked=0
with (O/'results/credit.csv').open() as f:credit=list(csv.DictReader(f))
for ds in DS:
 c=cfg(ds);ca=case(ds);rows=np.load(O/'inputs'/ds/'rows.npz')['rows']
 raw={cell:dict(np.load(O/'results'/ds/(cell+'.npz'))) for cell in CELLS}
 derived=dict(np.load(O/'results'/ds/'derived.npz'));h=derived['hits'];u=derived['U']
 for cell in ['C','F']:equal(raw[cell],dict(np.load(E41/'results'/ds/(cell+'.npz'))))
 source=np.fromfile(c['row_ids'],np.int64)
 old_case=next(x for x in read(E40/'results/attribution_cases.json')['cases'] if x['dataset']==ds)
 assert ca['observations']==old_case['observations'] and ca['original_added_hub']==old_case['hub']
 drift=[]
 for j,cell in enumerate(CELLS):
  m=next(x for x in diagnosis['metrics'] if x['dataset']==ds and x['cell']==cell);delta=h[j]-h[0]
  assert m['helped_queries']==sum(int(v)>0 for v in delta)
  assert m['harmed_queries']==sum(int(v)<0 for v in delta)
  assert m['failure_queries']==sum(int(v)==0 for v in h[j])
  assert m['rescued_zero']==sum(int(a)==0 and int(b)>0 for a,b in zip(h[0],h[j]))
  assert m['new_zero']==sum(int(a)>0 and int(b)==0 for a,b in zip(h[0],h[j]))
  assert m['changed_entry_queries']==sum(tuple(a)!=tuple(b) for a,b in zip(raw['C']['entries'],raw[cell]['entries']))
  route=sum(map(int,raw[cell]['route_ndc']))/1024;graph=sum(map(int,raw[cell]['graph_ndc']))/1024
  assert m['route_NDC']==route and m['graph_NDC']==graph and m['total_NDC']==route+graph
  drift.append(m['drift']);metrics_checked+=1
 # Explicitly check all three credit channels, not just hit-count conservation.
 records=[r for r in credit if r['dataset']==ds];assert len(records)==1024
 for i,rec in enumerate(records):
  assert int(rec['row'])==int(rows[i])
  for label,values in [('hits',h[:,i]),('utility',u[:,i]),('reward',u[:,i]-drift)]:
   vc,vf,vs,vr=map(float,values)
   expect=dict(alone=vs-vc,conditional=vf-vr,target=(vs-vc+vf-vr)/2,
      rest=(vr-vc+vf-vs)/2,interaction=vf-vs-vr+vc)
   for key,val in expect.items():assert abs(float(rec[label+'_'+key])-val)<1e-12
   assert abs(float(rec[label+'_target'])+float(rec[label+'_rest'])-(vf-vc))<1e-12
  credit_checked+=1
 obs=next(x for x in ca['observations'] if int(x['delta_hits'])<0);i=int(obs['qi'])
 assert int(rows[i])==int(obs['row']) and int(source[rows[i]])==int(obs['source_row_id'])
 hc,hf,hs,hr=map(int,h[:,i]);assert hc>hf
 out.append(dict(dataset=ds,negative_row=int(rows[i]),target_hub=ca['hub'],
   hits=dict(zip(CELLS,[hc,hf,hs,hr])),entries={cell:list(map(int,raw[cell]['entries'][i])) for cell in CELLS},
   target_row_change_sufficient=hs<=hf,target_row_change_necessary_in_full_background=hr>=hc,
   target_marginal_alone=hs-hc,target_marginal_with_rest=hf-hr,interaction=hf-hs-hr+hc,
   target_removed_in_S=ca['hub'] not in raw['S']['entries'][i],
   target_removed_in_R=ca['hub'] not in raw['R']['entries'][i],
   S_C_same_output_bits=all(raw['S'][k][i].tobytes()==raw['C'][k][i].tobytes() for k in ['ids','distances','graph_ndc']),
   E41_target_control='different partition; not a conflicting replication',
   R_minus_F_changed_hits=[dict(row=int(rows[k]),C=int(h[0,k]),F=int(h[1,k]),S=int(h[2,k]),R=int(h[3,k])) for k in range(1024) if h[3,k]!=h[1,k]],
   R_preserves_all_F_gains=all(int(h[3,k])==int(h[1,k]) for k in range(1024) if h[1,k]>h[0,k]),
   R_never_worse_than_F=bool(np.all(h[3]>=h[1]))))
assert metrics_checked==8 and credit_checked==2048
dump(O/'reviews/attribution_verification.json',dict(status='PASS',metrics_checked=metrics_checked,
 credit_queries_all_three_channels=credit_checked,E41_CF_regression=4096,cases=out,new_search=0))
print(json.dumps(out,ensure_ascii=False,indent=2))
