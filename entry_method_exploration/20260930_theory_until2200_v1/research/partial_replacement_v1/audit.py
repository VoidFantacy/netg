"""Separate weight-table and exhaustive-design checks; no search calls."""
import analyze as a
import hashlib
import itertools
import json
import time
from pathlib import Path
import numpy as np


def measured(vhat, truth):
    norm = np.sqrt(np.einsum('hd,hd->h', truth, truth))
    p = truth / norm[:, None]
    pp = vhat / np.sqrt(np.einsum('hd,hd->h', vhat, vhat))[:, None]
    chord = np.einsum('hd,hd->h', pp-p, pp-p)
    angle = np.degrees(np.arccos(np.clip(np.einsum('hd,hd->h', pp, p), -1, 1)))
    tangent = vhat - np.einsum('hd,hd->h', vhat, p)[:, None] * p
    return chord, angle, float(np.sum(np.einsum('hd,hd->h', tangent, tangent) / norm**2))


def enumerate_design():
    g = np.array([[.2, 1., 0.], [2., -.4, 1.], [-.3, .8, 2.], [1., 0., -.5], [.2, -.1, .1]])
    n, m = len(g), 2
    f = m/n
    bias = g.sum(0)
    B = float(bias @ bias)
    V = float(np.sum((g-g.mean(0))**2)/(n-1))
    noise = n*(1-f)*V/f
    gamma_star = B/(B+noise)
    errors = []
    for gamma in [0., f, 1., gamma_star, -.2, 1.4]:
        values = []
        for subset in itertools.combinations(range(n), m):
            e = gamma/f*g[list(subset)].sum(0)-bias
            values.append(e@e)
        expected = (1-gamma)**2*B + gamma**2*noise
        np.testing.assert_allclose(np.mean(values), expected, rtol=1e-13, atol=1e-13)
        errors.append(abs(np.mean(values)-expected))
    # The energy-optimal unbiased sampling law need not help unweighted replacement.
    g2 = np.array([2., 1., -2.])
    losses = (g2.sum()-g2)**2
    energy_law = np.abs(g2)/np.abs(g2).sum()
    assert energy_law@losses > losses.mean()
    return {'subsets': 10, 'gamma_values': 6, 'max_risk_error': max(errors),
            'energy_sampling_counterexample': {'uniform_replacement_risk': float(losses.mean()),
                                               'energy_weighted_replacement_risk': float(energy_law@losses)}}


def main():
    started = time.perf_counter()
    summary = json.loads((a.OUT/'results/summary.json').read_text())
    records = {}
    for index, (ds, record) in enumerate(summary['datasets'].items()):
        q,h,exact,approx = a.old.reconstruct(ds)
        truth = h+exact.T@q
        saved = np.load(a.OUT/'results'/(ds+'.npz'))
        n, m = record['n'], record['m']
        gamma = record['theory']['shrink_oracle_gamma']
        maximum_chord_error, maximum_angle_error = 0., 0.
        for rep in range(16):
            rows = np.random.default_rng(2026093002+index+1000*rep).permutation(n)[:m]
            np.testing.assert_array_equal(rows, saved['selected_rows'][rep])
            assert hashlib.sha256(rows.astype('<i4').tobytes()).hexdigest() == record['all_replications'][rep]['selected_sha256']
            if rep not in [0,5,10,15]:
                continue
            for method_index, name in enumerate(a.METHODS):
                if name == 'ExactSubset':
                    weight = np.zeros_like(approx)
                    weight[rows] = n/m*exact[rows]
                else:
                    weight = approx.copy()
                    factor = {'UniformReplacement': 1., 'UnbiasedCorrection': n/m, 'ShrinkOracle': gamma*n/m}[name]
                    weight[rows] = (1-factor)*approx[rows]+factor*exact[rows]
                if name == 'UniformReplacement':
                    assert weight.min() >= 0
                    np.testing.assert_allclose(weight.sum(1), 1., rtol=1e-13, atol=1e-13)
                chord, angle, tangent = measured(h+weight.T@q, truth)
                np.testing.assert_allclose(chord, saved['chord2'][rep,method_index], rtol=1e-10, atol=1e-13)
                np.testing.assert_allclose(angle, saved['angle_degrees'][rep,method_index], rtol=1e-8, atol=1e-5)
                np.testing.assert_allclose(tangent, record['all_replications'][rep]['methods'][name]['tangent_risk'], rtol=1e-11, atol=1e-12)
                maximum_chord_error = max(maximum_chord_error, float(np.max(np.abs(chord-saved['chord2'][rep,method_index]))))
                maximum_angle_error = max(maximum_angle_error, float(np.max(np.abs(angle-saved['angle_degrees'][rep,method_index]))))
        if ds.startswith('web'):
            c = a.old.CONFIG['datasets'][ds]['original']
            base = np.memmap(c['base'],'<f4',mode='r').reshape(-1,c['dimension']+1)[:,1:]
            gt = np.fromfile(c['fit_source']['gt_file'],'<i8').reshape(20000,100)
            rows = np.unique(np.r_[np.arange(0,n,199),saved['selected_rows'][0]])
            target = a.old.unit(np.array(base[gt[rows,0]],dtype='f4'))
            # Complete sorting is independent of the main top-two partition.
            scores = target @ h.astype('f4').T
            largest = np.sort(scores,axis=1)[:,-2:]
            gaps = (largest[:,1]-largest[:,0]).astype('f8')
            np.testing.assert_allclose(gaps, saved['gt1_gaps'][rows], rtol=0, atol=2e-7)
            for rep in range(16):
                temp = max(float(np.median(saved['gt1_gaps'][saved['selected_rows'][rep]])),1e-4)
                assert temp == record['all_replications'][rep]['pilot_temperature']
            assert float(np.median(saved['gt1_gaps'])) == record['full_temperature']
        records[ds] = {'seeds_checked':16,'full_weight_models_checked':16,
                       'max_chord_error':maximum_chord_error,'max_angle_degrees_error':maximum_angle_error,
                       'pilot_temperature_seed0':record['all_replications'][0].get('pilot_temperature')}
        print(ds, records[ds], flush=True)
    identities = 0
    for freeze in [a.OUT/'reviews/frozen.json',a.old.OUT/'reviews/frozen.json']:
        for path, expected in json.loads(freeze.read_text())['files'].items():
            assert a.old.identity(path) == expected, path
            identities += 1
    a.old.dump(a.OUT/'reviews/independent_audit.json',{'status':'PASS','scope':'same agent, separately formed full weight tables and exhaustive finite-population designs',
        'datasets':records,'toy':enumerate_design(),'identities_checked':identities,
        'audit_source':a.old.identity(Path(__file__)),'seconds':time.perf_counter()-started,
        'new_GT':0,'new_searches':0,'new_performance_points':0})
    print('PASS',round(time.perf_counter()-started,3),flush=True)


if __name__ == '__main__':
    main()
