"""Six predeclared curves, sequentially measured and regressed against E24 artifacts."""
import numpy as np
from common import RUN, E24, DATASETS, LS, read, dump, check_lock, frozen_gate_check, identity, update_state
from jobs import run_job
from verify_outputs import verify_folder


def main():
    check_lock(); frozen_gate_check()
    assert read(RUN / 'reviews/audit_report.json')['status'] == 'REPORT_ONLY_COMPLETE'
    checks = []
    for order, ds in enumerate(DATASETS):
        c = read(RUN / 'inputs' / ds / 'validation/config.json')
        old_folder = E24 / 'results' / ds
        old = read(old_folder / 'results.json')
        direct = next(m['configuration'] for m in old['methods'] if m['family'] == 'fast30k_3' and m['L'] == 128)
        c.update(timing_repeats=3, dataset_order=order, export_features=True,
                 policies=read(RUN / 'inputs' / ds / 'policies.json'), methods=[])
        for L in LS:
            for kind in ['nsg', 'fast30k', 'fast20k', 'e24', 'base_gate', 'dual_gate']:
                method = {'name': f'{kind}_L{L}', 'family': kind, 'kind': kind, 'L': L, 'component_wall': L == 128}
                if kind == 'fast30k':
                    method['direct'] = direct
                if kind in ['base_gate', 'dual_gate']:
                    method['model_path'] = str(RUN / 'models' / ds / f'{kind}.json')
                c['methods'].append(method)
        out = RUN / 'results' / ds
        results = run_job(f'validation_{ds}', c, out)
        check = verify_folder(out)
        aliases = {'nsg': 'nsg_medoid', 'fast30k': 'fast30k_3', 'fast20k': 'gt1_hard',
                   'e24': 'gt10_soft' if ds.startswith('webvid') else 'gt10_hard'}
        for m in results['methods']:
            if m['kind'] not in aliases:
                continue
            old_m = next(v for v in old['methods'] if v['family'] == aliases[m['kind']] and v['L'] == m['L'])
            for filename, dtype in [('ids.i32', '<i4'), ('distances.f32', '<u4'), ('entry_ids.i32', '<i4'),
                                    ('route_ndc.u32', '<u4'), ('graph_ndc.u32', '<u4'), ('hits.u8', 'u1'), ('hitmask.u16', '<u2')]:
                assert np.array_equal(np.fromfile(out / m['name'] / filename, dtype=dtype),
                                      np.fromfile(old_folder / old_m['name'] / filename, dtype=dtype)), (ds, m['name'], filename)
        for kind in ['base_gate', 'dual_gate']:
            for filename, dtype in [('choose_new.u8', 'u1'), ('entry_ids.i32', '<i4'), ('logits.f64', '<u8')]:
                first = np.fromfile(out / f'{kind}_L64' / filename, dtype=dtype)
                for L in LS[1:]:
                    assert np.array_equal(first, np.fromfile(out / f'{kind}_L{L}' / filename, dtype=dtype))
        check.update(dataset=ds, four_original_curves_E24_bit_regression='PASS',
                     gate_choices_logits_entries_identical_across_five_L='PASS', results=identity(out / 'results.json'))
        checks.append(check)
        frozen_gate_check()
    dump(RUN / 'reviews/validation_verification.json', {'status': 'PASS', 'datasets': checks, 'points': 60})
    update_state(status='VALIDATION_COMPLETE_ALL_PARITY_PASS')
    print('VALIDATION_ALL_PASS', flush=True)


if __name__ == '__main__':
    main()
