#!/usr/bin/env python3
"""Evaluate the frozen E176 dynamic public 10K sweep only after both native jobs finish."""
import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
L_VALUES = (200, 400, 800, 1000, 1200)
METHODS = ()
LEGACY_SAME_L_PAIRS = (('GT', 'NSG'), ('M5', 'GT'), ('M5', 'NSG'),
                ('M5REG96', 'GT'), ('M5REG96', 'M5'), ('M5REG96', 'NSG'))

def require(ok, message):
    if not ok:
        raise ValueError(message)

def read_json(p):
    return json.loads(Path(p).read_text())

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def stat4(p):
    s = Path(p).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]

def register_stat_source(path, expected, preflight, execution, sources, source_stats):
    # No query vector payload is opened here. Bind the actual preflight full
    # SHA to the execution lock and current metadata, then recheck at the end.
    path = str(Path(path))
    record = preflight['registered_input_files'][path]
    current = stat4(path)
    require(len(expected) == 64 and record['sha256'] == expected,
            f'registered preflight source SHA: {path}')
    require(current == execution['input_stats'][path], f'current frozen input stat: {path}')
    require(path not in sources or sources[path] == expected, f'consistent source SHA: {path}')
    sources[path] = expected
    source_stats[path] = current

def raw(p, dtype, shape):
    a = np.fromfile(p, dtype=dtype)
    require(a.size == int(np.prod(shape)) if -1 not in shape else a.size % int(np.prod([x for x in shape if x != -1])) == 0, f'shape: {p}')
    return a.reshape(shape)

def csv_write(p, rows):
    if not rows:
        p.write_text('')
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})

def ci(delta, K, key):
    values, counts = np.unique(delta, return_counts=True)
    seed = (20261010 + int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], 'little')) % 2**32
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(len(delta), counts / len(delta), size=2000)
    means = draws @ values.astype(float) / (len(delta) * K) * 100
    lo, hi = np.quantile(means, [.025, .975])
    return {'low_pp': float(lo), 'high_pp': float(hi), 'seed': seed, 'repeats': 2000,
            'scope': 'descriptive paired query bootstrap, no semantic IID or simultaneous comparison guarantee'}

def compare(a, b):
    p, r = a['point'], b['point']
    delta = a['hits'].astype(int) - b['hits'].astype(int)
    rescue = (a['members'] & ~b['members']).sum(axis=1)
    damage = (b['members'] & ~a['members']).sum(axis=1)
    require(np.array_equal(delta, rescue.astype(int) - damage.astype(int)), 'member delta identity')
    ratios = np.asarray(p['qps_rounds']) / np.asarray(r['qps_rounds'])
    key = f"{p['role']}|{p['dataset']}|{p['K']}|{p['L']}|{p['method']}|{r['L']}|{r['method']}"
    return {'role': p['role'], 'dataset': p['dataset'], 'K': p['K'], 'L': p['L'],
            'method': p['method'], 'reference_L': r['L'], 'reference': r['method'],
            'n': p['n'], 'recall_delta_pp': float(delta.sum() / (p['n'] * p['K']) * 100),
            'rescue_members': int(rescue.sum()), 'damage_members': int(damage.sum()),
            'queries_net_improved': int((delta > 0).sum()), 'queries_net_damaged': int((delta < 0).sum()),
            'paired_qps_ratio_rounds': ratios.tolist(), 'paired_qps_ratio_median': float(np.median(ratios)),
            'paired_qps_change_pct': float((np.median(ratios) - 1) * 100),
            'qps_ratio_pairing_scope': 'same KL round matched sequential methods' if p['L'] == r['L'] else 'cross L round index only, descriptive, not simultaneous or randomized pairing',
            'speed_ranges_separated': bool(min(p['qps_rounds']) > max(r['qps_rounds'])),
            'all_rounds_faster': bool(np.all(ratios > 1)),
            'observed_joint_gain': bool(delta.sum() > 0 and np.median(ratios) > 1),
            'delta_ci': ci(delta, p['K'], key)}

def posting_U(p):
    b = Path(p).read_bytes()
    require(b[:8] == b'M5POST1\0', 'posting magic')
    h = struct.unpack_from('<8I', b, 8)
    require(h[0] == 1 and h[2] == 8, 'posting header')
    H = h[1]
    counts = np.frombuffer(b, dtype='u1', count=H, offset=40 + 4 * H)
    ids = np.frombuffer(b, dtype='<i4', count=H * 8, offset=40 + 5 * H).reshape(H, 8)
    return set(int(ids[i, j]) for i in range(H) for j in range(int(counts[i])))


def methods_order(config):
    names = [m['name'] for m in config['methods']]
    require(len(set(names)) == len(names) and 'GT' in names and 'M5' in names, 'unique prelocked methods')
    return [x for x in names if x != 'M5RES12'] + (['M5RES12'] if 'M5RES12' in names else [])

def comparison_spec(config):
    order = methods_order(config)
    same = [(a, b) for i, a in enumerate(order) for b in order[:i]]
    candidates = [m['name'] for m in config['methods'] if m['family'] != 'base']
    return same, candidates

def model_path(config, K, L, family):
    value = config['completion_models'][f'k{K}_L{L}'][family]
    return Path(value['path'] if isinstance(value, dict) else value)

def completion_table(path, base_n, sources, source_stats, preflight, execution):
    expected = preflight['registered_input_files'][str(path)]['sha256']
    register_stat_source(str(path), expected, preflight, execution, sources, source_stats)
    require(sha(path) == expected, 'completion model exact bytes')
    require(path.stat().st_size % 28 == 0, 'Nx7 raw completion table')
    rows = raw(path, '<i4', (path.stat().st_size//28, 7))
    table, previous = {}, None
    for r in rows:
        hub, winner, count = map(int, r[:3]); key = (hub, winner)
        require(previous is None or key > previous, 'strict completion key order')
        require(0 <= hub < base_n and (winner == -1 or 0 <= winner < base_n) and 0 <= count <= 4,
                'completion key and count domain')
        targets = list(map(int, r[3:3+count]))
        require(len(set(targets)) == count and all(0 <= x < base_n for x in targets)
                and all(int(x) == -1 for x in r[3+count:]), 'completion IDs/padding')
        table[key] = targets; previous = key
    return table

def gate_configs(lock, state):
    require(state['status'] == 'NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION' and state.get('active') is None,
            'all native jobs must finish before GT decoding')
    require(len(state['completed']) == len(lock['jobs']) and all(x['exit_code'] == 0 for x in state['completed']), 'every native exit0')
    configs = []
    for job, expected in lock['jobs'].items():
        require(sha(job) == expected, 'frozen job SHA'); c = read_json(job)
        require(c['role'] == 'public_test' and c['n'] == 10000 and c['threads'] == 1 and c['cpu'] == 15
                and c['no_training'] and c['K_values'] == [1,100] and tuple(c['L']) == L_VALUES
                and c['timing_repeats'] == 3 and c['audit_n'] == 256, 'frozen public test scope')
        names = methods_order(c); require(len(names) == len(c['methods']), 'method matrix')
        complete = read_json(Path(c['out'])/'complete.json')
        require(complete['status'].startswith('PASS') and not complete['smoke_only'] and complete['no_GT_read']
                and complete['no_training'] and complete['full_plain_return_n'] == c['n']
                and complete['count_audit_n'] == 256, 'full formal native completion')
        count = len(c['methods'])*len(c['K_values'])*len(c['L'])
        require(len(complete['results']) == count and complete['wall_rounds'] == 3*count, 'complete dynamic matrix')
        require(read_json(Path(c['out'])/'job.json') == c, 'executed job identity')
        for K in c['K_values']:
            for L in c['L']:
                for method in c['methods']:
                    p = read_json(Path(c['out'])/f'k{K}/{method["name"]}_L{L}/complete.json')
                    require(p in complete['results'] and (p['method'],p['K'],p['L'],p['n']) == (method['name'],K,L,c['n']), 'point identity')
                    require(not p['smoke_only'] and p['plain_count_bits_equal'] and p['count_audit_n'] == 256
                            and p['full_plain_return_n'] == c['n'] and len(p['timing_seconds']) == 3
                            and p['full_plain_independent_replay_bits_equal'] is False
                            and p['full_plain_independent_replay_n'] == 0, 'one full oracle pass; no second replay claim')
                    require(p['full_plain_independent_scalar_linear_oracle'] is bool(method['table']), 'scalar/linear oracle scope')
                    require(p['original_scalar_main_kernel'] is True and p['main_packet_words_equal_fresh_GT'] is (method['name'] != 'NSG'), 'main kernel binding')
                    if method['optimized'] or method['family'] in ('bank','route_bank'):
                        require(p['cached_main_R_fresh_score_words_equal'] is True and p['cached_R_word_check_n'] == c['n']*K, 'full cached R word proof')
                    if method['family'] in ('opt','opt_reg'):
                        reference = 'M5' if method['family'] == 'opt' else 'M5REG96'
                        require(p['optimized_reference_method'] == reference and p['optimized_reference_packet_bits_equal'], 'optimized old packet identity')
        configs.append(c)
    require({c['dataset'] for c in configs} == set(DATASETS) and len(configs) == 2, 'both distinct data jobs')
    expected = sum(len(c['methods'])*len(c['L'])*len(c['K_values']) for c in configs)
    require(state['planned_points'] == expected and state['planned_timed_batches'] == 3*expected, 'state dynamic scope')
    return configs

def mechanism(packet, baseline, gt_packet, truth, method, table_rows, old_support, teacher,
              completion, sources, stats_sources):
    p = packet['point']; n,K = p['n'],p['K']; root=Path(p['source_complete']).parent
    light = method['family'] in ('bank','route_bank')
    trace_path=root/'raw'/('completion_trace.i32' if light else 'region_trace.i32')
    sources[str(trace_path)]=sha(trace_path); stats_sources[str(trace_path)]=stat4(trace_path)
    trace=raw(trace_path,'<i4',(n,20 if light else 128)); offset=8 if light else 32
    cap=12 if light else 96
    m={key:p[key] for key in ('role','dataset','K','L','method','n')}
    m.update(dict(C_total=0,X_total=0,selected_seeds_total=0,queries_with_X=0,
                  X_outside_original_M5_U=0,X_outside_original_TRAIN_GT100_U=0,
                  new_rescues_vs_M5=0,new_rescues_outside_original_M5_U=0,new_rescues_outside_original_TRAIN_GT100_U=0,
                  new_damage_vs_M5=0,new_damage_outside_original_M5_U=0,new_damage_outside_original_TRAIN_GT100_U=0,extension_aborted=0))
    for i,row in enumerate(trace):
        nc,nx,ns,committed,aborted=map(int,row[3:8])
        require(0<=nc<=24 and 0<=nx<=cap and 0<=ns<=3 and committed in (0,1) and aborted in (0,1), 'trace caps/status')
        R=set(map(int,gt_packet['ids'][i])); R.discard(-1)
        C=[]; seen=set(R)
        labels=list(map(int,gt_packet['entries'][i]))
        for label in gt_packet['entries'][i]:
            if any(h not in table_rows for h in labels):break
            for target in table_rows[int(label)]:
                if target not in seen:C.append(target);seen.add(target)
        require(not committed or len(C)==nc, 'entire original C retained')
        C=C[:nc]; X=list(map(int,row[offset:offset+nx])); winners=list(map(int,row[:3]))
        require(len(set(X))==nx and all(0<=x<packet['base_n'] for x in X) and not set(X)&(R|set(C)), 'X unique/domain and disjoint')
        require(all(int(x)==-1 for x in row[offset+nx:]), 'trace inactive padding')
        if not committed:require(nx==ns==aborted==0,'no extension before committed M5')
        if light:
            require(sum(x>=0 for x in winners)==ns, 'winner rows count; repeated winners permitted')
            for h,w in zip(gt_packet['entries'][i],winners):
                require(w==-1 or (w in C and w in table_rows.get(int(h),[])), 'winner belongs original route row C')
            plan=[]; seen=set(R)|set(C)
            if committed:
                for h,w in zip(gt_packet['entries'][i],winners):
                    if method['completion_family']=='pair' and w<0:continue
                    key=(int(h),w if method['completion_family']=='pair' else -1)
                    for target in completion.get(key,[]):
                        if target not in seen:plan.append(target);seen.add(target)
            require(X==plan[:nx] and (aborted or X==plan), 'independent completion arrival; pair miss stays empty')
        else:
            require(list(map(int,row[8:8+nc]))==C, 'full original C trace')
            require(all(w==-1 for w in winners[ns:]) and len(set(winners[:ns]))==ns and set(winners[:ns])<=set(C), 'old seed uniqueness')
        actual=set(map(int,packet['ids'][i]));actual.discard(-1)
        original=set(map(int,baseline['ids'][i]));original.discard(-1)
        require(actual<=R|set(C)|set(X),'returned support')
        if aborted:require(np.array_equal(packet['ids'][i],baseline['ids'][i]) and np.array_equal(packet['distances'][i].view('<u4'),baseline['distances'][i].view('<u4')),'extension failure original M5 word fallback')
        T=set(map(int,truth[i,:K]));plus=(actual-original)&T;minus=(original-actual)&T
        require(plus<=set(X),'true new rescue from X')
        m['C_total']+=nc;m['X_total']+=nx;m['selected_seeds_total']+=ns;m['queries_with_X']+=nx>0;m['extension_aborted']+=aborted
        m['X_outside_original_M5_U']+=len(set(X)-old_support);m['X_outside_original_TRAIN_GT100_U']+=len(set(X)-teacher)
        for prefix,values in [('new_rescues',plus),('new_damage',minus)]:
            m[prefix+'_vs_M5']+=len(values);m[prefix+'_outside_original_M5_U']+=len(values-old_support);m[prefix+'_outside_original_TRAIN_GT100_U']+=len(values-teacher)
    for key in ('C','X','selected_seeds'):m[key+'_mean']=m[key+'_total']/n
    return m

def posting_rows(path):
    b=Path(path).read_bytes();H=struct.unpack_from('<I',b,12)[0]
    labels=np.frombuffer(b,dtype='<i4',count=H,offset=40)
    counts=np.frombuffer(b,dtype='u1',count=H,offset=40+4*H)
    ids=np.frombuffer(b,dtype='<i4',count=8*H,offset=40+5*H).reshape(H,8)
    return {int(label):list(map(int,ids[i,:int(counts[i])])) for i,label in enumerate(labels)}

def completion_qualification(config, preflight, execution, sources, source_stats):
    if not any(m['family'] in ('bank','route_bank') for m in config['methods']):return
    path=Path(config.get('completion_manifest',ROOT/'models'/config['dataset']/'compile_manifest.json'))
    expected=preflight['registered_input_files'][str(path)]['sha256']
    register_stat_source(str(path),expected,preflight,execution,sources,source_stats)
    require(sha(path)==expected,'qualified compiler manifest bytes')
    manifest=read_json(path)
    require(manifest['status']=='FROZEN_TRAIN_ONLY_POST_M5_RESIDUAL_COMPLETION_ALL_10_POINTS' and manifest['role']=='fit' and manifest['n']==20000 and manifest['point_count']==10 and manifest['public_test_read'] is False and manifest['old_train_debt_reset'] is False and manifest['train_budget_is_not_zero'] is True,'complete TRAIN-only FIT/compiler eligibility')
    require(set(manifest['models'])=={f'k{K}_L{L}' for K in config['K_values'] for L in config['L']},'all ten prelocked models qualified')
    for K in config['K_values']:
        for L in config['L']:
            for family in ('pair','route'):
                row=manifest['models'][f'k{K}_L{L}'][family];model=model_path(config,K,L,family)
                require(str(model)==row['path'] and row['bytes']==model.stat().st_size and row['sha256']==preflight['registered_input_files'][str(model)]['sha256'],'job/compiler/preflight model identity')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=ROOT/'analysis/final_v1');args=parser.parse_args()
    require(args.out.is_absolute() and not args.out.exists(),'preserve absolute analysis output')
    lock=read_json(ROOT/'parameter_lock.json');require(sha(ROOT/'protocol.md')==lock['protocol_sha256'],'protocol frozen')
    state=read_json(ROOT/'run_state.json');configs=gate_configs(lock,state)
    preflight=read_json(ROOT/'reviews/data_preflight.json');execution=read_json(ROOT/'execution_lock.json')
    require(preflight['status'].startswith('PASS'),'identities and model qualification')
    for path,expected in execution['input_stats'].items():require(stat4(path)==expected,'frozen source metadata')
    points=[];comparisons=[];mechanisms=[];sources={};source_stats={};packets={};supports={};rows_cache={}
    inventory=read_json(ROOT/'reviews/inventory.json')
    for ds,data in inventory['datasets'].items():
        path=data['m5']['path'];require(sha(path)==data['m5']['sha256'],'old M5 byte identity');sources[path]=data['m5']['sha256'];source_stats[path]=stat4(path)
        rows_cache[ds]=posting_rows(path)
        manifest=read_json(data['compile_manifest']);sources[data['compile_manifest']]=sha(data['compile_manifest']);source_stats[data['compile_manifest']]=stat4(data['compile_manifest'])
        teacher_path=next(p for p in manifest['input_sha256'] if p.endswith('/fit/gt.i64'))
        require(sha(teacher_path)==manifest['input_sha256'][teacher_path],'legal old TRAIN GT support')
        sources[teacher_path]=manifest['input_sha256'][teacher_path];source_stats[teacher_path]=stat4(teacher_path)
        supports[ds]=(posting_U(path),set(map(int,np.unique(raw(teacher_path,'<i8',(20000,100))))))
    for c in configs:
        completion_qualification(c,preflight,execution,sources,source_stats)
        n,N,ds,role=c['n'],c['base_n'],c['dataset'],c['role']
        for key,hk in [('queries','query_sha256'),('source_query_fvecs','source_query_sha256'),('source_GT_ivecs','source_GT_sha256'),('GT','GT_sha256'),('rows','rows_sha256')]:
            register_stat_source(c[key],c[hk],preflight,execution,sources,source_stats)
        for key,hk in [('GT','GT_sha256'),('rows','rows_sha256')]:require(sha(c[key])==c[hk],'existing label/row bytes')
        gt=raw(c['GT'],'<i4',(n,100));require(np.all((gt>=0)&(gt<N)) and all(len(set(r))==100 for r in gt),'frozen GT domain/unique')
        require(np.array_equal(raw(c['rows'],'<i8',(n,)),np.arange(n)),'public prefix row positions')
        env=read_json(Path(c['out'])/'native_environment.json');ep=env['enterpoint']
        for K in c['K_values']:
            for L in c['L']:
                for method in c['methods']:
                    name=method['name'];folder=Path(c['out'])/f'k{K}/{name}_L{L}';r=read_json(folder/'complete.json')
                    require(r['normal_output_release_before_stop'] and not r['timed_output_retained'],'complete normal output lifetime')
                    wall=np.asarray(r['timing_seconds']);require(np.all(np.isfinite(wall)&(wall>0)),'positive actual wall')
                    ids=raw(folder/'raw/ids.i32','<i4',(n,K));distances=raw(folder/'raw/distances.f32','<f4',(n,K))
                    entries=raw(folder/'raw/entry_ids.i32','<i4',(n,3));profiles=raw(folder/'raw/profile_distances.f32','<u4',(n,3))
                    graph=raw(folder/'raw/graph_ndc.u64','<u8',(256,));route=raw(folder/'raw/route_ndc.u64','<u8',(256,))
                    audit_ids=np.arange(256)*(n-1)//255;require(np.array_equal(raw(folder/'raw/audit_query_ids.i32','<i4',(256,)),audit_ids),'uniform256 IDs')
                    require(np.all(np.isfinite(distances)) and np.all((ids==-1)|((ids>=0)&(ids<N))) and np.all(distances[ids==-1]==np.finfo(np.float32).max),'return words/domain')
                    hits=np.empty(n,dtype=np.int16);members=np.zeros((n,K),dtype=bool)
                    for i in range(n):
                        valid=list(map(int,ids[i][ids[i]>=0]));require(len(set(valid))==len(valid),'return unique')
                        members[i]=[int(x) in set(valid) for x in gt[i,:K]];hits[i]=int(members[i].sum())
                    qps=n/wall
                    p={'role':role,'dataset':ds,'K':K,'L':L,'method':name,'n':n,'recall_pct':float(hits.sum()/(n*K)*100),'matched_GT_members':int(hits.sum()),
                       'qps_rounds':qps.tolist(),'qps_median':float(np.median(qps)),'qps_min':float(qps.min()),'qps_max':float(qps.max()),'wall_seconds':wall.tolist(),
                       'graph_ndc_sample_mean':float(graph.mean()),'route_ndc_sample_mean':float(route.mean()),'count_audit_n':256,'count_scope':'fixed 256 only; post included in graph_ndc',
                       'stats':r['stats'],'source_complete':str(folder/'complete.json')}
                    packet={'base_n':N,'point':p,'hits':hits,'members':members,'ids':ids,'entries':entries,'profiles':profiles,'graph':graph,'route':route,'distances':distances}
                    packets[(role,ds,K,L,name)]=packet;points.append(p)
                    for path in list(folder.iterdir())+list((folder/'raw').iterdir()):
                        if path.is_file():sources[str(path)]=sha(path);source_stats[str(path)]=stat4(path)
                base=packets[(role,ds,K,L,'GT')]
                for method in c['methods']:
                    name=method['name'];p=packets[(role,ds,K,L,name)]
                    if name=='NSG':require(np.all(p['entries'][:,0]==ep) and np.all(p['entries'][:,1:]==-1) and np.all(p['profiles']==0) and np.all(p['route']==0),'original NSG fixed route');continue
                    require(np.array_equal(p['entries'],base['entries']) and np.array_equal(p['profiles'],base['profiles']) and np.array_equal(p['route'],base['route']),'original GT route preserved')
                    s=p['point']['stats'];require(sum(map(int,p['graph']))-sum(map(int,base['graph']))==s['post_dots']+s['new_distances']==s['additional_scalar_calls'],'sample physical score fee')
                    if method['family'] in ('opt','opt_reg'):
                        ref='M5' if method['family']=='opt' else 'M5REG96';original=packets[(role,ds,K,L,ref)]
                        require(np.array_equal(p['ids'],original['ids']) and np.array_equal(p['distances'].view('<u4'),original['distances'].view('<u4')),'optimized saved packet exact identity')
                    if method['family'] in ('reg','bank','route_bank'):
                        completion={}
                        if method['family'] in ('bank','route_bank'):
                            path=model_path(c,K,L,method['completion_family']);completion=completion_table(path,N,sources,source_stats,preflight,execution)
                            require(all((w==-1 if method['completion_family']=='route' else w>=0) for h,w in completion),'completion family key domain')
                        U,teacher=supports[ds]
                        mechanisms.append(mechanism(p,packets[(role,ds,K,L,'M5')],base,gt,method,rows_cache[ds],U,teacher,completion,sources,source_stats))
                same,candidates=comparison_spec(c)
                comparisons.extend(compare(packets[(role,ds,K,L,a)],packets[(role,ds,K,L,b)]) for a,b in same)
            for i,small in enumerate(c['L']):
                for big in c['L'][i+1:]:
                    comparisons.extend(compare(packets[(role,ds,K,small,name)],packets[(role,ds,K,big,'GT')]) for name in candidates)
    expected=sum(len(c['methods'])*len(c['L'])*len(c['K_values']) for c in configs)
    expected_cmp=sum(len(c['K_values'])*(len(c['L'])*len(comparison_spec(c)[0])+len(c['L'])*(len(c['L'])-1)//2*len(comparison_spec(c)[1])) for c in configs)
    require(len(points)==expected and len(packets)==expected and len(comparisons)==expected_cmp,'complete prelocked dynamic analysis')
    require(all(stat4(path)==before for path,before in source_stats.items()),'all existing source metadata stable')
    result={'status':'COMPLETE_E176_DYNAMIC_FROZEN_EVALUATION','points':points,'comparisons':comparisons,'mechanisms':mechanisms,'source_sha256':sources,
            'test_no_training':True,'training_increment_seconds':state.get('training_increment_seconds'), 'default_replacement':False,'primary_method':lock['primary_method'],
            'scope':{'points':expected,'formal_timed_batches':3*expected,'comparisons':expected_cmp,'mechanisms':len(mechanisms),'same_L_all_unique_pairs':True},
            'limits':['historically exposed public_test10K; descriptive, no new confirmation','one full oracle pass, no full second native replay; fixed256 count only; timed packets not retained','CI descriptive; no semantic IID or simultaneous comparison guarantee','FIT is separate actual phase, not formal test training; prior debt retained','five measured L only; no interpolation or causal modality proof']}
    args.out.mkdir(parents=True);(args.out/'metrics.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    csv_write(args.out/'points.csv',points);csv_write(args.out/'comparisons.csv',comparisons);csv_write(args.out/'mechanisms.csv',mechanisms)
    # Member arrays are transient; do not serialize redundant scored NPZ.
    print(json.dumps({'status':result['status'],'points':expected,'comparisons':expected_cmp,'mechanisms':len(mechanisms)}))

if __name__=='__main__':main()
