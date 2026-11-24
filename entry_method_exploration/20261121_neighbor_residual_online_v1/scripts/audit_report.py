"""Independently verify the formal counts and present complete online results."""
import csv
import math
from pathlib import Path

from prepare import DATASETS,LS,METHODS,ROOT,read,write
from score_formal import CONTROL,KS,N,NAMES,NEW,SAMPLES
from audit import language_neutral_array,load_truth


def load(name):
    with (ROOT/"analysis"/f"{name}.csv").open(newline="") as h:
        return list(csv.DictReader(h))


def near(a,b):
    assert math.isclose(float(a),b,rel_tol=1e-11,abs_tol=1e-11),(a,b)


def audit(pts,same,cross,front,threshold):
    assert (len(pts),len(same),len(cross),len(front),len(threshold))==(160,192,24,64,40)
    cfg=read(ROOT/"gt_eval.json")
    scored={}
    walls=0
    for d in DATASETS:
        g100,g1=load_truth(Path(cfg[d]["path"]),cfg[d]["format"])
        for k,l in SAMPLES:
            for m in METHODS:
                point=pts[d,k,l,m]
                folder=ROOT/"data"/d/"formal"/f"K{k}_L{l}"/m
                ids=language_neutral_array(folder/"raw/ids.i32","i")
                assert len(ids)==N*k
                if k==1:
                    hits=sum(a==b for a,b in zip(ids,g1))
                else:
                    query_hits=[sum(i in truth for i in ids[j*k:(j+1)*k]) for j,truth in enumerate(g100)]
                    hits=sum(query_hits)
                    assert int(point["low_recall"])==sum(n<10 for n in query_hits)
                assert hits==int(point["hits"])
                near(point["recall_pct"],hits*100/(N*k))
                times=[read(folder/f"round{rep}.json")["seconds"] for rep in range(2)]
                speeds=[N/t for t in times]
                near(point["qps"],sum(speeds)/2)
                near(point["qps0"],speeds[0])
                near(point["qps1"],speeds[1])
                scored[d,k,l,m]=(hits,sum(speeds)/2,min(speeds),max(speeds),sum(times)*1e6/(2*N))
                walls+=2
    for row in (*same,*cross):
        ds,k,l,m=row["dataset"],int(row["K"]),int(row["L"]),row["method"]
        a=scored[ds,k,l,m]
        b=scored[ds,k,int(row["control_L"]),row["control"]]
        assert int(row["hit_gain"])==a[0]-b[0]
        near(row["recall_delta_pp"],(a[0]-b[0])*100/(N*k))
        near(row["qps_delta_pct"],100*(a[1]/b[1]-1))
        near(row["slow_new_vs_fast_old_pct"],100*(a[2]/b[3]-1))
        near(row["extra_us_per_query"],a[4]-b[4])
    for row in front:
        ds,k,l,m=row["dataset"],int(row["K"]),int(row["L"]),row["method"]
        a=scored[ds,k,l,m]
        eligible=[scored[ds,k,old_l,old] for old_l in LS for old in CONTROL
                  if scored[ds,k,old_l,old][0]>=a[0]]
        covered=any(b[1]>=a[1] and (b[0]>a[0] or b[1]>a[1]) for b in eligible)
        assert (row["covered_by_control"]=="True")==covered
        assert (row["higher_recall_than_all_control_points"]=="True")== (not eligible)
        assert (row["slower_repeat_above_all_eligible_controls"]=="True")==bool(
                    eligible and a[2]>max(b[3] for b in eligible))
        if eligible:
            near(row["best_control_qps"],max(b[1] for b in eligible))
    for row in threshold:
        ds,k,m=row["dataset"],int(row["K"]),row["method"]
        ref=scored[ds,k,192,row["target_method"]][0]
        eligible=[(scored[ds,k,l,m][1],scored[ds,k,l,m][0],-l) for l in LS
                  if scored[ds,k,l,m][0]>=ref]
        if eligible:
            q,h,negative_l=max(eligible)
            assert row["L"]==str(-negative_l)
            near(row["recall_pct"],100*h/(N*k))
            near(row["qps"],q)
        else:
            assert not row["L"] and not row["qps"]
    return {"status":"PASS_E216_STDLIB_AUDIT","recall_points":len(scored),"walls":walls,
            "same_l_rows":len(same),"cross_l_rows":len(cross),"frontier_rows":len(front),
            "threshold_rows":len(threshold)}


def stats(front,heldout):
    recap={}
    for ds in DATASETS:
        recap[ds]={}
        for k in KS:
            recap[ds][k]={}
            for m in NEW:
                rows=[r for r in front if (r["dataset"],int(r["K"]),r["method"])==(ds,k,m)]
                recap[ds][k][m]={"covered":sum(r["covered_by_control"]=="True" for r in rows),
                    "robust_at_same_or_higher_recall":sum(r["slower_repeat_above_all_eligible_controls"]=="True" for r in rows),
                    "extends_recall":sum(r["higher_recall_than_all_control_points"]=="True" for r in rows)}
    resources={}
    for ds in DATASETS:
        m=ROOT/"models"/ds
        files=lambda names:sum((m/n).stat().st_size for n in names)
        common=files(("axes.f32","unit.f32","fit.hnsw"))
        held=read(m/"prepare.json")
        build=read(m/"graph_build.json")
        resources[ds]={"same_data":{"fit_queries":held["fit_queries"],"build_preparation_seconds":held["prep_wall_seconds"],
                                   "hnsw_build_seconds":build["wall_seconds"]},
            "VOTE_bytes":common+files(("omissions.ids.i32","omissions.offsets.u64")),
            "CACHE_bytes":common+files(("cache.ids.i32","cache.offsets.u64"))}
    return {"frontier_by_cell":recap,"fitted_payload":resources,"qualification_units":len(heldout["qualified"])}


STYLE={"GT10":("#576c84","o"),"B32":("#157465","D"),"B32-fit":("#85968f","x"),
       "VOTE":("#b34d2e","^"),"CACHE":("#795399","s")}


def draw(points,k):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt,font_manager
    from matplotlib.ticker import MaxNLocator
    for weight in ("Regular","Bold"):
        font_manager.fontManager.addfont(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{weight}.ttc")
    plt.rcParams.update({"font.family":"Noto Sans CJK JP","axes.spines.top":False,"axes.spines.right":False})
    fig,axes=plt.subplots(1,2,figsize=(13,5.9))
    for ax,d in zip(axes,DATASETS):
        for m in METHODS:
            rows=[points[d,k,l,m] for l in LS]
            x=[float(r["recall_pct"]) for r in rows]
            y=[float(r["qps"]) for r in rows]
            a=[q-float(r["qps_min"]) for q,r in zip(y,rows)]
            b=[float(r["qps_max"])-q for q,r in zip(y,rows)]
            color,marker=STYLE[m]
            ax.errorbar(x,y,yerr=[a,b],label=m,color=color,marker=marker,
                        linestyle="--" if m=="B32-fit" else "-",linewidth=1.6,capsize=2.2,markersize=4.9)
        ax.set_title(NAMES[d],loc="left",fontsize=13,weight="bold")
        ax.set_xlabel(f"Recall@{k}（%）")
        ax.set_ylabel("端到端 QPS")
        ax.xaxis.set_major_locator(MaxNLocator(6))
        ax.ticklabel_format(style="plain",axis="x",useOffset=False)
        ax.set_axisbelow(True)
        ax.grid(color="#dfe7ef",linewidth=.65)
    fig.suptitle(f"在线相近查询补点｜Recall@{k}–QPS",x=.08,y=.985,ha="left",fontsize=20,weight="bold")
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper left",bbox_to_anchor=(.069,.90),ncol=5,frameon=False)
    fig.text(.08,.019,"每集 3,072 条，CPU15 单线程，每点两遍完整计时。竖线表示两遍 QPS 范围。",
             fontsize=9,color="#526981")
    fig.subplots_adjust(left=.08,right=.977,top=.77,bottom=.155,wspace=.29)
    fig.savefig(ROOT/"analysis"/f"recall_qps_k{k}.png",dpi=150,facecolor="white")
    plt.close(fig)


def format_point(p,include_l=False):
    if not p["qps"]: return "—"
    text=f"{float(p['recall_pct']):.4f}% / {float(p['qps']):,.1f}"
    return f"L{p['L']} / "+text if include_l else text


def report(points,threshold,held,summary):
    text=["# E216 COCO 和 WebVid 在线相近查询补点", "",
        "复用原 raw-IP、GT10 和 E211 SPAN4。VOTE 在线取 32 个低维邻居后重排取 16 个，对实际遗漏投票。"
        "CACHE 在线低维取 4 个后重排取 1 个，再读取离线汇总的候选表。"
        "每查询最多替换原 fit-only B32 的 16 个尾部候选，同 L 实际精算预算相同。"
        "五臂包含纯 GT10、完整 16K B32、fit-only B32 和两条在线候选。", "",
        "资格回放中，VOTE 和 CACHE 均在两个数据集、两种 K 的 dev/cal 提高了同 L 净命中。"
        "正式每集 3,072 条公共查询，真实 K1/K100，8 档 L，160 点、320 批，CPU15 实际单线程，两遍 N/wall 平均。"
        "在线近邻投影、HNSW、重排、候选查找与投票和精算合并全部记入完整 wall。", "",
        "## L184 与 L192 的实际对照", "",
        "每格为 Recall / QPS。新方法都在 L184，两个 B32 对照都在 L192。", "",
        "| 数据集 | K | 完整 B32 L192 | B32-fit L192 | VOTE L184 | CACHE L184 |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for ds in DATASETS:
        for k in KS:
            cells=" | ".join(format_point(points[ds,k,l,m]) for l,m in (
                         (192,"B32"),(192,"B32-fit"),(184,"VOTE"),(184,"CACHE")))
            text.append(f"| {NAMES[ds]} | {k} | {cells} |")
    text.extend(["","## 以完整 B32 L192 为召回目标","",
        "每格为最快实际达标 L / Recall / QPS，破折号表示当前网格无达标配置。", "",
        "| 数据集 | K | GT10 | 完整 B32 | B32-fit | VOTE | CACHE |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"])
    index={(r["dataset"],int(r["K"]),r["target_method"],r["method"]):r for r in threshold}
    for ds in DATASETS:
        for k in KS:
            cells=" | ".join(format_point(index[ds,k,"B32",m],True) for m in METHODS)
            text.append(f"| {NAMES[ds]} | {k} | {cells} |")
    text.extend(["", "## 逐点离散前沿", "",
        "用纯 GT10、完整 B32 和 fit-only B32 的全部同期实际点共同作对照。"
        "下表每臂分母为 8，召回与 QPS 都达到且一项更高计为覆盖。"
        "慢遍领先是指新方法慢遍快于所有已达其召回的对照快遍。", "",
        "| 数据集 | K | 方法 | 被覆盖 | 慢遍领先 | 高于所有对照召回 |",
        "| --- | ---: | --- | ---: | ---: | ---: |"])
    for ds in DATASETS:
        for k in KS:
            for m in NEW:
                cell=summary["frontier_by_cell"][ds][k][m]
                text.append(f"| {NAMES[ds]} | {k} | {m} | {cell['covered']}/8 | "
                            f"{cell['robust_at_same_or_higher_recall']}/8 | {cell['extends_recall']}/8 |")
    text.extend(["","![Recall@1 曲线](analysis/recall_qps_k1.png)","","![Recall@100 曲线](analysis/recall_qps_k100.png)","",
        "## 补点重放和模型开销", "",
        "重放不走主图，额外时间为相对同条件 B32-fit 的微秒/查询。文件字节量按各臂所需投影、单位查询、"
        "HNSW 和各自的遗漏或预编表计算；运行器同时加载两套表，字节量不作实际峰值 RSS。", "",
        "| 数据集 | K | VOTE 额外 μs | CACHE 额外 μs | VOTE 模型 MiB | CACHE 模型 MiB |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"])
    h={(r["dataset"],int(r["K"]),r["role"],r["method"]):r for r in held}
    for ds in DATASETS:
        resource=summary["fitted_payload"][ds]
        for k in KS:
            a,b=(float(h[ds,k,"cal",m]["extra_vs_fit_b32_us"]) for m in NEW)
            text.append(f"| {NAMES[ds]} | {k} | {a:.2f} | {b:.2f} | "
                        f"{resource['VOTE_bytes']/2**20:.2f} | {resource['CACHE_bytes']/2**20:.2f} |")
    text.extend(["","正式结果来自实际返回，32 个纯 GT10 或完整 B32 包与 E214 对齐。"
        "固定样本核对四路与独立标量排序及实际候选数。两次计时范围用于描述运行波动。"
        "公共测试窗口已用于历史研究，跨 L 门槛由离散实测点判断。", "",
        "[协议](protocol.md) · [资格](analysis/heldout_quality.csv) · [全部实际点](analysis/points.csv) · "
        "[同 L 差](analysis/same_l.csv) · [L184 对 L192](analysis/cross_l.csv) · [门槛](analysis/recall_thresholds.csv) · "
        "[前沿](analysis/control_frontier.csv) · [独立复算](reviews/independent_audit.json) · [封存](seal.json)"])
    return "\n".join(text)+"\n"


def main():
    assert read(ROOT/"reviews/packet_audit.json")["status"]=="PASS_E216_PACKETS"
    p={(r["dataset"],int(r["K"]),int(r["L"]),r["method"]):r for r in load("points")}
    same,cross,front,threshold,held=map(load,("same_l","cross_l","control_frontier","recall_thresholds","heldout_quality"))
    write(ROOT/"reviews/independent_audit.json",audit(p,same,cross,front,threshold))
    summary=stats(front,read(ROOT/"analysis/heldout_decision.json"))
    write(ROOT/"analysis/conclusions.json",summary)
    for k in KS: draw(p,k)
    with (ROOT/"report.md").open("x") as f:
        f.write(report(p,threshold,held,summary))


if __name__=="__main__":
    main()
