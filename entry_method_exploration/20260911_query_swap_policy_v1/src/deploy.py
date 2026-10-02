from model import *
assert read(O/'state.json')['status']=='TRAINING_VERIFIED_DEPLOYMENT_PENDING';check(O/'reviews/models_after_training.json');resources()
freeze(O/'reviews/deployment_implementation.json',[O/'src/runner_v2.cpp',O/'bin/runner_v2',O/'bin/build_v2.json',Path(__file__)])
all_points=[];checks=[];source_records=[]
def run(name,cfg,out,cap):
 resources();reserve(name,cap);t=time.time();peak=0;nt=0
 with (O/'logs'/(name+'.log')).open('x') as f:
  p=subprocess.Popen([str(O/'bin/runner_v2'),str(cfg),str(out)],env=env(),stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   try:
    a=dict(line.split(':',1) for line in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in line);peak=max(peak,int(a.get('VmRSS','0 kB').split()[0]));nt=max(nt,int(a['Threads']))
   except FileNotFoundError:pass
   if time.time()-t>1200 or peak>40*(1<<20) or nt>1:p.kill();p.wait();raise RuntimeError('resource stop '+name)
   time.sleep(.1)
 assert p.returncode==0,'see log '+name
 done=read(out/'complete.json');finish(name,done['NSG_calls'],HNSW_calls=done['HNSW_calls'],seconds=time.time()-t,peak_RSS_KiB=peak,peak_threads=nt);print('DEPLOY_COMPLETE',name,time.time()-t,flush=True)
def methods(ds,include_controls=True):
 out=[dict(name='base',kind='base'),dict(name='random',kind='random')] if include_controls else []
 for arm in ARMS:
  for seed in SEEDS:out.append(dict(name=f'{arm}_{seed}',kind='model',arm=arm,seed=seed,model=str(O/'models'/ds/f'{arm}_{seed}/selected/model.json')))
 return out
def prepare(ds,split,wall=False,selected=None):
 base=read(O/'inputs'/ds/'config.json');dest=O/'inputs'/ds/split;dest.mkdir();n=64 if split=='fit_check' else 512
 if split=='fit_check':source=O/'inputs'/ds;old=dict(queries_file=str(source/'queries.f32'),gt_file=str(source/'gt.i64'),row_ids=str(source/'row_ids.i64'));source_n=2048
 else:
  source=E24/'inputs'/ds/split;old=read(source/'config.json');source_n=old['num_queries'];assert old['index_path']==base['index_path'] and sha(old['hub_ids'])==sha(base['hub_ids'])
 for key,dt,shape,name in [('queries_file',np.float32,(source_n,base['dim']),'queries.f32'),('gt_file',np.int64,(source_n,100),'gt.i64'),('row_ids',np.int64,(source_n,),'row_ids.i64')]:
  a=np.memmap(old[key],dt,'r',shape=shape);a[:n].tofile(dest/name);source_records.append(identity(old[key]))
 rows=np.fromfile(dest/'row_ids.i64',np.int64);assert len(np.unique(rows))==n
 if split!='fit_check':assert not np.intersect1d(rows,np.fromfile(O/'inputs'/ds/'row_ids.i64',np.int64)).size
 if split=='audit':assert not np.intersect1d(rows,np.fromfile(O/'inputs'/ds/'cal/row_ids.i64',np.int64)).size
 c={**base,'mode':'evaluate','split':split,'num_queries':n,'queries_file':str(dest/'queries.f32'),'row_ids':str(dest/'row_ids.i64'),'gt_file':str(dest/'gt.i64'),'methods':methods(ds,split!='fit_check'),'measure_wall':False}
 dump(dest/'config.json',c);freeze(O/'reviews'/f'inputs_{split}_{ds}.json',list(dest.glob('*')));return c,dest/'config.json'
def raw_features(c,pool,pdist):
 n=c['num_queries'];d=c['dim'];h=c['hub_count'];q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(float);norm=np.linalg.norm(q,axis=1,keepdims=True);qp=(q/norm)@np.fromfile(c['projection'],np.float64).reshape(16,d).T;hp=np.fromfile(c['hub_projection'],np.float64).reshape(h,16);pairs=np.fromfile(c['pair_cosine'],np.float32).reshape(h,h);cos=(1-pdist.astype(float))/norm;features=np.empty((n,56,76),np.float32)
 for s,t in enumerate(TRIP):
  parts=[]
  for k in t:parts += [np.full((n,1),k/7),cos[:,k,None],(cos[:,k]-cos[:,0])[:,None],qp*hp[pool[:,k]]]
  for a,b in itertools.combinations(t,2):parts.append(pairs[pool[:,a],pool[:,b],None])
  parts.append(qp);features[:,s]=np.concatenate(parts,axis=1)
 return features.astype(float)
def random_path(rows):
 mask=(1<<64)-1
 def mix(x):
  x=(x+0x9e3779b97f4a7c15)&mask;x=((x^(x>>30))*0xbf58476d1ce4e5b9)&mask;x=((x^(x>>27))*0x94d049bb133111eb)&mask;return x^(x>>31)
 states=np.zeros((len(rows),4),np.uint8);actions=np.full((len(rows),3),-1,np.int8)
 for i,row in enumerate(rows):
  s=0;alive=True
  for step in range(3):
   if alive:
    a=mix(int(row)^2026091719^((step*0xd1b54a32d192ed03)&mask))%16;actions[i,step]=a;s=NEXT[s,a];alive=a!=0
   states[i,step+1]=s
 return states,actions
def load_method(folder,n):
 result={}
 for key,name,dt,shape in [('ids','ids.i32',np.int32,(n,10)),('distances','distances.f32',np.float32,(n,10)),('entries','entries.i32',np.int32,(n,3)),('pool','pool.i32',np.int32,(n,8)),('pool_distance','pool_distance.f32',np.float32,(n,8)),('states','states.i32',np.int32,(n,4)),('actions','actions.i32',np.int32,(n,3)),('lengths','lengths.i32',np.int32,(n,)),('route_ndc','route_ndc.u32',np.uint32,(n,)),('graph_ndc','graph_ndc.u32',np.uint32,(n,)),('scores','scores.f64',np.float64,(n,56))]:result[key]=np.fromfile(folder/name,dt).reshape(shape)
 return result
def analyze(c,out,phase):
 ds=c['dataset'];n=c['num_queries'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100);hubs=np.fromfile(c['hub_ids'],np.int32);rows=np.fromfile(c['row_ids'],np.int64);ix=np.arange(n)
 if phase=='fit_check':
  source=O/'results'/('labels_'+ds);labels=np.load(source/'scored.npz');basehits=labels['hits'][:n,0];basendc=labels['graph_ndc'][:n,0];baseroute=labels['route_ndc'][:n];baseentries=np.fromfile(source/'entries.i32',np.int32).reshape(2048,56,3)[:n,0]
  ids56=np.fromfile(source/'ids.i32',np.int32).reshape(2048,56,10)[:n];distance56=np.fromfile(source/'distances.f32',np.float32).reshape(2048,56,10)[:n]
 else:
  bb=load_method(out/'base',n);basehits=score(bb['ids'],gt);basendc=bb['graph_ndc'];baseroute=bb['route_ndc'];baseentries=bb['entries']
 timing={x['name']:x['timings'] for x in read(out/'methods.json')};points=[];first_pool=None;feature=None
 for m in c['methods']:
  o=load_method(out/m['name'],n);hits=score(o['ids'],gt);o['hits']=hits;total=o['route_ndc'].astype(float)+o['graph_ndc'];basetotal=baseroute.astype(float)+basendc;utility=hits.astype(float)-basehits-.1*(total/basetotal-1);o['utility']=utility
  assert (o['ids']>=0).all() and (o['ids']<(2505000 if ds==DS[0] else 10000000)).all() and (np.diff(np.sort(o['ids'],axis=1),axis=1)!=0).all() and (np.diff(o['entries'],axis=1)>0).all()
  score_error=0.
  if m['kind']!='base':
   if first_pool is None:first_pool=o['pool'];feature=raw_features(c,o['pool'],o['pool_distance'])
   else:assert np.array_equal(first_pool,o['pool'])
   assert np.array_equal(np.sort(hubs[o['pool'][:,:3]],axis=1),baseentries) and np.array_equal(o['route_ndc'],baseroute)
   if m['kind']=='model':
    f=numpy_forward(feature,read(m['model']));score_error=float(np.abs(f-o['scores']).max());assert score_error<2e-6,(ds,m['name'],score_error);ss,aa=greedy(f)
   else:ss,aa=random_path(rows)
   assert np.array_equal(ss,o['states']) and np.array_equal(aa,o['actions']) and np.array_equal((aa>=0).sum(axis=1),o['lengths'])
   final=ss[:,-1].astype(int);chosen=np.sort(hubs[o['pool'][ix[:,None],TRIP[final]]],axis=1);assert np.array_equal(chosen,o['entries'])
  if phase=='fit_check':
   final=o['states'][:,-1];assert np.array_equal(o['ids'],ids56[ix,final]) and np.array_equal(o['distances'],distance56[ix,final]) and np.array_equal(o['graph_ndc'],labels['graph_ndc'][:n][ix,final])
  if phase=='wall':
   previous=load_method(O/'results'/('audit_'+ds)/m['name'],n)
   for key in previous:assert np.array_equal(o[key],previous[key]),(ds,m['name'],key)
  dh=hits.astype(float)-basehits;qps=[x['QPS'] for x in timing[m['name']]]
  rec=dict(dataset=ds,phase=phase,method=m['name'],kind=m['kind'],queries=n,L=128,recall_pct=float(hits.mean()*10),delta_recall_pp=float(dh.mean()*10),failure_pct=float((hits==0).mean()*100),failure_delta_pp=float(((hits==0).astype(float)-(basehits==0)).mean()*100),
   helped=int((dh>0).sum()),harmed=int((dh<0).sum()),rescued=int(((basehits==0)&(hits>0)).sum()),new_failures=int(((basehits>0)&(hits==0)).sum()),utility=float(utility.mean()),
   route_ndc=float(o['route_ndc'].mean()),graph_ndc=float(o['graph_ndc'].mean()),total_ndc=float(total.mean()),total_NDC_change_pct=float((total.mean()/basetotal.mean()-1)*100),
   changed_queries=int((o['states'][:,-1]!=0).sum()),mean_swaps=float((o['actions']>0).sum(axis=1).mean()),first_stop_pct=float((o['actions'][:,0]==0).mean()*100) if m['kind']!='base' else 100.,
   QPS_median=float(np.median(qps)) if qps else None,QPS_min=min(qps) if qps else None,QPS_max=max(qps) if qps else None,timings=timing[m['name']],native_numpy_score_max_error=score_error)
  np.savez_compressed(out/m['name']/'scored.npz',hits=hits,utility=utility,delta_hits=dh,base_hits=basehits);points.append(rec);checks.append(dict(dataset=ds,phase=phase,method=m['name'],queries=n,status='PASS',native_numpy_score_max_error=score_error,cache_full_result_parity=phase=='fit_check',wall_audit_result_parity=phase=='wall'))
 dump(out/'points.json',points);all_points.extend(points);dump(O/'results/points.json',all_points);dump(O/'reviews/deployment_verification.json',dict(status='IN_PROGRESS',checks=checks));return points
for ds in DS:
 c,path=prepare(ds,'fit_check');out=O/'results'/('fit_check_'+ds);run('fit_check_'+ds,path,out,4*(2*64+16));analyze(c,out,'fit_check')
cal=[]
for ds in DS:
 c,path=prepare(ds,'cal');out=O/'results'/('cal_'+ds);run('cal_'+ds,path,out,6*(2*512+16));cal+=analyze(c,out,'cal')
selected={}
for ds in DS:
 selected[ds]={}
 for arm in ARMS:
  options=[x for x in cal if x['dataset']==ds and x['method'].startswith(arm+'_')];best=min(options,key=lambda z:(-z['utility'],z['total_ndc'],z['method']));selected[ds][arm]=best
dump(O/'results/cal_selection.json',selected);freeze(O/'reviews/before_audit.json',[O/'results/cal_selection.json']+[Path(m['model']) for ds in DS for m in methods(ds) if m['kind']=='model']+[p for ds in DS for p in (O/'results'/('cal_'+ds)).rglob('*') if p.is_file()]);print('CAL_SELECTION_FROZEN',selected,flush=True)
for ds in DS:
 c,path=prepare(ds,'audit');out=O/'results'/('audit_'+ds);run('audit_'+ds,path,out,6*(2*512+16));analyze(c,out,'audit')
for ds in DS:
 c=read(O/'inputs'/ds/'audit/config.json');names=['base',selected[ds]['rl']['method'],selected[ds]['exact']['method']];c['methods']=[m for m in c['methods'] if m['name'] in names];c['measure_wall']=True;c['split']='audit_wall';path=O/'inputs'/ds/'wall_config.json';dump(path,c)
 freeze(O/'reviews'/('before_wall_'+ds+'.json'),[path]+[Path(m['model']) for m in c['methods'] if m['kind']=='model']);out=O/'results'/('wall_'+ds);run('wall_'+ds,path,out,3*(8*512+16));analyze(c,out,'wall')
dump(O/'reviews/development_sources.json',dict(files=source_records));dump(O/'reviews/deployment_verification.json',dict(status='PASS',checks=checks));dump(O/'state.json',dict(status='DEVELOPMENT_AND_WALL_COMPLETE_ANALYSIS_PENDING',training_runs=8,optimizer_updates=24000,NSG_calls=sum(x['actual'] for x in read(O/'logs/jobs.json')),validation_read=False,heldout_read=False));print('DEVELOPMENT_AND_WALL_COMPLETE',flush=True)
