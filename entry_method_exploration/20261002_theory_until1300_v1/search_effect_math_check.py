"""Finite synthetic proof checks; no native ANN, NSG, vectors, labels or graph files.

All 'nodes' below are integer symbols with fixed strict scores. They are a
finite-state model of ordered bounded-pool insertion, not a performance test.
The two transition implementations use different representations/schedulers.
"""
from fractions import Fraction
from itertools import combinations, product
import hashlib
import json
from pathlib import Path
import time


def cursor_machine(graph, seeds, capacity):
    pool = [(x, True) for x in sorted(seeds)[:capacity]]
    seen = set(x for x, _ in pool)
    expanded = []
    k = 0
    while k < len(pool) and k < capacity:
        updated = capacity
        if pool[k][1]:
            node = pool[k][0]
            pool[k] = (node, False)
            expanded.append(node)
            for nxt in graph[node]:
                if nxt in seen:
                    continue
                seen.add(nxt)
                if len(pool) == capacity and nxt >= pool[-1][0]:
                    continue
                pos = sum(x < nxt for x, _ in pool)
                pool.insert(pos, (nxt, True))
                pool = pool[:capacity]
                updated = min(updated, pos)
                assert [x for x, _ in pool] == sorted(seen)[:capacity]
        k = updated if updated <= k else k + 1
    return tuple(x for x, _ in pool), frozenset(seen), tuple(expanded)


def pending_machine(graph, seeds, capacity, pending=None, visited=None):
    candidates = set(seeds)
    todo = set(seeds) if pending is None else set(pending)
    discovered = set(seeds) if visited is None else set(visited)
    expanded = []
    evaluations = 0
    while todo:
        node = min(todo)
        todo.remove(node)
        expanded.append(node)
        for nxt in graph[node]:
            if nxt in discovered:
                continue
            discovered.add(nxt)
            evaluations += 1
            if len(candidates) < capacity or nxt < max(candidates):
                candidates.add(nxt)
                todo.add(nxt)
                if len(candidates) > capacity:
                    dropped = max(candidates)
                    candidates.remove(dropped)
                    todo.discard(dropped)
    return tuple(sorted(candidates)), frozenset(discovered), tuple(expanded), evaluations


def rank_safe_closure(graph, seeds, capacity):
    # Independent set-closure computation, using only the safe rank prefix.
    closure = set(seeds).intersection(range(capacity))
    while True:
        nxt = closure | {w for v in closure for w in graph[v] if w < capacity}
        if nxt == closure:
            return frozenset(closure)
        closure = nxt


def check_pool_and_reachability():
    n = 4
    edges = [(u, v) for u in range(n) for v in range(n) if u != v]
    seed_sets = [s for size in range(1, 4) for s in combinations(range(n), size)]
    count = 0
    for edge_mask in range(1 << len(edges)):
        graph = [[] for _ in range(n)]
        for bit, (u, v) in enumerate(edges):
            if edge_mask & (1 << bit):
                graph[u].append(v)
        for reverse in (False, True):
            g = [tuple(reversed(row)) if reverse else tuple(row) for row in graph]
            for capacity in range(1, n + 1):
                for seeds in seed_sets:
                    if len(seeds) > capacity:
                        continue
                    first = cursor_machine(g, seeds, capacity)
                    second = pending_machine(g, seeds, capacity)
                    assert first == second[:3]
                    if reverse:
                        assert first == cursor_machine(graph, seeds, capacity)
                    assert first[0] == tuple(sorted(first[1])[:capacity])
                    safe = rank_safe_closure(g, seeds, capacity)
                    assert safe <= first[1]
                    assert safe <= set(first[2])
                    outside_expanded = {v for v in first[2] if v >= capacity}
                    boundary = (set(seeds) | {w for v in outside_expanded for w in g[v]}) & set(range(capacity))
                    assert rank_safe_closure(g, boundary, capacity) == first[1] & set(range(capacity))
                    for output_k in range(1, capacity + 1):
                        true_top_k = set(range(output_k))
                        returned = set(first[0][:output_k])
                        assert returned & true_top_k == first[1] & true_top_k
                        assert safe & true_top_k <= returned
                    count += 1
    return {"directed_graphs": 4096, "strict_rank_node_count": 4,
            "neighbor_orders": 2, "machine_cases": count,
            "pool_invariant": True, "independent_scheduler_parity": True,
            "reverse_adjacency_row_response_and_count_parity": True,
            "safe_nodes_discovered_and_expanded": True,
            "outside_expansion_boundary_closure_exact": True,
            "native_calls": 0}


def check_differential_support():
    count = 0
    for k in (1, 2, 3):
        sets = [frozenset(s) for s in combinations(range(6), k)]
        for a, b, t, t2 in product(sets, repeat=4):
            delta = len(a & t) - len(b & t)
            delta2 = len(a & t2) - len(b & t2)
            direct = len((a - b) & t) - len((b - a) & t)
            assert delta == direct
            assert abs(delta2 - delta) <= len((a ^ b) & (t ^ t2))
            if a == b:
                assert delta == delta2 == 0
            count += 1
    return {"universe": 6, "K": [1, 2, 3], "quadruples": count,
            "support_identity_and_change_bound": True}


def reached_row_states(graph, seeds, capacity):
    pool, todo, seen = set(seeds), set(seeds), set(seeds)
    snapshots = []
    while True:
        snapshots.append((tuple(sorted(pool)), frozenset(todo), frozenset(seen)))
        if not todo:
            return snapshots, tuple(sorted(pool))
        node = min(todo)
        todo.remove(node)
        for nxt in graph[node]:
            if nxt in seen:
                continue
            seen.add(nxt)
            if len(pool) < capacity or nxt < max(pool):
                pool.add(nxt)
                todo.add(nxt)
                if len(pool) > capacity:
                    dropped = max(pool)
                    pool.remove(dropped)
                    todo.discard(dropped)


def check_valid_row_pool_abstraction():
    # Valid states only: flagged-clear pool nodes have completed their entire
    # adjacency row. Arbitrary manufactured visited/pending states are excluded.
    n = 4
    edges = [(u, v) for u in range(n) for v in range(n) if u != v]
    seed_sets = [s for size in range(1, 4) for s in combinations(range(n), size)]
    count = different_pending = different_seen = 0
    for mask in range(1 << len(edges)):
        graph = [[] for _ in range(n)]
        for bit, (u, v) in enumerate(edges):
            if mask & (1 << bit):
                graph[u].append(v)
        for capacity in range(1, n + 1):
            by_pool = {}
            for seeds in seed_sets:
                if len(seeds) > capacity:
                    continue
                states, returned = reached_row_states(graph, seeds, capacity)
                for pool, todo, seen in states:
                    if pool in by_pool:
                        prior_answer, prior_todo, prior_seen = by_pool[pool]
                        assert returned == prior_answer
                        different_pending += todo != prior_todo
                        different_seen += seen != prior_seen
                    else:
                        by_pool[pool] = returned, todo, seen
                    count += 1
    return {"directed_graphs": 4096, "strict_rank_node_count": 4,
            "whole_row_state_occurrences": count,
            "same_pool_final_output_parity": True,
            "same_pool_pairs_with_different_pending": different_pending,
            "same_pool_pairs_with_different_visited": different_seen,
            "arbitrary_unreachable_states_excluded": True}


def check_affine_path_radius():
    # Three fixed comparisons, with rational arithmetic and the L-infinity
    # perturbation bound |w.dot(delta)| <= ||w||_1 ||delta||_infinity.
    q0 = (Fraction(3), Fraction(2))
    normals = [(Fraction(1), Fraction(-1)),
               (Fraction(2), Fraction(1)),
               (Fraction(-1), Fraction(3))]
    dot = lambda w, q: sum(a * b for a, b in zip(w, q))
    signs0 = tuple(dot(w, q0) > 0 for w in normals)
    radius = min(abs(dot(w, q0)) / sum(abs(a) for a in w) for w in normals)
    cases = 0
    for i, j in product(range(-9, 10), repeat=2):
        delta = (radius * Fraction(i, 10), radius * Fraction(j, 10))
        q = tuple(x + y for x, y in zip(q0, delta))
        signs = tuple(dot(w, q) > 0 for w in normals)
        assert signs == signs0
        for w in normals:
            assert abs(dot(w, delta)) <= sum(abs(a) for a in w) * max(map(abs, delta))
        cases += 1
    return {"rational_norm": "Linfinity/L1 dual", "radius": str(radius),
            "strict_interior_perturbations": cases, "all_signs_preserved": True,
            "neither_real_queries_nor_real_search_traces": True}


def interval_safe_set(bounds, width):
    return {v for v, (_, upper) in enumerate(bounds)
            if sum(lower <= upper for u, (lower, _) in enumerate(bounds) if u != v) < width}


def arbitrary_score_machine(graph, seeds, capacity, scores):
    pool, pending, seen = set(seeds), set(seeds), set(seeds)
    expanded = set()
    order = lambda v: (scores[v], v)
    while pending:
        node = min(pending, key=order)
        pending.remove(node)
        expanded.add(node)
        for nxt in graph[node]:
            if nxt in seen:
                continue
            seen.add(nxt)
            if len(pool) == capacity and scores[nxt] >= max(scores[v] for v in pool):
                continue
            pool.add(nxt)
            pending.add(nxt)
            if len(pool) > capacity:
                dropped = max(pool, key=order)
                pool.remove(dropped)
                pending.discard(dropped)
    return tuple(sorted(pool, key=order)), seen, expanded


def allowed_closure(graph, seeds, allowed):
    closure = set(seeds) & allowed
    while True:
        new = closure | {w for v in closure for w in graph[v] if w in allowed}
        if new == closure:
            return closure
        closure = new


def check_interval_safe_frontier():
    # Exhaustive tiny graphs and all endpoint choices model any one-time
    # scoring value in that set. Ties are allowed and deliberately tested.
    # The theorem is interval-based; no global common-order premise is used.
    fixtures = [((0, 0), (1, 1), (2, 2)),
                ((0, 2), (0, 2), (0, 2)),
                ((0, 0), (1, 2), (1, 3)),
                ((0, 1), (2, 2), (2, 4)),
                ((2, 3), (0, 0), (1, 1)),
                ((0, 1), (1, 2), (3, 4)),
                ((0, 10), (2, 3), (4, 5))]
    n = 3
    edges = [(u, v) for u in range(n) for v in range(n) if u != v]
    seed_sets = [s for size in range(1, 4) for s in combinations(range(n), size)]
    cases = ties = nonempty = 0
    for mask in range(1 << len(edges)):
        graph = [[] for _ in range(n)]
        for bit, (u, v) in enumerate(edges):
            if mask & (1 << bit):
                graph[u].append(v)
        for bounds in fixtures:
            for scores in product(*bounds):
                for width in range(1, n + 1):
                    safe = interval_safe_set(bounds, width)
                    for seeds in seed_sets:
                        if len(seeds) > width:
                            continue
                        pool, seen, expanded = arbitrary_score_machine(graph, seeds, width, scores)
                        closure = allowed_closure(graph, seeds, safe)
                        assert safe & seen <= expanded
                        assert closure <= seen
                        outside = expanded - safe
                        boundary = (set(seeds) | {w for v in outside for w in graph[v]}) & safe
                        assert allowed_closure(graph, boundary, safe) == seen & safe
                        for k in range(1, width + 1):
                            return_safe = interval_safe_set(bounds, k)
                            returned = set(pool[:k])
                            assert seen & return_safe <= returned
                            for truth in combinations(range(n), k):
                                certificate = closure & set(truth) & return_safe
                                assert certificate <= returned
                        cases += 1
                        ties += len(set(scores)) < n
                        nonempty += bool(safe)
    return {"directed_graphs": 64, "interval_fixtures": len(fixtures),
            "strict_rank_node_count": None, "ties_allowed": True,
            "endpoint_machine_cases": cases, "cases_with_tied_scores": ties,
            "cases_with_nonempty_safe_frontier": nonempty,
            "interval_safe_nodes_retained_and_expanded": True,
            "interval_safe_boundary_closure_exact": True,
            "QK_return_and_true_label_certificate": True,
            "pool_response_abstraction_not_asserted": True}


def check_counterexamples():
    # Strictly ranked strongly connected six-cycle: a better seed evicts a
    # useful worse seed before the latter can expand. This phenomenon is
    # already known (record145/ABS); this is a finite independent fixture.
    graph = [(1,), (2,), (3,), (5,), (0,), (4,)]
    far = pending_machine(graph, (4,), 2)
    near = pending_machine(graph, (1,), 2)
    joint = pending_machine(graph, (1, 4), 2)
    assert far[0][0] == 0 and near[0][0] == joint[0][0] == 1
    # Valid row-boundary states, same pool+pending but different already
    # scored and discarded members. The only effect here is extra scoring.
    cost_graph = [(), (2,), (1,)]
    unseen = pending_machine(cost_graph, (1,), 1, pending=(1,), visited=(1,))
    seen = pending_machine(cost_graph, (1,), 1, pending=(1,), visited=(1, 2))
    assert unseen[:1] == seen[:1] and unseen[3] == 1 and seen[3] == 0
    return {"strong_cycle": [list(row) for row in graph],
            "far_seed": 4, "near_seed": 1, "L": 2, "GT1": 0,
            "far_return": far[0][0], "near_return": near[0][0],
            "joint_return": joint[0][0],
            "closer_seed_and_seed_addition_nonmonotonic": True,
            "same_pool_pending_return_but_different_scoring": True,
            "previously_scored_discarded_state_is_rank_consistent": True}


def main():
    started = time.perf_counter()
    result = {"status": "PURE_SYNTHETIC_MATHEMATICAL_CHECK_PASS",
              "scope": "finite integer symbols/rational signs only; no measured latency",
              "pool_and_reachability": check_pool_and_reachability(),
              "differential_output_support": check_differential_support(),
              "valid_row_pool_response_abstraction": check_valid_row_pool_abstraction(),
              "path_radius": check_affine_path_radius(),
              "interval_safe_frontier": check_interval_safe_frontier(),
              "counterexamples": check_counterexamples(),
              "new_real_ANN": 0, "new_NSG": 0, "new_GT": 0,
              "real_vector_graph_or_query_inputs": [],
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "seconds": time.perf_counter() - started}
    out = Path(__file__).with_suffix('.json')
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'seconds', 'new_real_ANN', 'new_NSG', 'new_GT']}))


if __name__ == '__main__':
    main()
