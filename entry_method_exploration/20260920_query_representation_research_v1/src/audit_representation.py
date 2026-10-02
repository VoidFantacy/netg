"""Cached FIT geometry only. Never imports a training/evaluation runner."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
from pathlib import Path
import hashlib
import json
import time
import warnings
import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1]
E28 = ROOT / "entry_method_exploration/20260911_gt10_shared_transform_v1"
E24 = ROOT / "entry_method_exploration/20260910_gt_topk_profiles_v1"
DATASETS = ["webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1"]
ROWS = list(range(0, 20000, 2500))
MARGIN = 1e-4


def identity(path):
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    result_path = OUT / "results/representation.json"
    assert not result_path.exists(), "Preserve old results; use an independent version."
    lock = dict(rows=ROWS, margin=MARGIN, lp_seconds_per_row=5,
                scope="historical E28 FIT teachers, exact profile scores only",
                selection="fixed equally spaced row positions, before payload access",
                new_training_runs=0, ann_calls=0, gt_calls=0, graph_builds=0,
                qps_rounds=0, evaluation_payload_access=False)
    (OUT / "reviews/geometry_lock.json").write_text(json.dumps(lock, indent=2)+"\n")
    start = time.monotonic()
    all_results, before, witnesses = [], [], {}
    for ds in DATASETS:
        config_path = E28 / "inputs" / ds / "fit/config.json"
        c = json.loads(config_path.read_text())
        assert c["split"] == "fit" and c["num_queries"] == 20000
        n, d, h = c["num_queries"], c["dim"], c["hub_count"]
        q_path = Path(c["queries_file"])
        p_path = E24 / "models" / ds / "gt10_hard/W.f32"
        t_path = E28 / "labels" / ds / "teacher.i32"
        paths = [config_path, q_path, p_path, t_path]
        before.extend(identity(p) for p in paths)
        q = np.memmap(q_path, mode="r", dtype="float32", shape=(n,d))[ROWS].astype("float64")
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        p = np.fromfile(p_path, "float32").reshape(h,d).astype("float64")
        teachers = np.memmap(t_path, mode="r", dtype="int32", shape=(n,3))[ROWS].copy()
        assert np.isfinite(p).all() and np.isfinite(q).all()
        records = []
        for row, x, selected in zip(ROWS, q, teachers):
            assert len(set(selected.tolist())) == 3 and min(selected)>=0 and max(selected)<h
            outside = np.setdiff1d(np.arange(h), selected)
            # D z >= margin guarantees every chosen item outranks every other item.
            D = (p[selected,None,:] - p[outside][None,:,:]).reshape(-1,d)
            A = np.vstack([np.column_stack([-D, np.zeros(len(D))]),
                           np.column_stack([np.eye(d), -np.ones(d)]),
                           np.column_stack([-np.eye(d), -np.ones(d)])])
            b = np.concatenate([D@x-MARGIN, np.zeros(2*d)])
            obj = np.r_[np.zeros(d),1.]
            t0 = time.monotonic()
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Unrecognized options detected")
                opt = linprog(obj, A_ub=A, b_ub=b, bounds=[(None,None)]*d+[(0,None)],
                              method="highs", options={"time_limit":5., "threads":1})
            rec = dict(row=row, teacher_slots=selected.tolist(), solver_status=int(opt.status),
                       seconds=time.monotonic()-t0, original_min_margin=float((D@x).min()))
            if opt.success:
                z=x+opt.x[:d]
                exact=np.argsort(-(p@z), kind="stable")[:3]
                rec.update(witness_min_margin=float((D@z).min()),
                           linf_delta=float(np.abs(z-x).max()),
                           l2_delta=float(np.linalg.norm(z-x)),
                           direction_cosine=float(x@z/np.linalg.norm(z)),
                           exact_teacher_set_recovered=set(exact)==set(selected))
                assert rec["witness_min_margin"] >= MARGIN-1e-7
                assert rec["exact_teacher_set_recovered"]
                witnesses[f"{ds}_{row}"]=z
            records.append(rec)
        # Affine query scores equal static hub weights plus hub-specific biases.
        rng=np.random.default_rng(20260920)
        u=rng.normal(size=(d,16))*.01;v=rng.normal(size=(16,d))*.01
        bias=rng.normal(size=d)*.01
        direct=(q+(q@v.T)@u.T+bias)@p.T
        folded=q@(p+(p@u)@v).T+(p@bias)
        err=float(np.max(np.abs(direct-folded)))
        assert err<1e-10
        all_results.append(dict(dataset=ds, hub_count=h, dim=d, records=records,
                                affine_folding_max_abs_error=err))
        assert all(identity(path)==before[-4+i] for i,path in enumerate(paths))
    np.savez(OUT/"results/geometry_witnesses.npz", **witnesses)
    report=dict(status="COMPLETE_GEOMETRY_ONLY", protocol=lock, datasets=all_results,
                inputs=before, input_identity_unchanged=True, wall_seconds=time.monotonic()-start,
                source=identity(Path(__file__).resolve()),
                limitation="Old K10 teacher geometry is neither K1/K100 utility nor generalization or HNSW feasibility.")
    result_path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"seconds":report["wall_seconds"],
        "datasets":[{"dataset":x["dataset"],"verified_witnesses":sum(r.get("exact_teacher_set_recovered",False) for r in x["records"]),
                     "rows":len(x["records"]),"folding_error":x["affine_folding_max_abs_error"]} for x in all_results]}))


if __name__ == "__main__":
    main()
