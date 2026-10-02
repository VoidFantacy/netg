"""Report-only replay of the two frozen rules on independently scored audit searches."""
import numpy as np
from common import RUN, DATASETS, FEATURES, read, dump, identity, check_lock, frozen_gate_check, update_state
from gate_stats import load_pair, ratios_stats, cross_L_stats
from verify_outputs import arrays, predict


def main():
    check_lock(); frozen_gate_check()
    assert read(RUN / 'reviews/audit_pairs_verification.json')['status'] == 'PASS'
    assert not (RUN / 'reviews/audit_report.json').exists()
    selections = read(RUN / 'models/selections.json')
    report = {}
    for ds in DATASETS:
        folder, x, h0, h1 = load_pair(ds, 'audit')
        c = read(folder / 'config.json')
        gt = np.fromfile(c['gt_file'], dtype='<i8').reshape(len(x), 100)[:, :10]
        methods = read(folder / 'results.json')['methods']
        record = {'primary_frozen_on_cal': selections[ds]['primary'],
                  'cross_L': cross_L_stats(h0, h1), 'gates': {},
                  'control': ratios_stats(h0, h1, np.ones(len(x), bool)),
                  'counterfactual_cached_two_real_searches': True, 'online_QPS_measured': False}
        for kind in ['base_gate', 'dual_gate']:
            model = read(RUN / 'models' / ds / f'{kind}.json')
            z, choose = predict(x, model)
            independent = np.einsum('ij,j->i', np.clip((x[:, :len(model['beta'])] - model['mean']) / model['scale'], -6, 6), model['beta']) + model['bias']
            assert np.max(np.abs(independent - z)) < 1e-11
            assert np.array_equal(independent >= model['threshold'], choose)
            out = RUN / 'diagnostics' / ds / 'audit_counterfactual' / kind
            out.mkdir(parents=True, exist_ok=False)
            z.astype('<f8').tofile(out / 'logits.f64')
            choose.astype('u1').tofile(out / 'choose_new.u8')
            per_L = {}
            for j, L in enumerate([64, 128]):
                b = arrays(folder, next(m for m in methods if m['name'] == f'fast20k_L{L}'), len(x))
                a = arrays(folder, next(m for m in methods if m['name'] == f'e24_L{L}'), len(x))
                dest = out / f'L{L}'; dest.mkdir()
                selected = {}
                for field, name, dtype in [('ids', 'ids.i32', '<i4'), ('distances', 'distances.f32', '<f4'),
                                            ('entries', 'entry_ids.i32', '<i4'), ('graph_ndc', 'graph_ndc.u32', '<u4'),
                                            ('hits', 'hits.u8', 'u1'), ('mask', 'hitmask.u16', '<u2')]:
                    selected[field] = np.where(choose[:, None] if b[field].ndim == 2 else choose, a[field], b[field])
                    selected[field].astype(dtype).tofile(dest / name)
                masks = np.zeros(len(x), '<u2')
                for k in range(10):
                    masks |= (selected['ids'] == gt[:, k, None]).any(axis=1).astype('<u2') << k
                assert np.array_equal(masks, selected['mask'])
                assert np.array_equal([int(v).bit_count() for v in masks], selected['hits'])
                route = b['route_ndc'] + (a['route_ndc'] + 6 if kind == 'dual_gate' else np.where(choose, a['route_ndc'], 0) + 3)
                route.astype('<u4').tofile(dest / 'derived_route_ndc.u32')
                per_L[str(L)] = {**ratios_stats(h0[:, j], h1[:, j], choose),
                                'derived_mean_route_ndc': float(route.mean()),
                                'selected_mean_graph_ndc': float(selected['graph_ndc'].mean())}
            record['gates'][kind] = {'pooled_L64_L128': ratios_stats(h0, h1, choose), 'per_L': per_L,
                                    'logit_parity_max_error': float(np.abs(independent - z).max()),
                                    'minimum_logit_threshold_distance': float(np.min(np.abs(z - model['threshold']))),
                                    'choice': identity(out / 'choose_new.u8'), 'selected_ID_rescoring': 'PASS'}
        report[ds] = record
        print(ds, record['primary_frozen_on_cal'], record['gates'][record['primary_frozen_on_cal']]['pooled_L64_L128'], flush=True)
    dump(RUN / 'reviews/audit_report.json', {'status': 'REPORT_ONLY_COMPLETE', 'datasets': report,
         'models_unchanged': True, 'selection_or_retraining_on_audit': False, 'additional_NSG_calls': 0})
    frozen_gate_check()
    update_state(status='AUDIT_REPORT_ONLY_COMPLETE')
    print('AUDIT_REPORT_ONLY_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
