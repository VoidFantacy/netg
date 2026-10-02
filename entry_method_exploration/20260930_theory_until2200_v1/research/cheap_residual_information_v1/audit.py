import analyze as a
import json
import time
from pathlib import Path
import numpy as np


def tree_forward(model, features):
    x = features.astype("f4")
    leaves = np.empty(len(x), dtype=int)
    values = np.empty(len(x))
    for i, row in enumerate(x):
        node = 0
        while model["children_left"][node] != -1:
            node = model["children_left"][node] if row[model["feature"][node]] <= model["threshold"][node] else model["children_right"][node]
        leaves[i] = node
        values[i] = model["value_scaled"][node] * model["scale"]
    return leaves, values


def main():
    started = time.perf_counter()
    summary = json.loads((a.OUT / "results/summary.json").read_text())
    records = {}
    for index, ds in enumerate(summary["datasets"]):
        model = json.loads((a.OUT / "models" / (ds+".json")).read_text())
        saved = np.load(a.OUT / "models" / (ds+".npz"))
        energy = np.load(a.OUT / "results" / (ds+".npz"))["energy"]
        features, pilot, accepted = saved["features"], saved["pilot"], saved["accepted"]
        order = np.random.default_rng(2026093002+index).permutation(20000)
        assert np.array_equal(pilot, order[:2048]) and np.array_equal(accepted, order[2048:])
        assert set(pilot).isdisjoint(set(accepted)) and len(set(order)) == 20000
        max_error = 0.
        for name in ["RiskTree", "ShuffledTree"]:
            leaves, predictions = tree_forward(model[name], features)
            np.testing.assert_allclose(predictions, saved["prediction_"+name], rtol=1e-12, atol=1e-16)
            target = energy[pilot] if name == "RiskTree" else energy[pilot][model["shuffle_order"]]
            assert model[name]["n_node_samples"][0] == 2048
            for leaf in np.unique(leaves[pilot]):
                mask = leaves[pilot] == leaf
                assert mask.sum() == model[name]["n_node_samples"][leaf]
                assert mask.sum() >= 128
                expected = target[mask].mean()
                actual = model[name]["value_scaled"][leaf]*model[name]["scale"]
                np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-16)
                max_error=max(max_error,abs(actual-expected))
        cuts = np.quantile(features[pilot,6],[.25,.5,.75])
        np.testing.assert_array_equal(cuts,model["table_cuts"])
        bins = np.searchsorted(cuts,features[pilot,6],side="right")
        for j in range(4):
            expected=energy[pilot][bins==j].mean()
            np.testing.assert_allclose(expected,model["table_means"][j],rtol=1e-12,atol=1e-16)
        q,h,exact,approx=a.old.reconstruct(ds)
        v=h+approx.T@q; norm=np.linalg.norm(v,axis=1); p=v/norm[:,None]
        direct_errors=[]
        for i in np.linspace(0,19999,32,dtype=int):
            z=(exact[i]-approx[i])[:,None]*q[i]
            z-=np.einsum("hd,hd->h",z,p)[:,None]*p
            value=float(np.sum(np.sum(z*z,axis=1)/norm**2))
            np.testing.assert_allclose(value,energy[i],rtol=1e-10,atol=1e-15)
            direct_errors.append(abs(value-energy[i]))
        counts=0
        for part, sl in [("all_accept",slice(None)),("accept_half1",slice(0,8976)),("accept_half2",slice(8976,None))]:
            rows=accepted[sl]
            residual_sum=(exact[rows]-approx[rows]).T@q[rows]
            residual_sum-=np.einsum("hd,hd->h",residual_sum,p)[:,None]*p
            B=float(np.sum(np.sum(residual_sum**2,axis=1)/norm**2))
            for method, values in summary["datasets"][ds]["assessments"][part]["methods"].items():
                if method=="Oracle":
                    probs=np.sqrt(energy[rows]); probs/=probs.sum()
                else:
                    if method=="Uniform":raw_probs=np.ones(len(accepted))/len(accepted)
                    else:
                        prediction=saved["prediction_"+method][accepted]
                        weights=np.sqrt(np.maximum(prediction,0))
                        raw_probs=.5/len(accepted)+.5*weights/weights.sum()
                        np.testing.assert_allclose(raw_probs,saved["probability_"+method],rtol=1e-13,atol=1e-18)
                        assert raw_probs.min()>=.5/len(accepted)-1e-16
                    probs=raw_probs[sl]; probs=probs/probs.sum()
                numerator=sum(float(energy[i]/prob) if prob else 0. for i,prob in zip(rows,probs))-B
                np.testing.assert_allclose(numerator,values["HH_variance_numerator"],rtol=1e-11,atol=1e-8)
                counts+=1
        records[ds]={"all_scalar_tree_predictions":40000,"pilot_labels":2048,"accept_rows":len(accepted),
            "max_leaf_mean_error":max_error,"direct_energy_checks":32,"max_direct_energy_error":max(direct_errors),
            "independent_variance_numerators":counts}
        print(ds,records[ds],flush=True)
    freezes=[a.OUT/"reviews/frozen.json", a.old.OUT/"reviews/frozen.json"]
    freezes += sorted((a.OUT/"reviews").glob("*.prediction_frozen.json"))
    identity_count=0
    for path in freezes:
        for file, expected in json.loads(path.read_text())["files"].items():
            assert a.old.identity(file)==expected,file
            identity_count+=1
    a.old.dump(a.OUT/"reviews/independent_audit.json",{"status":"PASS","datasets":records,
        "seconds":time.perf_counter()-started,"identities_checked":identity_count,
        "audit_source":a.old.identity(Path(__file__)),
        "scope":"same agent; independent scalar tree, leaf means, direct energy and variance summation",
        "new_searches":0,"new_GT":0})
    print("PASS",round(time.perf_counter()-started,3),flush=True)


if __name__=="__main__":main()
