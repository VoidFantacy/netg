"""Independent explicit projections and exhaustive finite-population controls."""
import itertools
import json
import time
from pathlib import Path
import analyze as source
import numpy as np


def close(actual, expected, atol=1e-10):
    if not np.allclose(actual, expected, atol=atol, rtol=1e-9):
        raise AssertionError((actual, expected))


def synthetic():
    cases = []
    base = np.array([2., 0., 0.])
    for e in [np.array([1., 0., 0.]), np.array([0., 1., 0.]),
              np.array([-3., 0., 0.]), np.array([-1.999999, 1e-6, 0.])]:
        norm = np.linalg.norm(base)
        p = base / norm
        alpha = float(p @ e)
        perpendicular = e - alpha * p
        r2 = float(perpendicular @ perpendicular)
        exact = float(np.sum(((base + e) / np.linalg.norm(base + e) - p) ** 2))
        formula = 2 * (1 - (norm + alpha) / np.sqrt((norm + alpha) ** 2 + r2))
        close(exact, formula, 1e-14)
        if norm + alpha > 0:
            assert exact <= r2 / (norm + alpha) ** 2 + 1e-12
        cases.append({"error": e.tolist(), "chord2": exact})
    rng = np.random.default_rng(2026093001)
    n, m = 6, 3
    g = rng.normal(size=(n, 7))
    total = g.sum(0)
    estimates = np.array([n / m * g[list(ix)].sum(0) for ix in itertools.combinations(range(n), m)])
    close(estimates.mean(0), total)
    mse = float(np.mean(np.sum((estimates - total) ** 2, axis=1)))
    trace = float(np.sum((g - g.mean(0)) ** 2) / (n - 1))
    close(mse, (n*n/m-n)*trace)
    replacement = []
    for name, probs in [("uniform", np.full(n, 1/n)), ("oracle", np.linalg.norm(g, axis=1)/np.linalg.norm(g, axis=1).sum())]:
        mse_enum = 0.
        mean_enum = np.zeros(g.shape[1])
        for i, j in itertools.product(range(n), repeat=2):
            z = .5 * (g[i]/probs[i] + g[j]/probs[j])
            mean_enum += probs[i] * probs[j] * z
            mse_enum += probs[i] * probs[j] * float((z-total) @ (z-total))
        close(mean_enum, total)
        formula = (np.sum(np.sum(g*g, axis=1)/probs) - total@total)/2
        close(mse_enum, formula)
        replacement.append({"method": name, "enumerated_MSE": mse_enum, "formula_MSE": float(formula)})
    return {"geometric_counterexamples": cases, "srs_subsets": len(estimates),
            "srs_MSE": mse, "replacement_enumeration": replacement}


def main():
    started = time.perf_counter()
    summary = json.loads((source.OUT / "results/summary.json").read_text())
    audit = {"synthetic": synthetic(), "datasets": {}}
    for ds, record in summary["datasets"].items():
        q, h, a, b = source.reconstruct(ds)
        n, d = q.shape
        saved = np.load(source.OUT / "results" / (ds + ".npz"))
        p = saved["v"] / np.linalg.norm(saved["v"], axis=1)[:, None]
        errors = []
        for hub in np.linspace(0, len(h)-1, 16, dtype=int):
            # Explicit d-dimensional residual centering, then projection.
            residual = (a[:, hub]-b[:, hub])[:, None] * q
            centered = residual - residual.mean(0)
            projection = centered - (centered @ p[hub])[:, None] * p[hub]
            explicit = float(np.sum(projection * projection) / (n-1))
            close(explicit, saved["var_t"][hub])
            sum_r = residual.sum(0)
            perp = sum_r - np.dot(sum_r, p[hub]) * p[hub]
            close(float(perp @ perp), saved["bias_t"][hub])
            errors.append(abs(explicit-float(saved["var_t"][hub])))
        energy_errors = []
        for i in np.linspace(0, n-1, 32, dtype=int):
            residual = (a[i]-b[i])[:, None] * q[i]
            normal = np.sum(residual * p, axis=1)
            tangent = residual - normal[:, None] * p
            energy = float(np.sum(np.sum(tangent*tangent, axis=1) / np.sum(saved["v"]**2, axis=1)))
            close(energy, saved["energy"][i])
            energy_errors.append(abs(energy-float(saved["energy"][i])))
        lambdas = [0., .5, 1., record["control_variate_oracles"]["global_lambda"]]
        cv_errors = []
        for hub in np.linspace(0, len(h)-1, 4, dtype=int):
            for lam in lambdas:
                residual = (a[:,hub]-lam*b[:,hub])[:,None]*q
                residual -= residual.mean(0)
                tangent = residual - (residual @ p[hub])[:,None]*p[hub]
                direct = float(np.sum(tangent*tangent)/(n-1))
                via_covariance = saved["var_y"][hub] - 2*lam*saved["cov_yz"][hub] + lam*lam*saved["var_z"][hub]
                close(direct, via_covariance)
                cv_errors.append(abs(direct-float(via_covariance)))
        audit["datasets"][ds] = {"explicit_variance_hubs": 16, "explicit_query_energies": 32,
            "control_variate_direct_checks": len(cv_errors), "max_variance_abs_error": max(errors),
            "max_energy_abs_error": max(energy_errors), "max_control_variate_error": max(cv_errors)}
        print(ds, audit["datasets"][ds], flush=True)
    frozen = json.loads((source.OUT / "reviews/frozen.json").read_text())
    for path, expected in frozen["files"].items():
        assert source.identity(path) == expected, path
    audit.update(status="PASS", seconds=time.perf_counter()-started,
                 independent_scope="independent formula and explicit projections; same verified weight reconstruction, same agent",
                 source_identities_checked=len(frozen["files"]), new_searches=0, new_GT=0,
                 audit_source=source.identity(Path(__file__)))
    source.dump(source.OUT / "reviews/independent_audit.json", audit)
    print("PASS", audit["seconds"], flush=True)


if __name__ == "__main__":
    main()
