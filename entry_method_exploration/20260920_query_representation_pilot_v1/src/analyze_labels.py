from common import *
import sys,struct

def vectors_in_nsg(path):
    with open(path,'rb') as f:
        def rd(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))
        version,n,d,metric,trained,built,build=rd('iqii??c')
        assert version in (1,2) and metric==0 and trained and built
        rd('ffffiiiiiq')
        for _ in range(2):
            count,=rd('Q');assert count==n;f.seek(count*4,1)
        k,count=rd('iQ');assert count==n*k;f.seek(count*4,1)
        count,=rd('Q');assert count==n*d;offset=f.tell()
    return np.memmap(path,mode='r',dtype='<f4',offset=offset,shape=(n,d))

def analyze(split):
    records=[]
    for ds in DS:
        c=read(RUN/'inputs'/ds/split/'config.json');n,d=c['n'],c['dimension']
        dest=RUN/'labels'/ds/(split+'_labels');completed=read(dest/'complete.json');assert completed['status']=='PASS'
        gt=np.fromfile(c['gt'],'int64').reshape(n,100)
        q=np.fromfile(c['queries'],'float32').reshape(n,d)
        slots=np.fromfile(dest/'baseline_slots.i32','int32').reshape(n,2)
        triples=np.fromfile(dest/'triples.i32','int32').reshape(n,56,3)
        candidates=np.fromfile(dest/'candidates.i32','int32').reshape(n,8)
        hubs=np.fromfile(c['hub_ids'],'int32')
        anchors=np.fromfile(dest/'anchor_entries.i32','int32').reshape(n,3)
        assert np.array_equal(hubs[triples[np.arange(n),slots[:,0]]],anchors)
        assert all(len({tuple(t) for t in row})==56 for row in triples)
        assert all(set(row.ravel())==set(candidates[i]) for i,row in enumerate(triples))
        metric=[];hits_by_k={};arrays={};distances={};ndcs={}
        base=vectors_in_nsg(c['index'])
        for K in (1,100):
            ids=np.memmap(dest/f'k{K}.ids.i32',mode='r',dtype='int32',shape=(n,56,K))
            dd=np.memmap(dest/f'k{K}.distances.f32',mode='r',dtype='float32',shape=(n,56,K))
            ndc=np.fromfile(dest/f'k{K}.ndc.u64','uint64').reshape(n,56)
            saved=np.fromfile(dest/f'k{K}.hits.u8','uint8').reshape(n,56)
            assert ids.min()>=0 and ids.max()<c['base_n'] and np.isfinite(dd).all()
            assert np.all(ndc>=3) and np.all(np.diff(dd,axis=2)>=0)
            hits=np.empty_like(saved)
            for i in range(n):
                if K>1:assert np.all(np.diff(np.sort(ids[i],axis=1),axis=1)>0)
                hits[i]=np.isin(ids[i],gt[i,:K]).sum(1)
            assert np.array_equal(hits,saved),'independent GT recomputation'
            errors=[]
            for i in np.linspace(0,n-1,16,dtype=int):
                for t in (0,int(slots[i,0])):
                    exact=-(base[ids[i,t]].astype('float64')@q[i].astype('float64'))
                    err=np.max(np.abs(exact-dd[i,t]));errors.append(float(err))
                    assert np.allclose(exact,dd[i,t],rtol=2e-5,atol=2e-5),'raw-IP distance audit'
            anchor=hits[np.arange(n),slots[:,0]]/K;oracle=hits.max(1)/K
            metric.append(dict(K=K,anchor_recall=float(anchor.mean()),finite_pool_oracle_recall=float(oracle.mean()),
                               oracle_gain_pp=float((oracle-anchor).mean()*100),oracle_improved_fraction=float((oracle>anchor).mean()),
                               anchor_zero_fraction=float((anchor==0).mean()),oracle_zero_fraction=float((oracle==0).mean()),
                               anchor_ndc_mean=float(ndc[np.arange(n),slots[:,0]].mean()),max_float64_distance_error=max(errors)))
            hits_by_k[K]=hits;arrays[K]=ids;distances[K]=dd;ndcs[K]=ndc
        assert np.array_equal(arrays[1][:,:,0],arrays[100][:,:,0])
        assert np.array_equal(distances[1][:,:,0],distances[100][:,:,0])
        assert np.array_equal(ndcs[1],ndcs[100])
        h1,h100=hits_by_k[1].astype('int32'),hits_by_k[100].astype('int32')
        a1=h1[np.arange(n),slots[:,0]];a100=h100[np.arange(n),slots[:,0]]
        anygain=((h1>a1[:,None])|(h100>a100[:,None])).any(1)
        safe=(h1>=a1[:,None])&(h100>=a100[:,None])
        safe_gain=(safe&((h1>a1[:,None])|(h100>a100[:,None]))).any(1)
        teacher_score=h1*100+h100;teacher_mask=teacher_score==teacher_score.max(1,keepdims=True)
        teacher_mask.astype('uint8').tofile(dest/'teacher_mask.u8')
        teacher_k1_harm=teacher_mask&(h1<a1[:,None]);teacher_k100_harm=teacher_mask&(h100<a100[:,None])
        passed=max(x['oracle_gain_pp'] for x in metric)>=0.5 and anygain.mean()>=0.05
        records.append(dict(dataset=ds,split=split,n=n,metrics=metric,any_K_improved_fraction=float(anygain.mean()),
                            both_K_safe_improvement_fraction=float(safe_gain.mean()),
                            selected_mean_utility_teacher_K1_harm_fraction=float(teacher_k1_harm.any(1).mean()),
                            selected_mean_utility_teacher_K100_harm_fraction=float(teacher_k100_harm.any(1).mean()),
                            mean_teacher_count=float(teacher_mask.sum(1).mean()),headroom_pass=bool(passed),
                            raw_unit_route_differences=completed['raw_unit_route_differences'],
                            outputs=[identity(p) for p in sorted(dest.iterdir()) if p.is_file()]))
        print(json.dumps({k:v for k,v in records[-1].items() if k!='outputs'}),flush=True)
    result=dict(status='PASS' if all(x['headroom_pass'] for x in records) else 'STOP_HEADROOM',
                split=split,datasets=records,independent_hits_and_distance_check=True,source=identity(Path(__file__)))
    dump(RUN/'results'/f'{split}_label_analysis.json',result)
    if split=='fit':dump(RUN/'reviews/headroom_gate.json',result)
    return result

if __name__=='__main__':analyze(sys.argv[1])
