#!/usr/bin/env python3
"""Prepare fit/cal/audit only; never open validation or held-out here."""
import hashlib, importlib.util, json, time
from pathlib import Path
import numpy as np

ROOT=Path('/data/netg/ACSG')
OUT=ROOT/'entry_method_exploration/20260909_ab_experiment_v1'
SEEDS=[20260828,20260829,20260830]

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def dump(p,o): p.write_text(json.dumps(o,indent=2)+'\n')

def main():
    spec=importlib.util.spec_from_file_location('original_fast',ROOT/'benches/run/build_fast_entry_variants.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    rows=np.r_[np.arange(10000,30000),np.arange(2048)].astype('int64')
    summaries=[]
    for dataset in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
        p=OUT/'inputs'/dataset;p.mkdir(exist_ok=True)
        assert not (p/'complete.json').exists(),'refuse replacing prepared data'
        old=ROOT/'fast_router_diagnosis/20260908_v1/inputs/prepared_v2'/dataset
        c=json.loads((old/'runner_config.json').read_text())
        ids=json.loads((old/'verified_identities.json').read_text())
        verified={}
        for key in ['base','graph','query_train','gt_train']:
            x=ids[key];t=time.monotonic();actual=sha(x['path']);assert actual==x['sha256'],key
            verified[key]={**x,'verified_now_sha256':actual,'verify_seconds':time.monotonic()-t}
        q=mod.read_fvecs(Path(ids['query_train']['path']));gt=mod.read_ivecs(Path(ids['gt_train']['path']))
        assert len(q)==30000 and q.shape[1]==c['dim'] and len(gt)==30000
        np.ascontiguousarray(q[rows],dtype='float32').tofile(p/'queries.f32')
        np.ascontiguousarray(gt[rows],dtype='int64').tofile(p/'gt.i64');rows.tofile(p/'row_ids.i64')
        base,d=mod.fvecs_memmap(Path(ids['base']['path']))
        target=np.asarray(base[gt[10000:,0],1:],dtype='float32')
        configs=[];all_hubs=[]
        for seed in SEEDS:
            f=ROOT/f'fast_entry_variants/{dataset}_seed{seed}'
            manifest=json.loads((f/'manifest.json').read_text())
            v=manifest['variants'];hc=v['qgt_cover'];pc=v['qgt_gt_basin_prototype']
            for obj in [hc,pc]:
                for key in ['hubs','ids']:
                    fp=ROOT/obj[key+'_file'];assert sha(fp)==obj[key+'_sha256'],str(fp)
            hubs=np.fromfile(ROOT/hc['ids_file'],dtype='int32');raw=np.fromfile(ROOT/hc['hubs_file'],dtype='float32').reshape(-1,d)
            assert np.array_equal(raw,base[hubs,1:]),'hub/base row mismatch'
            proto,details=mod.build_gt_basin_prototypes(q[10000:],gt[10000:],target,raw,1.0)
            details['requires_aco_dpc']=False
            dest=p/f'seed{seed}';dest.mkdir(exist_ok=True)
            proto.tofile(dest/'prototype.f32');hubs.tofile(dest/'hub_ids.i32')
            parity=None
            if seed==SEEDS[0]:
                prior=np.fromfile(c['prototypes'],dtype='float32').reshape(proto.shape)
                parity={'bit_equal':bool(np.array_equal(proto,prior)),'max_abs':float(np.abs(proto-prior).max())}
                assert parity['max_abs']<1e-6,'paired Fast reconstruction differs'
            cfg={'seed':seed,'hub_count':len(hubs),'hub_ids':str(dest/'hub_ids.i32'),'prototypes':str(dest/'prototype.f32'),
                 'fast30k_prototypes':str(ROOT/pc['hubs_file']),'prototype_details':details,'paired20k_reconstruction':parity,
                 'source_manifest':str(f/'manifest.json'),'source_manifest_sha256':sha(f/'manifest.json')}
            configs.append(cfg);all_hubs.append(hubs)
        union=np.unique(np.concatenate(all_hubs));union.tofile(p/'union_hub_ids.i32')
        for cfg,hubs in zip(configs,all_hubs):
            cols=np.searchsorted(union,hubs).astype('int32');assert np.array_equal(union[cols],hubs)
            dest=p/f"seed{cfg['seed']}";cols.tofile(dest/'union_columns.i32');cfg['union_columns']=str(dest/'union_columns.i32')
            dump(dest/'config.json',cfg)
        conf={'dataset':dataset,'dim':d,'num_queries':len(rows),'fit_count':20000,'cal_count':1024,'audit_count':1024,
              'index_path':c['index_path'],'queries_file':str(p/'queries.f32'),'gt_file':str(p/'gt.i64'),
              'row_ids':str(p/'row_ids.i64'),'hub_ids':str(p/'union_hub_ids.i32'),'hub_count':len(union),'gt_k':100,
              'L':[64,128],'threads':16,'block_rows':16,'seeds':configs}
        dump(p/'runner_config.json',conf);dump(p/'verified_sources.json',verified)
        summary={'dataset':dataset,'status':'PREPARED','union_hubs':len(union),'queries':len(rows),'logical_label_calls':len(rows)*len(union)*2,
                 'expected_thin_label_bytes':len(rows)*len(union)*2*7,'prepared_files':[]}
        for file in sorted(p.rglob('*')):
            if file.is_file():summary['prepared_files'].append({'path':str(file),'bytes':file.stat().st_size,'sha256':sha(file)})
        dump(p/'complete.json',summary);summaries.append(summary)
        print(json.dumps({k:v for k,v in summary.items() if k!='prepared_files'}),flush=True)
    dump(OUT/'inputs/complete.json',{'datasets':summaries,'protocol_sha256':sha(OUT/'protocol.md')})

if __name__=='__main__': main()
