"""Write the E211 report, current method docs and sealed evidence after release checks."""
import csv
from pathlib import Path

from run import ROOT, REPO, DATASETS, digest, read, verify, write


NAMES=dict(zip(DATASETS,("COCO","Flickr30k","WebVid","Yandex first10M")))
REL_ROOT=ROOT.relative_to(REPO).as_posix()
HISTORY="211_span4_production_default_v1.md"


def csv_rows(name):
    with (ROOT/"analysis"/name).open() as handle:
        return list(csv.DictReader(handle))


def update(path, before, after):
    content=path.read_text()
    assert content.count(before)==1,path
    path.write_text(content.replace(before,after,1))


def verify_sources():
    freeze=read(ROOT/"input_freeze.json")["files"]
    header=REPO/"ACSG/ACSG.h"
    qualified=ROOT/"source_tested/ACSG/ACSG.h"
    assert digest(qualified)==freeze[str(header)]["sha256"]
    original=qualified.read_text()
    old="bool flat_ip_batch4_enabled_ = false;"
    assert original.count(old)==1
    assert header.read_text()==original.replace(old,"bool flat_ip_batch4_enabled_ = true;")
    verify({p:row for p,row in freeze.items() if Path(p)!=header})
    for manifest in (ROOT/"bin/freeze.json",ROOT/"release/freeze.json",ROOT/"release/sources.json"):
        verify(read(manifest)["files"])


def attest():
    verify_sources()
    output=read(ROOT/"reviews/output_audit.json")
    assert output["status"]=="PASS_E211_OUTPUT_AUDIT"
    release=read(ROOT/"reviews/release_dispatch.json")
    assert release["status"]=="PASS_E211_DISPATCH" and release["release_default_untouched"]
    assert [r["case"] for r in release["outcomes"]]==["fixture",*DATASETS,
             "deep10m_l2_v1","sift10m_bigann_l2_v1","gist1m_l2_v1"]
    for row in release["outcomes"]:
        assert digest(row["receipt"])==row["sha256"]
    assert digest(ROOT/"release/verify_dispatch")==release["binary"]["sha256"]
    assert digest(ROOT/"release/test")==read(ROOT/"release/bench_build.json")["binary"]["sha256"]
    assert (ROOT/"logs/release_test_help.log").stat().st_size>0


def report():
    decision=read(ROOT/"analysis/decision.json")
    assert decision["passes_production_performance_gate"]
    pairs=csv_rows("matched_deltas.csv")
    assert len(pairs)==112
    short={}
    for m in ("GT10","B32"):
        numbers=[float(p["delta_qps_pct"]) for p in pairs if p["baseline"]==m]
        short[m]=f"{min(numbers):+.2f}%至{max(numbers):+.2f}%"
    comparisons=(
        f'112个新旧配对返回逐字节相同，{decision["passing_points"]}/112个配对通过逐点速度筛选。'
        f'纯GT10完整QPS变化{short["GT10"]}，GT10+B32变化{short["B32"]}。'
    )
    results=[
        "| 数据集 | 纯 GT10 完整 QPS 变化 | GT10+B32 完整 QPS 变化 | 速度筛选 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for ds in DATASETS:
        rows=[p for p in pairs if p["dataset"]==ds]
        cols=[]
        for m in ("GT10","B32"):
            num=[float(p["delta_qps_pct"]) for p in rows if p["baseline"]==m]
            cols.append(f"{min(num):+.2f}% 至 {max(num):+.2f}%")
        passed=sum(p["passes"]=="True" for p in rows)
        results.append(f"| {NAMES[ds]} | {' | '.join(cols)} | {passed}/{len(rows)} |")
    nonpassing=decision["not_passing"]
    exceptions="全部配对通过两遍速度筛选。"
    if nonpassing:
        entries=[f"- {NAMES[p['dataset']]} {p['baseline']} K{p['K']}/L{p['L']}，"
                 f"平均 {p['delta_qps_pct']:+.2f}%，新慢遍相对旧快遍 "
                 f"{p['slowest_new_vs_fastest_old_pct']:+.2f}%。" for p in nonpassing]
        exceptions="有以下配对落在两遍速度筛选外。\n\n"+"\n".join(entries)
    l200=[
        "| 数据集 | K | 链路 | Recall | 标量 QPS | SPAN4 QPS |",
        "| --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for p in pairs:
        if p["L"]=="200":
            l200.append(f"| {NAMES[p['dataset']]} | {p['K']} | {p['baseline']} | "
                        f"{float(p['recall_pct']):.4f}% | {float(p['baseline_qps']):.2f} | "
                        f"{float(p['span4_qps']):.2f} |")
    gate=decision["passing_points"]
    text=f"""# E211 GT10 正式入口测试和默认切换

**正式验收通过。** 已在源码和重新构建的版本中启用平铺 raw-IP、mode 2 的 SPAN4 默认分流。{comparisons}

## 四个真实数据集

每集使用 3,072 条固定公共查询，真实 K1/K100 各七个 L。总计 224 个点、448 个完整批次和 1,376,256 次计时查询。新旧共用同一构建的 `ACSG::search_new`、图、GT10 画像和原 B32 表。CPU15 实际单线程。完整 wall 含路由、主搜、补点（相应方法）以及输出批生命周期，QPS 取两遍均值。测试 GT 在全部计时完成后用于评分。

{chr(10).join(results)}

{exceptions}

![Recall@1 与完整 QPS](analysis/recall_qps_k1.png)

![Recall@100 与完整 QPS](analysis/recall_qps_k100.png)

![同预算完整 QPS 变化](analysis/speed_delta.png)

L200 的同配置对照如下。

{chr(10).join(l200)}

## 工程验证

- E211 的 224 个正式输出包均和 E210 对应真实输出逐字节一致。3,584 次额外配对核对整个候选池的 ID、距离位元和扩展标记及 visited 表。原 B32 做了 172,032 次逐查询独立重归并。
- 邻接行在线确定有效末端，按邻接顺序收集和插入，距离以原 Faiss 四路 raw-IP 计算。四路不足时逐项评分。旧索引通过原读盘入口加载，索引另存的 span 数组为零字节。
- 默认构建在四个 raw-IP 数据集的 K1/K100、L200、GT10/B32 组合上实测原生 batch4 入口被调用。显式标量回退的返回逐条一致。Deep10M、SIFT10M 和 GIST1M 使用相同发布产物验证默认标量分流及返回一致，每种组合 256 条。这三个 L2 数据集的检查属于兼容性测试。
- 合成图覆盖批尾、重复入口、预访问、空入口、并列分数、边编辑、visited 轮换、mode0/1、显式 trace 和外部距离函数。四个线程共享同索引并使用独立 scratch 的 1,200 次查询通过。当前 Faiss 构建下对 d=1 至2048 的 131,072 个生成点积做了位级对照。
- 粒度为索引的回退接口是 `acsg.set_flat_ip_batch4_enabled(false)`。在线程启动前配置。正常 CMake 目标 `benches/test` 也已用发布库重新链接，并通过命令行启动检查。

[协议](protocol.md) · [验收判定](analysis/decision.json) · [完整配对](analysis/matched_deltas.csv) · [正式原始批次](data/) · [发布路径核验](reviews/release_dispatch.json) · [发布构建命令](release/build.json) · [产物哈希](seal.json)
"""
    (ROOT/"report.md").write_text(text)
    return comparisons,gate


def update_docs(comparisons,gate):
    report_link=f"[E211 报告]({REL_ROOT}/report.md)"
    history_link=f"[E211 历史卡片](experiment_history/{HISTORY})"
    state_link=f"[状态]({REL_ROOT}/state.json)"
    source_before=f"[切换前源码与文档]({REL_ROOT}/source_before/)"
    current=("2026-11-20 完成 E211 并切换默认。标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` "
             "默认走 SPAN4，L2 等其他距离路径走标量。四个真实数据集各3,072条，真实K1/K100各7个L，"
             "224点、448个完整CPU15单线程批次。"+comparisons)
    details="显式回退调用 `acsg.set_flat_ip_batch4_enabled(false)`，查询开始前设定。"
    (REPO/"summary.md").write_text(f"""# ACSG 当前结论

{current}

GT10 画像沿各数据集原配置。启用完整 B32 时同样调用 SPAN4 主搜索，补点收益继续按实际 Recall–QPS 判断。候选池与 visited 配对、同索引并发调用、边修改和三套 L2 的标量分流均通过核对。{details}

{report_link} · [逐配置配对]({REL_ROOT}/analysis/matched_deltas.csv) · {history_link} · {source_before}

[E210 独立适配](experiment_history/210_span4_four_dataset_retest_v1.md)、[E209 两窗](experiment_history/209_webvid_b32_span_confirmation_v1.md)、[E208 四集补点](experiment_history/208_b32_equivalent_speed_v1.md)、[E207 分段](experiment_history/207_b32_stage_cost_v1.md)及历史条件收益按原范围保留。旧数据范围见[存储简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。
""")
    (REPO/"LOCAL_CODEX_START.md").write_text(f"""# ACSG 本地 Codex 入口

{current} 当前无待恢复实验。

先读 AGENTS、summary、spec、s-target、s-experiment，再读 {report_link}、{history_link}、{state_link}及[发布验证]({REL_ROOT}/reviews/release_dispatch.json)。

后续 raw-IP GT10 性能实验链接新构建的 ACSG 或使用[已验收的发布静态库]({REL_ROOT}/release/libACSG.a)。查历史实验时使用其冻结二进制。{source_before}及[旧数据简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。
""")
    (REPO/"s-target.md").write_text(f"""# ACSG 后续研究边界

E211 已完成四集正式入口验证与默认切换。后续 raw-IP GT10 及该链路上的残差成本比较采用 SPAN4，旧标量内核可作显式对照。L2 采用标量，并完成了发布兼容性验证。当前无待恢复实验。

B32 的候选质量和额外开销依据实际召回门槛、同内核原方法与完整链路验证。E206 候选缺口、E207 分段和 E209 预取跨窗证据各按原合同；历史原始 QPS 各自保留来源。

{report_link} · [E210 独立适配](experiment_history/210_span4_four_dataset_retest_v1.md) · [历史索引](s-experiment.md)。
""")
    update(REPO/"s-experiment.md","# ACSG 实验与研究索引\n\n",
           f"# ACSG 实验与研究索引\n\n{current} {history_link}\n\n")
    hist=REPO/"experiment_history/README.md"
    old=hist.read_text().splitlines()[2]
    update(hist,old,f"2026-11-20 完成 [E211 正式入口默认验证]({HISTORY})。{comparisons} 当前见[summary](../summary.md)。")
    needle="| [210_span4_four_dataset_retest_v1.md]"
    update(hist,needle,f"| [{HISTORY}]({HISTORY}) | E211 GT10 正式入口 A/B 与默认切换 |\n{needle}")
    (hist.parent/HISTORY).write_text(f"""# E211 GT10 正式入口 A/B 与默认切换

{current}

两臂调用同一个正式 `ACSG::search_new` 和相同路由、图及表。候选版在线读取每次展开的邻接跨度并以原 Faiss 计算至多四路距离，按原序进行候选竞争。{details}

预先固定 4 数据集、2 真 K、7 L、4 臂、2 遍。全部实测输出及 E210 对应输出一致。候选池和 visited 3,584 次配对，B32 独立归并 172,032 次。{gate}/112 点通过逐点速度筛选。通过阈值后把源码的默认值设为 true，另编译发布库及常规 bench 程序。四个 raw-IP 数据集、三个 L2 数据集和 1,200 次共享索引并发都核验了发布路径。

[正式报告](../{REL_ROOT}/report.md) · [预锁协议](../{REL_ROOT}/protocol.md) · [产物和来源封存](../{REL_ROOT}/seal.json) · [前置研究 E210](210_span4_four_dataset_retest_v1.md)
""")
    spec=REPO/"spec.md"
    update(spec,"生产主链沿2026-11-10合同，E201–E210独立研究实现见4.17–4.26。",
          "GT10 主搜索内核已按 E211 更新。E201–E211 见4.17–4.27。")
    update(spec,"→ 原NSG search_new(mode=2) →","→ ACSG::search_new(mode=2) →")
    anchor="E99共享NSG预取和候选复制优化的合同见"
    update(spec,anchor,
           "- 标准 `IndexFlat`/`IndexFlatIP` 的 raw-IP 距离由 `storage_distance_computer` 标识，"
           "mode2 默认用 SPAN4。每次展开从当前邻接行尾取有效跨度，按原顺序计算并插入，"
           "四个有效未访问邻居使用原 Faiss batch4。候选池由调用方复用或由本次查询创建。\n"
           "- `set_flat_ip_batch4_enabled(false)` 对该索引选择标量回退；在启动查询线程前配置。"
           "mode0/1、trace、L2、外部距离计算器以及空入口回退使用标量。每个线程持有各自的 "
           "DistanceComputer、visited 和候选池。索引文件沿原读写合同，邻接跨度无持久化数组。\n\n"
           +anchor)
    update(spec,"## 5. 指标、计时与证据",
           f"""### 4.27 E211 GT10 正式入口与默认替换

[生产实现](ACSG/ACSG.cpp)的 SPAN4 在同一 `search_new(mode=2)` 下和标量做 A/B。E210 原输入、真实K1/K100各7档L，四集224点448个完整CPU15单线程批次。{comparisons} 完整候选池与 visited 逐条配对，独立 B32 合并与历史 E210 实际包交叉验证。发布版和正式 A/B 版源码差异为默认值。四集原生 batch4、三集 L2 标量及共享索引并发通过断言。参见{report_link}与[发布构建产物]({REL_ROOT}/release/)。

## 5. 指标、计时与证据""")


def main():
    attest()
    comparisons,gate=report()
    update_docs(comparisons,gate)
    write(ROOT/"state.json",{"status":"SEALED_E211_FLAT_IP_BATCH4_DEFAULT",
        "datasets":list(DATASETS),"points":224,"batches":448,"queries":1376256,
        "matching_paired_points":112,"speed_screen_passing_points":gate,
        "qualification_scratch_pairs":3584,"concurrent_per_binary_queries":1200,
        "default":"SPAN4, plain native Flat IP, ACSG::search_new mode 2",
        "rollback":"set_flat_ip_batch4_enabled(false) before query threads",
        "fallback":["L2","mode0/1","trace","non-native distance"],
        "release_build":"release/libACSG.a","normal_bench_build":"release/test"})
    documents=("summary.md","spec.md","s-target.md","s-experiment.md","LOCAL_CODEX_START.md",
               "experiment_history/README.md",f"experiment_history/{HISTORY}")
    files={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(ROOT.rglob("*"))
           if p.is_file() and "__pycache__" not in p.parts and p.name!="seal.json"}
    assert files["release/libACSG.a"] and files["analysis/recall_qps_k100.png"]
    write(ROOT/"seal.json",{"status":"SEALED_E211","experiment_files":files,
         "working_tree_files":{p:digest(REPO/p) for p in (*documents,"ACSG/ACSG.cpp","ACSG/ACSG.h")}})
    print(comparisons)


if __name__=="__main__":
    main()
