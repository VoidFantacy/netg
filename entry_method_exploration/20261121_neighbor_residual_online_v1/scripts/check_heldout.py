"""Evaluate the frozen dev/cal results and apply the formal-run rule."""
import csv
from pathlib import Path
from statistics import mean

from prepare import DATASETS,E215,N,ROOT,read,write
import numpy as np


def arr(path,dtype,n,k):
    a=np.fromfile(path,dtype)
    assert a.size==n*k,(path,a.size)
    return a.reshape(n,k)


def hit_counts(ids,gt):
    return np.fromiter((len(set(x).intersection(y)) for x,y in zip(ids,gt)),dtype=np.int16,count=len(gt))


def save(name,rows):
    with (ROOT/"analysis"/name).open("x",newline="") as f:
        w=csv.DictWriter(f,list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    assert read(ROOT/"heldout_complete.json")["status"]=="PASS_E216_HELDOUT"
    with (E215/"analysis/neighbor_source.csv").open() as f:
        earlier={(p["dataset"],int(p["K"]),p["role"]):p for p in csv.DictReader(f)
                 if p["source"]=="all" and p["new_slot_limit"]=="16"}
    rows,qualified=[],[]
    for ds in DATASETS:
        cfg=read(ROOT/"configs"/f"{ds}.heldout.json")
        roles=arr(cfg["roles"],"i1",N,1).ravel()
        groups=arr(cfg["identity_groups"],"<i4",N,1).ravel()
        m=Path(cfg["model_dir"])
        held=np.fromfile(m/"held_rows.i32","<i4")
        fit=np.fromfile(m/"fit_rows.i32","<i4")
        assert np.array_equal(held,np.flatnonzero(roles>0)) and np.array_equal(fit,np.flatnonzero(roles==0))
        assert not set(groups[held]).intersection(groups[fit])
        g=cfg["train_gt"]
        assert g["format"]=="raw_i64" and g.get("row_start",0)==0
        truth=np.fromfile(g["path"],"<i8").reshape(-1,100)[held]
        for k in (1,100):
            root=Path(cfg["output_dir"])/("k"+str(k))
            source=Path(cfg["packets"][str(k)]["target"])
            target=hit_counts(arr(source/"ids.i32","<i4",N,k)[held],truth[:,:k])
            receipt=read(root/"timing.json")
            quali=read(root/"qualification.json")
            budget=quali["B32-fit"]["actual_scores"]
            assert len(budget)==128 and max(budget)<=96
            old_raw=arr(Path(cfg["packets"][str(k)]["anchor"])/"ids.i32","<i4",N,k)[held]
            out_base=arr(root/"B32-fit/raw/ids.i32","<i4",len(held),k)
            assert np.array_equal(old_raw,out_base)
            baseline=hit_counts(out_base,truth[:,:k])
            wall={arm:mean([e["seconds"]*1e6/len(held) for e in receipt if e["arm"]==arm])
                  for arm in ("B32-fit","VOTE","CACHE")}
            for arm in ("B32-fit","VOTE","CACHE"):
                assert quali[arm]["actual_scores"]==budget and max(quali[arm]["replaced"])<=16
                got=arr(root/arm/"raw/ids.i32","<i4",len(held),k)
                assert np.all(np.diff(np.sort(got,axis=1),axis=1)>0)
                h=hit_counts(got,truth[:,:k])
                delta=[]
                for r,name in ((1,"dev"),(2,"cal")):
                    mask=roles[held]==r
                    n=int(mask.sum())
                    a,b,c=(int(x[mask].sum()) for x in (baseline,h,target))
                    ref=earlier[ds,k,name]
                    assert (a,c)==(int(ref["anchor_hits"]),int(ref["reference_hits"]))
                    rows.append({"dataset":ds,"K":k,"role":name,"queries":n,"method":arm,"hits":b,
                        "recall_pct":100*b/(n*k),"same_l_gain":b-a,"vs_L192":b-c,
                        "E215_exact_neighbor_hits":int(ref["hits"]),
                        "extra_vs_fit_b32_us":wall[arm]-wall["B32-fit"],"replay_us":wall[arm],
                        "candidate_replaced_mean_sample":mean(quali[arm]["replaced"])})
                    delta.append(b-a)
                if arm!="B32-fit" and min(delta)>0:
                    qualified.append({"dataset":ds,"K":k,"method":arm,"dev_cal_net_gain":delta})
    save("heldout_quality.csv",rows)
    decision={"decision":"RUN_FORMAL" if qualified else "NO_FORMAL","qualified":qualified,
              "public_test_read":False,"heldout_rows_replayed":15906}
    write(ROOT/"analysis/heldout_decision.json",decision)
    print(decision)


if __name__=="__main__":
    main()
