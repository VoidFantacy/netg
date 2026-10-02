"""Fit only the frozen pilot; assess residual sampling information on the rest."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "8"
os.sched_setaffinity(0, set(range(8)))
import hashlib
import importlib.util
import json
import time
from pathlib import Path
import numpy as np
from sklearn.tree import DecisionTreeRegressor

OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("directional_source", OUT.parent / "directional_error_v1/analyze.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
NAMES = ["query_norm", "mean_top10_distance_per_qnorm", "gap10_11_per_qnorm",
         "spread1_10_per_qnorm", "assignment_entropy", "assignment_l2_squared",
         "approx_tangent_leverage", "weighted_inverse_resultant"]


def tree_record(model, scale):
    t = model.tree_
    return {"children_left": t.children_left.tolist(), "children_right": t.children_right.tolist(),
            "feature": t.feature.tolist(), "threshold": t.threshold.tolist(),
            "value_scaled": t.value[:, 0, 0].tolist(), "n_node_samples": t.n_node_samples.tolist(),
            "scale": scale, "input_cast": "float32", "max_depth": 2, "min_samples_leaf": 128}


def fit_only_pilot(pilot_features, pilot_energy, all_features, seed):
    # No accepted energy argument or global risk available in this function.
    scale = float(pilot_energy.mean())
    if scale <= 0:
        scale = 1.
    model = DecisionTreeRegressor(max_depth=2, min_samples_leaf=128, random_state=2026093002)
    model.fit(pilot_features, pilot_energy / scale)
    predicted = model.predict(all_features) * scale
    shuffle = np.random.default_rng(2026093003 + seed).permutation(len(pilot_energy))
    control = DecisionTreeRegressor(max_depth=2, min_samples_leaf=128, random_state=2026093002)
    control.fit(pilot_features, pilot_energy[shuffle] / scale)
    shuffled = control.predict(all_features) * scale
    cuts = np.quantile(pilot_features[:, 6], [.25, .5, .75])
    pilot_bins = np.searchsorted(cuts, pilot_features[:, 6], side="right")
    table = np.array([pilot_energy[pilot_bins == i].mean() if np.any(pilot_bins == i) else pilot_energy.mean() for i in range(4)])
    binned = table[np.searchsorted(cuts, all_features[:, 6], side="right")]
    return {"RiskTree": predicted, "ShuffledTree": shuffled, "QuartileTable": binned,
            "Leverage": all_features[:, 6].copy()}, {
            "RiskTree": tree_record(model, scale), "ShuffledTree": tree_record(control, scale),
            "table_cuts": cuts.tolist(), "table_means": table.tolist(),
            "shuffle_order": shuffle.tolist(), "pilot_target_mean": float(pilot_energy.mean())}


def probabilities(prediction):
    n = len(prediction)
    weights = np.sqrt(np.maximum(prediction, 0.))
    if weights.sum() == 0:
        return np.full(n, 1/n)
    out = .5/n + .5 * weights/weights.sum()
    assert out.min() >= .5/n - 1e-15
    return out


def projected_bias(delta, query, profiles, norms):
    sums = delta.T @ query
    sums -= np.sum(sums * profiles, axis=1)[:, None] * profiles
    return float(np.sum(np.sum(sums*sums, axis=1)/norms**2))


def assess(rows, probs, energy, exact_energy, delta, q, pp, nn, ep, en):
    n = len(rows)
    B = projected_bias(delta[rows], q[rows], pp, nn)
    Bexact = projected_bias(delta[rows], q[rows], ep, en)
    out = {}
    normalized = {name: value / value.sum() for name, value in probs.items()}
    oracle = np.sqrt(energy[rows]); oracle /= oracle.sum()
    normalized["Oracle"] = oracle
    for name, prob in normalized.items():
        energy_numerator = float(np.divide(energy[rows], prob, out=np.zeros(n), where=prob>0).sum() - B)
        exact_numerator = float(np.divide(exact_energy[rows], prob, out=np.zeros(n), where=prob>0).sum() - Bexact)
        if np.any(prob == 0):
            assert np.all(energy[rows][prob == 0] == 0) and np.all(exact_energy[rows][prob == 0] < 1e-25)
        assert energy_numerator >= -1e-8 and exact_numerator >= -1e-8
        out[name] = {"HH_variance_numerator": energy_numerator,
                     "HH_numerator_exact_geometry_diagnostic": exact_numerator,
                     "probability_min": float(prob.min()), "probability_max": float(prob.max()),
                     "effective_distribution_size": float(1/np.sum(prob*prob)),
                     "top10percent_probability_energy_capture": float(energy[rows][np.argsort(prob)[-int(np.ceil(.1*n)):]].sum()/energy[rows].sum())}
    for name in out:
        out[name]["ratio_to_uniform"] = out[name]["HH_variance_numerator"] / out["Uniform"]["HH_variance_numerator"]
        out[name]["ratio_to_uniform_exact_geometry_diagnostic"] = out[name]["HH_numerator_exact_geometry_diagnostic"] / out["Uniform"]["HH_numerator_exact_geometry_diagnostic"]
    return {"n": n, "projected_residual_total_squared": B, "methods": out}


def main():
    started = time.perf_counter()
    for part in ["results", "models", "reviews"]:
        (OUT / part).mkdir(exist_ok=True)
    assert not (OUT / "results/summary.json").exists()
    protected = {str(Path(__file__)): old.identity(__file__), str(OUT / "protocol.md"): old.identity(OUT / "protocol.md")}
    for ds, dc in old.CONFIG["datasets"].items():
        for file in [old.E125 / "results" / ds / "labels/distances.f32", old.OUT / "results" / (ds + ".npz")]:
            protected[str(file)] = old.identity(file)
    old.dump(OUT / "reviews/frozen.json", {"unix": time.time(), "files": protected,
             "source_reconstruction_freeze": str(old.OUT / "reviews/frozen.json")})
    records = {}
    for dataset_index, ds in enumerate(old.CONFIG["datasets"]):
        t0 = time.perf_counter()
        q, h, a, b = old.reconstruct(ds)
        n, d = q.shape
        c = old.CONFIG["datasets"][ds]["original"]
        rawq = np.fromfile(c["fit_source"]["queries_file"], "<f4").reshape(n, d).astype("f8")
        qnorm = np.linalg.norm(rawq, axis=1)
        distances = np.fromfile(old.E125 / "results" / ds / "labels/distances.f32", "<f4").reshape(n, 100).astype("f8")
        assert np.all(np.diff(distances, axis=1) >= 0)
        prior = np.load(old.OUT / "results" / (ds + ".npz"))
        vp = h + b.T @ q
        assert np.max(np.abs(vp-prior["vp"])) < 1e-9
        nn = np.linalg.norm(vp, axis=1); pp = vp/nn[:,None]
        en = np.linalg.norm(prior["v"], axis=1); ep = prior["v"]/en[:,None]
        tq = np.maximum((q*q).sum(1)[:,None] - (q @ pp.T)**2, 0)
        delta = a-b
        # Target uses only the query's own exact assignment and known approximate geometry.
        energy = (delta**2*tq) @ (1/nn**2)
        leverage = (b**2*tq) @ (1/nn**2)
        entropy = -np.sum(b*np.log(np.maximum(b, 1e-300)), axis=1)
        features = np.column_stack([qnorm, distances[:,:10].mean(1)/qnorm,
            (distances[:,10]-distances[:,9])/qnorm, (distances[:,9]-distances[:,0])/qnorm,
            entropy, np.sum(b*b,axis=1), leverage, b @ (1/nn)])
        assert np.isfinite(features).all() and np.isfinite(energy).all()
        order = np.random.default_rng(2026093002+dataset_index).permutation(n)
        pilot, accepted = order[:2048], order[2048:]
        assert len(set(pilot)&set(accepted)) == 0
        predictions, model = fit_only_pilot(features[pilot], energy[pilot], features, dataset_index)
        probs = {name: probabilities(value[accepted]) for name, value in predictions.items()}
        probs["Uniform"] = np.full(len(accepted), 1/len(accepted))
        model.update(dataset=ds, feature_names=NAMES, pilot_rows=pilot.tolist(), accepted_rows=accepted.tolist(),
                     seed=2026093002+dataset_index, labels_used_for_fit=2048)
        model_file = OUT / "models" / (ds + ".json")
        old.dump(model_file, model)
        prediction_file = OUT / "models" / (ds + ".npz")
        np.savez_compressed(prediction_file, features=features, pilot=pilot, accepted=accepted,
                            **{"prediction_"+name: value for name,value in predictions.items()},
                            **{"probability_"+name: value for name,value in probs.items()})
        old.dump(OUT / "reviews" / (ds + ".prediction_frozen.json"), {
            "unix":time.time(), "files": {str(model_file):old.identity(model_file),str(prediction_file):old.identity(prediction_file)},
            "fit_target_role":"pilot 2048 only; rest exact labels decoded for diagnostic but not passed to estimator"})
        parts = {"all_accept": accepted, "accept_half1": accepted[:8976], "accept_half2": accepted[8976:]}
        assessments = {}
        for name, rows in parts.items():
            select = slice(None) if name == "all_accept" else (slice(0,8976) if name == "accept_half1" else slice(8976,None))
            assessments[name] = assess(rows, {method: prob[select] for method,prob in probs.items()},
                 energy, prior["energy"], delta, q, pp, nn, ep, en)
        record = {"pilot_n":2048, "accepted_n":len(accepted), "pilot_energy_mean":float(energy[pilot].mean()),
            "accepted_energy_mean":float(energy[accepted].mean()), "assessments":assessments,
            "seconds":time.perf_counter()-t0}
        records[ds] = record
        np.savez_compressed(OUT / "results" / (ds+".npz"), energy=energy, exact_geometry_energy=prior["energy"])
        print(ds, {name: m["ratio_to_uniform"] for name,m in assessments["all_accept"]["methods"].items()},flush=True)
        assert time.perf_counter()-started < 180
    for path, expected in protected.items():
        assert old.identity(path)==expected,path
    old.dump(OUT / "results/summary.json", {"status":"COMPUTED_PENDING_AUDIT", "datasets":records,
        "seconds":time.perf_counter()-started, "new_GT":0, "new_searches":0,
        "new_candidate_profiles":0, "new_performance_points":0, "labels_revealed_to_models_per_dataset":2048,
        "historically_exposed_training_pool":True})
    print("COMPUTED",round(time.perf_counter()-started,3),flush=True)


if __name__ == "__main__":
    main()
