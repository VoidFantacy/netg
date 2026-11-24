"""Extend the frozen B32 with real training omissions on Flickr30k and Yandex."""
from hashlib import sha256
from pathlib import Path
import subprocess
from time import monotonic

import numpy as np

from run import E183, ENV, digest, lock, read, vectors, write

LEVELS = (176, 192, 208)


def keys(matrix):
    return {sha256(row.tobytes()).digest() for row in matrix}


def flickr_extra(c, old_queries, folder):
    import faiss

    p = Path(c["queries"]["path"]).parent
    role_rows = {r: p / f"{r}.source_rows.i64" for r in ("test", "profile", "qgt", "residual")}
    groups_path = p / "source_group_ids.i64"
    groups = np.fromfile(groups_path, "<i8")
    role_ids = {r: groups[np.fromfile(f, "<i8")] for r, f in role_rows.items()}
    profile = p / "profile.f32"
    new_source = np.memmap(profile, "<f4", "r").reshape(len(role_ids["profile"]), c["base"]["d"])
    forbidden = set(role_ids["test"]) | set(role_ids["residual"]) | set(role_ids["qgt"])
    seen = keys(old_queries) | keys(vectors(c["queries"]))
    chosen = []
    for i, group in enumerate(role_ids["profile"]):
        h = sha256(new_source[i].tobytes()).digest()
        if group in forbidden or h in seen:
            continue
        seen.add(h)
        forbidden.add(group)
        chosen.append(i)
        if len(chosen) == 4096:
            break
    assert len(chosen) == 4096
    q = np.ascontiguousarray(new_source[chosen])
    base = np.ascontiguousarray(vectors(c["base"]))
    faiss.omp_set_num_threads(4)
    index = faiss.IndexFlatIP(base.shape[1])
    index.add(base)
    dist, gt = index.search(q, 100)
    assert np.isfinite(dist).all() and (np.diff(dist, axis=1) <= 0).all()
    # Re-evaluate sampled labels independently in double precision.
    audit = np.linspace(0, len(q) - 1, 64, dtype=int)
    scores = q[audit].astype(np.float64) @ base.astype(np.float64).T
    chosen_scores = np.take_along_axis(scores, gt[audit], axis=1)
    np.put_along_axis(scores, gt[audit], -np.inf, axis=1)
    max_gap = float(np.max(scores.max(axis=1) - chosen_scores.min(axis=1)))
    assert max_gap < 2e-6, max_gap
    readout = folder / "extra_gt_audit.json"
    write(readout, dict(metric="exhaustive raw IP", training_queries=len(q), checked=64, max_gap=max_gap))
    np.asarray(chosen, "<i4").tofile(folder / "extra_rows.i32")
    return q, gt, [profile, groups_path, *role_rows.values(), readout], "prepared profile role, exact group and query overlap checked"


def yandex_extra(c, teacher, folder):
    base = Path(c["base"]["path"]).parent
    manifest = base / "manifest.json"
    meta = read(manifest)
    names = ("query.router_train.fvecs", "gt.router_train.ip.ivecs", "query.test.public100K.fvecs", "query.validation.fvecs")
    for name in names:
        p = base / name
        assert p.stat().st_size == meta["files"][name]["bytes"] and digest(p) == meta["files"][name]["sha256"]
    assert meta["ground_truth"] == {"k": 100, "metric": "exact_inner_product"}
    assert c["base"]["n"] == 10_000_000
    d = c["base"]["d"]
    roles = [(names[0], 30000), (names[2], 100000), (names[3], 10000)]
    train, public, validation = [vectors(dict(path=str(base / name), format="fvecs", d=d, n=n)) for name, n in roles]
    full_fit = vectors(dict(teacher, n=teacher["total_n"], row_start=0))
    blocked = keys(full_fit) | keys(public) | keys(validation)
    chosen = []
    for i, row in enumerate(train):
        h = sha256(row.tobytes()).digest()
        if h in blocked:
            continue
        blocked.add(h)
        chosen.append(i)
        if len(chosen) == 8192:
            break
    assert len(chosen) == 8192
    gt = np.memmap(base / names[1], "<i4", "r").reshape(30000, 101)[chosen]
    assert (gt[:, 0] == 100).all()
    np.asarray(chosen, "<i4").tofile(folder / "extra_rows.i32")
    return train[chosen], gt[:, 1:], [manifest, *(base / name for name in names)], "official router_train, full fit/validation/public excluded by exact bytes"


def events(teacher_dir, gt, prefix, folder):
    (folder / "raw").mkdir(parents=True)
    n = len(gt)
    offsets = np.arange(n, dtype=np.int64)[:, None] * (1 << 32)
    probe = gt + offsets
    queries, targets, routes = [], [], []
    covered = 0
    per_level = {}
    for ordinal, l in enumerate(LEVELS):
        p = teacher_dir / f"K100_L{l}/raw"
        main = np.fromfile(p / "ids.i32", "<i4").reshape(n, 100)
        route = np.fromfile(p / "entry_ids.i32", "<i4").reshape(n, 3)
        found = (np.sort(main, axis=1) + offsets).ravel()
        pos = np.minimum(np.searchsorted(found, probe), len(found) - 1)
        missing = found[pos] != probe
        for j in np.linspace(0, n - 1, 64, dtype=int):
            assert set(gt[j][missing[j]]) == set(gt[j]) - set(main[j])
        qi, rank = np.nonzero(missing)
        truths = gt[qi, rank]
        unions = [prefix[a] | prefix[b] | prefix[c] for a, b, c in route]
        count = sum(t in unions[i] for i, t in zip(qi, truths))
        covered += count
        per_level[str(l)] = {"events": len(qi), "B32_covered": count}
        queries.append(qi + ordinal * n)
        targets.append(truths)
        routes.append(route)
    np.concatenate(queries).astype("<i4").tofile(folder / "token_queries.i32")
    np.concatenate(targets).astype("<i4").tofile(folder / "token_targets.i32")
    np.concatenate(routes).astype("<i4").tofile(folder / "raw/entry_ids.i32")
    return covered, per_level


def build_mixed(ds, c, root, compiler, native):
    begin = monotonic()
    scope = root / "models" / ds
    scope.mkdir()
    train_spec = E183 / "configs" / f"{ds}.teacher.json"
    spec = read(train_spec)["queries"]
    old_query = vectors(spec)
    table = Path(c["table"])
    prior = table.parent.parent / "compile_manifest.json"
    source = read(prior)
    gt_spec = source["train_gt"]
    assert gt_spec["format"] == "raw_i64"
    old_gt_path = Path(gt_spec["path"])
    old_gt = np.memmap(old_gt_path, "<i8", "r").reshape(gt_spec.get("total_n", gt_spec["n"]), 100)[:len(old_query)]
    files = [train_spec, Path(spec["path"]), prior, old_gt_path]
    if ds == "flickr30k":
        q, g, added, description = flickr_extra(c, old_query, scope)
    else:
        q, g, added, description = yandex_extra(c, spec, scope)
    files.extend(added)
    full = np.concatenate((old_query, q))
    gt = np.concatenate((old_gt, g)).astype("<i4")
    assert len(old_query) == 16000 and len(keys(full)) == len(full)
    assert not (keys(full) & keys(vectors(c["queries"])))
    assert gt.min() >= 0 and gt.max() < c["base"]["n"]
    assert (np.diff(np.sort(gt, axis=1), axis=1) > 0).all()
    query_file = scope / "train.f32"
    full.astype("<f4").tofile(query_file)
    gt.tofile(scope / "train.gt.i32")
    out = root / "data" / "teachers" / ds
    cfg = root / "configs" / f"{ds}.teacher.json"
    write(cfg, dict(c, train_n=len(full), train_queries=str(query_file), build_teacher=True, grid=LEVELS,
                    output_dir=str(out)))
    native(cfg, root / "logs" / f"{ds}.teacher.log")
    receipt = read(out / "complete.json")
    assert (receipt["status"], receipt["n"], receipt["points"], receipt["threads"], receipt["GT_read"]) == (
        "PASS_E251_TRAIN_MAIN", len(full), len(LEVELS), 1, False
    )
    raw = table.read_bytes()
    assert raw[:8] == b"M5POST1\0"
    _, h, width = map(int, np.frombuffer(raw, "<u4", 3, 8))
    assert width == 32
    ids = np.frombuffer(raw, "<i4", h, 40)
    counts = np.frombuffer(raw, "u1", h, 40 + h * 4)
    values = np.frombuffer(raw, "<i4", 32 * h, 40 + h * 5).reshape(h, 32)
    prefix = {row: set(items[:size]) for row, items, size in zip(ids, values, counts)}
    tokens = scope / "tokens"
    cover, units = events(out, gt, prefix, tokens)
    pool = scope / "mixed"
    compile_cfg = root / "configs" / f"{ds}.compile.json"
    write(compile_cfg, dict(base_n=c["base"]["n"], table=c["table"], token_source=str(tokens),
                            teacher_root=str(tokens), old_covered=cover, output_dir=str(pool)))
    with (root / "logs" / f"{ds}.compile.log").open("x") as log:
        subprocess.run(["taskset", "-c", "15", str(compiler), "compile64", str(compile_cfg)],
                       stdout=log, stderr=subprocess.STDOUT, env=ENV, check=True)
    stats = read(pool / "complete.json")
    assert stats["teacher"] == len(LEVELS) * len(full) and stats["covered_B32"] == cover
    roles = scope / "roles.json"
    write(roles, dict(original=len(old_query), extra=len(q), n=len(full), source=description,
                      levels=LEVELS, events=units, offline_seconds=monotonic() - begin))
    teacher_lock = scope / "teacher_outputs.json"
    lock(teacher_lock, sorted(p for p in out.rglob("*") if p.is_file()))
    files.extend([cfg, compile_cfg, *[p for p in scope.rglob("*") if p.is_file()]])
    return pool, roles, files
