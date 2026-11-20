"""Audit E212 actual packets and compare measured Recall-QPS points and tails."""
import csv
import gzip
import hashlib
import math
import struct
from statistics import mean,median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager
import numpy as np

from run import ROOT,E211,DATASETS,MATRIX,N,LS,read,write,digest,verify

METHODS=("NSG","GT10-new","GT10-new-B32","GT10-old-B32")
DISPLAY=dict(zip(METHODS,("NSG（SPAN4）","新 GT10","新 GT10 + B32","旧 GT10 + B32")))
E211_METHOD={"GT10-new":"SPAN4-GT10","GT10-new-B32":"SPAN4-B32","GT10-old-B32":"B32"}
E200=ROOT.parent/"20261110_multimodal_four_method_retest_v1"
COMPARISONS=(("GT10-new","NSG"),("GT10-new-B32","GT10-new"),("GT10-new-B32","GT10-old-B32"),
             ("GT10-new-B32","NSG"))
NAMES=dict(zip(DATASETS,("COCO","Flickr30k","WebVid","Yandex")))
PALETTE=dict(zip(METHODS,("#66788a","#c15d3e","#168174","#3b5486")))
MARKS=dict(zip(METHODS,("o","^","D","s")))
RAW=("ids.i32","distances.f32","entry_ids.i32","profile_distances.f32")


def save(path, rows):
    with path.open("x",newline="") as f:
        writer=csv.DictWriter(f,list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def gt(c):
    assert digest(c["path"])==c["expected_sha256"]
    assert c["k"]==100 and c["n"]>=N and c.get("row_start",0)==0
    if c["format"]=="ivecs":
        val=np.fromfile(c["path"],"<i4").reshape(-1,101)
        assert np.all(val[:,0]==100)
        return val[:N,1:]
    assert c["format"]=="raw_i64"
    return np.fromfile(c["path"],"<i8").reshape(-1,100)[:N]


def packet(path,k):
    raw=tuple((path/f).read_bytes() for f in RAW)
    sha=hashlib.sha256(struct.pack("<QQ",N,k))
    for buf,width in zip(raw,(k,k,3,3)):
        assert len(buf)==N*width*4
        sha.update(buf)
    sha.update(bytes(N*16))
    ids=np.frombuffer(raw[0],"<i4").reshape(N,k)
    distances=np.frombuffer(raw[1],"<f4").reshape(N,k)
    assert np.isfinite(distances).all() and np.all(np.diff(distances,axis=1)>=0)
    assert np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
    return sha.hexdigest(),ids,raw


def prior_nsg(ds,k,l,bits,config):
    ref=E200/f"results/{ds}/k{k}_run/k{k}/NSG_L{l}/raw"
    if not ref.exists():
        assert k==1 and l==100
        return False
    old=read(E200/f"configs/{ds}.formal_k{k}.json")
    assert old["index"]==config["index"]
    assert all(old["queries"][name]==config["queries"][name] for name in ("path","d","format"))
    assert old["queries"].get("row_start",0)==config["queries"].get("row_start",0)
    for name,buf in zip(RAW,bits):
        with gzip.open(ref/(name+".gz"),"rb") as f:
            assert f.read(len(buf))==buf,(ds,k,l,name)
    return True


def audit_and_score():
    stage=read(ROOT/"timing_complete.json")
    assert stage=={"status":"PASS_E212_TIMING_COMPLETE","datasets":list(DATASETS),
                   "points":224,"batches":448,"query_calls":1376256}
    verify(read(ROOT/"input_freeze.json")["files"])
    verify(read(ROOT/"bin/freeze.json")["files"])
    score_config=read(ROOT/"gt_eval.json")
    points,rounds=[],[]
    hits_by_query={}
    anchored211=anchored200=oracle_queries=nsg_qualification=0
    for ds in DATASETS:
        root=ROOT/"data"/ds
        complete=read(root/"complete.json")
        config=read(ROOT/f"configs/{ds}.json")
        assert complete["status"]=="PASS_E212_NATIVE" and complete["dataset"]==ds
        assert not complete["public_GT_read"] and complete["formal_batches"]==112
        oracle_queries+=complete["independent_merge_queries"]
        nsg_qualification+=complete["nsg_scalar_qualification"]
        env=read(root/"environment.json")
        assert env["dataset"]==ds and (env["threads"],env["cpu"])==(1,15)
        assert env["nsg_backend"]=="SPAN4"
        test=gt(score_config[ds])
        assert test.shape==(N,100)
        assert np.min(test)>=0 and np.max(test)<env["binding"]["N"]
        assert (np.diff(np.sort(test,axis=1),axis=1)>0).all()
        truth={k:[set(x[:k]) for x in test] for k in LS}
        all_qual=read(root/"qualification.json")
        assert len(all_qual)==len(complete["points"])==56
        for k,l in MATRIX:
            key=f"K{k}_L{l}"
            node=root/key
            runs=[p for p in complete["points"] if (p["K"],p["L"])==(k,l)]
            qual=[p for p in all_qual if (p["K"],p["L"])==(k,l)]
            assert [p["method"] for p in runs]==[p["method"] for p in qual]==list(METHODS)
            assert all(p["n"]==256 for p in qual) and qual[2]["sha256"]==qual[3]["sha256"]
            assert sorted(r["order"] for p in runs for r in p["rounds"])==list(range(1,9))
            state_bits={}
            for p in runs:
                m=p["method"]
                assert p==read(node/m/"complete.json") and p["n"]==N
                assert p["backend"]==("scalar" if m=="GT10-old-B32" else "SPAN4")
                sha,ids,bits=packet(node/m/"raw",k)
                assert np.min(ids)>=0 and np.max(ids)<env["binding"]["N"]
                state_bits[m]=bits
                if m=="NSG":
                    routed=np.frombuffer(bits[2],"<i4").reshape(N,3)
                    assert (routed[:,0]==env["nsg_fixed_entry"]).all() and (routed[:,1:]==-1).all()
                    anchored200+=prior_nsg(ds,k,l,bits,config)
                else:
                    old=E211/f"data/{ds}/{key}/{E211_METHOD[m]}/raw"
                    assert bits==tuple((old/name).read_bytes() for name in RAW),(ds,k,l,m)
                    anchored211+=1
                walls=[]
                for rep,r in enumerate(p["rounds"]):
                    assert r==read(node/m/f"round{rep}.json")
                    assert (r["n"],r["cpu"],r["threads"],r["method"],r["K"],r["L"],r["rep"],r["sha256"])==(N,15,1,m,k,l,rep,sha)
                    assert r["seconds"]>0 and math.isclose(N/r["seconds"],r["qps"],rel_tol=1e-13)
                    walls.append(r["seconds"])
                    rounds.append({"dataset":ds,**r})
                assert len(walls)==2
                per_query=np.array([len(t.intersection(a)) for t,a in zip(truth[k],ids)],dtype=np.int16)
                hits_by_query[ds,k,l,m]=per_query
                hits=int(per_query.sum())
                speeds=[N/w for w in walls]
                points.append({"dataset":ds,"K":k,"L":l,"method":m,"backend":p["backend"],"n":N,
                    "hits":hits,"recall_pct":100*hits/(N*k),"qps":mean(speeds),
                    "qps0":speeds[0],"qps1":speeds[1],"qps_min":min(speeds),"qps_max":max(speeds),
                    "wall_us":mean(walls)*1e6/N,"low_recall":int((per_query<10).sum()) if k==100 else "",
                    "packet_sha256":sha})
            assert state_bits["GT10-new-B32"]==state_bits["GT10-old-B32"]
            assert state_bits["GT10-new-B32"][2:]==state_bits["GT10-new"][2:]
    assert (len(points),len(rounds),anchored211,anchored200,oracle_queries,nsg_qualification)==(224,448,168,52,172032,14336)
    audit={"status":"PASS_E212_PACKETS","points":224,"batches":448,"gt_after_timing":True,
           "bit_equivalent_new_and_old_B32":56,"exact_E211_packets":anchored211,
           "exact_E200_nsg_prefixes":anchored200,"native_B32_oracle_rows":oracle_queries,
           "nsg_new_vs_scalar_qualification_rows":nsg_qualification}
    return points,rounds,hits_by_query,audit


def same_l(points,hits):
    lookup={(p["dataset"],p["K"],p["L"],p["method"]):p for p in points}
    rows=[]
    for ds in DATASETS:
        for k,l in MATRIX:
            for method,baseline in COMPARISONS:
                old=lookup[ds,k,l,baseline]
                new=lookup[ds,k,l,method]
                a,b=hits[ds,k,l,baseline],hits[ds,k,l,method]
                rows.append({"dataset":ds,"K":k,"L":l,"baseline":baseline,"method":method,
                    "baseline_recall_pct":old["recall_pct"],"recall_pct":new["recall_pct"],
                    "recall_delta_pp":100*(new["hits"]-old["hits"])/(N*k),
                    "baseline_qps":old["qps"],"qps":new["qps"],
                    "qps_delta_pct":100*(new["qps"]/old["qps"]-1),
                    "slow_new_vs_fast_old_pct":100*(new["qps_min"]/old["qps_max"]-1),
                    "fast_new_vs_slow_old_pct":100*(new["qps_max"]/old["qps_min"]-1),
                    "saved_us_per_query":old["wall_us"]-new["wall_us"],
                    "better_queries":int((b>a).sum()),"worse_queries":int((b<a).sum()),
                    "equal_queries":int((b==a).sum()),
                    "low_before":int((a<10).sum()) if k==100 else "",
                    "low_after":int((b<10).sum()) if k==100 else "",
                    "escaped_low":int(((a<10)&(b>=10)).sum()) if k==100 else "",
                    "entered_low":int(((a>=10)&(b<10)).sum()) if k==100 else ""})
    assert len(rows)==224
    return rows


def threshold_rows(points):
    rows=[]
    for ds in DATASETS:
        for k in LS:
            targets=(70,80,85,90,95,99) if NAMES[ds]=="WebVid" and k==100 else (90,95,99)
            applicable=[p for p in points if (p["dataset"],p["K"])==(ds,k)]
            for threshold in targets:
                matched={m:max((p for p in applicable if p["method"]==m and
                                p["hits"]*100>=threshold*N*k),
                               key=lambda p:(p["qps"],p["hits"],-p["L"]),default=None) for m in METHODS}
                achieved=[p["qps"] for p in matched.values() if p]
                fastest=max(achieved,default=0)
                for m,p in matched.items():
                    rows.append({"dataset":ds,"K":k,"target_pct":threshold,"method":m,
                                 "L":p["L"] if p else "",
                                 "recall_pct":p["recall_pct"] if p else "",
                                 "qps":p["qps"] if p else "",
                                 "qps_min":p["qps_min"] if p else "",
                                 "qps_max":p["qps_max"] if p else "",
                                 "fastest_at_target":bool(p and p["qps"]==fastest)})
    return rows


def frontier_rows(points):
    def dominates(a,b):
        return a["hits"]>=b["hits"] and a["qps"]>=b["qps"] and (
            a["hits"]>b["hits"] or a["qps"]>b["qps"])
    rows=[]
    for ds in DATASETS:
        for k in LS:
            pool=[p for p in points if (p["dataset"],p["K"])==(ds,k)]
            for p in pool:
                covering=[q for q in pool if dominates(q,p)]
                line={m:sum(q["method"]==m for q in covering) for m in METHODS}
                rows.append({"dataset":ds,"K":k,"L":p["L"],"method":p["method"],
                             "recall_pct":p["recall_pct"],"qps":p["qps"],"on_frontier":not covering,
                             **{f"covering_{m}":cnt for m,cnt in line.items()}})
    return rows


def fonts():
    for weight in ("Regular","Bold"):
        font_manager.fontManager.addfont(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc")
    plt.rcParams.update({"font.family":"Noto Sans CJK JP","axes.spines.top":False,
        "axes.spines.right":False,"xtick.color":"#435269","ytick.color":"#435269","axes.labelcolor":"#25354c"})


def chart_recall(points,k):
    fig,axes=plt.subplots(2,2,figsize=(12,7.9))
    handles=[]
    for ax,ds in zip(axes.flat,DATASETS):
        for m in METHODS:
            group=[p for p in points if (p["dataset"],p["K"],p["method"])==(ds,k,m)]
            xs=[p["recall_pct"] for p in group]
            ys=[p["qps"] for p in group]
            err=[[p["qps"]-p["qps_min"] for p in group],[p["qps_max"]-p["qps"] for p in group]]
            line=ax.errorbar(xs,ys,yerr=err,lw=1.8,color=PALETTE[m],label=DISPLAY[m],
                             marker=MARKS[m],ms=4.8,capsize=2.2,
                             linestyle="--" if m=="GT10-old-B32" else "-")
            if ax is axes[0,0]:
                handles.append(line)
        ax.set_title(NAMES[ds],loc="left",fontsize=13,weight="bold",color="#182738")
        ax.set_xlabel(f"Recall@{k}（%）")
        ax.set_ylabel("完整 QPS")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(6))
        ax.ticklabel_format(style="plain",axis="x",useOffset=False)
        ax.grid(color="#dfe7ef",linewidth=.65)
        ax.set_axisbelow(True)
    fig.suptitle(f"NSG 与三种 GT10 链路｜Recall@{k}–QPS",x=.08,y=.985,
                 ha="left",fontsize=20,weight="bold",color="#17263a")
    fig.legend(handles=handles,loc="upper left",bbox_to_anchor=(.075,.927),ncol=4,frameon=False)
    simple=" / ".join(map(str,LS[k]))
    fig.text(.08,.025,f"每集 3,072 条，CPU15 单线程，每点两遍。L 为 {simple}。竖线为两遍范围。",
             fontsize=9,color="#435269")
    fig.subplots_adjust(left=.08,right=.978,bottom=.110,top=.83,wspace=.25,hspace=.44)
    fig.savefig(ROOT/f"analysis/recall_qps_k{k}.png",dpi=180,facecolor="white")
    plt.close(fig)


def main():
    points,rounds,hits,audit=audit_and_score()
    pairs=same_l(points,hits)
    targets=threshold_rows(points)
    frontier=frontier_rows(points)
    save(ROOT/"analysis/points.csv",points)
    save(ROOT/"analysis/rounds.csv",rounds)
    save(ROOT/"analysis/same_l.csv",pairs)
    save(ROOT/"analysis/recall_thresholds.csv",targets)
    save(ROOT/"analysis/frontier.csv",frontier)
    np.savez_compressed(ROOT/"analysis/query_hits.npz",
                        **{f"{ds}__K{k}_L{l}__{m}":vals for (ds,k,l,m),vals in hits.items()})
    fonts()
    for k in LS:
        chart_recall(points,k)
    write(ROOT/"reviews/output_audit.json",audit)


if __name__=="__main__":
    main()
