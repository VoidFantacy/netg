"""Cross-check actual E211 packets, derive paired speeds and create four-dataset curves."""
import csv
import hashlib
import math
import struct
from pathlib import Path
from statistics import mean,median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager
import numpy as np

from run import ROOT,E210,DATASETS,MATRIX,N,LS,read,write,digest,verify

METHODS=("GT10","B32","SPAN4-GT10","SPAN4-B32")
NAMES=dict(zip(DATASETS,("COCO","Flickr30k","WebVid","Yandex")))
PALETTE=dict(zip(METHODS,("#718194","#263f65","#c0643f","#168174")))
MARKS=dict(zip(METHODS,("o","s","^","D")))
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


def prior_match(root, raw, rows, k):
    widths=(k,k,3,3)
    for p,buf,w in zip(RAW,raw,widths):
        length=rows*w*4
        assert (root/p).read_bytes()==buf[:length],(root,p)


def eval_all(complete):
    score_config=read(ROOT/"gt_eval.json")
    points,rounds=[],[]
    anchors210=0
    for ds in DATASETS:
        root=ROOT/"data"/ds
        test=gt(score_config[ds])
        truth={k:[set(x[:k]) for x in test] for k in LS}
        env=read(root/"environment.json")
        assert env["dataset"]==ds and (env["threads"],env["cpu"])==(1,15)
        assert env["span_bytes"]==0
        qual=read(root/"qualification.json")
        assert len(qual)==len(complete[ds]["points"])==56 and complete[ds]["formal_batches"]==112
        assert complete[ds]["scratch_pairs"]==896
        for k,l in MATRIX:
            node=root/f"K{k}_L{l}"
            runs=[p for p in complete[ds]["points"] if (p["K"],p["L"])==(k,l)]
            qs=[p for p in qual if (p["K"],p["L"])==(k,l)]
            assert [p["method"] for p in runs]==[p["method"] for p in qs]==list(METHODS)
            assert sorted(r["order"] for p in runs for r in p["rounds"])==list(range(1,9))
            qual_hash={p["method"]:p["sha256"] for p in qs}
            assert all(p["n"]==256 for p in qs)
            controls={}
            for p in runs:
                m=p["method"]
                ref=m.removeprefix("SPAN4-")
                assert p==read(node/m/"complete.json") and p["n"]==N and p["reference"]==ref
                assert qual_hash[m]==qual_hash[ref]
                hash_,ids,bits=packet(node/m/"raw",k)
                if m in ("GT10","B32"):
                    controls[m]=bits
                    if m=="B32":
                        assert controls["GT10"][2:]==bits[2:]
                else:
                    assert bits==controls[ref],(ds,k,l,m)
                prior_match(E210/"data"/ds/f"K{k}_L{l}"/m/"raw",bits,N,k)
                anchors210+=1
                durations=[]
                for rep,r in enumerate(p["rounds"]):
                    assert r==read(node/m/f"round{rep}.json")
                    assert (r["n"],r["cpu"],r["threads"],r["method"],r["K"],r["L"],r["rep"],r["sha256"])==(N,15,1,m,k,l,rep,hash_)
                    assert r["seconds"]>0 and math.isclose(N/r["seconds"],r["qps"],rel_tol=1e-13)
                    durations.append(r["seconds"])
                    rounds.append({"dataset":ds,**r})
                assert len(durations)==2
                hits=sum(len(t.intersection(a)) for t,a in zip(truth[k],ids))
                speeds=[N/x for x in durations]
                points.append({"dataset":ds,"K":k,"L":l,"method":m,"n":N,"hits":hits,
                    "recall_pct":100*hits/(N*k),"qps":mean(speeds),"qps0":speeds[0],"qps1":speeds[1],
                    "qps_min":min(speeds),"qps_max":max(speeds),"wall_us":1e6*mean(durations)/N,
                    "packet_sha256":hash_})
    assert (len(points),len(rounds),anchors210)==(224,448,224)
    return points,rounds


def paired(points):
    lookup={(p["dataset"],p["K"],p["L"],p["method"]):p for p in points}
    out=[]
    for p in points:
        ds,k,l,m=(p[f] for f in ("dataset","K","L","method"))
        if not m.startswith("SPAN4-"):
            continue
        base=lookup[ds,k,l,m.removeprefix("SPAN4-")]
        assert (p["hits"],p["packet_sha256"])==(base["hits"],base["packet_sha256"])
        delta=100*(p["qps"]/base["qps"]-1)
        lower=100*(p["qps_min"]/base["qps_max"]-1)
        upper=100*(p["qps_max"]/base["qps_min"]-1)
        out.append({"dataset":ds,"K":k,"L":l,"method":m,"baseline":base["method"],
            "recall_pct":p["recall_pct"],"baseline_qps":base["qps"],"span4_qps":p["qps"],
            "delta_qps_pct":delta,"round0_pct":100*(p["qps0"]/base["qps0"]-1),
            "round1_pct":100*(p["qps1"]/base["qps1"]-1),
            "slowest_new_vs_fastest_old_pct":lower,"fastest_new_vs_slowest_old_pct":upper,
            "passes":delta>=1 and lower>0,"both_runs_regress_gt_3pct":upper < -3,"wall_saved_us":base["wall_us"]-p["wall_us"]})
    assert len(out)==112
    return out


def summarize(pairs):
    rows=[]
    for ds in DATASETS:
        for k in LS:
            for m in ("SPAN4-GT10","SPAN4-B32"):
                rs=[r for r in pairs if (r["dataset"],r["K"],r["method"])==(ds,k,m)]
                assert len(rs)==7
                vals=[r["delta_qps_pct"] for r in rs]
                rows.append({"dataset":ds,"K":k,"method":m,"min_delta_pct":min(vals),"max_delta_pct":max(vals),
                    "median_delta_pct":median(vals),"positive_points":sum(r["passes"] for r in rs),
                    "all_points":len(rs),"repeat_stable_regressions":sum(r["both_runs_regress_gt_3pct"] for r in rs)})
    return rows


def recall_targets(points):
    rows=[]
    for ds in DATASETS:
        for k in LS:
            for threshold in (90,95,99):
                group={
                    m:max((p for p in points if (p["dataset"],p["K"],p["method"])==(ds,k,m)
                           and p["hits"]*100>=threshold*N*k),key=lambda p:p["qps"],default=None)
                    for m in METHODS}
                for m in METHODS:
                    p=group[m]
                    rows.append({"dataset":ds,"K":k,"target_recall_pct":threshold,"method":m,
                                 "L":p["L"] if p else "","recall_pct":p["recall_pct"] if p else "",
                                 "qps":p["qps"] if p else ""})
    return rows


def fonts():
    for weight in ("Regular","Bold"):
        font_manager.fontManager.addfont(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc")
    plt.rcParams.update({"font.family":"Noto Sans CJK JP","axes.spines.top":False,
        "axes.spines.right":False,"xtick.color":"#435269","ytick.color":"#435269","axes.labelcolor":"#25354c"})


def finish_fig(fig, handles, title, caption, filename):
    fig.suptitle(title,x=.082,y=.982,ha="left",fontsize=20,weight="bold",color="#17263a")
    fig.legend(handles=handles,loc="upper left",bbox_to_anchor=(.074,.92),ncol=4,frameon=False,fontsize=9.5)
    fig.text(.082,.027,caption,fontsize=9,color="#435269")
    fig.subplots_adjust(left=.082,right=.975,bottom=.113,top=.825,wspace=.245,hspace=.42)
    fig.savefig(ROOT/"analysis"/filename,dpi=180,facecolor="white")
    plt.close(fig)


def chart_recall(pts,k):
    fig,axis=plt.subplots(2,2,figsize=(11.8,7.8))
    handles=[]
    for ax,ds in zip(axis.flat,DATASETS):
        for method in METHODS:
            rs=[r for r in pts if (r["dataset"],r["K"],r["method"])==(ds,k,method)]
            xs=[r["recall_pct"] for r in rs]
            ys=[r["qps"] for r in rs]
            yerr=[[r["qps"]-r["qps_min"] for r in rs],[r["qps_max"]-r["qps"] for r in rs]]
            line=ax.errorbar(xs,ys,yerr=yerr,lw=1.75,color=PALETTE[method],label=method,
                             marker=MARKS[method],ms=4.8,capsize=2.1,
                             linestyle="--" if method.startswith("SPAN4") else "-")
            if ax is axis[0,0]:
                handles.append(line)
        ax.set_title(NAMES[ds],loc="left",fontsize=13,weight="bold",color="#182738")
        ax.set_xlabel(f"Recall@{k}（%）")
        ax.set_ylabel("完整 QPS")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(6))
        ax.ticklabel_format(style="plain",axis="x",useOffset=False)
        ax.grid(color="#dfe7ef",linewidth=.65)
        ax.set_axisbelow(True)
    simple=" / ".join(map(str,LS[k]))
    finish_fig(fig,handles,f"E211  GT10 正式入口对照 | Recall@{k}–QPS",
             f"每集3,072条，CPU15单线程，每点两遍。连线依次为 L {simple}。竖线为两遍范围。",
             f"recall_qps_k{k}.png")


def chart_delta(pairs):
    fig,axis=plt.subplots(2,2,figsize=(11.8,7.8),sharey=True)
    style=((1,"SPAN4-GT10","#94a491","o"),(1,"SPAN4-B32","#285b78","s"),
           (100,"SPAN4-GT10","#cd7e51","^"),(100,"SPAN4-B32","#11816f","D"))
    handles=[]
    y=[r["delta_qps_pct"] for r in pairs]
    for ax,ds in zip(axis.flat,DATASETS):
        for k,m,colour,mark in style:
            rs=[r for r in pairs if (r["dataset"],r["K"],r["method"])==(ds,k,m)]
            label=f"K{k}  {'GT10+B32' if m.endswith('B32') else '纯 GT10'}"
            line,=ax.plot([r["L"] for r in rs],[r["delta_qps_pct"] for r in rs],
                          label=label,color=colour,marker=mark,ms=5.2,lw=1.6,ls="--" if m.endswith("GT10") else "-")
            if ax is axis[0,0]:
                handles.append(line)
        ax.set_xscale("log",base=2)
        ax.set_xticks([64,100,160,200,320,400,640,800,960])
        ax.set_xticklabels([64,100,160,200,320,400,640,800,960],fontsize=8)
        ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.set_ylim(min(-1,min(y)-1),max(y)*1.16)
        ax.axhline(0,color="#99a8b5",linewidth=.8)
        ax.set_title(NAMES[ds],loc="left",fontsize=13,weight="bold",color="#182738")
        ax.set_xlabel("主搜索 L（对数刻度）")
        ax.set_ylabel("完整 QPS 变化（%）")
        ax.grid(axis="y",color="#dfe7ef",linewidth=.65)
        ax.set_axisbelow(True)
    finish_fig(fig,handles,"E211  正式入口 SPAN4 相对同 L 原内核的提速",
        "每条曲线对照同数据集、同 K、同 L、同补点后端的原内核。主搜索和补点后返回分别核对。",
        "speed_delta.png")


def main():
    stage=read(ROOT/"timing_complete.json")
    assert stage["status"]=="PASS_E211_TIMING_COMPLETE" and stage["datasets"]==list(DATASETS)
    verify(read(ROOT/"input_freeze.json")["files"])
    verify(read(ROOT/"bin/freeze.json")["files"])
    complete={d:read(ROOT/"data"/d/"complete.json") for d in DATASETS}
    assert all(p["status"]=="PASS_E211_NATIVE" and p["dataset"]==d and not p["public_GT_read"]
               for d,p in complete.items())
    # Ground truth is read only once all four timing receipts have passed.
    points,rounds=eval_all(complete)
    deltas=paired(points)
    groups=summarize(deltas)
    save(ROOT/"analysis/points.csv",points)
    save(ROOT/"analysis/rounds.csv",rounds)
    save(ROOT/"analysis/matched_deltas.csv",deltas)
    save(ROOT/"analysis/summary_by_dataset_k.csv",groups)
    save(ROOT/"analysis/recall_thresholds.csv",recall_targets(points))
    write(ROOT/"analysis/decision.json",{
        "passing_points":sum(r["passes"] for r in deltas),
        "paired_points":len(deltas),
        "matched_return_points":len(deltas),
        "all_points_faster":all(r["delta_qps_pct"]>0 for r in deltas),
        "passes_production_performance_gate":all(g["positive_points"]>=5 and
            g["repeat_stable_regressions"]==0 for g in groups),
        "not_passing":[r for r in deltas if not r["passes"]],
        "groups":groups,
    })
    fonts()
    for k in LS:
        chart_recall(points,k)
    chart_delta(deltas)
    write(ROOT/"reviews/output_audit.json",{"status":"PASS_E211_OUTPUT_AUDIT","packets":224,
        "rounds":448,"qualification_packets":224,"optimized_bit_equivalent_packets":112,
        "paired_candidate_pool_and_visited_queries":3584,"independent_merge_queries":sum(x["independent_merge_queries"] for x in complete.values()),
        "anchored_E210":224,"GT_opened_after_timing":True})


if __name__=="__main__":
    main()
