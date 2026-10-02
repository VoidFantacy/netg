"""Training-only finite-population geometry; no search or model export."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "8"
os.sched_setaffinity(0, set(range(8)))
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_info

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
OLD = ROOT / "entry_method_exploration/20260922_until2200_improvement_v1"
E125 = OLD / "stages/e125_approximate_target_profiles_v1"
CONFIG = json.loads((E125 / "config.locked.json").read_text())


def unit(x):
    return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)


def identity(path):
    path = Path(path)
    return {"bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def dump(path, obj):
    path = Path(path)
    with path.open("x") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write("\n")


def reconstruct(dataset):
    c = CONFIG["datasets"][dataset]["original"]
    n, d = 20000, c["dimension"]
    raw = np.memmap(c["base"], "<f4", mode="r").reshape(-1, d + 1)
    base = raw[:, 1:]
    ids = np.fromfile(c["anchor"]["ids"], "<i4")
    hub = unit(np.array(base[ids], dtype="f4"))
    query = unit(np.fromfile(c["fit_source"]["queries_file"], "<f4").reshape(n, d))
    exact = np.fromfile(c["fit_source"]["gt_file"], "<i8").reshape(n, 100)
    approx = np.fromfile(E125 / "results" / dataset / "labels/ids.i32", "<i4").reshape(n, 100)
    meta = json.loads((E125 / "models" / dataset / "profiles.json").read_text())
    weights = []
    for name, targets in (("ExactAudit", exact), ("ApproxTarget10", approx)):
        a = np.zeros((n, len(hub)))
        for rank in range(10):
            z = unit(np.array(base[targets[:, rank]], dtype="f4"))
            for lo in range(0, n, 4096):
                hi = min(lo + 4096, n)
                scores = z[lo:hi] @ hub.T
                if meta["temperature"] is None:
                    a[np.arange(lo, hi), scores.argmax(1)] += 0.1
                else:
                    scores = scores.astype("f8")
                    scores -= scores.max(1, keepdims=True)
                    scores /= meta["temperature"]
                    np.exp(scores, out=scores)
                    scores /= scores.sum(1, keepdims=True)
                    a[lo:hi] += scores / 10
        assert hashlib.sha256(a.tobytes()).hexdigest() == meta[name]["assignment_sha256"]
        weights.append(a)
    return query.astype("f8"), hub.astype("f8"), weights[0], weights[1]


def threshold(n, variance, bias):
    den = bias + n * variance
    return n * n * variance / den if den > 0 else None


def run():
    started = time.perf_counter()
    results = OUT / "results"
    reviews = OUT / "reviews"
    results.mkdir(exist_ok=True)
    reviews.mkdir(exist_ok=True)
    assert not (results / "summary.json").exists()
    protected = {}
    base_stats = {}
    for dataset, dc in CONFIG["datasets"].items():
        c = dc["original"]
        paths = [c["anchor"]["ids"], c["anchor"]["W"],
                 c["fit_source"]["queries_file"], c["fit_source"]["gt_file"],
                 E125 / "results" / dataset / "labels/ids.i32",
                 E125 / "models" / dataset / "profiles.json",
                 E125 / "models" / dataset / "direction_diagnostic.npz",
                 OLD / "research/approximate_residual_variance_v1/results" / (dataset + ".npz")]
        for path in paths:
            protected[str(path)] = identity(path)
        stat = Path(c["base"]).stat()
        base_stats[c["base"]] = {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    for path in [Path(__file__), OUT / "protocol.md", OUT / "theory.md", E125 / "config.locked.json"]:
        protected[str(path)] = identity(path)
    dump(reviews / "frozen.json", {"unix": time.time(), "files": protected, "large_base_stat_only": base_stats})
    records = {}
    for dataset in CONFIG["datasets"]:
        t0 = time.perf_counter()
        q, h, a, b = reconstruct(dataset)
        n, dimension = q.shape
        total_y, total_z = a.T @ q, b.T @ q
        v, vp = h + total_y, h + total_z
        old_direction = np.load(E125 / "models" / dataset / "direction_diagnostic.npz")
        assert np.max(np.abs(v - old_direction["exact_v"])) < 1e-9
        assert np.max(np.abs(vp - old_direction["approx_v"])) < 1e-9
        norms = np.linalg.norm(v, axis=1)
        p = v / norms[:, None]
        e = vp - v
        parallel = np.einsum("hd,hd->h", e, p)
        tangent = e - parallel[:, None] * p
        bias_t = (tangent * tangent).sum(1)
        bias_all = (e * e).sum(1)
        relative_weight = 1 / norms ** 2
        qnorm2 = (q * q).sum(1)
        qp = q @ p.T
        tangent_qnorm2 = qnorm2[:, None] - qp ** 2
        assert tangent_qnorm2.min() > -1e-12
        np.maximum(tangent_qnorm2, 0, out=tangent_qnorm2)
        delta = a - b
        var_all = ((delta ** 2).T @ qnorm2 - bias_all / n) / (n - 1)
        uncentered_t = (delta ** 2 * tangent_qnorm2).sum(0)
        var_t = (uncentered_t - bias_t / n) / (n - 1)
        old_variance = np.load(OLD / "research/approximate_residual_variance_v1/results" / (dataset + ".npz"))
        assert np.max(np.abs(var_all - old_variance["trace_residual_cov"])) < 1e-10
        assert np.max(np.abs(bias_all - old_variance["approx_squared_bias"])) < 1e-8
        assert np.all(var_t >= -1e-12) and np.all(var_t <= var_all + 1e-12)
        var_t = np.maximum(var_t, 0)
        chord2 = ((unit(vp) - p) ** 2).sum(1)
        radial_result = norms + parallel
        analytic_chord2 = 2 * (1 - radial_result / np.sqrt(radial_result ** 2 + bias_t))
        assert np.max(np.abs(chord2 - analytic_chord2)) < 2e-14
        t_y = total_y - np.einsum("hd,hd->h", total_y, p)[:, None] * p
        t_z = total_z - np.einsum("hd,hd->h", total_z, p)[:, None] * p
        var_y = ((a ** 2 * tangent_qnorm2).sum(0) - (t_y * t_y).sum(1) / n) / (n - 1)
        var_z = ((b ** 2 * tangent_qnorm2).sum(0) - (t_z * t_z).sum(1) / n) / (n - 1)
        cov_yz = ((a * b * tangent_qnorm2).sum(0) - (t_y * t_z).sum(1) / n) / (n - 1)
        assert np.max(np.abs(var_y + var_z - 2 * cov_yz - var_t)) < 1e-10
        Vy, Vz, Cyz = [float(x @ relative_weight) for x in [var_y, var_z, cov_yz]]
        lam = Cyz / Vz
        lam_h = np.divide(cov_yz, var_z, out=np.zeros_like(cov_yz), where=var_z > 1e-15)
        Vopt = Vy - 2 * lam * Cyz + lam * lam * Vz
        Vopt_h = float((var_y - 2 * lam_h * cov_yz + lam_h ** 2 * var_z) @ relative_weight)
        Vt, Bt = float(var_t @ relative_weight), float(bias_t @ relative_weight)
        Va, Ba = float(var_all @ relative_weight), float(bias_all @ relative_weight)
        energy = (delta ** 2 * tangent_qnorm2) @ relative_weight
        numerator_uniform = n * float(energy.sum()) - Bt
        numerator_oracle = float(np.sqrt(energy).sum()) ** 2 - Bt
        assert abs(numerator_uniform - n * (n - 1) * Vt) < 1e-6 * max(1, numerator_uniform)
        sorted_energy = np.sort(energy)[::-1]
        ess_b = b.sum(0) ** 2 / np.maximum((b * b).sum(0), 1e-300)
        cohorts = {}
        for name, values in [("exact_resultant_norm", norms), ("approx_assignment_ESS", ess_b)]:
            groups = np.array_split(np.argsort(values, kind="stable"), 4)
            cohorts[name] = [{"n_hubs": len(ix), "value_min": float(values[ix].min()),
                              "value_max": float(values[ix].max()),
                              "chord_MSE_mean": float(chord2[ix].mean()),
                              "tangent_bias_share": float((bias_t[ix] * relative_weight[ix]).sum() / Bt),
                              "tangent_variance_share": float((var_t[ix] * relative_weight[ix]).sum() / Vt)} for ix in groups]
        record = {
            "n": n, "hubs": len(h), "dimension": dimension,
            "original_assignment_and_vectors_restored": True,
            "old_total_variance_restored": True,
            "normalized_sum_bias": Ba, "tangent_bias": Bt,
            "normalized_sum_variance": Va, "tangent_variance": Vt,
            "tangent_bias_fraction": Bt / Ba, "tangent_variance_fraction": Vt / Va,
            "total_MSE_critical_m": threshold(n, Va, Ba),
            "tangent_MSE_critical_m": threshold(n, Vt, Bt),
            "actual_chord2_sum": float(chord2.sum()),
            "tangent_approx_to_actual_chord_ratio": Bt / float(chord2.sum()),
            "radial_ratio_quantiles": np.quantile(radial_result / norms, [0, .25, .5, .75, 1]).tolist(),
            "nonpositive_radial_hubs": int((radial_result <= 0).sum()),
            "HH_with_replacement": {"uniform_numerator": numerator_uniform,
                "oracle_numerator": numerator_oracle, "oracle_to_uniform_variance": numerator_oracle / numerator_uniform,
                "oracle_critical_m_vs_direct_tangent_bias": numerator_oracle / Bt,
                "oracle_uses_all_exact_training_labels": True},
            "energy_top_fraction_shares": {str(f): float(sorted_energy[:int(np.ceil(n * f))].sum() / energy.sum()) for f in [.01, .05, .1, .25]},
            "control_variate_oracles": {"global_lambda": lam,
                "global_tangent_variance_ratio_to_lambda1": Vopt / Vt,
                "perhub_tangent_variance_ratio_to_lambda1": Vopt_h / Vt,
                "perhub_lambda_quantiles": np.quantile(lam_h, [0, .25, .5, .75, 1]).tolist(),
                "uses_all_exact_training_labels": True},
            "cohorts": cohorts, "seconds": time.perf_counter() - t0}
        records[dataset] = record
        np.savez_compressed(results / (dataset + ".npz"),
                            v=v, vp=vp, parallel=parallel, bias_t=bias_t,
                            bias_all=bias_all, var_t=var_t, var_all=var_all,
                            chord2=chord2, energy=energy, ess_b=ess_b,
                            var_y=var_y, var_z=var_z, cov_yz=cov_yz, lambda_h=lam_h)
        print(dataset, json.dumps({k: val for k, val in record.items() if k != "cohorts"}), flush=True)
        assert time.perf_counter() - started < 180
    for path, expected in protected.items():
        assert identity(path) == expected, path
    for path, expected in base_stats.items():
        stat = Path(path).stat()
        assert {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns} == expected
    summary = {"status": "COMPUTED_PENDING_INDEPENDENT_AUDIT", "datasets": records,
               "seconds": time.perf_counter() - started, "new_searches": 0, "new_GT": 0,
               "new_candidate_profiles": 0, "new_performance_points": 0,
               "cpu_affinity": sorted(os.sched_getaffinity(0)),
               "threadpools": threadpool_info(),
               "resident_threads_at_end": len(list(Path('/proc/self/task').iterdir()))}
    dump(results / "summary.json", summary)
    print("COMPUTED", round(summary["seconds"], 3), flush=True)


if __name__ == "__main__":
    run()
