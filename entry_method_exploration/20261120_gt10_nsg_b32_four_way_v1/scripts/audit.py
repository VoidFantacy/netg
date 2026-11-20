"""Independently recompute the reported metrics from actual IDs and raw batch walls."""
from array import array
import csv
from math import isclose
import sys

from run import ROOT, DATASETS, MATRIX, N, read, write


def language_neutral_array(path,kind):
    data=array(kind)
    data.frombytes(path.read_bytes())
    if sys.byteorder!="little":
        data.byteswap()
    return data


def load_truth(path,fmt):
    stride=101 if fmt=="ivecs" else 100
    words=language_neutral_array(path,"i" if fmt=="ivecs" else "q")
    if fmt=="ivecs":
        assert all(words[i*stride]==100 for i in range(N))
    start=stride-100
    truth=[set(words[i*stride+start:(i+1)*stride]) for i in range(N)]
    assert all(len(t)==100 for t in truth)
    return truth,[words[i*stride+start] for i in range(N)]


def rows(name):
    with (ROOT/f"analysis/{name}.csv").open() as handle:
        return list(csv.DictReader(handle))


def key(p):
    return p["dataset"],int(p["K"]),int(p["L"]),p["method"]


def check(value,expected):
    assert isclose(float(value),expected,abs_tol=1e-11,rel_tol=1e-11),(value,expected)


def main():
    from pathlib import Path
    packet_audit=read(ROOT/"reviews/output_audit.json")
    assert packet_audit["status"]=="PASS_E212_PACKETS"
    points=rows("points")
    point_map={key(p):p for p in points}
    cfg=read(ROOT/"gt_eval.json")
    hits={}
    walls={}
    for ds in DATASETS:
        cfg_ds=cfg[ds]
        truth_k100,truth_k1=load_truth(Path(cfg_ds["path"]),cfg_ds["format"])
        for p in points:
            dataset,k,l,m=key(p)
            if dataset!=ds:
                continue
            directory=ROOT/f"data/{ds}/K{k}_L{l}/{m}"
            ids=language_neutral_array(directory/"raw/ids.i32","i")
            assert len(ids)==N*k
            if k==1:
                counts=[int(x==y) for x,y in zip(ids,truth_k1)]
            else:
                counts=[sum(id_ in t for id_ in ids[i*k:(i+1)*k]) for i,t in enumerate(truth_k100)]
                assert int(p["low_recall"])==sum(c<10 for c in counts)
            hits[dataset,k,l,m]=counts
            assert sum(counts)==int(p["hits"])
            check(p["recall_pct"],sum(counts)*100/(N*k))
            times=tuple(read(directory/f"round{rep}.json")["seconds"] for rep in range(2))
            speeds=tuple(N/t for t in times)
            walls[dataset,k,l,m]=times
            check(p["qps"],sum(speeds)/2)
            check(p["qps_min"],min(speeds))
            check(p["qps_max"],max(speeds))
    assert len(point_map)==len(hits)==len(DATASETS)*len(MATRIX)*4
    for row in rows("same_l"):
        ds,k,l,m=key(row)
        before=hits[ds,k,l,row["baseline"]]
        after=hits[ds,k,l,m]
        pair=list(zip(before,after))
        assert int(row["better_queries"])==sum(b>a for a,b in pair)
        assert int(row["worse_queries"])==sum(b<a for a,b in pair)
        assert int(row["equal_queries"])==sum(b==a for a,b in pair)
        check(row["recall_delta_pp"],100*(sum(after)-sum(before))/(N*k))
        a,b=walls[ds,k,l,row["baseline"]],walls[ds,k,l,m]
        check(row["qps_delta_pct"],100*(sum(1/t for t in b)/sum(1/t for t in a)-1))
        check(row["saved_us_per_query"],1e6*(sum(a)-sum(b))/(2*N))
        if k==100:
            assert int(row["escaped_low"])==sum(a<10<=b for a,b in pair)
            assert int(row["entered_low"])==sum(b<10<=a for a,b in pair)
    targets=rows("recall_thresholds")
    for r in targets:
        ds,k,m,target=r["dataset"],int(r["K"]),r["method"],int(r["target_pct"])
        eligible=[p for p in points if (p["dataset"],int(p["K"]),p["method"])==(ds,k,m)
                  and int(p["hits"])*100>=N*k*target]
        cross=[p for p in points if (p["dataset"],int(p["K"]))==(ds,k)
               and int(p["hits"])*100>=N*k*target]
        if eligible:
            best=max(eligible,key=lambda p:float(p["qps"]))
            assert r["L"]==best["L"]
            check(r["qps"],float(best["qps"]))
            assert (r["fastest_at_target"]=="True")==(
                float(best["qps"])==max(float(p["qps"]) for p in cross))
        else:
            assert not r["L"] and not r["qps"] and r["fastest_at_target"]=="False"
    for row in rows("frontier"):
        ds,k,l,m=key(row)
        base=point_map[ds,k,l,m]
        R,Q=int(base["hits"]),float(base["qps"])
        stronger=[p for p in points if (p["dataset"],int(p["K"]))==(ds,k)
                  and int(p["hits"])>=R and float(p["qps"])>=Q
                  and (int(p["hits"])>R or float(p["qps"])>Q)]
        assert (row["on_frontier"]=="True")== (not stronger)
    write(ROOT/"reviews/independent_audit.json",{"status":"PASS_E212_STDLIB_AUDIT",
          "recall_points":len(hits),"batch_walls":2*len(walls),"threshold_rows":len(targets),
          "query_hit_rows":sum(map(len,hits.values()))})


if __name__=="__main__":
    main()
