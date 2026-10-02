"""Locked cost-sensitive linear gates. No audit/validation data access."""
import math
import time
import numpy as np
from common import RUN, DATASETS, FEATURES, read, dump, identity, check_lock, update_state
from gate_stats import load_pair, ratios_stats, cross_L_stats
from verify_outputs import predict

LAMBDAS = [.01, .1, 1.0]
QUANTILES = [.10, .25, .50, .75]


def sigmoid(z):
    out = np.empty_like(z)
    positive = z >= 0
    out[positive] = 1 / (1 + np.exp(-z[positive]))
    ez = np.exp(z[~positive])
    out[~positive] = ez / (1 + ez)
    return out


def objective(theta, X, P, N, lam):
    z = X @ theta
    total = (P + N).sum()
    probability = sigmoid(z)
    penalty = np.r_[np.full(X.shape[1] - 1, lam), 0.0]
    value = ((P * np.logaddexp(0.0, -z) + N * np.logaddexp(0.0, z)).sum() / total
             + .5 * np.sum(penalty * theta * theta))
    gradient = X.T @ ((P + N) * probability - P) / total + penalty * theta
    curvature = (P + N) * probability * (1 - probability) / total
    hessian = X.T @ (X * curvature[:, None]) + np.diag(penalty)
    return float(value), gradient, hessian


def fit_model(x, P, N, lam, feature_set):
    start = time.monotonic()
    mu = x.mean(axis=0)
    scale = np.maximum(x.std(axis=0), 1e-6)
    normalized = np.clip((x - mu) / scale, -6, 6)
    X = np.column_stack([normalized, np.ones(len(x))])
    theta = np.zeros(X.shape[1])
    trace = []
    if P.sum() == 0 or N.sum() == 0:
        constant = int(P.sum() > 0)
        theta[-1] = 1.0 if constant else -1.0
        status = 'NO_TWO_CLASS_SIGNAL_CONSTANT_REFERENCE'
    else:
        theta[-1] = math.log(float(P.sum() / N.sum()))
        status = 'SOLVER_NOT_CONVERGED'
        for iteration in range(201):
            loss, g, H = objective(theta, X, P, N, lam)
            grad_inf = float(np.abs(g).max())
            row = {'iteration': iteration, 'loss': loss, 'gradient_inf': grad_inf}
            trace.append(row)
            if grad_inf <= 1e-8:
                status = 'CONVERGED'
                break
            if iteration == 200:
                break
            step = np.linalg.solve(H, g)
            descent = float(g @ step)
            assert descent > 0 and np.isfinite(step).all()
            fraction = 1.0
            for _ in range(60):
                proposal = theta - fraction * step
                new_loss = objective(proposal, X, P, N, lam)[0]
                if new_loss <= loss - 1e-4 * fraction * descent:
                    theta = proposal
                    row['step_fraction'] = fraction
                    break
                fraction *= .5
            else:
                raise RuntimeError('Locked Newton backtracking failed')
        assert status == 'CONVERGED', trace[-1]
    model = {'feature_set': feature_set, 'features': FEATURES[:x.shape[1]],
             'mean': mu.tolist(), 'scale': scale.tolist(),
             'beta': theta[:-1].tolist(), 'bias': float(theta[-1]), 'threshold': 0.0,
             'lambda': lam, 'fit_queries': len(x), 'status': status,
             'positive_hit_weight': int(P.sum()), 'negative_hit_weight': int(N.sum()),
             'standardization': 'fit_all_rows_population_std_floor_1e-6_clip_minus6_plus6',
             'decision': 'sequential_float64_logit_greater_equal_threshold',
             'training_seconds': time.monotonic() - start}
    return model, trace


def candidate_key(c, closest=False):
    s = c['cal']
    rest = (s['net_delta_hits'], -s['negative_events_retained'], -s['switch_queries'],
            c['model']['lambda'], -c['threshold_index'])
    return (s['S'], *rest) if closest else rest


def select(candidates):
    nonconstant = [c for c in candidates if c['cal']['nonconstant_on_this_split']]
    feasible = [c for c in nonconstant if c['cal']['target_met']]
    if feasible:
        chosen = max(feasible, key=candidate_key)
        status = 'CAL_TARGET_MET'
    elif nonconstant:
        chosen = max(nonconstant, key=lambda c: candidate_key(c, closest=True))
        status = 'CAL_TARGET_NOT_MET'
    else:
        chosen = max(candidates, key=lambda c: candidate_key(c, closest=True))
        status = 'CONSTANT_FALLBACK_NO_NONCONSTANT_CAL_RULE'
    return chosen, status


def selftest():
    rng = np.random.Generator(np.random.PCG64(20260910))
    X = np.column_stack([rng.normal(size=(31, 4)), np.ones(31)])
    P = rng.integers(0, 12, 31).astype(float)
    N = rng.integers(0, 12, 31).astype(float)
    theta = rng.normal(size=5)
    value, gradient, hessian = objective(theta, X, P, N, .1)
    eps = 1e-5
    fdg, fdh = [], []
    for j in range(5):
        e = np.zeros(5); e[j] = eps
        plus = objective(theta + e, X, P, N, .1)
        minus = objective(theta - e, X, P, N, .1)
        fdg.append((plus[0] - minus[0]) / (2 * eps))
        fdh.append((plus[1] - minus[1]) / (2 * eps))
    assert np.max(np.abs(np.asarray(fdg) - gradient)) < 1e-9
    assert np.max(np.abs(np.asarray(fdh).T - hessian)) < 1e-9
    assert np.linalg.eigvalsh(hessian).min() > 0
    # Equivalent repetition of weighted positive and negative logistic examples.
    z = X @ theta
    repeated = np.r_[np.repeat(np.logaddexp(0, -z), P.astype(int)),
                     np.repeat(np.logaddexp(0, z), N.astype(int))].mean()
    assert abs(value - repeated - .05 * np.sum(theta[:-1] ** 2)) < 1e-12
    model, trace = fit_model(X[:, :4], P, N, .1, 'test')
    assert trace[-1]['gradient_inf'] <= 1e-8
    for p, n, expected in [(np.zeros(31), np.zeros(31), False), (np.ones(31), np.zeros(31), True), (np.zeros(31), np.ones(31), False)]:
        m, _ = fit_model(X[:, :4], p, n, 1., 'test')
        assert np.all(predict(X[:, :4], m)[1] == expected)
    h0 = np.full((4, 2), 5)
    h1 = h0 + np.asarray([[2, -1], [0, 3], [-4, 0], [0, 0]])
    s = ratios_stats(h0, h1, [1, 1, 0, 0])
    assert s['positive_hits_retained'] == 5 and s['negative_hits_avoided'] == 4
    assert s['net_delta_hits'] == 4 and s['R'] == 1 and s['A'] == .5 and s['Ah'] == .8
    all0 = ratios_stats(h0, h1, np.zeros(4, bool))
    all1 = ratios_stats(h0, h1, np.ones(4, bool))
    assert all0['R'] == 0 and all0['A'] == 1 and not all0['target_met']
    assert all1['R'] == 1 and all1['A'] == 0 and not all1['target_met']
    # Feasible gate wins before raw net; fewer harmed, fewer switches, stronger lambda are ties.
    def fake(name, net, harm=1, switches=2, lam=.1, idx=0, feasible=True, S=1):
        return {'name': name, 'threshold_index': idx, 'model': {'lambda': lam},
                'cal': {'nonconstant_on_this_split': True, 'target_met': feasible, 'S': S,
                        'net_delta_hits': net, 'negative_events_retained': harm, 'switch_queries': switches}}
    assert select([fake('bad', 100, feasible=False), fake('good', 4)])[0]['name'] == 'good'
    assert select([fake('weak', 4, lam=.01), fake('strong', 4, lam=1)])[0]['name'] == 'strong'
    assert select([fake('lowS', 100, feasible=False, S=.2), fake('highS', 4, feasible=False, S=.8)])[0]['name'] == 'highS'
    return {'status': 'PASS', 'finite_difference_gradient_max_error': float(np.max(np.abs(np.asarray(fdg)-gradient))),
            'finite_difference_hessian_max_error': float(np.max(np.abs(np.asarray(fdh).T-hessian))),
            'weighted_repetition_equivalence': 'PASS', 'constant_and_zero_signal': 'PASS',
            'event_and_hit_accounting_with_cross_L_conflict': 'PASS', 'selection_order_and_ties': 'PASS'}


def main():
    lock = check_lock()
    assert not (RUN / 'models/frozen_before_audit.json').exists()
    assert read(RUN / 'reviews/cal_pairs_verification.json')['status'] == 'PASS'
    assert not any(j['status'] == 'RUNNING' for j in read(RUN / 'reviews/search_jobs.json'))
    dump(RUN / 'reviews/learner_selftest.json', selftest())
    selections, frozen = {}, []
    for ds in DATASETS:
        fit_folder, fit_x, fit_h0, fit_h1 = load_pair(ds, 'fit')
        cal_folder, cal_x, cal_h0, cal_h1 = load_pair(ds, 'cal')
        d = fit_h1 - fit_h0
        P = np.maximum(d, 0).sum(axis=1).astype(float)
        N = np.maximum(-d, 0).sum(axis=1).astype(float)
        by_kind = {}
        for kind, width in [('base_gate', 7), ('dual_gate', 13)]:
            candidates, fits = [], []
            for lam in LAMBDAS:
                model, trace = fit_model(fit_x[:, :width], P, N, lam, kind)
                z, _ = predict(fit_x, model)
                thresholds = [0.] + np.quantile(z, QUANTILES, method='linear').tolist()
                fits.append({'model_at_threshold_zero': model, 'optimization_trace': trace,
                             'fit_logit_quantiles': thresholds[1:]})
                for i, threshold in enumerate(thresholds):
                    current = {**model, 'threshold': float(threshold)}
                    _, cf = predict(fit_x, current)
                    _, cc = predict(cal_x, current)
                    candidates.append({'name': f'{kind}_lambda{lam:g}_threshold{i}', 'threshold_index': i,
                                       'threshold_source': 'zero' if i == 0 else f'fit_logit_quantile_{QUANTILES[i-1]}',
                                       'model': current, 'fit': ratios_stats(fit_h0, fit_h1, cf),
                                       'cal': ratios_stats(cal_h0, cal_h1, cc)})
            assert len(candidates) == 15
            selected, status = select(candidates)
            path = RUN / 'models' / ds / f'{kind}.json'
            assert not path.exists()
            dump(path, {**selected['model'], 'selection_status': status, 'candidate': selected['name'],
                        'protocol_sha256': lock['protocol_sha256']})
            frozen.append(path)
            table_path = RUN / 'models' / ds / f'{kind}_candidates.json'
            dump(table_path, {'candidates': candidates, 'fits': fits, 'selected': selected['name'], 'status': status})
            frozen.append(table_path)
            by_kind[kind] = {'model_path': str(path), 'candidate': selected['name'], 'status': status,
                             'cal': selected['cal'], 'fit': selected['fit']}
        def primary_key(item):
            kind, value = item
            c = value['cal']
            return (value['status'] == 'CAL_TARGET_MET', c['S'], c['net_delta_hits'],
                    -c['negative_events_retained'], kind == 'base_gate')
        primary = max(by_kind.items(), key=primary_key)[0]
        selections[ds] = {'primary': primary, 'gates': by_kind,
                          'fit_cross_L': cross_L_stats(fit_h0, fit_h1), 'cal_cross_L': cross_L_stats(cal_h0, cal_h1),
                          'feature_quartile_boundaries_fit_only': {FEATURES[j]: np.quantile(fit_x[:, j], [.25,.5,.75]).tolist() for j in range(13)},
                          'controls': {stage: {name: ratios_stats(h0, h1, np.full(len(h0), choice, bool))
                                             for name, choice in [('always_A0', False), ('always_A1', True)]}
                                       for stage, h0, h1 in [('fit', fit_h0, fit_h1), ('cal', cal_h0, cal_h1)]}}
        for folder in [fit_folder, cal_folder]:
            frozen.extend([folder / 'features.f64', folder / 'config.json', folder / 'results.json',
                           folder / 'independent_verification.json'])
            for kind in ['fast20k', 'e24']:
                for L in [64,128]:
                    frozen.extend([folder / f'{kind}_L{L}/hits.u8', folder / f'{kind}_L{L}/hitmask.u16'])
        frozen.extend([p for p in (RUN / 'inputs' / ds).rglob('*') if p.is_file()])
        print(ds, primary, by_kind[primary]['status'], by_kind[primary]['cal'], flush=True)
    dump(RUN / 'models/selections.json', selections)
    frozen.extend([RUN / 'models/selections.json', RUN / 'src/train.py', RUN / 'src/gate_stats.py',
                   RUN / 'src/verify_outputs.py', RUN / 'src/gate_policy.hpp', RUN / 'src/evaluate.cpp',
                   RUN / 'bin/evaluate', RUN / 'bin/evaluate.build.json', RUN / 'reviews/learner_selftest.json',
                   RUN / 'protocol.md', RUN / 'config.locked.json', RUN / 'reviews/protocol_lock.json'])
    dump(RUN / 'models/frozen_before_audit.json', {'status': 'FROZEN_BEFORE_AUDIT_AND_VALIDATION',
         'frozen_unix': time.time(), 'protocol_sha256': lock['protocol_sha256'],
         'files': [identity(p) for p in frozen], 'data_access': 'fit_and_cal_only',
         'candidates_per_dataset': 30, 'primary': {ds: selections[ds]['primary'] for ds in DATASETS}})
    update_state(status='MODELS_FROZEN_BEFORE_AUDIT')
    print('ALL_MODELS_FROZEN', flush=True)


if __name__ == '__main__':
    main()
