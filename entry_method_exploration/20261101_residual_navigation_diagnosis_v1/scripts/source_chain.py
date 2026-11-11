from common import *
import collections,gzip,struct
t=time.perf_counter();summary=[];perquery=[];novelty=[];provenance=[]
points=list(csv.DictReader((R/'analysis/points.csv').open()))
for ds in DS:
    c=read(OLD/'configs'/f'{ds}.json');source=Path(c['source_dir']);global_ids=set(map(int,np.fromfile(source/'global_ids.i32','<i4')));hubids=np.fromfile(c['router']['ids'],'<i4');off=np.fromfile(source/'hub_offsets.u64','<u8');targets=np.fromfile(source/'hub_targets.i32','<i4');hubs={int(label):set(map(int,targets[off[j]:off[j+1]])) for j,label in enumerate(hubids)}
    provenance += [ident(source/name) for name in ['global_ids.i32','hub_offsets.u64','hub_targets.i32']] + [ident(c['train_gt']['path'])]
    train=set(map(int,np.asarray(gt(c['train_gt'])).reshape(-1)));assert global_ids<=train
    data=Path(c['table']).read_bytes();head=struct.unpack_from('<8I',data,8);H,b=head[1:3];labels=np.frombuffer(data,'<i4',H,40);counts=np.frombuffer(data,'u1',H,40+H*4);table=np.frombuffer(data,'<i4',H*b,40+H*5).reshape(H,b);rows={int(label):set(map(int,table[j,:counts[j]])) for j,label in enumerate(labels)}
    for w in ['A','B']:
        conf=read(R/'configs'/f'{ds}.{w}.json');root=Path(conf['output_dir']);G=np.fromfile(conf['test_gt']['path'],'<i4').reshape(-1,100);n=len(G)
        for K in [1,100]:
            for L in [100,200,400]:
                main=np.fromfile(root/f'k{K}/GT10_L{L}/raw/ids.i32','<i4').reshape(n,K);final=np.fromfile(root/f'k{K}/B32_L{L}/raw/ids.i32','<i4').reshape(n,K);route=np.fromfile(root/f'k{K}/GT10_L{L}/raw/entry_ids.i32','<i4').reshape(n,3);total=collections.Counter()
                for i in range(n):
                    gs=set(map(int,G[i,:K]));rs=set(map(int,main[i]));fs=set(map(int,final[i]));missing=gs-rs;labels=list(map(int,route[i]));insource=missing&global_ids;routed={x for x in missing if any(x in hubs[h] for h in labels)};selected={x for x in missing if any(x in rows[h] for h in labels)};rescued=missing&fs;lost=(gs&rs)-fs
                    assert rescued<=selected<=routed<=insource<=missing
                    a=dict(missing=len(missing),in_train_GT=len(missing&train),global_source=len(insource),routed_source=len(routed),C_selected=len(selected),B32_rescued=len(rescued),B32_lost=len(lost),source_lost=len(missing-insource),route_lost=len(insource-routed),capacity_lost=len(routed-selected),merge_lost=len(selected-rescued));total.update(a);perquery.append(dict(dataset=ds,window=w,K=K,L=L,query=i,**a))
                summary.append(dict(dataset=ds,window=w,K=K,L=L,n=n,**dict(total)))
    for w in ['A','B']:
        conf=read(R/'configs'/f'{ds}.{w}.json');root=Path(conf['output_dir']);G=np.fromfile(conf['test_gt']['path'],'<i4').reshape(-1,100);n=len(G);cache={}
        for point in [a for a in points if a['dataset']==ds and a['window']==w]:
            K,L=int(point['K']),int(point['L']);method=point['method'];key=K,L
            if key not in cache:cache[key]=np.fromfile(root/f'k{K}/GT10_L{L}/raw/ids.i32','<i4').reshape(n,K)
            main=cache[key];final=np.fromfile(root/f'k{K}/{method}_L{L}/raw/ids.i32','<i4').reshape(n,K);tot=collections.Counter()
            for i in range(n):
                gs=set(map(int,G[i,:K]));missing=gs-set(map(int,main[i]));rescued=missing&set(map(int,final[i]));outside=rescued-global_ids
                tot.update(rescued=len(rescued),rescued_outside_residual_source=len(outside),rescued_outside_train_GT=len(rescued-train),queries_with_source_outside_rescue=bool(outside),queries_global_source_covers_no_missing_and_rescued=not(missing&global_ids) and bool(rescued))
            assert tot['rescued']==int(point['rescued_vs_GT'])
            if method in ['B32','OPT-B32']:assert tot['rescued_outside_residual_source']==0
            novelty.append(dict(dataset=ds,window=w,K=K,L=L,method=method,n=n,**dict(tot)))
    print('SOURCE_CHAIN',ds,len(global_ids),flush=True)
dump(R/'analysis/source_chain_inputs.json',dict(files=provenance))
csvwrite(R/'analysis/source_chain.csv',summary)
csvwrite(R/'analysis/rescue_source_novelty.csv',novelty)
with gzip.open(R/'analysis/query_source_chain.csv.gz','wt') as f:
    ww=csv.DictWriter(f,list(perquery[0]));ww.writeheader();ww.writerows(perquery)
dump(R/'analysis/source_chain_receipt.json',dict(status='PASS_EXACT_SET_CONTAINMENT_AND_FIXED_SOURCE_CHAIN',rows=len(perquery),summary_rows=len(summary),seconds=time.perf_counter()-t,scope='same new public windows; no new ANN, model, GT or performance'))
