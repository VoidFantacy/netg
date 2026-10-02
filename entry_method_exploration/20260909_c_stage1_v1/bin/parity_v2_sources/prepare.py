#!/usr/bin/env python3
"""C0 inputs. Reads training queries and manifests; never opens GT files."""
import datetime, hashlib, json, math
from pathlib import Path
import numpy as np

ROOT = Path('/data/netg/ACSG')
V = ROOT / 'entry_method_exploration/20260909_c_stage1_v1'
def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''): h.update(b)
    return h.hexdigest()

def prepare():
    configs = []
    for ds in ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']:
        old = ROOT / 'fast_router_diagnosis/20260908_v1/inputs/prepared_v2' / ds
        c = json.loads((old/'runner_config.json').read_text())
        identities = json.loads((old/'verified_identities.json').read_text())
        out = V/'inputs'/ds
        out.mkdir(exist_ok=False)
        ids = np.random.Generator(np.random.PCG64(20260909)).permutation(10000)[:2000].astype('<i8')
        ids.tofile(out/'row_ids.i64')
        qpath = Path(identities['query_train']['path'])
        dim = c['dim']
        rows = np.memmap(qpath, mode='r', dtype='<i4').reshape(-1, dim+1)
        assert len(rows)==30000 and np.all(rows[:,0] == dim)
        q = np.asarray(rows[ids,1:]).view('<f4').copy()
        assert np.isfinite(q).all()
        q.tofile(out/'queries.f32')
        checked = {}
        # Existing train GT identity is declared, but byte access is deferred until offline scoring.
        for key in ['base','graph','query_train','prototypes','hub_ids','raw_hubs']:
            rec = identities[key]; path=Path(rec['path'])
            sha=digest(path)
            assert sha == rec['sha256'], (key, path)
            checked[key]={'path':str(path),'sha256':sha,'bytes':path.stat().st_size}
        paired=Path(c['prototypes']).parent/'manifest.json'
        pm=json.loads(paired.read_text())
        assert pm['fit_range']==[10000,30000] and pm['seed']==20260828
        checked['paired_manifest']={'path':str(paired),'sha256':digest(paired)}
        checked['gt_train_deferred']=identities['gt_train']
        checked['query_sample']={'path':str(out/'queries.f32'),'sha256':digest(out/'queries.f32')}
        checked['row_ids']={'path':str(out/'row_ids.i64'),'sha256':digest(out/'row_ids.i64')}
        dump(out/'identities.json',checked)
        cc={k:c[k] for k in ['dataset','dim','hub_count','base_count','index_path','hub_ids','prototypes']}
        cc.update({'queries_file':str(out/'queries.f32'),'row_ids':str(out/'row_ids.i64'),
                   'num_queries':2000,'calibration_queries':128,'gt_train_path':identities['gt_train']['path'],
                   'gt_train_sha256':identities['gt_train']['sha256'],'gt_k':100,'K':10,'L':[64,128],
                   'hnsw_seed':20260828,'hnsw_M':16,'ef_construction':200,'ef_search':10,'threads':1,
                   'sample_seed':20260909,'query_split':'drl_train','identity_file':str(out/'identities.json')})
        dump(out/'config.json',cc); configs.append(str(out/'config.json'))
    dump(V/'config.prelock.json',{'datasets':configs,'L':[64,128],'K':10,'max_candidates':4,
        'candidate_generator':'independent paired HNSW top7, ranks 3:7 zero-based; remove initial/duplicate IDs without refill',
        'start_policy':'paired Fast20K direct HNSW top3; reverse maxheap to rank order',
        'checkpoint_rule':'per L: max(1,floor(0.5 * min_dataset median native completed expansions)))',
        'B_rule':'single global B=max(128,64*ceil(max_dataset_L percentile75(native graph NDC)/128))',
        'primary_family_size':4,'bootstrap_repetitions':20000,'bootstrap_seed':20260909,
        'familywise_alpha':0.05,'minimum_mean_recall_gain':0.005,
        'resources':{'cpu_only':True,'max_threads':16,'worker_threads':1,'max_distinct_queries_per_dataset':2000,
                     'max_native_or_branch_calls':200000,'max_wall_seconds_per_stage':7200,'max_rss_gib':32,'max_new_disk_gib':5},
        'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})

def lock():
    c=json.loads((V/'config.prelock.json').read_text())
    data=[json.loads((V/'results'/('calibration_'+ds+'.json')).read_text())
          for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']]
    for ds,d in zip(['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'],data):
        ids=np.fromfile(V/'inputs'/ds/'row_ids.i64',dtype='<i8')
        assert d['dataset']==ds and d['GT_accessed'] is False and len(d['rows'])==256
        for row,(L,i) in zip(d['rows'],[(L,i) for L in [64,128] for i in range(128)]):
            assert row['L']==L and row['sample_index']==i and row['row_id']==int(ids[i])
            assert 0<row['ndc']<=10000000 and 0<row['expansions']<=10000000
            assert math.isfinite(row['wall']) and row['wall']>=0
    cp={str(L):max(1,int(min(np.median([r['expansions'] for r in d['rows'] if r['L']==L]) for d in data)*0.5)) for L in [64,128]}
    costs=[np.percentile([r['ndc'] for r in d['rows'] if r['L']==L],75) for d in data for L in [64,128]]
    B=max(128,64*math.ceil(max(costs)/128))
    c.update({'checkpoint_completed_expansions':cp,'B':B,'locked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'calibration_files':[{ 'path':str(V/'results'/('calibration_'+d['dataset']+'.json')),
                                    'sha256':digest(V/'results'/('calibration_'+d['dataset']+'.json'))} for d in data]})
    assert not (V/'config.locked.json').exists()
    dump(V/'config.locked.json',c)
    bound_files=[V/'src'/x for x in ['prepare.py','common.hpp','calibrate.cpp','build.sh','run_logged.py']]+[V/'bin/calibrate']
    for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
        bound_files += [V/'inputs'/ds/x for x in ['config.json','identities.json','row_ids.i64','queries.f32']]
    dump(V/'protocol_lock.json',{'config_sha256':digest(V/'config.locked.json'),
        'protocol_sha256':digest(V/'protocol.md'),'prelock_config_sha256':digest(V/'config.prelock.json'),
        'bound_files':[{'path':str(p),'sha256':digest(p)} for p in bound_files],
        'locked_utc':c['locked_utc'],'GT_opened_before_lock':False,'C2_quality_seen':False})
    s=json.loads((V/'state.json').read_text());s.update({'status':'C0_LOCKED_C1_PENDING','C0':'PASS','C1':'IN_PROGRESS'})
    dump(V/'state.json',s)
    print(json.dumps({'checkpoint':cp,'B':B}))

if __name__=='__main__':
    import sys
    {'prepare':prepare,'lock':lock}[sys.argv[1]]()
