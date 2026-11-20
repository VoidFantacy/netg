"""Report the four-way comparison and record workspace handoff."""
import csv
from pathlib import Path

from run import ROOT,REPO,DATASETS,N,read,write,digest,verify


METHODS=("NSG","GT10-new","GT10-new-B32","GT10-old-B32")
DISPLAY=dict(zip(METHODS,("NSG（SPAN4）","新 GT10","新 GT10+B32","旧 GT10+B32")))
NAMES=dict(zip(DATASETS,("COCO","Flickr30k","WebVid","Yandex first10M")))
REL=ROOT.relative_to(REPO).as_posix()
HISTORY="212_gt10_nsg_b32_four_way_v1.md"
E211="entry_method_exploration/20261120_span4_production_default_v1"
LINK=f"[E212 四集对比]({REL}/report.md)"


def csv_rows(filename):
    with (ROOT/f"analysis/{filename}.csv").open() as f:
        return list(csv.DictReader(f))


def span(rows,key,unit):
    values=[float(r[key]) for r in rows]
    return f"{min(values):+.2f}{unit} 至 {max(values):+.2f}{unit}"


def table(head,body):
    grid=[head,["---"]*len(head),*body]
    return "\n".join("| "+" | ".join(map(str,row))+" |" for row in grid)


def fmt(p):
    return f'{float(p["recall_pct"]):.3f}% / {float(p["qps"]):.1f}'


def fmt_target(p):
    if not p["qps"]:
        return "—"
    cell=f'L{p["L"]} / {fmt(p)}'
    return f"**{cell}**" if p["fastest_at_target"]=="True" else cell


def build_report():
    points=csv_rows("points")
    matched=csv_rows("same_l")
    targets=csv_rows("recall_thresholds")
    frontier=csv_rows("frontier")

    def select(rows,**kwargs):
        return [p for p in rows if all(p[k]==str(v) for k,v in kwargs.items())]

    def compare(method,baseline):
        return select(matched,method=method,baseline=baseline)

    def at_l(ds,k,l,m):
        p,=select(points,dataset=ds,K=k,L=l,method=m)
        return p

    kernel=compare("GT10-new-B32","GT10-old-B32")
    routes=compare("GT10-new","NSG")
    b32=compare("GT10-new-B32","GT10-new")
    assert len(kernel)==len(routes)==len(b32)==56
    release_speed=span(kernel,"qps_delta_pct","%")
    perf_faster=sum(float(p["qps_delta_pct"])>0 for p in kernel)
    both_races=sum(float(p["slow_new_vs_fast_old_pct"])>0 for p in kernel)
    qps_loss_b32=sum(float(p["qps_delta_pct"])<0 for p in b32)
    recall_gain_b32=sum(float(p["recall_delta_pp"])>0 for p in b32)
    recall_gain_routes=sum(float(p["recall_delta_pp"])>0 for p in routes)
    assert all(int(p["equal_queries"])==N for p in kernel)
    cross=[]
    panel=[]
    fixed=[]
    tail=[]
    feasible=[]
    front=[]
    for ds in DATASETS:
        for k in (1,100):
            here=select(routes,dataset=ds,K=k)
            add=select(b32,dataset=ds,K=k)
            reuse=select(kernel,dataset=ds,K=k)
            cross.append([NAMES[ds],k,span(here,"recall_delta_pp"," pp"),span(here,"qps_delta_pct","%"),
                        span(add,"recall_delta_pp"," pp"),span(add,"qps_delta_pct","%"),
                        span(reuse,"qps_delta_pct","%")])
            fixed.append([NAMES[ds],k,*(fmt(at_l(ds,k,200,m)) for m in METHODS)])
            front.append([NAMES[ds],k,*(len(select(frontier,dataset=ds,K=k,method=m,on_frontier=True))
                                            for m in METHODS)])
        nsg=at_l(ds,100,200,"NSG")
        gt=at_l(ds,100,200,"GT10-new")
        post=at_l(ds,100,200,"GT10-new-B32")
        p_route,=select(routes,dataset=ds,K=100,L=200)
        p_post,=select(b32,dataset=ds,K=100,L=200)
        tail.append([NAMES[ds],nsg["low_recall"],gt["low_recall"],post["low_recall"],
                    f'{p_route["escaped_low"]} / {p_route["entered_low"]}',
                    f'{p_post["escaped_low"]} / {p_post["entered_low"]}'])
        panel.append({"dataset":ds,"L":200,"K":100,"route_recall_gain_pp":float(p_route["recall_delta_pp"]),
                      "residual_recall_gain_pp":float(p_post["recall_delta_pp"]),
                      "low_recall":[int(nsg["low_recall"]),int(gt["low_recall"]),int(post["low_recall"])]})
        for k in (1,100):
            for threshold in sorted({int(r["target_pct"]) for r in select(targets,dataset=ds,K=k)}):
                methods=select(targets,dataset=ds,K=k,target_pct=threshold)
                assert [p["method"] for p in methods]==list(METHODS)
                feasible.append([NAMES[ds],k,f"{threshold}%",*(fmt_target(p) for p in methods)])

    threshold_advantages=[]
    threshold_losses=[]
    threshold_reach=[]
    for p in select(targets,method="GT10-new-B32"):
        base,=select(targets,dataset=p["dataset"],K=p["K"],target_pct=p["target_pct"],method="GT10-new")
        if p["qps"] and base["qps"]:
            delta=100*(float(p["qps"])/float(base["qps"])-1)
            record={"dataset":p["dataset"],"K":int(p["K"]),"target_pct":int(p["target_pct"]),
                    "pure":base,"B32":p,"delta_pct":delta}
            if delta>0:
                threshold_advantages.append(record)
            elif delta<0:
                threshold_losses.append(record)
        elif p["qps"]:
            threshold_reach.append({"dataset":p["dataset"],"K":int(p["K"]),"target_pct":int(p["target_pct"]),
                                    "B32":p})

    brief=[]
    for ds in DATASETS:
        ups=[r for r in threshold_advantages if r["dataset"]==ds]
        downs=[r for r in threshold_losses if r["dataset"]==ds]
        more=[r for r in threshold_reach if r["dataset"]==ds]
        line=f"- {NAMES[ds]}，在双方均能达到的门槛里，新 GT10+B32 快 {len(ups)} 项、慢 {len(downs)} 项。"
        if ups:
            best=max(ups,key=lambda p:p["delta_pct"])
            line+=f' 以 K{best["K"]}/{best["target_pct"]}% 为例，纯新 GT10 在 L{best["pure"]["L"]} 得到 {fmt(best["pure"])}，B32 在 L{best["B32"]["L"]} 得到 {fmt(best["B32"])}，QPS 变化 {best["delta_pct"]:+.2f}%。'
        if more:
            line+=" 仅补点版达到 "+ "、".join(f'K{p["K"]}/{p["target_pct"]}%' for p in more)+"。"
        brief.append(line)
    text=f"""# E212 四集同期对比

对比 NSG（固定单入口、SPAN4）、新 GT10、新 GT10+B32、旧 GT10+B32。新 GT10 使用 E211 发布内核，GT10 画像沿原配置，WebVid 用 soft-t1，其他三集用 hard。补点版共用原 B32 表。全部四集使用既有 NSG 图和原始内积。每集 3,072 条公开查询，真实 K1/K100 各7档 L，224点448批，CPU15 单线程，完整 QPS 取两遍均值。

- 新、旧 GT10+B32 的 56 组同 K/L 返回逐字节相同。新版本完整 QPS 变化 **{release_speed}**，均值更快 {perf_faster}/56，慢遍快于旧版快遍 {both_races}/56。
- 同用 SPAN4 时，新 GT10 相比固定单入口在 {recall_gain_routes}/56 个同 L 点增加平均 Recall。完整 QPS 包含路由成本，各集各 K 见下表。
- 在新 GT10 上启用 B32 有 {recall_gain_b32}/56 个同 L 点增加平均 Recall，有 {qps_loss_b32}/56 个同 L 点的完整 QPS 降低。能否换来更快的达标配置取决于数据集、K 和 Recall 要求。

## Recall–QPS 曲线

![四集 Recall@1–QPS](analysis/recall_qps_k1.png)

![四集 Recall@100–QPS](analysis/recall_qps_k100.png)

## 相同 K 和 L 的差异

每行给出 7 个实测 L 的最小到最大变化。召回差以百分点计。

{table(["数据集","K","新 GT10 比 NSG 召回","新 GT10 比 NSG QPS","补点比纯新 GT10 召回","补点比纯新 GT10 QPS","同表新比旧 QPS"],cross)}

以下是 L200 的实际 Recall / QPS。

{table(["数据集","K",*(DISPLAY[m] for m in METHODS)],fixed)}

## 达到召回目标后能跑多快

以达到门槛的最快实测 L 比较，单元格是 L / 实际 Recall / QPS。粗体为该门槛下四种链路中最快的点。破折号表示当前网格没有达标点。

{chr(10).join(brief)}

{table(["数据集","K","门槛",*(DISPLAY[m] for m in METHODS)],feasible)}

同一数据集和 K 的 28 个实测点中，若另一点的 Recall 和 QPS 都至少相同且有一项更高，该点被支配。下表统计未被支配的实测点数。

{table(["数据集","K",*(DISPLAY[m] for m in METHODS)],front)}

## K100 低召回

每集 3,072 条。L200 下若一个查询命中 0–9 个 GT 成员，计为低召回。脱离和新增配对使用同一查询。

{table(["数据集","NSG","新 GT10","新 GT10+B32","换入口脱离 / 新增","补点脱离 / 新增"],tail)}

## 复核

168 个 GT10 / B32 实际返回包与 E211 对应结果一致。52 个 NSG 实际返回包与 E200 对应配置输出的前3,072条一致。NSG 标量与 SPAN4 做了每个配置256条资格比对，共14,336次配对。172,032 条 B32 合并由独立线性 oracle 核对。正式两轮包对齐。分析从实际 ID 和测试 GT 算 Recall，再用标准库实现复算全部 224 点、448 wall、同预算净变化、低召回转移及离散门槛。

[协议](protocol.md) · [完整测点](analysis/points.csv) · [同 L 对比](analysis/same_l.csv) · [门槛表](analysis/recall_thresholds.csv) · [前沿](analysis/frontier.csv) · [独立核验](reviews/independent_audit.json) · [来源和产物封存](seal.json)
"""
    (ROOT/"report.md").write_text(text)
    metrics={"kernel_qps_change":release_speed,"kernel_faster":perf_faster,
             "kernel_faster_in_both_runs":both_races,"routing_recall_gain_points":recall_gain_routes,
             "b32_recall_gain_points":recall_gain_b32,"b32_same_l_slower_points":qps_loss_b32,
             "L200_K100":panel,"threshold_advantages":threshold_advantages,
             "threshold_losses":threshold_losses,"threshold_only_b32_reaches":threshold_reach}
    write(ROOT/"analysis/summary.json",metrics)
    return metrics


def current_docs(metrics):
    result=(f'E212 四个真实数据集各3072条，真实 K1/K100 各7个 L。224点448批。'
            f'同表的新 GT10+B32 相对旧 GT10+B32 56组返回逐字相同，'
            f'完整 QPS 变化 {metrics["kernel_qps_change"]}。'
            f'固定同 L 补点平均 Recall 增加 {metrics["b32_recall_gain_points"]}/56 点，'
            f'完整 QPS 降低 {metrics["b32_same_l_slower_points"]}/56 点。')
    summary=REPO/"summary.md"
    summary.write_text(f"""# ACSG 当前结论

{result} {LINK}。

默认标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` 使用 E211 SPAN4。L2 等路径使用标量。显式标量回退调用 `acsg.set_flat_ip_batch4_enabled(false)`，在启动查询线程前设定。画像的配置以冻结输入为准。

E212 的 NSG 和新 GT10 使用同一 SPAN4，分别采用图的固定单入口和画像三入口。完整 B32 的部署取舍依据同内核两条曲线及实际达标配置。新旧 B32 的比较衡量主搜索内核的提速。

[E212 逐配置]({REL}/analysis/same_l.csv) · [E212 门槛表]({REL}/analysis/recall_thresholds.csv) · [E211 默认切换]({E211}/report.md) · [修改前文档]({REL}/source_before/)。

[E210 独立适配](experiment_history/210_span4_four_dataset_retest_v1.md)、[E209 两窗](experiment_history/209_webvid_b32_span_confirmation_v1.md)、[E208 四集补点](experiment_history/208_b32_equivalent_speed_v1.md)及历史证据按原配置索引。旧数据范围见[存储简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。
""")
    local=REPO/"LOCAL_CODEX_START.md"
    old=local.read_text()
    local.write_text(old.replace("先读 AGENTS、",f"最新四方法实测。{result} {LINK}。\n\n先读 AGENTS、",1))
    target=REPO/"s-target.md"
    old=target.read_text()
    target.write_text(old.replace("[E211 报告]",f"{LINK} · [E211 报告]",1))
    experiment=REPO/"s-experiment.md"
    old=experiment.read_text()
    experiment.write_text(old.replace("# ACSG 实验与研究索引\n\n",
              f"# ACSG 实验与研究索引\n\n{result} [历史卡片](experiment_history/{HISTORY})。\n\n",1))
    index=REPO/"experiment_history/README.md"
    old=index.read_text()
    old=old.replace("下面按原卡片文件号排序",
                f"[E212 四集同期对照]({HISTORY})。{result}\n\n下面按原卡片文件号排序",1)
    row="| [211_span4_production_default_v1.md]"
    index.write_text(old.replace(row,f"| [{HISTORY}]({HISTORY}) | E212 四集 NSG、新 GT10、新 GT10+B32、旧 GT10+B32 |\n{row}",1))
    spec=REPO/"spec.md"
    old=spec.read_text()
    anchor="## 5. 指标、计时与证据"
    assert old.count(anchor)==1
    body=f"""### 4.28 E212 四集 NSG 与三条 GT10 链路

[评测入口]({REL}/src/benchmark.cpp)链接 E211 发布静态库。NSG 固定使用原图入口及 SPAN4，新 GT10 使用原三入口及 SPAN4。新旧补点版共用原完整 B32，旧版显式关闭 SPAN4。四集真实 K1/K100 各7 L，每点两遍 CPU15/T1，完整 wall。保存各点首轮返回包、两轮时间、输入与发布库冻结，计时结束后评估。对比见{LINK}。

"""
    spec.write_text(old.replace(anchor,body+anchor,1).replace("E201–E211 见4.17–4.27。","E201–E212 见4.17–4.28。",1))
    (index.parent/HISTORY).write_text(f"""# E212 四集 NSG 和三条 GT10 链路同期对照

{result}

原图上的固定单入口 NSG 使用同一 SPAN4，与新 GT10 的三入口画像比较。新旧 GT10+B32 共用各集对应 B32 表，旧主搜索显式选择标量。所有方法使用 E211 发布二进制对应库和同一计时边界。公开3,072条的真实 K1/K100 各7个 L，每点两遍、完整 wall。168 个包与 E211 相同，52 个 NSG 返回前缀与 E200 相同，GT 评分及独立审计见原件。

[报告](../{REL}/report.md) · [协议](../{REL}/protocol.md) · [状态](../{REL}/state.json) · [E211](211_span4_production_default_v1.md)
""")


def main():
    verify(read(ROOT/"input_freeze.json")["files"])
    verify(read(ROOT/"bin/freeze.json")["files"])
    assert read(ROOT/"reviews/output_audit.json")["status"]=="PASS_E212_PACKETS"
    assert read(ROOT/"reviews/independent_audit.json")["status"]=="PASS_E212_STDLIB_AUDIT"
    metrics=build_report()
    current_docs(metrics)
    write(ROOT/"state.json",{"status":"SEALED_E212_FOUR_WAY","datasets":list(DATASETS),
        "points":224,"batches":448,"query_calls":1376256,"methods":list(METHODS),
        "kernel":"E211 production","main_report":"report.md"})
    final=("summary.md","s-target.md","s-experiment.md","LOCAL_CODEX_START.md","spec.md",
           "experiment_history/README.md",f"experiment_history/{HISTORY}")
    files={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob("*"))
           if p.is_file() and "__pycache__" not in p.parts and p.name!="seal.json"}
    write(ROOT/"seal.json",{"status":"SEALED_E212","artifacts":files,
                           "root_documents":{p:digest(REPO/p) for p in final}})
    print(metrics["kernel_qps_change"],metrics["routing_recall_gain_points"],
          metrics["b32_recall_gain_points"],metrics["b32_same_l_slower_points"])


if __name__=="__main__":
    main()
