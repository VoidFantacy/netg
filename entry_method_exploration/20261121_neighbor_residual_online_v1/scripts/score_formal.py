"""Score actual measured E216 packets after timing and derive the discrete comparisons."""
import math
from statistics import mean
import sys

from prepare import DATASETS,E212,E214,LS,METHODS,PUBLIC_N,ROOT,read,verify,write
from check_heldout import save
import numpy as np

sys.path.append(str(E212/"scripts"))
from analyze import RAW,gt,packet

N=PUBLIC_N
KS=(1,100)
SAMPLES=tuple((k,l) for k in KS for l in LS)
CONTROL=METHODS[:3]
NEW=METHODS[3:]
NAMES=dict(zip(DATASETS,("COCO","WebVid")))


def score():
    phase=read(ROOT/"formal_complete.json")
    assert phase=={"status":"PASS_E216_FORMAL","datasets":list(DATASETS),"points":160,
                   "batches":320,"query_calls":983040}
    for filename in ("prepare_freeze.json","native_freeze.json"):
        verify(read(ROOT/filename)["files"])
    cfg=read(ROOT/"gt_eval.json")
    points,rounds,qual=[],[],[]
    anchored=0
    for ds in DATASETS:
        truth=gt(cfg[ds])
        assert truth.shape==(N,100) and np.all(np.diff(np.sort(truth,axis=1),axis=1)>0)
        root=ROOT/"data"/ds/"formal"
        complete=read(root/"complete.json")
        assert complete["status"]=="PASS_E216_FORMAL" and complete["points"]==80 and complete["batches"]==160
        assert not complete["public_GT_read"]
        max_id=complete["binding"]["N"]
        assert np.min(truth)>=0 and np.max(truth)<max_id
        for order,(k,l) in enumerate(SAMPLES):
            node=root/f"K{k}_L{l}"
            orient={}
            if l==184:
                evidence=read(node/"qualification.json")
                assert set(evidence)==set(METHODS[2:])
                ref=evidence["B32-fit"]["scores"]
                for m,v in evidence.items():
                    vscore=v["scores"]
                    new=v["new_ids"]
                    assert vscore==ref and len(ref)==len(new)==256 and max(ref)<=96 and max(new)<=16
                    qual.append({"dataset":ds,"K":k,"L":l,"method":m,"queries":len(ref),
                                 "mean_scores":mean(ref),"mean_new_ids":mean(new)})
            for i,m in enumerate(METHODS):
                mpath=node/m
                sha,ids,bits=packet(mpath/"raw",k)
                orient[m]=bits[2:]
                assert np.min(ids)>=0 and np.max(ids)<max_id
                if m in ("GT10","B32") and l in (160,200,320,400):
                    prev="B32-batch4" if m=="B32" else m
                    old=E214/"data"/ds/node.name/prev/"raw"
                    assert bits==tuple((old/name).read_bytes() for name in RAW),(ds,k,l,m)
                    anchored+=1
                walls=[]
                for r in range(2):
                    row=read(mpath/f"round{r}.json")
                    assert (row["method"],row["K"],row["L"],row["n"],row["rep"],
                            row["threads"],row["cpu"],row["sha256"])==(m,k,l,N,r,1,15,sha)
                    pos=(i-order)%len(METHODS)
                    assert row["order"]==(pos+1 if r==0 else 2*len(METHODS)-pos)
                    assert row["seconds"]>0 and math.isclose(row["qps"],N/row["seconds"],rel_tol=1e-13)
                    walls.append(row["seconds"])
                    rounds.append({"dataset":ds,**row})
                if k==1:
                    h=(ids==truth[:,:1]).ravel()
                else:
                    h=(ids[:,:,None]==truth[:,None,:]).any(axis=2).sum(axis=1,dtype=np.uint8)
                hits=int(h.sum())
                speeds=[N/w for w in walls]
                points.append({"dataset":ds,"K":k,"L":l,"method":m,"n":N,"hits":hits,
                               "recall_pct":100*hits/(N*k),"qps":mean(speeds),"qps0":speeds[0],"qps1":speeds[1],
                               "qps_min":min(speeds),"qps_max":max(speeds),"wall_us":mean(walls)*1e6/N,
                               "low_recall":int((h<10).sum()) if k==100 else "","packet_sha256":sha})
            assert all(v==orient["GT10"] for v in orient.values()),"same native GT10 route"
    assert (len(points),len(rounds),len(qual),anchored)==(160,320,12,32)
    return points,rounds,qual,anchored


def delta(a,b):
    assert a["dataset"]==b["dataset"] and a["K"]==b["K"]
    return {"dataset":a["dataset"],"K":a["K"],"method":a["method"],"L":a["L"],
            "control":b["method"],"control_L":b["L"],"recall_pct":a["recall_pct"],
            "control_recall_pct":b["recall_pct"],"hit_gain":a["hits"]-b["hits"],
            "recall_delta_pp":100*(a["hits"]-b["hits"])/(N*a["K"]),
            "qps":a["qps"],"control_qps":b["qps"],"qps_delta_pct":100*(a["qps"]/b["qps"]-1),
            "slow_new_vs_fast_old_pct":100*(a["qps_min"]/b["qps_max"]-1),
            "extra_us_per_query":a["wall_us"]-b["wall_us"]}


def comparisons(points):
    p={(r["dataset"],r["K"],r["L"],r["method"]):r for r in points}
    same_l,cross_l,frontier,threshold=[],[],[],[]
    for ds in DATASETS:
        for k in KS:
            current=[a for a in points if (a["dataset"],a["K"])==(ds,k)]
            controls=[a for a in current if a["method"] in CONTROL]
            for l in LS:
                for n in NEW:
                    for c in CONTROL:
                        same_l.append(delta(p[ds,k,l,n],p[ds,k,l,c]))
            for n in NEW:
                for c in CONTROL:
                    cross_l.append(delta(p[ds,k,184,n],p[ds,k,192,c]))
            for a in (t for t in current if t["method"] in NEW):
                eligible=[b for b in controls if b["hits"]>=a["hits"]]
                b=max(eligible,key=lambda r:(r["qps"],r["hits"],-r["L"]),default=None)
                row={key:a[key] for key in ("dataset","K","L","method","recall_pct","qps")}
                row["covered_by_control"]=any(c["hits"]>=a["hits"] and c["qps"]>=a["qps"] and
                    (c["hits"]>a["hits"] or c["qps"]>a["qps"]) for c in eligible)
                row["slower_repeat_above_all_eligible_controls"]=bool(b and a["qps_min"]>max(c["qps_max"] for c in eligible))
                row["higher_recall_than_all_control_points"]=not eligible
                row.update({key:value for key,value in (("best_control",b["method"] if b else ""),
                    ("best_control_L",b["L"] if b else ""),("best_control_qps",b["qps"] if b else ""),
                    ("qps_delta_pct",100*(a["qps"]/b["qps"]-1) if b else ""))})
                frontier.append(row)
            for name in ("B32","B32-fit"):
                target=p[ds,k,192,name]
                for m in METHODS:
                    q=max((a for a in current if a["method"]==m and a["hits"]>=target["hits"]),
                          key=lambda a:(a["qps"],a["hits"],-a["L"]),default=None)
                    threshold.append({"dataset":ds,"K":k,"target_method":name,"target_L":192,
                        "target_recall":target["recall_pct"],"method":m,
                        **{key:q[key] if q else "" for key in ("L","recall_pct","qps","qps_min","qps_max")}})
    return same_l,cross_l,frontier,threshold


def main():
    points,rounds,qual,anchors=score()
    same_l,cross_l,coverage,threshold=comparisons(points)
    tables={"points":points,"rounds":rounds,"qualification":qual,"same_l":same_l,
            "cross_l":cross_l,"control_frontier":coverage,"recall_thresholds":threshold}
    for name,rows in tables.items():
        save(name+".csv",rows)
    write(ROOT/"reviews/packet_audit.json",{"status":"PASS_E216_PACKETS","recall_points":len(points),
          "formal_batches":len(rounds),"exact_E214_anchor_packets":anchors,
          "scalar_qualification_queries":sum(r["queries"] for r in qual),"GT_read_after_timing":True})


if __name__=="__main__":
    main()
