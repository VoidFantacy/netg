"""Rational algebra and manufactured scalar examples only; no real data reads.

Checks corrected full-cost control gates, MIPS metric-transfer consequences,
and the scope of a current-pivot bound under changing thresholds.
"""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import json
import struct


def cost_controls():
    count = 0
    for base, excess, save_a, save_b in product(
            (F(10), F(20)), (F(-2), F(0), F(2)),
            (F(-3), F(0), F(1), F(3), F(6)),
            (F(-3), F(0), F(1), F(3), F(6))):
        target = base + excess
        target_memo = target - save_a
        base_memo = base - save_b
        assert min(target, target_memo, base, base_memo) > 0
        assert target_memo - base_memo == excess - (save_a - save_b)
        best_base = min(base, base_memo)
        assert best_base == base - max(save_b, F(0))
        assert (target_memo < best_base) == (
            save_a > excess + max(save_b, F(0)))
        for g in (F(0), F(1, 100), F(1, 10)):
            qps_gain = best_base / target_memo - 1
            needed = excess + max(save_b, F(0)) + g / (1 + g) * best_base
            assert (qps_gain >= g) == (save_a >= needed)
            count += 1
    # The matched-memo inequality alone accepts a degraded default control.
    base, target, target_memo, base_memo = F(10), F(12), F(11), F(13)
    assert target_memo < base_memo and target_memo > base
    return {"rational_cases": count, "matched_and_best_default_gates": True,
            "negative_default_savings_counterexample": True}


def metric_transfer():
    count = 0
    # Synthetic 2D rational symbols, never real query/base vectors.
    items = [(F(3), F(0)), (F(0), F(4)), (F(-3), F(4)),
             (F(0), F(-5)), (F(4), F(3))]
    for q, radius in product(
            [(F(i), F(j)) for i, j in product(range(-2, 3), repeat=2)
             if i or j], (F(5), F(10), F(100))):
        c = sum(v*v for v in q) + radius*radius
        ips, distances_squared = [], []
        for x in items:
            ip = sum(a*b for a, b in zip(q, x))
            residual_squared = radius*radius - sum(v*v for v in x)
            assert residual_squared >= 0
            dsq = sum((a-b)**2 for a, b in zip(q, x)) + residual_squared
            assert dsq == c - 2*ip
            ips.append(ip)
            distances_squared.append(dsq)
        # Pairwise strict comparisons and ties are preserved in real arithmetic.
        for i, j in product(range(len(items)), repeat=2):
            assert (ips[i] > ips[j]) == (distances_squared[i] < distances_squared[j])
            assert (ips[i] == ips[j]) == (distances_squared[i] == distances_squared[j])
        opt = max(ips)
        dopt2 = min(distances_squared)
        for alpha in (F(1), F(3, 2), F(2)):
            lower_ip = alpha*alpha*opt - (alpha*alpha-1)*c/2
            for ip, dsq in zip(ips, distances_squared):
                assert (dsq <= alpha*alpha*dopt2) == (ip >= lower_ip)
                count += 1
    return {"rational_approximation_cases": count,
            "exact_rank_reduction": True, "additive_IP_penalty_required": True}


def bound_and_float_scope():
    # q=1, old pivot x_i=0, neighbor x_j=.05: its translation-CS bound=.05.
    score_i, bound = F(0), F(1, 20)
    threshold_at_start, threshold_after_update = F(0), F(4, 5)
    assert bound >= score_i >= threshold_at_start
    assert not bound < threshold_at_start
    assert bound < threshold_after_update
    # Distinct float32 native dots may fold to the same float32 1-dot value.
    f32 = lambda x: struct.unpack('<f', struct.pack('<f', float(x)))[0]
    dot_a, dot_b = f32(1e-9), f32(2e-9)
    da, db = f32(1.0-dot_a), f32(1.0-dot_b)
    assert dot_a < dot_b and da == db == 1.0
    return {"pivot_bound_no_margin_while_inside_current_threshold": True,
            "tightened_within_row_threshold_can_enable_rejection": True,
            "raw_dot_order_need_not_equal_native_distance_strict_order": True,
            "folded_native_distance_bits": struct.pack('<f', da).hex()}


def main():
    result = {"status": "PASS", "cost": cost_controls(),
              "metric": metric_transfer(), "scope": bound_and_float_scope(),
              "real_data_reads": 0, "native_ANN_NSG_GT_calls": 0,
              "new_models_graphs_or_performance_runs": 0,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out = Path(__file__).with_name('algebra_checks.json')
    with out.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
