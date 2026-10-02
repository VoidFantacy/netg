"""Independent set scoring, immutable-action geometry, cache and rule verification."""
from shared import *
import csv, struct

threads(8);resources();check_freeze();started=time.monotonic()
assert all(read(O/'results'/ds/'query_complete.json')['status']=='PASS_NATIVE_FIXED_ACTION_REPLAY' for ds in DS)
points=[];states=[];summaries=[];scored=0;parity_rows=0;physical_graphs=0;new_patch_rows=0

def ihits(ids,gt):
    assert all(len(set(map(int,x)))==10 for x in ids)
    return np.array([len(set(map(int,x)) & set(map(int,g[:10]))) for x,g in zip(ids,gt)],np.int16)

def effects(h,h0):
    d=h.astype(int)-h0.astype(int)
    result=dict(gain_hits=int(d[d>0].sum()),loss_hits=int(-d[d<0].sum()),net_hits=int(d.sum()),
        helped_queries=int((d>0).sum()),harmed_queries=int((d<0).sum()),
        rescued=int(((h0==0)&(h>0)).sum()),new_failures=int(((h0>0)&(h==0)).sum()),
        quality_null=bool(not np.any(d)))
    assert result['gain_hits']-result['loss_hits']==result['net_hits']
    assert result['rescued']-result['new_failures']==int((h0==0).sum()-(h==0).sum())
    return result

def inspect_graph(path,W,mapping):
    data=path.read_bytes();fmt='<6QiI3QdQ';head=struct.unpack_from(fmt,data);start=struct.calcsize(fmt)
    off,mx,n,size,label,coord,maxlevel,entry,M,M0,m,mult,ef=head
    assert off==0 and mx==n==len(W) and M==m==16 and M0==32 and ef==200 and label-coord==W.shape[1]*4
    cursor=start+n*size;upper=[];levels=[]
    for i in range(n):
        count=struct.unpack_from('<I',data,cursor)[0];cursor+=4;assert count%(M*4+4)==0
        levels.append(count//(M*4+4));upper.append(data[cursor:cursor+count]);cursor+=count
    assert cursor==len(data) and max(levels)==maxlevel
    topo=[n,W.shape[1],entry,maxlevel]
    for i in range(n):
        row=start+i*size;lab=struct.unpack_from('<Q',data,row+label)[0]
        assert lab==int(mapping[i]) and data[row+coord:row+label]==W[i].tobytes()
        topo.extend([lab,levels[i]])
        blocks=[data[row:row+M0*4+4]]+[upper[i][j*(M*4+4):(j+1)*(M*4+4)] for j in range(levels[i])]
        for lev,block in enumerate(blocks):
            count=struct.unpack_from('<H',block)[0];assert count<=(M0 if lev==0 else M)
            adj=np.frombuffer(block,dtype='<u4',count=count,offset=4)
            assert (adj<n).all() and len(set(map(int,adj)))==count and i not in adj
            topo.append(count);topo.extend(map(int,adj))
    return digest(np.array(topo,np.int32))

for ds in DS:
    c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(2064,100)
    P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);B=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16)
    scale=np.load(E53/'inputs'/ds/'local_parameters.npz')['scale'];mapping=np.fromfile(c['hub_ids'],np.int32)
    dest=O/'results'/ds;anchor=dict(np.load(dest/'anchor/raw.npz'));base={k:v[:2048] for k,v in anchor.items()}
    assert np.array_equal(ihits(anchor['ids'],gt),anchor['hits']);scored+=2064
    ident=read(dest/'anchor/identity.json');assert inspect_graph(dest/'anchor/graph.hnsw',P,mapping)==ident['topology_sha']
    ar=dict(np.load(dest/'anchor/parity.npz'));equal(ar,{k:anchor[k][ar['local_rows']] for k in FIELDS});parity_rows+=32;physical_graphs+=1
    assert raw_digest(anchor)==ident['cache_sha']
    ds_contexts=[x for x in read(O/'inputs/contexts.json') if x['dataset']==ds];matrix=[];selector=[]
    for rec in ds_contexts:
        src=Path(rec['source']);step=rec['step'];cpstep=((step-1)//20)*20;slot=rec['slot']
        with np.load(src/'checkpoints'/f'{cpstep:04}.npz') as cp:W=cp['W'].copy()
        for st in range(cpstep+1,step):
            with np.load(src/'trajectory'/f'{st:04}.npz') as t:W[int(t['slot'])]=t['next_row']
        frozen=dict(np.load(O/'inputs'/ds/'contexts'/f"{rec['name']}.npz"));t=dict(np.load(rec['trajectory']))
        radius=sum(sorted(sum(float(x)**2 for x in row)**.5 for row in .3*t['eps'])[3:5])/2
        direction=t['adam_mu_proposal']-t['mu_before'];dn=sum(float(x)**2 for x in direction)**.5
        for i,factor in enumerate([.25,.5,1.]):
            coeff=np.clip(t['mu_before']+(factor*radius/dn)*direction,-2,2) if dn else t['mu_before'].copy()
            np.testing.assert_allclose(coeff,frozen['d_coeff'][i],atol=1e-14,rtol=1e-14)
            row=P[slot].astype(float).copy()
            if np.any(coeff):
                for j in range(16):row+=.0625*float(scale[slot])*float(np.tanh(coeff[j]))*B[:,j]
                row/=sum(float(x)**2 for x in row)**.5
            np.testing.assert_allclose(row,frozen['d_rows'][i],atol=4e-8,rtol=1e-7)
        original=max(range(4),key=lambda k:(0. if k==0 else rec['d_rewards'][k-1],-k))
        assert original-1==rec['original_choice']
        raw=[];hit=[];current_row=W[slot].copy()
        for i,label in enumerate(['C','D25','D50','D100']):
            folder=dest/rec['name']/label;out=dict(np.load(folder/'raw.npz'));patch=dict(np.load(folder/'patch.npz'));iden=read(folder/'identity.json')
            W[slot]=current_row if i==0 else frozen['d_rows'][i-1]
            assert digest(W)==iden['W_sha']==(rec['current_W_sha'] if i==0 else rec['d_W_sha'][i-1])
            assert digest(np.load(folder/'topology.npz')['topology'])==iden['topology_sha']==(rec['current_topology_sha'] if i==0 else rec['d_topology_sha'][i-1])
            assert raw_digest(out)==iden['cache_sha']==str(patch['cache_sha'])
            parent=base if i==0 else raw[0];assert raw_digest(parent)==str(patch['parent_cache_sha'])
            changed=np.flatnonzero((out['entries']!=parent['entries']).any(1));mask=np.ones(2048,bool);mask[changed]=False
            assert np.array_equal(changed,patch['changed_rows']) and len(changed)==iden['new_NSG'];new_patch_rows+=len(changed)
            assert (np.diff(out['entries'],axis=1)>0).all() and np.isin(out['entries'],mapping).all()
            for k in ['ids','distances','graph_ndc']:
                assert out[k][mask].tobytes()==parent[k][mask].tobytes() and out[k][changed].tobytes()==patch[k].tobytes()
            assert out['entries'][changed].tobytes()==patch['entries'].tobytes() and out['route_ndc'].tobytes()==patch['route_ndc'].tobytes()
            hh=ihits(out['ids'],gt[:2048]);assert np.array_equal(hh,out['hits']);scored+=2048
            if rec['physical_parity']:
                assert sha(folder/'graph.hnsw')==iden['graph_sha']
                assert inspect_graph(folder/'graph.hnsw',W,mapping)==iden['topology_sha']
                pr=dict(np.load(folder/'parity.npz'));equal(pr,{k:out[k][pr['local_rows']] for k in FIELDS})
                parity_rows+=16;physical_graphs+=1
            raw.append(out);hit.append(hh)
        hit=np.stack(hit);matrix.append(hit)
        eligible=[]
        for i,label in enumerate(['D25','D50','D100'],1):
            aux=effects(hit[i,:1024],hit[0,:1024]);trans=effects(hit[i,1024:],hit[0,1024:]);tr=effects(frozen['train_hits'][i],frozen['train_hits'][0])
            legal=rec['d_rewards'][i-1]>=0;allowed=legal and aux['net_hits']>0 and aux['gain_hits']>=1 and aux['new_failures']==0
            if allowed:eligible.append(i)
            points.append(dict(dataset=ds,seed=rec['seed'],step=step,point=label,train_delta_J=rec['d_rewards'][i-1],train_legal=legal,
                               auxiliary_supported=allowed,**{'train_'+k:v for k,v in tr.items()},
                               **{'aux_'+k:v for k,v in aux.items()},**{'transfer_'+k:v for k,v in trans.items()},
                               auxiliary_changed_entries=int((raw[i]['entries'][:1024]!=raw[0]['entries'][:1024]).any(1).sum()),
                               transfer_changed_entries=int((raw[i]['entries'][1024:]!=raw[0]['entries'][1024:]).any(1).sum())))
        selected=max([0]+eligible,key=lambda k:(0. if k==0 else rec['d_rewards'][k-1],-k));selector.append([original,selected])
        row=dict(dataset=ds,seed=rec['seed'],step=step,eligible_actions=len(eligible),supported=bool(eligible),original_choice=original,constrained_choice=selected)
        for tag,k in [('original',original),('constrained',selected)]:
            for phase,sl in [('aux',slice(0,1024)),('transfer',slice(1024,2048))]:
                row.update({f'{tag}_{phase}_{key}':v for key,v in effects(hit[k,sl],hit[0,sl]).items()})
            row.update({f'{tag}_train_{key}':v for key,v in effects(frozen['train_hits'][k],frozen['train_hits'][0]).items()})
        states.append(row)
    matrix=np.stack(matrix);selector=np.asarray(selector,np.int32)
    save(dest/'aligned_effects.npz',hits=matrix,delta_hits=matrix-matrix[:,0:1],choices=selector,
         source_rows=np.fromfile(c['row_ids'],np.int64)[:2048],seeds=np.array([x['seed'] for x in ds_contexts]),steps=np.array([x['step'] for x in ds_contexts]))
    sr=[x for x in states if x['dataset']==ds];pr=[x for x in points if x['dataset']==ds]
    summary=dict(dataset=ds,states=40,actions=120,supported_states=sum(x['supported'] for x in sr),
        support_gate_pass=sum(x['supported'] for x in sr)>=10,eligible_actions=sum(x['eligible_actions'] for x in sr),
        original_non_noop=sum(x['original_choice']>0 for x in sr),constrained_non_noop=sum(x['constrained_choice']>0 for x in sr),
        auxiliary_quality_null_actions=sum(x['aux_quality_null'] for x in pr),transfer_quality_null_actions=sum(x['transfer_quality_null'] for x in pr),
        auxiliary_any_gain_queries=int((matrix[:,1:,:1024]>matrix[:,0:1,:1024]).any((0,1)).sum()),
        transfer_any_gain_queries=int((matrix[:,1:,1024:]>matrix[:,0:1,1024:]).any((0,1)).sum()),
        constrained_transfer_positive_states=sum(x['constrained_choice']>0 and x['constrained_transfer_net_hits']>0 for x in sr),
        constrained_transfer_negative_states=sum(x['constrained_choice']>0 and x['constrained_transfer_net_hits']<0 for x in sr),
        constrained_transfer_null_states=sum(x['constrained_choice']>0 and x['constrained_transfer_quality_null'] for x in sr),
        diagnostic_step_sums={k:sum(x[k] for x in sr) for k in sr[0] if any(k.startswith(p) for p in ['original_aux_','constrained_aux_','original_transfer_','constrained_transfer_','original_train_','constrained_train_']) and not k.endswith('quality_null')})
    summaries.append(summary)

for name,rows in [('actions',points),('states',states)]:
    with (O/'results'/f'{name}.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
costs=[read(O/'results'/ds/'query_complete.json') for ds in DS]
assert scored==659488 and parity_rows==576 and physical_graphs==34
assert sum(x['NSG_calls'] for x in costs)==new_patch_rows+2*(2064+864)
cost=dict(datasets=costs,NSG_calls=sum(x['NSG_calls'] for x in costs),HNSW_calls=sum(x['HNSW_calls'] for x in costs),builds=sum(x['builds'] for x in costs),
          native_process_seconds=sum(x['seconds'] for x in costs),reused_NSG_outputs=sum(x['reused_NSG_outputs'] for x in costs),new_GT=0,optimizer_updates=0,formal_QPS_points=0)
dump(O/'results/cost.json',cost)
gate=dict(status='PASS_SUPPORT_FOR_CONTINUOUS_CONTROL' if all(x['support_gate_pass'] for x in summaries) else 'STOP_SAME_LOCAL_ACTION_CONTINUOUS_EXPANSION',
          datasets=summaries,threshold='at least 10 of 40 fixed states per dataset',scope='One-step historical development diagnostic; no deployable combined model, no formal performance GO')
dump(O/'results/gate.json',gate)
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_scores=scored,physical_graphs=physical_graphs,three_way_parity_rows=parity_rows,
     deterministic_radius_and_row_controls=240,cache_verified_rows=655360,new_patch_rows=new_patch_rows,rule_verified_states=80,
     all_native_processes_complete=True,new_native_calls=0,seconds=time.monotonic()-started))
dump(O/'state.json',dict(status='COMPLETE_VERIFIED_FIXED_ACTION_SUPPORT',gate=gate['status'],new_NSG=cost['NSG_calls'],optimizer_updates=0,
     next_action='Write report/figures, freeze artifacts and synchronized root documents; evaluate any distinct next direction under new protocol'))
print(json.dumps(gate,ensure_ascii=False,indent=2),flush=True)
