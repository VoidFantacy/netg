#!/usr/bin/env python3
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];rel=R.relative_to(REPO).as_posix()
def get(name):return list(csv.DictReader((R/f'analysis/{name}.csv').open()))
def main():
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md','readme.md','LOCAL_CODEX_START.md','experiment_history/README.md']:
        assert (REPO/name).read_bytes()==(R/'source_before'/name).read_bytes(),f'root changed since pre-run snapshot; review before synchronizing: {name}'
    conclude=json.loads((R/'analysis/conclusion.json').read_text());summary=json.loads((R/'analysis/summary.json').read_text());audit=json.loads((R/'reviews/results_audit.json').read_text())
    assert audit['status']=='PASS_E187_STDLIB_SECOND_IMPLEMENTATION'
    pts={(x['dataset'],x['method'],int(x['L'])):x for x in get('points')};pairs={(x['dataset'],x['method'],int(x['L'])):x for x in get('paired')}
    link=f'[{"E187实验报告"}]({rel}/report_zh.md)';pdf=f'[六页图表PDF]({rel}/ACSG_自适应残差补全_实验对比_20261028.pdf)'
    table=['| 数据 | 方法L200 | Recall@100 | 完整QPS | 对GT10 ΔRecall pp / ΔQPS |','| --- | --- | --- | --- | --- |']
    for ds,label in [('coco','COCO'),('deep10m_l2_v1','Deep10M')]:
        for m in ['GT10','B32','REG-NN','REG-Q','REG-R']:
            x=pts[ds,m,200];z=pairs.get((ds,m,200));delta=f"{float(z['recall_delta_pp']):+.4f} / {float(z['qps_delta_pct']):+.2f}%" if z else '—'
            table.append(f"| {label} | {m} | {float(x['recall_pct']):.4f}% | {float(x['qps']):.2f} | {delta} |")
    body='\n'.join(table)
    cost='；'.join(f"{s['dataset']}正式内部wall {s['formal_internal_seconds']:.2f}s，suite {s['formal_outer_seconds']:.2f}s" for s in summary['summaries'])
    hist=f'''# E187：全base区域残差补全的来源与费用pilot

2026-10-28，用户授权开始实验并给出提升。实施E186的首轮候选来源pilot：COCO raw-IP 118272×512、Deep10M squared-L2 10M×96，真实K100，原base/NSG/GT10保持。原46点/138单线程10K批次完成，另以独立冻结协议增加6个GT10控制/18轮（合计52点/156轮），不扩展K1/其他五集或动作选择器。

**{conclude['lead']}** {conclude['verdict']}

{body}

原模型/原46点不改；读出原结果后为排除L网格错觉，单独冻结COCO408/432/464及Deep101/201/401，仅GT10六点。补充为测试曝光后的保守费用核验，不是盲确认；时间窗口差异与漂移限制保留，原分析在analysis_original_v1。

三种区域对照：REG-NN最近2区域；REG-Q只q/区域特征；REG-R加入原R摘要。同后端1024区域、global PQ M16×8bit、top8选2，完整扫描后96精算严格合并。候选来自全base，与E174/E175从残差seed作同NSG一跳有实质区别；IVF/PQ本身不作创新主张。R是否有效及源外救回详见实际CSV，不从几何相关推导净收益。

合法16K训练中12K fit/4K cal（cal不选参数）；B32为原16K冻结参考。原test已历史曝光，无新盲确认。原L200教师模型固定用于L100/200/400；GT10密集11个L，三轮轮转顺序，不改配置到通过。

计时CPU15/实际1线程，所有库1线程；完整Batch分配初始化、原路由/主搜、区域选择/扫描/精算/合并、六数组复制及正常销毁。预热/加载/保存/hash/GT/oracle在外；{cost}。内部wall包含在suite中，不能相加；额外区域数组和构建费用见报告。B32原计数0为未插桩，第二实现重构实际候选数。

核验52点/156轮实际包、成员/查询救损与严格<10%尾部；三轮bit/SHA、冻结输入、大资产stat、实际主包补全oracle、旧程序128query前缀位一致、全base分区及4096编码抽查通过。stdlib第二实现{audit['seconds']:.3f}s。提前启动资格汇总造成的FileNotFoundError保留过程说明，随后等待完成原脚本通过；不回写失败或旧科学产物。

默认E99 GT10不变；不宣称完整E186接口/动作开关已实现，不从两集pilot推出流形因果或跨集净收益准入器。更多方法/预算若继续须另立冻结协议。E186设计原件继续保留当时纯理论身份。

[{"完整报告"}](../{rel}/report_zh.md) · [PDF](../{rel}/ACSG_自适应残差补全_实验对比_20261028.pdf) · [协议](../{rel}/protocol.md) · [冻结](../{rel}/freeze.json) · [核验](../{rel}/reviews/results_audit.json)。
'''
    (REPO/'experiment_history/187_adaptive_completion_pilot_v1.md').write_text(hist)
    old=(R/'source_before/s-experiment.md').read_text();old=old.replace('更新于2026-10-27。最新设计E186未实施；最新实测诊断E185；最新正式性能E183。','更新于2026-10-28。最新正式性能为E187两集K100来源pilot；七集两K综合证据仍为E183，几何诊断为E185/E184。E186保留当时理论原件，部分候选后端现已在E187实施。')
    old=old.replace('| E186 |',f'| E187 | 全base区域残差补全pilot | 52点/156完整T1（原46+6控制）；{conclude["regional_dominated"]}/18区域点被实测GT10覆盖，默认不变 | [卡片](experiment_history/187_adaptive_completion_pilot_v1.md) |\n| E186 |',1)
    old=old.replace('645点/1935完整T1；最新正式性能，默认不变','645点/1935完整T1；七集两K综合证据，默认不变')
    (REPO/'s-experiment.md').write_text(old)
    old=(R/'source_before/experiment_history/README.md').read_text()
    old=old.replace('更新于2026-10-27。最新理论设计[E186](186_adaptive_completion_design_v1.md)未实施；最新诊断是[E185](185_manifold_residual_probe_v1.md)，最新正式性能是[E183](183_gt10_residual_comprehensive_v1.md)。','更新于2026-10-28。最新正式pilot是[E187](187_adaptive_completion_pilot_v1.md)两集K100；七集两K综合证据仍为[E183](183_gt10_residual_comprehensive_v1.md)，几何诊断为[E185](185_manifold_residual_probe_v1.md)。E186原设计保留历史纯理论身份，候选来源部分已另在E187实施。')
    old=old.replace('| [186_', '| [187_adaptive_completion_pilot_v1.md](187_adaptive_completion_pilot_v1.md) | E187：全base区域残差补全来源与费用pilot |\n| [186_',1)
    (REPO/'experiment_history/README.md').write_text(old)
    current=f'''# ACSG 当前结论

更新于2026-10-28。**默认保留GT10：WebVid GT10-soft-t1、Yandex GT10-hard，E99共享NSG优化保持。** 最新正式实验是{link}，七集两K综合证据仍为E183。E187已完成，没有正在等待恢复的矩阵；长期可靠Recall–QPS目标尚未达成。

**{conclude['lead']}** {conclude['verdict']} 全量见{pdf}。

## 最新两集K100实际结果

COCO/Deep保留原base、图、metric和GT10。原46点加6个GT10控制，52点、每点10K query、3轮、实际单线程完整wall；原GT10测11个L，每集另补3个L，B32及REG-NN/Q/R在L100/200/400。下面固定L200；QPS是本轮中位数，不拼接旧kernel或计时批次。

{body}

另冻6个GT10控制用于排除原网格错觉，原46点及首轮分析保留，未改模型或补全参数；补充与原候选时间窗口不同，不作为精确速度估计或盲确认。

区域后端覆盖全base，允许提出旧训练残差源外ID；突破候选来源与获得净性能是两项证据。REG-Q只看q与区域，REG-R另看原始返回；同样top8选2、96精算上限不意味着同扫描量。R相对Q的三L结果、源内外救回/损伤、真实更大L的离散预算对照均保留[全部CSV]({rel}/analysis/)。不按测试挑赢家，不把曲线插值当新增等Recall测量。

原区域模型12K训练、4K校准（不选参数）；B32为完整16K训练的冻结参考。原测试历史曝光，非盲确认；本轮未验证K1/其他五集，未实现逐query动作开关，未替换默认。

## 失败率与救回率

用户定义的失败为单query Recall@100<10%，即0–9个GT100命中；恰好10个排除。失败率以同数据/方法/L全部query为分母；改善与升至≥10%分别统计。E187两集三L及配对尾部见报告，不能把平均Recall增加或成员修复率解释为严重失败修复。

七集已有全L失败分布继续见[全L修正版](reports/20261024_failure_rescue_residual_lt10_v2/report_zh.md)及其PDF；其147点引用E183既有返回。旧“未满100”图保留历史身份，不作当前失败率口径。两集尾部样本很少，不用0/1、1/2推导普遍规律。

## 残差、几何与跨集判断

E184/E185支持局部连续性与遗漏共享存在关联，不支持单一“越低维越有效”，也没形成免费在线净收益准入器。COCO局部有效秩高于Deep/SIFT，不能以PCA秩作为真实流形维数或残差适用标签。根本研究问题是可迁移的剩余目标结构能否在有限访问预算下被利用，不能只看失败量或源内重现。

固定ID表受遗漏目标在训练中重现、当前路由覆盖及有限容量约束；Deep/SIFT源外主导，GIST还受路由/选择限制。E187用独立全base后端检验源外可达性与费用，结论只及这组固定实现/模型。不能把区域法失败解释为数据没有流形，也不能把源外救回当已发现流形因果。

E183七集两K：WebVid/COCO旧残差共同Recall区间折线受益，Flickr/GIST混合，Deep/SIFT及Yandex K100未支持统一替换。旧数值与边界见[E183报告](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)，本轮未重新测另外五集，不跨核拼QPS。

## 核验、成本与限制

{cost}。内部wall已在suite中，不能相加。后端构建8线程、训练/查询1线程，数组RAM与每query扫描/精算见报告；B32原JSON计数0为未插桩，不是0精算，第二实现已重构。

旧程序前128query ID/score/route逐字一致，全base分区、4096编码抽查、全部补全从同L实际主包重构oracle、52真实包/156轮bits/SHA、冻结输入/大资产stat及第二份stdlib质量统计通过。第二实现由同一执行者完成，不称独立人员审查。技术失败过程留[说明]({rel}/reviews/process_notes.md)。

单图/单模型、曝光公共query、两集pilot、固定模型跨L迁移与计时波动限制保留，无新盲确认、流形因果、跨集准入器或默认替换。原科学产物/历史seal保持；根文档旧版本见[E187快照]({rel}/source_before/)。

## 证据入口

{link} · {pdf} · [52点]({rel}/analysis/points.csv) · [救损]({rel}/analysis/paired.csv) · [实际预算对照]({rel}/analysis/discrete_comparisons.csv) · [第二实现核验]({rel}/reviews/results_audit.json) · [E185](entry_method_exploration/20261024_manifold_residual_probe_v1/report_zh.md) · [E184](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)。
'''
    (REPO/'summary.md').write_text(current)
    spec=(R/'source_before/spec.md').read_text().replace('更新于2026-10-27','更新于2026-10-28',1)
    begin=spec.index('[E186设计]');end=spec.index('## 5.',begin)
    spec=spec[:begin]+f'''[E186设计](entry_method_exploration/20261027_adaptive_completion_design_v1/design_zh.md)的原件保留当时纯理论身份。其候选来源部分现已在[E187]({rel}/protocol.md)实现并测量；完整统一动作接口/不补全门控/逐query选择器未实现。原search_new没有新增暂停/恢复能力。

### E187区域候选实现合同

- [prepare_backend.py]({rel}/scripts/prepare_backend.py)：原base抽65536训练coarse1024及global PQ M16×8bit；全base稳定分区，显式centroids/codebooks/ID映射/offset/PQ codes，IP粗代表球面训练只用于辅助路由。导出raw布局，不跨Python/C++Faiss版本交换序列化。
- [pilot.cpp]({rel}/src/pilot.cpp)：共用E183原主核与路由，主搜索后REG-NN/Q/R从coarse top8选2区域，完整扫PQ码，排除原R，最多96原metric精算严格合并。NN取最近；Q用5特征ridge；R用10特征，额外包含R区域/分数摘要。选区、LUT/扫描/去重/精排/合并全部计时。
- [train_selector.py]({rel}/scripts/train_selector.py)：合法原16K前12K fit、后4K cal只描述，不调参；标签为原L200教师遗漏在各region的计数，标准化ridge α10，负预测裁0，ties回粗rank。冻结模型固定迁移L100/200/400。B32原16K表保留。在线不读GT。
- 正式两集真实K100；23点/集、3轮；CPU15实际1线程、完整六数组生命周期，原timed包保存。零NDC为未插桩布局；REG扫描/精算实时计数。B32原JSON的Stats0为占位，第二实现从实际主包/冻结表重构候选数，不能当作0访问。
- [freeze.json]({rel}/freeze.json)绑定源码/binary/静态库/配置/模型/小输入，原base/图沿E183身份并核当前stat；编码记录完整消费向量流SHA，不冒称原容器全量hash。保存三轮raw SHA、点/轮收据、主包合并oracle、旧程序前缀/全分区/抽样编码核验及第二实现统计。
- [analysis]({rel}/analysis/)：52点（原46+6控制）、配对成员/查询救损、严格<10%尾部、源内外救回、全离散预算对照、逐query压缩CSV及矢量PDF。单独部署区域法需额外全base后端RAM；共同benchmark进程加载后端不意味着GT10生产依赖它。结果不属于默认主链。

'''+spec[end:]
    (REPO/'spec.md').write_text(spec)
    target=f'''# ACSG 后续研究问题

更新于2026-10-28。目标仍为可靠Recall–QPS综合改进，默认E99 GT10保持。E187两集K100来源pilot已完成，没有待恢复矩阵；{conclude['lead']}

## 当前证据与停止边界

{conclude['verdict']} 完整数值、同L取舍、源内外实际救回、R相对Q与预算对照见[summary](summary.md)及{link}。本轮只检验一个固定区域后端与两个简单模型，不否定所有主结果条件化或流形相关机制。

原46点及另冻6个GT10费用控制全部完成即收口；不继续增加区域扫描、改PQ/模型或按原测试调参到通过。E186的完整动作接口、数据集/K/L配置选择及逐query门控仍未实现；K1与其余五集尚未测试该新来源。原E183–186状态/失败/seal保留历史身份。

## 下一门：先把来源费用降下来

若继续，应另立协议验证廉价区域路由、更小扫描预算或成本感知region选择，冻结模型/预算/样本和停止条件，先证明对充分测量的更大L GT10有实际优势。新增候选数相同不等于费用相同；完整计入路由、选择、PQ码扫描、访存、精算、合并和输出。若没有成本优势，不先训练复杂动作开关。

保持ID表和不补全为可选动作。只有来源支付得起，再验证R相对同后端q-only/最近区域的稳定增量；最后在合法独立校准角色选择数据集/K/L配置，用未参与选择的query确认。原公共test已曝光，不能当新盲确认。

## 泛化与几何问题

残差适用性不由失败率或PCA秩单独决定。E184/E185的局部连续性关联不是流形因果或在线免费特征；新集需要合法小规模校准，以实际救回、额外费用和损伤决定是否补全。先离线做数据集级选择，逐query复杂选择器须有异质性与成本依据。

未来更广的正式结论须覆盖真实K1/K100和SIFT/GIST/Web/Y/Flickr等反例，不按结果排除。尾部仍按Recall@100<10%（0–9命中），成员修复与严重失败修复分开。统一实际单线程串行，曝光角色与未盲限制披露，不更改GT或旧历史。

## 接续

从[LOCAL_CODEX_START.md](LOCAL_CODEX_START.md)开始；本轮原目标快照见[E187 source_before]({rel}/source_before/s-target.md)，E186理论原件在原目录。旧期限/预算/runner不自动恢复。

<a id="2026-10-03-新对话接续入口"></a>
'''
    (REPO/'s-target.md').write_text(target)
    readme=(R/'source_before/readme.md').read_text().replace('更新于2026-10-27','更新于2026-10-28',1)
    readme=readme.replace('## 最新研究\n','## 最新研究\n\n- '+link+'。两集K100、52点/156完整单线程批次（含6个补充GT10控制）；'+conclude['lead']+' '+pdf+'。\n',1)
    readme=readme.replace('**纯理论，未实施或测试**','**原件为当时纯理论；候选来源部分已另在E187实施**')
    readme=readme.replace('这次整理没有训练、性能重测、Git提交或发布。','E187新增后端构建、模型训练与正式性能；没有Git提交或发布。旧整理本身不改变原科学产物。')
    (REPO/'readme.md').write_text(readme)
    start=f'''# ACSG 当前接续入口

更新于2026-10-28；仓库`/data/netg/ACSG`，分支`research/state-20261002`，基底HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–187为本地未提交工作，HEAD不包含这些完整产物。当前没有待恢复的实验矩阵，默认GT10不变。

## 阅读顺序

1. [AGENTS.md](AGENTS.md)：数据/单线程/文档职责及历史保护。
2. [summary.md](summary.md)、[spec.md](spec.md)、[s-target.md](s-target.md)、[s-experiment.md](s-experiment.md)。
3. {link}、{pdf}、[52点]({rel}/analysis/points.csv)、[离散预算对照]({rel}/analysis/discrete_comparisons.csv)、[核验]({rel}/reviews/results_audit.json)。
4. 涉及几何看E185/E184原报告；七集两K性能看E183。旧方案从历史索引进卡片、原协议、结果与修正。

## 当前边界

{conclude['lead']} {conclude['verdict']} E187仅两集K100曝光数据pilot；全base新来源已实现，完整动作接口/逐query开关尚未实现，未验证K1/其余五集，无新盲确认或默认替换。E186原件仍保留当时理论身份。

失败严格是单query Recall@100<10%，即0–9命中，成员修复与尾部改善/脱离分开。新来源源外可达不等于费用可支付；下一步若继续须新协议降访问成本，不能在旧test上改模型到通过。几何关联不作流形因果或净收益准入器。

## 只读接续提示词

```text
在/data/netg/ACSG接续。先只读核branch与HEAD，再依LOCAL_CODEX_START.md读AGENTS和四主文档。报告GT10默认、E187两集K100真实Recall/QPS与更大L预算对照、源外救回与成本、R相对Q的作用、严格<10%尾部及证据范围。说明E186哪些部分已实现、哪些仍未实现；七集两K仍读E183，几何读E185/E184。旧方法沿卡片到原协议与结果，不改历史，不训练、不恢复runner、不调参或重测，除非当前用户另行授权。
```

修改前入口见[E187快照]({rel}/source_before/LOCAL_CODEX_START.md)。原大资产、静态库、对象和数据/图并不因Git文件齐全就可移植复跑。
'''
    (REPO/'LOCAL_CODEX_START.md').write_text(start)
    print('PASS synchronized current docs and E187 history')
if __name__=='__main__':main()
