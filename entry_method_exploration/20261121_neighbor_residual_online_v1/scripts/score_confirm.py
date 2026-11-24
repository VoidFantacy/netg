"""Score the dense confirmation and verify its shared points against the first wave."""
import math
from pathlib import Path
from statistics import mean

from confirm import STUDY
from prepare import LS,ROOT,read,verify,write
from check_heldout import save
from score_formal import CONTROL,N,NAMES,RAW,gt,packet
from audit import language_neutral_array,load_truth


def score():
    phase=read(ROOT/"confirm_complete.json")
    assert phase=={"status":"PASS_E216_DENSE","points":59,"batches":118}
    for file in ("prepare_freeze.json","native_freeze.json","confirm_freeze.json"):
        verify(read(ROOT/file)["files"])
    allpoints,rounds=[],[]
    anchored=0
    cfg=read(ROOT/"gt_eval.json")
    for dataset,k,focus,ls in STUDY:
        truth=gt(cfg[dataset])
        g100,g1=load_truth(Path(cfg[dataset]["path"]),cfg[dataset]["format"])
        for ordinal,l in enumerate(ls):
            node=ROOT/"data"/dataset/"confirm"/f"K{k}_L{l}"
            arms=CONTROL+("CACHE",) if l==focus else CONTROL
            route=None
            for i,arm in enumerate(arms):
                box=node/arm
                sha,ids,bits=packet(box/"raw",k)
                if route is not None: assert bits[2:]==route
                route=bits[2:]
                if l in LS:
                    old=ROOT/"data"/dataset/"formal"/node.name/arm/"raw"
                    assert bits==tuple((old/name).read_bytes() for name in RAW)
                    anchored+=1
                walls=[]
                for rep in range(2):
                    row=read(box/f"round{rep}.json")
                    assert (row["method"],row["K"],row["L"],row["n"],row["rep"],row["cpu"],
                            row["threads"],row["sha256"])==(arm,k,l,N,rep,15,1,sha)
                    pos=(i-ordinal)%len(arms)
                    assert row["order"]==(pos+1 if rep==0 else 2*len(arms)-pos)
                    assert row["seconds"]>0 and math.isclose(row["qps"],N/row["seconds"],rel_tol=1e-13)
                    walls.append(row["seconds"])
                    rounds.append({"dataset":dataset,**row})
                if k==1:
                    h=int((ids[:,0]==truth[:,0]).sum())
                else:
                    h=sum(len(set(a).intersection(b)) for a,b in zip(ids,truth))
                actual=language_neutral_array(box/"raw/ids.i32","i")
                if k==1:
                    check=sum(a==b for a,b in zip(actual,g1))
                else:
                    check=sum(sum(x in g for x in actual[j*k:(j+1)*k]) for j,g in enumerate(g100))
                assert check==h
                speeds=[N/t for t in walls]
                allpoints.append({"dataset":dataset,"K":k,"L":l,"method":arm,"hits":h,
                    "recall_pct":h*100/(N*k),"qps":mean(speeds),"qps_min":min(speeds),"qps_max":max(speeds),
                    "qps0":speeds[0],"qps1":speeds[1],"sha256":sha})
    assert (len(allpoints),len(rounds),anchored)==(59,118,23)
    return allpoints,rounds,anchored


def main():
    points,rounds,anchored=score()
    save("dense_points.csv",points)
    save("dense_rounds.csv",rounds)
    outcomes=[]
    lines=["# E216 两个代表点的加密对照", "",
        "COCO K100 固定 CACHE L200，WebVid K1 固定 CACHE L192。"
        "每条对照加密 9 或 10 档 L，同期两遍完整计时。本阶段单独比较，查询沿用已曝光公共 3,072 条。","",
        "| 数据集 | K | CACHE | 最快达标控制 | 完整 QPS 变化 | 慢遍相对最快达标控制快遍 |",
        "| --- | ---: | --- | --- | ---: | ---: |"]
    for ds,k,_,_ in STUDY:
        p=[r for r in points if r["dataset"]==ds]
        new=next(r for r in p if r["method"]=="CACHE")
        good=[r for r in p if r["method"] in CONTROL and r["hits"]>=new["hits"]]
        assert good
        b=max(good,key=lambda r:r["qps"])
        d=100*(new["qps"]/b["qps"]-1)
        slow=100*(new["qps_min"]/max(r["qps_max"] for r in good)-1)
        fmt=lambda r:f"{r['method']} L{r['L']} / {r['recall_pct']:.4f}% / {r['qps']:,.1f} QPS"
        lines.append(f"| {NAMES[ds]} | {k} | {fmt(new)} | {fmt(b)} | {d:+.2f}% | {slow:+.2f}% |")
        outcomes.append({"dataset":ds,"K":k,"candidate":new,"fastest_control":b,"delta_pct":d,
                         "slow_new_vs_fastest_control_pct":slow})
    lines.extend(["","59 点、118 wall 和 23 个与首轮共有的实际返回包全部复核。"
        "对照 L 的加密程度限于本协议各自区间。两遍范围描述该轮计时波动。","",
        "[协议](confirmation.md) · [加密点 CSV](analysis/dense_points.csv) · [原始批次 CSV](analysis/dense_rounds.csv) · [原 160 点](report.md)"])
    write(ROOT/"analysis/dense_decision.json",{"outcomes":outcomes,"matched_QPS_points":59,
         "report":"confirmation_result.md","exact_primary_packets":anchored})
    with (ROOT/"confirmation_result.md").open("x") as f: f.write("\n".join(lines)+"\n")


if __name__=="__main__":
    main()
