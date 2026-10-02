"""Independent Counter/set/struct audit of the frozen historical-ID diagnostic."""
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import hashlib
import json
import struct

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = Path('/data/netg/ACSG')
OLD = ROOT / 'entry_method_exploration/20260930_theory_until2200_v1/research'


def unpack(path, code):
    data = Path(path).read_bytes()
    size = struct.calcsize('<' + code)
    assert len(data) % size == 0
    return list(struct.unpack('<' + code * (len(data) // size), data))


def stats(values):
    ordered = sorted(values)
    def quantile(num, den):
        at = Fraction((len(ordered) - 1) * num, den)
        lo = at.numerator // at.denominator
        remainder = at - lo
        return float(Fraction(ordered[lo]) + remainder * (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo]))
    return dict(mean=float(Fraction(sum(values), len(values))), p50=quantile(1, 2),
                p90=quantile(9, 10), p99=quantile(99, 100), min=min(values), max=max(values))


def close(got, expected):
    assert abs(got - expected) <= 1e-10 * max(1, abs(got), abs(expected)), (got, expected)


def main():
    saved = json.loads((HERE / 'bucket_feasibility.json').read_text())
    cfg = json.loads((OLD / 'target_bank_frozen_curve_v1/config.locked.json').read_text())
    prior = json.loads((OLD / 'query_target_transfer_v1/config.locked.json').read_text())
    identities = json.loads((HERE / 'bucket_input_identity.json').read_text())
    for p, lock in identities.items():
        data = Path(p).read_bytes()
        assert len(data) == lock['bytes'] and hashlib.sha256(data).hexdigest() == lock['sha256']
    checks = {}
    for ds, c in cfg['datasets'].items():
        targets = unpack(c['targets'], 'i')
        hubs = unpack(prior['datasets'][ds]['hub_mapping'], 'i')
        hids = unpack(c['anchor']['ids'], 'i')
        counts = Counter(hubs)
        bucket_ids = defaultdict(set)
        id_bucket = {}
        for t, h in zip(targets, hubs):
            if t in id_bucket:
                assert id_bucket[t] == h
            id_bucket[t] = h
            bucket_ids[h].add(t)
        with np.load(HERE / f'{ds}.bucket_alignment.npz', allow_pickle=False) as z:
            reference = {key: z[key].tolist() for key in z.files}
        v = saved['datasets'][ds]
        physical = []; unique = []; covered = []
        for row, (triple, slot) in enumerate(zip(reference['default_entries'], reference['target_slots'])):
            assert len(set(triple)) == 3
            physical.append(sum(counts[h] for h in triple))
            union = set()
            for h in triple:
                union.update(bucket_ids[h])
            unique.append(len(union))
            covered.append(hubs[slot] in set(triple))
        assert physical == reference['physical_candidate_count']
        assert unique == reference['unique_candidate_count']
        assert covered == reference['old_slot_covered']
        for name, vals in [('M_physical', physical), ('M_unique', unique),
                           ('physical_bucket_distribution', [counts[h] for h in hids]),
                           ('unique_bucket_distribution', [len(bucket_ids[h]) for h in hids])]:
            for key, val in stats(vals).items():
                close(val, v[name][key])
        assert sum(covered) == v['old_TargetBank_slot_covered_count']
        for pi, point in enumerate(c['points']):
            loc = OLD / 'target_bank_frozen_curve_v1/results' / ds / f'k{point["K"]}_L{point["L"]}'
            raw_entries = unpack(loc / 'Default3/entry_ids.i32', 'i')
            assert [raw_entries[i:i + 3] for i in range(0, len(raw_entries), 3)] == reference['default_entries']
            assert unpack(loc / 'TargetBank1/route_slots.i32', 'i') == reference['target_slots']
            delta = [r[pi][2] - r[pi][0] for r in reference['old_hits']]
            for name, wanted in [('all', None), ('old_slot_covered', True), ('old_slot_not_covered', False)]:
                values = [d for i, d in enumerate(delta) if wanted is None or covered[i] == wanted]
                group = v['points'][pi][name]
                assert len(values) == group['n']
                assert sum(values) == group['net_hits']
                assert sum(d > 0 for d in values) == group['rescued_queries']
                assert sum(d < 0 for d in values) == group['damaged_queries']
                assert sum(max(d, 0) for d in values) == group['query_net_positive_hits']
                assert sum(max(-d, 0) for d in values) == group['query_net_negative_hits']
                if values:
                    close(float(Fraction(sum(values) * 100, len(values) * point['K'])), group['delta_Recall_pp'])
            default_g = unpack(loc / 'Default3/graph_ndc.u64', 'Q')
            target_g = unpack(loc / 'TargetBank1/graph_ndc.u64', 'Q')
            close(float(Fraction(sum(default_g) - sum(target_g), c['n'])), v['points'][pi]['old_graph_NDC_saving_mean'])
            default_r = unpack(loc / 'Default3/route_ndc.u64', 'Q')
            target_r = unpack(loc / 'TargetBank1/route_ndc.u64', 'Q')
            close(float(Fraction(sum(default_r), c['n'])), v['Default3_route_NDC_mean'])
            close(float(Fraction(sum(target_r), c['n'])), v['TargetBank_route_NDC_mean'])
        checks[ds] = {'aligned_rows': len(covered), 'points': len(c['points']),
                      'empty_candidate_queries': physical.count(0),
                      'covered': sum(covered), 'physical_total': sum(physical), 'unique_total': sum(unique),
                      'checks': ['struct_ID_read', 'Counter_physical', 'set_union_unique', 'Fraction_quantiles',
                                 'all_group_hit_events', 'all_old_NDC', 'route_invariance_across_K_L']}
    with (HERE / 'bucket_independent_audit.json').open('x') as f:
        json.dump({'status': 'PASS', 'datasets': checks, 'consumed_files_verified': len(identities),
                   'independence': 'same agent, separate Counter/set/struct/Fraction implementation',
                   'no_vectors_GT_new_search_or_model': True}, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('INDEPENDENT_COUNTER_SET_STRUCT_AUDIT_PASS', json.dumps(checks, ensure_ascii=False))


if __name__ == '__main__':
    main()
