"""Independent set scoring and scalar reward / LOO-gradient reconstruction."""
from control import *

def set_hits(ids, gt):
    out=[]
    for returned, truth in zip(ids,gt):
        assert len(set(map(int,returned)))==10
        out.append(len(set(map(int,returned)) & set(map(int,truth[:10]))))
    return np.array(out,dtype=np.float64)

def cos(a,b):
    den=np.sqrt(np.dot(a,a)*np.dot(b,b))
    return float(np.dot(a,b)/den) if den else None

def close(a,b):
    if a is None or b is None: assert a is None and b is None
    else: assert np.isclose(a,b,rtol=1e-9,atol=1e-10),(a,b)

def verify():
    start=time.monotonic();decision=read(O/'results/diagnosis.json');scored=0;parity=0;gradients={}
    check(O/'reviews/prequery_freeze.json')
    for di,ds in enumerate(DS):
        c=cfg(ds);qids=np.load(O/'inputs'/ds/'rows.npz');rows=qids['rows'];eligible=qids['eligible']
        assert len(np.unique(rows))==1024 and rows.min()>=0 and rows.max()<4096
        assert not np.intersect1d(rows,qids['excluded']).size
        repeat=np.random.Generator(np.random.PCG64(2026091201+di)).choice(eligible,1024,replace=False).astype(np.int32)
        assert np.array_equal(repeat,rows)
        gt=np.fromfile(c['gt_file'],np.int64).reshape(4096,100)[rows]
        base=dict(np.load(E/'results'/ds/'baseline.npz'))
        h0=set_hits(base['ids'][rows],gt)
        for name in ['zero','selected']:
            t=context(ds,name);saved=dict(np.load(O/'results'/ds/(name+'_derived.npz')))
            meta=read(O/'inputs'/ds/(name+'.json'))
            old=dict(np.load(meta['trajectory']));cp=dict(np.load(meta['checkpoint']))
            rewards=np.empty((8,1024));all_hits=[];drift=[]
            p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']).astype(float)
            for j in range(9):
                label='center' if j==8 else f'action{j}'
                raw=dict(np.load(O/'results'/ds/name/(label+'.npz')))
                hh=set_hits(raw['ids'],gt);scored+=1024
                if j==8: assert np.array_equal(hh,saved['center_hits'])
                else:
                    all_hits.append(hh)
                    for qi in range(1024):
                        total=int(raw['route_ndc'][qi])+int(raw['graph_ndc'][qi])
                        total0=int(base['route_ndc'][rows[qi]])+int(base['graph_ndc'][rows[qi]])
                        rewards[j,qi]=(hh[qi]-h0[qi]-.1*(total/total0-1)
                                           -.1*(int(hh[qi]==0)-int(h0[qi]==0)))
                    w=np.fromfile(O/'models'/ds/name/label/'W.f32',np.float32).reshape(p.shape).astype(float)
                    drift.append(float(sum(np.dot(wi-pi,wi-pi) for wi,pi in zip(w,p))/len(p)))
                pp=dict(np.load(O/'models'/ds/name/label/'parity.npz'))
                reference={k:cp[k][:16] if j==8 else old[k][j,:16] for k in FIELDS}
                equal(pp,reference);parity+=16
            assert np.array_equal(all_hits,saved['hits'])
            assert np.allclose(rewards,saved['U'],atol=1e-14,rtol=1e-14)
            # Explicit leave-one-out baseline per candidate, instead of centered M multiplication.
            g=np.zeros((256,1024));reg=np.zeros(256)
            for j in range(8):
                others=[i for i in range(8) if i!=j]
                advantage=rewards[j]-sum(rewards[i] for i in others)/7
                g+=np.outer(t['eps'][j],advantage)/(8*.3)
                reg+=t['eps'][j]*(-drift[j]+sum(drift[i] for i in others)/7)/(8*.3)
            assert np.allclose(g,saved['G'],rtol=1e-10,atol=1e-11)
            assert np.allclose(reg,saved['reg'],rtol=1e-10,atol=1e-11)
            gradients[(ds,name)]=(g,reg,len(eligible))
            s=next(x for x in decision['contexts'] if x['dataset']==ds and x['context']==name)
            close(cos(g[:,:512].mean(1),g[:,512:].mean(1)),s['primary512_cos_data'])
            close(cos(g[:,:512].mean(1)+reg,g[:,512:].mean(1)+reg),s['primary512_cos_total'])
    group_count=0
    for record in csv.DictReader((O/'results/groups.csv').open()):
        g,reg,N=gradients[(record['dataset'],record['context'])]
        blocks=list(map(int,record['blocks'].split('-')))
        loc=[q for block in blocks for q in range(block*128,(block+1)*128)]
        values=g[:,loc];n=len(loc);mean=values.sum(1)/n
        # Independent raw second-moment identity for the trace variance.
        v=(1-n/N)*(np.einsum('ij,ij->',values,values)-n*np.dot(mean,mean))/(n*(n-1))
        close(v,float(record['query_variance_trace']));close(np.linalg.norm(mean),float(record['data_norm']))
        group_count+=1
    pair_count=0;stats={}
    for record in csv.DictReader((O/'results/disjoint_pairs.csv').open()):
        g,reg,N=gradients[(record['dataset'],record['context'])]
        blocks=[list(map(int,record[k].split('-'))) for k in ['blocks_a','blocks_b']]
        assert set(blocks[0]).isdisjoint(blocks[1])
        means=[g[:,[q for b in bs for q in range(b*128,(b+1)*128)]].mean(1) for bs in blocks]
        for kind,r in [('data',0),('total',reg)]:
            value=cos(means[0]+r,means[1]+r)
            close(value,float(record['cos_'+kind]) if record['cos_'+kind] else None)
            stats.setdefault((record['dataset'],record['context'],int(record['batch']),kind),[]).append(value)
        pair_count+=1
    for s in decision['contexts']:
        flags=[]
        for kind in ['data','total']:
            values=stats[(s['dataset'],s['context'],512,kind)]
            assert len(values)==35 and all(x is not None for x in values)
            median=float(np.median(values));pos=float(np.mean(np.array(values)>0))
            close(median,s['balanced512_median_'+kind]);close(pos,s['balanced512_positive_'+kind])
            flags.append(s['primary512_cos_'+kind]>=.3 and median>=.3 and pos>=.75)
        assert s['stable']==all(flags)
    assert scored==36864 and parity==576 and group_count==428 and pair_count==1092
    result=dict(status='PASS',independent_set_scored=scored,old_parity_records=parity,
                independently_reconstructed_query_gradients=4096,group_variances=group_count,
                disjoint_pairs=pair_count,all_four_stable=decision['all_four_stable'],
                seconds=time.monotonic()-start,extra_NSG=0,optimizer_updates=0)
    dump(O/'reviews/independent_verification.json',result);print(json.dumps(result))

if __name__=='__main__':verify()
