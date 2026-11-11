from common import *
from archive import load_packets
import gzip,struct
assert read(R/'formal_complete.json')['status']=='PASS_FROZEN_FORMAL_MATRIX_COMPLETE'
identity=read(R/'reviews/decision_source_identity.json')
assert sha(identity['formal_source'])==identity['formal_source_sha256']
subprocess.run([str(REPO/'.venv_cpu/bin/python'),str(R/'scripts/build.py'),'decision'],cwd=REPO,check=True)

def prediction(model,X):
    if model['type']=='ridge':return np.asarray(X[:,:model['feature_count']],float)@np.array(model['coef'])+model['bias']
    value=np.full(len(X),model['bias'],dtype=float)
    for tree in model['trees']:
        feature=np.array([n['f'] for n in tree],dtype=int);threshold=np.array([n['t'] for n in tree],float)
        left=np.array([n['l'] for n in tree],int);right=np.array([n['r'] for n in tree],int)
        leaf=np.array([n['leaf'] for n in tree],bool);values=np.array([n['v'] for n in tree],float)
        current=np.zeros(len(X),int)
        while True:
            active=np.flatnonzero(~leaf[current])
            if not len(active):break
            nodes=current[active]
            current[active]=np.where(X[active,feature[nodes]]<=threshold[nodes],left[nodes],right[nodes])
        value+=values[current]
    return value

began=time.perf_counter();records=[];total_rows=total_queries=0;maximum=0.
for ds in DS:
    selected=read(R/'storage/models'/ds/'selected.json')
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.json');scratch=Path(c['scratch']);scratch.mkdir(exist_ok=True)
        transient=scratch/f'decision_features.{window}.bin';assert not transient.exists()
        argv=['taskset','-c','15',str(R/'storage/decision_benchmark'),str(R/'configs'/f'{ds}.{window}.json'),str(transient)]
        t=time.perf_counter()
        with (R/'reviews'/f'{ds}.{window}.decision_replay.log').open('w') as log:
            p=subprocess.Popen(argv,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
            dump(R/'live_process.json',dict(dataset=ds,stage='actual_model_decision_audit',pid=p.pid,argv=argv,started_unix=time.time()))
            code=p.wait()
        assert code==0,(ds,window)
        data=transient.read_bytes();offset=0;entries=[];features=[];native_values=[];row_start=0
        dtype=np.dtype([('id','<i4'),('feature','<f4',(104,)),('native','<f8')]);assert dtype.itemsize==428
        while offset<len(data):
            K,L,qi,bank,nc=struct.unpack_from('<5I',data,offset);offset+=20
            assert K in [1,100] and L in [100,200,400] and bank in [0,1] and nc<=96
            value=np.frombuffer(data,dtype,count=nc,offset=offset);offset+=nc*428
            entries.append(dict(K=K,L=L,query=qi,bank=bank,start=row_start,end=row_start+nc,ids=value['id']))
            features.append(value['feature']);native_values.append(value['native']);row_start+=nc
        assert offset==len(data)
        X=np.vstack(features);native=np.concatenate(native_values);python=np.empty(len(X),float)
        for K in [1,100]:
            take=[e for e in entries if e['K']==K];first=take[0]['start'];last=take[-1]['end']
            python[first:last]=prediction(selected['K'][str(K)],X[first:last])
        error=np.abs(native-python);assert np.all(error<=1e-8*(1+np.abs(native)))
        maximum=max(maximum,float(error.max(initial=0)))
        raw=load_packets(Path(c['output_dir']));proof=[]
        for e in entries:
            K,L,qi,bank=e['K'],e['L'],e['query'],e['bank'];a,b=e['start'],e['end'];model=selected['K'][str(K)]
            if b>a:
                ni=a+int(np.argmax(native[a:b]));pi=a+int(np.argmax(python[a:b]));native_seed=int(e['ids'][ni-a]);python_seed=int(e['ids'][pi-a])
                assert native_seed==python_seed,('actual argmax numerical discrepancy',ds,window,K,L,qi,bank)
                native_best=float(native[ni]);python_best=float(python[pi])
            else:native_seed=python_seed=-1;native_best=python_best=0.
            full='MODEL-FULL' if bank else 'MODEL1';gate='MODEL-GATE-FULL' if bank else 'MODEL-GATE'
            actual_full=np.frombuffer(raw[f'k{K}/{full}_L{L}/seeds.i32'],'<i4').reshape(c['queries']['n'],3)[qi]
            actual_gate=np.frombuffer(raw[f'k{K}/{gate}_L{L}/seeds.i32'],'<i4').reshape(c['queries']['n'],3)[qi]
            assert actual_full[0]==native_seed and np.all(actual_full[1:]==-1)
            expected_gate=native_seed if (native_seed>=0 and not model['gate_all_off'] and native_best>=model['threshold']) else -1
            python_gate=python_seed if (python_seed>=0 and not model['gate_all_off'] and python_best>=model['threshold']) else -1
            assert expected_gate==python_gate==actual_gate[0] and np.all(actual_gate[1:]==-1),('gate mismatch',ds,window,K,L,qi,bank)
            proof.append(dict(dataset=ds,window=window,K=K,L=L,query=qi,bank='FULL' if bank else 'Q8',
                candidate_count=b-a,native_seed=native_seed,python_seed=python_seed,actual_timed_seed=int(actual_full[0]),
                native_best=native_best,python_best=python_best,actual_timed_gate_seed=int(actual_gate[0])))
        with gzip.open(R/'analysis'/f'{ds}.{window}.decisions.csv.gz','wt',compresslevel=6) as f:
            w=csv.DictWriter(f,fieldnames=list(proof[0]));w.writeheader();w.writerows(proof)
        record=dict(dataset=ds,window=window,queries=len(entries),candidate_rows=len(X),
            feature_stream_sha256=hashlib.sha256(data).hexdigest(),native_replay_receipt=read(str(transient)+'.json'),
            max_prediction_absolute_error=float(error.max(initial=0)),actual_all_seed_and_gate_ID_equal=True,
            transient_features_reconstructable_from_frozen_source=True,seconds=time.perf_counter()-t)
        dump(R/'reviews'/f'{ds}.{window}.decision_replay.json',record)
        total_rows+=len(X);total_queries+=len(entries);records.append(record)
        transient.unlink();Path(str(transient)+'.json').unlink()
        del X,data,native,python,raw,features,native_values,entries
        print('ACTUAL_DECISIONS_VERIFIED',ds,window,record['candidate_rows'],flush=True)
dump(R/'analysis/decision_audit.json',dict(status='PASS_ALL_ACTUAL_MODEL_FEATURE_INFERENCE_AND_TIMED_SELECTIONS',
    candidate_rows=total_rows,query_K_L_bank_decisions=total_queries,max_absolute_error=maximum,
    records=records,raw_GT_or_teacher_masks_used=False,seconds=time.perf_counter()-began,
    all_actual_timed_seed_and_gate_ID_equal=True))
