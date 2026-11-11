from common import *
import gzip,collections
t=time.perf_counter();allfeatures=[];roles=[];associations=[];receipts=[]
def rank(a):
    a=np.asarray(a);o=np.argsort(a,kind='stable');r=np.empty(len(a),float);i=0
    while i<len(a):
        j=i+1
        while j<len(a) and a[o[i]]==a[o[j]]:j+=1
        r[o[i:j]]=(i+j-1)/2;i=j
    return r
def corr(a,b):return float(np.corrcoef(a,b)[0,1]) if len(a)>1 and np.std(a)>0 and np.std(b)>0 else ''
for ds in DS:
    c=read(OLD/'configs'/f'{ds}.json');base=view(c['base']);rng=np.random.default_rng(19520261103);background=rng.choice(len(base),8192,False);random=rng.choice(len(base),1024,False);ids=set(map(int,random));pr=[];dsroles=[]
    for x in random:dsroles.append(dict(dataset=ds,window='pooled',query=-1,role='random',target=int(x)))
    for w in ['A','B']:
        conf=read(R/'configs'/f'{ds}.{w}.json');out=Path(conf['output_dir']);g=np.fromfile(conf['test_gt']['path'],'<i4').reshape(-1,100);n=len(g);returned=np.fromfile(out/'k100/GT10_L200/raw/ids.i32','<i4').reshape(n,100)
        with gzip.open(out/'single_seed.csv.gz','rt') as f:
            for a in csv.DictReader(f):
                a=dict(a,window=w);pr.append(a);ids.add(int(a['seed']))
        for i in range(64):
            rr=set(map(int,returned[i]));found=[int(x) for x in g[i] if int(x) in rr][:8];miss=[int(x) for x in g[i] if int(x) not in rr][:8]
            for label,values in [('GT_found',found),('GT_missing',miss)]:
                for x in values:ids.add(x);dsroles.append(dict(dataset=ds,window=w,query=i,role=label,target=x))
        counts=collections.Counter()
        with gzip.open(out/'C_nodes.csv.gz','rt') as f:
            for a in csv.DictReader(f):
                if int(a['K'])!=100 or int(a['L'])!=200 or int(a['query'])>=64:continue
                role='C_GT' if a['is_GT']=='1' else 'C_nonGT';key=int(a['query']),role
                if counts[key]>=8:continue
                counts[key]+=1;x=int(a['target']);ids.add(x);dsroles.append(dict(dataset=ds,window=w,query=int(a['query']),role=role,target=x))
    ids=np.array(sorted(ids),dtype='<i4');B=np.asarray(base[background],dtype=np.float64);normb=np.einsum('ij,ij->i',B,B);rows=[];lookup={}
    for start in range(0,len(ids),128):
        sel=ids[start:start+128];X=np.asarray(base[sel],dtype=np.float64);normx=np.einsum('ij,ij->i',X,X);D=normx[:,None]+normb[None,:]-2*(X@B.T);D=np.maximum(D,0)
        for j,id in enumerate(sel):D[j,background==id]=np.inf
        near=np.partition(D,7,axis=1)[:,:8]
        for j,id in enumerate(sel):
            a=dict(dataset=ds,target=int(id),r8=float(np.sqrt(near[j].max())),mean_first8_radius=float(np.sqrt(near[j]).mean()),norm=float(np.sqrt(normx[j])),metric=c['metric_id'],definition='original-coordinate Euclidean to fixed8192 background; raw-IP is geometry proxy only');rows.append(a);lookup[int(id)]=a
        if start==0:
            # Independent direct coordinate subtraction checks full background on eight fixed nodes.
            for j in range(min(8,len(sel))):
                direct=np.square(B-X[j]).sum(1);direct[background==sel[j]]=np.inf;expect=np.sqrt(np.partition(direct,7)[7]);assert np.isclose(expect,lookup[int(sel[j])]['r8'],rtol=1e-9,atol=1e-7)
    for w in ['A','B']:
        for K in [1,100]:
            pp=[a for a in pr if a['window']==w and int(a['K'])==K];y=np.array([int(a['net_vs_B32']) for a in pp]);groups=collections.defaultdict(list)
            for i,a in enumerate(pp):groups[int(a['query'])].append(i)
            for feature in ['r8','norm']:
                x=np.array([lookup[int(a['seed'])][feature] for a in pp]);xx=x.copy();yy=y.astype(float)
                for ix in groups.values():xx[ix]-=xx[ix].mean();yy[ix]-=yy[ix].mean()
                associations.append(dict(dataset=ds,window=w,K=K,feature=feature,probes=len(pp),spearman=corr(rank(x),rank(y)),within_query_centered_pearson=corr(xx,yy)))
    np.asarray(background,dtype='<i4').tofile(R/f'analysis/{ds}.geometry_background.i32');allfeatures+=rows;roles+=dsroles;receipts.append(dict(dataset=ds,nodes=len(rows),background=8192,roles=len(dsroles),source=ident(c['base']['path'],False)))
    print('GEOMETRY',ds,len(rows),flush=True)
csvwrite(R/'analysis/node_geometry.csv',allfeatures);csvwrite(R/'analysis/geometry_roles.csv',roles);csvwrite(R/'analysis/geometry_seed_associations.csv',associations)
summary=[];byid={(x['dataset'],x['target']):x for x in allfeatures};group=collections.defaultdict(list)
for a in roles:group[a['dataset'],a['window'],a['role']].append(byid[a['dataset'],a['target']])
for (ds,w,role),aa in group.items():summary.append(dict(dataset=ds,window=w,role=role,incidences=len(aa),unique_nodes=len(set(x['target'] for x in aa)),mean_r8=float(np.mean([x['r8'] for x in aa])),median_r8=float(np.median([x['r8'] for x in aa])),mean_norm=float(np.mean([x['norm'] for x in aa]))))
csvwrite(R/'analysis/geometry_role_summary.csv',summary);dump(R/'analysis/geometry_receipt.json',dict(status='PASS_OFFLINE_GEOMETRY_PROXY_AND_DIRECT_DISTANCE_CHECKS',seconds=time.perf_counter()-t,background_seed=19520261103,datasets=receipts,raw_IP_task_metric_unchanged=True,no_new_performance=True,protocol_sha=sha(R/'geometry_protocol.md')))
