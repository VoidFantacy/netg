#!/usr/bin/env python3
"""Open evaluation splits only after every pre-registered model is frozen."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np

OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1]
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];SEEDS=[20260828,20260829,20260830]
def dump(p,j):p.write_text(json.dumps(j,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def vecs(p,kind):
    a=np.fromfile(p,dtype='int32');width=int(a[0]);assert len(a)%(width+1)==0
    a=a.reshape(-1,width+1);assert np.all(a[:,0]==width)
    return (a[:,1:].view('float32') if kind=='float' else a[:,1:]).copy()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--split',choices=['calibration_check','audit','validation','heldout'],required=True);args=parser.parse_args()
    protocol=json.loads((OUT/'config.locked.json').read_text())
    frozen=[]
    for ds in DATASETS:
        for seed in SEEDS:
            for L in [64,128]:
                p=OUT/'models'/ds/f'seed{seed}'/f'L{L}'/'complete.json';j=json.loads(p.read_text())
                assert j['status']=='TRAINING_COMPLETE_MODEL_FROZEN' and j['protocol_sha256']==protocol['protocol_sha256']
                assert not j['audit_used'] and not j['validation_used'] and not j['heldout_used']
                for s in sorted(p.parent.rglob('*')):
                    if s.is_file():frozen.append({'path':str(s),'sha256':sha(s)})
    splitroot=OUT/'inputs/evaluation'/args.split;assert not splitroot.exists();splitroot.mkdir(parents=True)
    dump(splitroot/'models_frozen_before_evaluation.json',{'status':'FROZEN','files':frozen,'protocol_sha256':protocol['protocol_sha256']})
    configs=[]
    for ds in DATASETS:
        original=OUT/'inputs'/ds;c=json.loads((original/'runner_config.json').read_text());d=c['dim']
        dest=splitroot/ds;dest.mkdir()
        if args.split in ['calibration_check','audit']:
            begin=c['fit_count'] if args.split=='calibration_check' else c['fit_count']+c['cal_count']
            end=begin+c['cal_count'] if args.split=='calibration_check' else c['num_queries']
            q=np.memmap(original/'queries.f32',dtype='float32',mode='r',shape=(c['num_queries'],d))[begin:end].copy()
            gt=np.memmap(original/'gt.i64',dtype='int64',mode='r',shape=(c['num_queries'],100))[begin:end].copy()
            rows=np.fromfile(original/'row_ids.i64',dtype='int64')[begin:end];sources={'source':'historical router_train; frozen-model check only','source_rows':rows.tolist()}
        else:
            web=ds.startswith('webvid');base=ROOT/'benches/datasets'/('WebVid2.5M_light_v1' if web else 'YandexT2I_official10M_ip_v1')
            if args.split=='validation':
                qname='query.validation.seed20260826.fvecs' if web else 'query.validation.fvecs'
                gname='gt.validation.seed20260826.ip.ivecs' if web else 'gt.validation.ip.ivecs'
            else:
                qname='query.test.public10K.fvecs' if web else 'query.test.public100K.fvecs'
                gname='gt.test.public10K.ip.top100.ivecs' if web else 'gt.test.public100K.ip.ivecs'
            manifest=json.loads((base/'manifest.json').read_text());sources={}
            for name in [qname,gname]:
                actual=sha(base/name);assert actual==manifest['files'][name]['sha256'];sources[name]={'sha256':actual,'source':str(base/name)}
            # Only first 10K are copied/scored; Yandex's source file contains 100K.
            q=vecs(base/qname,'float')[:10000];gt=vecs(base/gname,'int')[:10000].astype('int64');rows=np.arange(len(q),dtype='int64')
            assert len(q)==10000 and len(gt)==10000
        np.ascontiguousarray(q,dtype='float32').tofile(dest/'queries.f32');np.ascontiguousarray(gt,dtype='int64').tofile(dest/'gt.i64');rows.tofile(dest/'row_ids.i64')
        dump(dest/'sources.json',sources)
        for seed_index,seed in enumerate(SEEDS):
            sc=json.loads((original/f'seed{seed}/config.json').read_text());methods=[]
            common={'seed':seed,'hub_count':sc['hub_count'],'tie_ids':sc['hub_ids']}
            for L in [64,128]:
                def add(name,W,mapping,**options):
                    methods.append({**common,'name':name+f'_L{L}','family':name,'L':L,'W':str(W),'mapping':str(mapping),'k':1,'slot_labels':False,'exact':False,**options})
                for k in [1,3]:
                    add(f'fast20k_{k}',sc['prototypes'],sc['hub_ids'],k=k,hnsw_seed=seed)
                    add(f'fast30k_{k}',sc['fast30k_prototypes'],sc['hub_ids'],k=k,hnsw_seed=100,legacy_heap_order=True)
                add('fast20k_exact1',sc['prototypes'],sc['hub_ids'],exact=True)
                model=OUT/'models'/ds/f'seed{seed}'/f'L{L}'
                for family in ['w_only','mapping_only','joint','staged']:
                    sel=json.loads((model/family/'selection.json').read_text());candidate=sel['candidate']
                    for exact in [False,True]:
                        add(family+('_exact' if exact else ''),candidate['W'],candidate['mapping'],slot_labels=True,exact=exact,hnsw_seed=seed)
                joint=json.loads((model/'joint/selection.json').read_text())
                if joint['best_including_fast']==0:
                    add('joint_selected',sc['prototypes'],sc['hub_ids'],hnsw_seed=seed,selected_fallback=True)
                else:
                    sel=joint['selected'];add('joint_selected',sel['W'],sel['mapping'],slot_labels=True,hnsw_seed=seed,selected_fallback=False)
            config={'dataset':ds,'split':args.split,'dim':d,'num_queries':len(q),'gt_k':100,'threads':16,'index_path':c['index_path'],
                    'queries_file':str(dest/'queries.f32'),'gt_file':str(dest/'gt.i64'),'row_ids':str(dest/'row_ids.i64'),
                    'methods':methods,'order_offset':seed_index*3,'timing_repeats':3 if args.split in ['validation','heldout'] else 0,
                    'audit_timing_note':'audit reports quality/cost only; QPS from validation/heldout full10K'}
            fp=dest/f'seed{seed}.json';dump(fp,config);configs.append(str(fp))
    dump(splitroot/'complete.json',{'status':'PREPARED','split':args.split,'configs':configs,'models_frozen_before_access':True})

if __name__=='__main__':main()
