from shared import *
import ast
threads(8)
for name in ['inputs','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
resources();assert not (O/'config.locked.json').exists();check(E50/'reviews/final_artifact_freeze.json');assert read(E50/'reviews/final_audit.json')['status']=='PASS'
freeze(O/'reviews/protected.json',[Path(x['path']) for x in read(E50/'reviews/protected.json')['files']]+files(E50))
shutil.copy2(E49/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json');check(O/'reviews/native_dependencies.json')
shutil.copy2(E46/'bin/environment.so',O/'bin/environment.so');assert sha(O/'bin/environment.so')==sha(E46/'bin/environment.so')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/39_candidate_commit_diagnosis.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
contexts=[]
def patched(cur,t,prefix,route):
 out={k:cur[k].copy() for k in FIELDS+['hits']};out['route_ndc']=route;rows=t[prefix+'rows']
 for k in ['ids','distances','entries','graph_ndc','hits']:out[k][rows]=t[prefix+k]
 return out
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir();c=read(E37/'inputs'/ds/'config.json');c.update(native_call_cap=20000,native_hnsw_cap=600000);dump(inp/'config.json',c)
 p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16);scale=np.load(E47/'inputs'/ds/'local_parameters.npz')['scale'];hubs=np.fromfile(c['hub_ids'],np.int32)
 for seed in SEEDS:
  src=E47/'models'/ds/f'rl_{seed}'
  for st in STEPS:
   prev=((st-1)//20)*20;cp=src/'checkpoints'/f'{prev:04}.npz';cc=dict(np.load(cp));w=cc['W'].copy();cur={k:cc[k][:4096].copy() for k in FIELDS+['hits']}
   for k in range(prev+1,st):
    t=dict(np.load(src/'trajectory'/f'{k:04}.npz'));assert raw_digest(cur)==str(t['current_cache_sha']);cur=patched(cur,t,'mean_',t['mean_route_ndc']);w[int(t['slot'])]=t['next_row'];assert raw_digest(cur)==str(t['mean_cache_sha'])
   tp=src/'trajectory'/f'{st:04}.npz';t=dict(np.load(tp));slot=int(t['slot']);assert raw_digest(cur)==str(t['current_cache_sha']) and w[slot].tobytes()==t['current_row'].tobytes()
   mean=patched(cur,t,'mean_',t['mean_route_ndc']);best=max(range(9),key=lambda i:(0. if i==0 else float(t['rewards'][i-1]),-i));bestout=cur if best==0 else patched(cur,t,f'a{best-1}_',t['route_ndc'][best-1])
   radius=float(np.median(np.linalg.norm(t['actions']-t['mu_before'],axis=1)));direction=t['mu_after']-t['mu_before'];norm=float(np.linalg.norm(direction));d=direction/norm if norm else np.zeros(16)
   bd=np.zeros(16) if best==0 else t['actions'][best-1]-t['mu_before'];coeff=[];rows=[];unclipped=[]
   for tag,z in [(f'D{f}',t['mu_before']+factor*radius*d) for f,factor in [(25,.25),(50,.5),(100,1.)]]+[(f'B{f}',t['mu_before']+factor*bd) for f,factor in [(25,.25),(50,.5)]]:
    zz=np.clip(z,-2,2);coeff.append(zz);unclipped.append(z);rows.append(row_profile(p[slot],b,scale[slot],zz))
   for a in range(8):
    ww=w.copy();ww[slot]=t['candidate_rows'][a];assert digest(ww)==str(t['W_sha'][a])
   wp=inp/f'{seed}_{st:04}_current.f32';w.tofile(wp);context=inp/f'{seed}_{st:04}_context.npz'
   save(context,coeff=np.stack(coeff),unclipped=np.stack(unclipped),proposed_rows=np.stack(rows),radius=np.array(radius),mu_before=t['mu_before'],mu_after=t['mu_after'],candidate_actions=t['actions'],best_action=np.array(best-1),
    **{'current_'+k:x for k,x in cur.items()},**{'mean_'+k:x for k,x in mean.items()},**{'best_'+k:x for k,x in bestout.items()})
   contexts.append(dict(dataset=ds,seed=seed,step=st,slot=slot,hub=int(hubs[slot]),current_W=str(wp),current_W_sha=digest(w),context=str(context),trajectory=str(tp),checkpoint=str(cp),
    current_topology_sha=str(t['current_topology_sha']),mean_topology_sha=str(t['mean_topology_sha']),mean_W_sha=str(t['mean_W_sha']),best_action=best-1,radius=radius,
    tags=['D25','D50','D100','B25','B50'],proposed_W_sha=[digest(np.concatenate([w[:slot],row[None,:],w[slot+1:]])) for row in rows]))
dump(O/'inputs/contexts.json',contexts)
dump(O/'config.locked.json',dict(datasets=DS,seeds=SEEDS,steps=STEPS,arm='rl',contexts=40,states=280,new_counterfactuals=200,ordinary_builds=280,HNSW_calls=1148672,physical_graphs=56,parity_NSG=2688,
 NSG_hard_cap=40000,per_dataset_reservation=20000,optimizer_updates=0,threads=1,latest_launch=LATEST_LAUNCH,query_stop=QUERY_STOP))
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'bin')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_UPDATE_DIRECTION_RADIUS',NSG_calls=0));print('E51 all 40 C/mean/candidate identities recovered; frozen',flush=True)
