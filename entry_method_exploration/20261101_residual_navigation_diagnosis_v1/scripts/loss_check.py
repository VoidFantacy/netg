from common import *
t=time.perf_counter();points=list(csv.DictReader((R/'analysis/points.csv').open()));cases=[];summaries=[]
for ds in DS:
    c=read(OLD/'configs'/f'{ds}.json');base=view(c['base']);p=c['table'];data=Path(p).read_bytes();import struct
    hd=struct.unpack_from('<8I',data,8);H,b=hd[1:3];labels=np.frombuffer(data,'<i4',H,40);counts=np.frombuffer(data,'u1',H,40+H*4);tab=np.frombuffer(data,'<i4',H*b,40+H*5).reshape(H,b);table={int(h):set(map(int,tab[j,:counts[j]])) for j,h in enumerate(labels)}
    for w in ['A','B']:
        conf=read(R/'configs'/f'{ds}.{w}.json');q=view(conf['queries']);G=np.fromfile(conf['test_gt']['path'],'<i4').reshape(-1,100);n=len(G);root=Path(conf['output_dir']);cache={}
        def ids(K,L,m):
            key=K,L,m
            if key not in cache:cache[key]=np.fromfile(root/f'k{K}/{m}_L{L}/raw/ids.i32','<i4').reshape(n,K)
            return cache[key]
        for a in [x for x in points if x['dataset']==ds and x['window']==w]:
            K,L,m=int(a['K']),int(a['L']),a['method'];final=ids(K,L,m);targets=[]
            if int(a['lost_vs_GT']) or int(a['lost_vs_B32']):
                for i in range(n):
                    gs=set(map(int,G[i,:K]));ff=set(map(int,final[i]));lost=((set(map(int,ids(K,L,'GT10')[i]))|set(map(int,ids(K,L,'B32')[i])))&gs)-ff
                    for target in lost:targets.append((i,target,'actual_member_loss_vs_GT_or_B32'))
            if m=='B32' and L in [100,200,400]:
                main=ids(K,L,'GT10');route=np.fromfile(root/f'k{K}/GT10_L{L}/raw/entry_ids.i32','<i4').reshape(n,3)
                for i in range(n):
                    missing=set(map(int,G[i,:K]))-set(map(int,main[i]));selected=missing&set.union(*(table[int(h)] for h in route[i]));blocked=selected-set(map(int,final[i]))
                    for target in blocked:targets.append((i,target,'selected_C_correct_not_final'))
            unique={};
            for i,target,role in targets:unique.setdefault((i,target),set()).add(role)
            for (i,target),role in unique.items():
                v=np.asarray(base[final[i]],dtype='<f4');targetv=np.asarray(base[target],dtype='<f4');same=np.flatnonzero((v.view('<u4')==targetv.view('<u4')).all(1));x=np.asarray(q[i],dtype=np.float64);tv=targetv.astype(np.float64);last=v[-1].astype(np.float64)
                score=lambda z:float(np.square(x-z).sum()) if c['metric_id']==1 else -float(x@z)
                st,sw=score(tv),score(last);cases.append(dict(dataset=ds,window=w,K=K,L=L,method=m,query=i,target=target,role=';'.join(sorted(role)),identical_returned_ids=';'.join(str(int(final[i,j])) for j in same),target_score64=st,worst_score64=sw,score_difference64=st-sw,near_boundary=abs(st-sw)<=5e-5+3e-6*abs(sw)))
            summaries.append(dict(dataset=ds,window=w,K=K,L=L,method=m,checked_unique_loss_or_blocked_events=len(unique),identical_vector_events=sum(bool(x['identical_returned_ids']) for x in cases if x['dataset']==ds and x['window']==w and x['K']==K and x['L']==L and x['method']==m)))
if cases:csvwrite(R/'analysis/loss_cases.csv',cases)
else:(R/'analysis/loss_cases.csv').write_text('dataset,window,K,L,method,query,target,role,identical_returned_ids,target_score64,worst_score64,score_difference64,near_boundary\n')
csvwrite(R/'analysis/loss_summary.csv',summaries);dump(R/'analysis/loss_receipt.json',dict(status='PASS_ACTUAL_LOSS_AND_C_BLOCKED_CASE_DIAGNOSIS',events=len(cases),identical_vector_events=sum(bool(x['identical_returned_ids']) for x in cases),seconds=time.perf_counter()-t,GT_or_tie_changed=False,scope='actual losses vs GT/B32 plus selected-C nonreturn; not every SQ shortlist loss'))
