"""Independent raw-return, budget-transfer and optional neighbor-control audit."""
from common import RUN, ROOT, OLD, read, dump, identity, protected_check
import time
import numpy as np

start = time.monotonic()
lock = read(RUN/'config.locked.json')
response = read(RUN/'analysis/response.json')
jobs = read(RUN/'reviews/jobs_v2.json')
assert all(j['exit_code'] == 0 for j in jobs)
assert sum(j['reserved_calls'] for j in jobs) == lock['planned_NSG_calls'] == 331136
assert all(j['observed_max_tasks'] == 1 for j in jobs if j['reserved_calls'])
assert read(RUN/'reviews/header_dependencies.json')['new_searches_before_repair'] == 0
points = 0
query_outputs = 0
transfers = 0
neighbor_checks = 0
for ds, cfg in lock['datasets'].items():
    native = cfg['native']
    stored = np.load(RUN/'analysis'/f'{ds}.npz')
    gt = np.fromfile(native['GT'],'<i4').reshape(4096,100)
    methods = [m['name'] for m in native['methods']]
    cols = [methods.index(m) for m in lock['actions']]
    assert np.array_equal(stored['source_rows'],np.fromfile(native['rows'],'<i8'))
    for K in [1,100]:
        gt_sets = [set(map(int,row[:K])) for row in gt]
        for L in sorted(set(cfg['old_K_L'][str(K)]+cfg['missing'][str(K)])):
            origin = RUN if L in cfg['missing'][str(K)] else OLD
            for a, method in enumerate(methods):
                path = origin/'results'/('main_'+ds)/method/f'k{K}_L{L}'
                ids = np.fromfile(path/'ids.i32','<i4').reshape(4096,K)
                counts = np.array([sum(int(v) in members for v in row) for row,members in zip(ids,gt_sets)],'i2')
                assert np.array_equal(counts,stored[f'K{K}_L{L}'][:,a])
                assert np.array_equal(np.fromfile(path/'ndc.u64','<u8'),stored[f'NDC_K{K}_L{L}'][:,a])
                if origin == RUN and method == 'DefaultANN':
                    ref = __import__('pathlib').Path(native['reference'])/f'k{K}'/(native['reference_method']+f'_L{L}')
                    for new_name,old_name in [('ids.i32','ids.i32'),('distances.f32','distances.f32'),('ndc.u64','graph_ndc.u64')]:
                        assert (path/new_name).read_bytes() == (ref/old_name).read_bytes()
                points += 1
                query_outputs += 4096
    for record in [r for r in response['all_transfers'] if r['dataset'] == ds]:
        K,L = record['K'],record['L']
        low = stored[f'K{K}_L128'][:,cols]
        target = stored[f'K{K}_L{L}'][:,cols]
        chosen = np.array([max(range(7),key=lambda a:int(row[a])) for row in low])
        selected = np.array([int(row[a]) for row,a in zip(target,chosen)])
        upper = np.array([max(map(int,row)) for row in target])
        gain = (upper-target[:,0]).mean()/K
        inherited = (selected-target[:,0]).mean()/K
        assert abs(100*gain-record['oracle_gain_pp'])<1e-10
        assert abs(100*inherited-record['transferred_gain_pp'])<1e-10
        if gain:
            assert abs(inherited/gain-record['retention'])<1e-10
        overlap = np.mean([bool(set(np.flatnonzero(a==max(a)))&set(np.flatnonzero(b==max(b)))) for a,b in zip(low,target)])
        assert abs(overlap-record['optimal_set_overlap'])<1e-12
        transfers += 1
    if (RUN/'analysis/information.json').exists():
        info = np.load(RUN/'analysis'/f'{ds}.information.npz')
        roles = read(RUN/'analysis'/f'{ds}.information_roles.json')
        q = np.fromfile(native['queries'],'<f4').reshape(4096,native['dimension']).astype('f8')
        q /= np.sqrt((q*q).sum(1))[:,None]
        high = np.stack([stored[f'K{K}_L{cfg["target"][str(K)][1]}'][:,cols] for K in [1,100]],axis=-1)
        low = np.stack([stored[f'K{K}_L128'][:,cols] for K in [1,100]],axis=-1)
        delta = high-high[:,:1]
        low_delta = low-low[:,:1]
        for f in range(4):
            fit = np.array(roles[str(f)]['fit'])
            outer = np.array(roles[str(f)]['outer'])
            shuffled = np.array(roles[str(f)]['shuffled_fit'])
            assert not set(fit)&set(outer) and len(set(fit)|set(outer)) == 4096
            assert np.all(info['folds'][fit]!=f) and np.all(info['folds'][outer]==f)
            assert np.array_equal(np.sort(shuffled),fit)
            lookup = {int(a):int(b) for a,b in zip(fit,shuffled)}
            for i in outer:
                nn = info['neighbors'][i]
                assert len(set(map(int,nn))) == 55 and np.all(info['folds'][nn]!=f)
                perm = np.array([lookup[int(j)] for j in nn])
                expected = {
                    'TargetKNN':sum((delta[j].astype('i8') for j in nn))/(55*np.array([1.,100.])),
                    'LowKNN':sum((low_delta[j].astype('i8') for j in nn))/(55*np.array([1.,100.])),
                    'ShuffleKNN':sum((delta[j].astype('i8') for j in perm))/(55*np.array([1.,100.])),
                    'TargetFixed':delta[fit].sum(0,dtype='i8')/(3072*np.array([1.,100.]))}
                for method,pred in expected.items():
                    assert np.array_equal(pred,info[method+'_scores'][i])
                    action = np.array([max(range(7),key=lambda a:pred[a,k]) for k in range(2)])
                    assert np.array_equal(action,info[method+'_actions'][i])
                    payoff = np.array([delta[i,action[k],k]/K for k,K in enumerate([1,100])])
                    assert np.array_equal(payoff,info[method+'_delta'][i])
                if i%64 == 0:
                    sim = np.array([np.dot(q[i],q[j]) for j in fit])
                    cutoff = np.partition(sim,-55)[-55]
                    assert min(float(np.dot(q[i],q[j])) for j in nn) >= cutoff-1e-12
                    neighbor_checks += 1
    print('AUDITED',ds,flush=True)

primary = response['primary']
headroom = all(p['oracle_gain_pp']>=.25 for p in primary)
mismatch = any(p['retention'] is None or p['retention']<.8 for p in primary if p['L']!=128)
assert (headroom and mismatch) == response['information_control_eligible']
if response['information_control_eligible']:
    info = read(RUN/'analysis/information.json')
    passes = []
    for ds, r in info['results'].items():
        main = r['methods']['TargetKNN']
        c = r['contrasts']
        passed = main['mean_gain_pp']>0 and main['CI95_pp'][0]>0 and min(main['K_mean_gain_pp'])>=0
        passed = passed and c['TargetFixed']['CI95_pp'][0]>0 and c['ShuffleKNN']['CI95_pp'][0]>0 and c['LowKNN']['gain_pp']>0
        assert bool(passed) == r['pass_all']
        passes.append(bool(passed))
    assert all(passes) == info['pass_all']

protected_check()
for name in ['execution_started_v2.json','pre_response_information_design.json']:
    for item in read(RUN/'reviews'/name)['files']:
        assert identity(item['path']) == item
for item in read(RUN/'reviews/header_dependencies.json')['files']:
    assert identity(item['path']) == item
assert identity(RUN/'bin/evaluate') == read(RUN/'reviews/binary.json')
dump(RUN/'reviews/independent_audit.json',dict(status='PASS',points=points,query_outputs=query_outputs,
    budget_transfers=transfers,neighbor_boundary_checks=neighbor_checks,
    raw_GT_rescoring='all old and new points, independent Python membership loops',
    source_and_input_identity=True,actual_native_threads=1,independent_implementation=True,
    independent_person=False,seconds=time.monotonic()-start))
print('PASS',points,query_outputs,transfers,neighbor_checks,flush=True)
