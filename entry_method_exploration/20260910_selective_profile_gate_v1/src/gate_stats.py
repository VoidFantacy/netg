"""Paired hit/event accounting, including neutral queries in every Recall denominator."""
import numpy as np
from common import RUN, read


def load_pair(dataset, stage):
    folder = RUN / 'diagnostics' / dataset / stage
    assert read(folder / 'independent_verification.json')['status'] == 'PASS'
    c = read(folder / 'config.json')
    n = c['num_queries']
    x = np.fromfile(folder / 'features.f64', dtype='<f8').reshape(n, 13)
    h0 = np.column_stack([np.fromfile(folder / f'fast20k_L{L}/hits.u8', dtype='u1') for L in [64, 128]]).astype('int16')
    h1 = np.column_stack([np.fromfile(folder / f'e24_L{L}/hits.u8', dtype='u1') for L in [64, 128]]).astype('int16')
    return folder, x, h0, h1


def ratios_stats(h0, h1, choose):
    h0 = np.asarray(h0, dtype='int16')
    h1 = np.asarray(h1, dtype='int16')
    if h0.ndim == 1:
        h0 = h0[:, None]
        h1 = h1[:, None]
    choose = np.asarray(choose, dtype=bool)
    assert choose.shape == (len(h0),)
    d = h1 - h0
    chosen = choose[:, None]
    pos, neg = d > 0, d < 0
    dp, dn = np.maximum(d, 0), np.maximum(-d, 0)
    pos_n, neg_n = int(pos.sum()), int(neg.sum())
    pos_h, neg_h = int(dp.sum()), int(dn.sum())
    retained_n, harmed_n = int((pos & chosen).sum()), int((neg & chosen).sum())
    retained_h, harmed_h = int((dp * chosen).sum()), int((dn * chosen).sum())
    ratio = lambda a, b: float(a / b) if b else None
    R, A = ratio(retained_n, pos_n), ratio(neg_n - harmed_n, neg_n)
    Rh, Ah = ratio(retained_h, pos_h), ratio(neg_h - harmed_h, neg_h)
    terms = [None if v is None else v / t for v, t in zip([R, A, Rh, Ah], [.75, .25, .75, .25])]
    S = min(terms) if all(v is not None for v in terms) else 0.0
    net = retained_h - harmed_h
    net_required = max(0, int(d.sum()))
    selected = np.where(chosen, h1, h0)
    return {
        'queries': len(h0), 'L_count': h0.shape[1], 'query_L_events': h0.size,
        'switch_queries': int(choose.sum()), 'switch_fraction': float(choose.mean()),
        'nonconstant_on_this_split': bool(0 < choose.sum() < len(choose)),
        'positive_events_available': pos_n, 'negative_events_available': neg_n,
        'neutral_events': int((d == 0).sum()),
        'positive_events_retained': retained_n, 'positive_events_lost': pos_n - retained_n,
        'negative_events_retained': harmed_n, 'negative_events_avoided': neg_n - harmed_n,
        'positive_hits_available': pos_h, 'negative_hits_available': neg_h,
        'positive_hits_retained': retained_h, 'positive_hits_lost': pos_h - retained_h,
        'negative_hits_retained': harmed_h, 'negative_hits_avoided': neg_h - harmed_h,
        'R': R, 'A': A, 'Rh': Rh, 'Ah': Ah, 'S': float(S),
        'net_delta_hits': net, 'always_A1_net_delta_hits': int(d.sum()),
        'net_delta_required': net_required,
        'target_met': bool(all(v is not None and v >= t for v, t in zip([R, A, Rh, Ah], [.75, .25, .75, .25])) and net >= net_required),
        'A0_recall': float(h0.mean() / 10), 'A1_recall': float(h1.mean() / 10),
        'selected_recall': float(selected.mean() / 10),
        'delta_recall_pp_vs_A0': float((selected - h0).mean() * 10),
        'delta_recall_pp_vs_A1': float((selected - h1).mean() * 10),
        'zero_hits_A0': int((h0 == 0).sum()), 'zero_hits_A1': int((h1 == 0).sum()),
        'zero_hits_selected': int((selected == 0).sum()),
        'zero_hit_rescues_vs_A0': int(((h0 == 0) & (selected > 0)).sum()),
        'new_zero_hit_failures_vs_A0': int(((h0 > 0) & (selected == 0)).sum()),
    }


def cross_L_stats(h0, h1):
    d = h1 - h0
    return {
        'has_positive': int((d > 0).any(axis=1).sum()),
        'has_negative': int((d < 0).any(axis=1).sum()),
        'opposite_signs_across_L': int(((d > 0).any(axis=1) & (d < 0).any(axis=1)).sum()),
        'neutral_at_all_L': int((d == 0).all(axis=1).sum()),
        'positive_net_queries': int((d.sum(axis=1) > 0).sum()),
        'negative_net_queries': int((d.sum(axis=1) < 0).sum()),
        'zero_net_queries': int((d.sum(axis=1) == 0).sum()),
        'same_L_oracle_delta_hits_non_deployable': int(np.maximum(d, 0).sum()),
        'L_invariant_oracle_delta_hits_non_deployable': int(np.maximum(d.sum(axis=1), 0).sum()),
    }
