#!/usr/bin/env python3
"""Documentation-only closeout; preserve the sealed E187 experiment."""
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[2]
NOTE='experiment_history/_maintenance/20261028_completion_cost_handoff_v1/conclusion_zh.md'
OLD='本轮区域补全尚未建立可支付的Recall–QPS提升，保留GT10默认，停止该固定后端进入动作选择器。'
NEW='本轮区域补全的单位新增召回成本过高，未取得完整Recall–QPS综合提升。默认保留GT10，暂不将这版区域后端接入动作选择器。'
def main():
    names=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','readme.md','experiment_history/README.md']
    for name in names:
        assert (REPO/name).read_bytes()==(R/'source_before'/name).read_bytes(),f'Changed since snapshot, review first: {name}'
    s=(REPO/'summary.md').read_text().replace(OLD,NEW)
    marker='## 失败率与救回率'
    extra=f'''## 单位新增召回的访问成本

这版区域补全的主要瓶颈是救回量不足以偿还额外访问费用。固定L200，按完整中位QPS倒数推算平均查询耗时：COCO B32增5.70%、REG-R增29.30%；Deep B32增3.51%、REG-R增62.60%。这与上表QPS降幅不是同一数值，不能混用。

Deep REG-R救回4821个成员，其中4794个在旧训练残差源外；平均扫描约26134个PQ码/query，COCO约282个/query。Deep不使用学习模型的REG-NN仍增耗时54.60%，说明基础区域补查已有显著费用。当前只测完整wall与扫描/精算计数，尚未测粗路由、LUT、扫描/堆、精算和合并的分段占比，不能宣称某一项已被确认为最大瓶颈。

固定ID表的来源问题仍独立存在：Deep B32开销较小，却只增加0.0021pp；COCO同表增加1.3715pp。因此不能把所有残差问题简化为执行慢，也不能把当前结果概括成所有补全都不值得。分段计时、硬访问预算、成本感知选区和按query跳过补全均是后续提案，未实施或测试。详见[费用结论与新对话接续]({NOTE})。

'''
    assert marker in s;s=s.replace(marker,extra+marker,1);(REPO/'summary.md').write_text(s)
    s=(REPO/'spec.md').read_text().replace('### 4.1 尚未实施的适配设计','### 4.1 适配设计与实际实施范围')
    s=s.replace('正式两集真实K100；23点/集、3轮；','正式两集真实K100；原矩阵23点/集，独立C1控制每集另3个GT10点，共52点/156轮；')
    marker='## 5. 指标、计时与证据'
    extra=f'''### 4.2 已测费用与尚未实现的省费方案

E187已有完整batch wall和REG扫描/额外精算计数；平均query耗时增幅可由中位QPS比值`QPS_GT10/QPS_method−1`派生。尚无粗路由、特征/预测、PQ LUT、码扫描/堆维护、精算、合并的分段耗时；不得把计数当耗时占比。

当前区域法固定选2区域并完整扫描，没有硬码数/字节数上限、成本感知训练目标或逐query跳过补全开关。R原分数已用于合并缓存；更广的候选/距离复用需先核现有接口和生命周期，不假设search_new导出了完整搜索状态。上述省费方向均未实现，本次只在[接续说明]({NOTE})登记；原E187代码、模型、返回、计时和seal不变。

'''
    assert marker in s;s=s.replace(marker,extra+marker,1);(REPO/'spec.md').write_text(s)
    s=(REPO/'s-target.md').read_text().replace(OLD,NEW)
    a=s.index('## 下一门：先把来源费用降下来');b=s.index('## 泛化与几何问题',a)
    s=s[:a]+f'''## 下一门：先量清访问费用，再验证省费方案

本节均为下一阶段提案，尚未实现、未测试、未启动队列。先做分段计时，拆出粗路由、特征/预测、PQ LUT、扫描/排除/堆维护、原metric精算、合并和输出；保留完整外层wall，区分插桩诊断与正式性能，不把嵌套耗时重复相加。现有数据只能确认整体性价比不足，尚不能指定最大单项耗时。

在测量基础上优先讨论三项：固定码数/字节数/精算量的硬访问预算；主搜索已产生信息的合法复用；预测实际可救回量与访问费用的成本感知区域选择。固定2个区域不能保证固定费用；主结果的已有距离缓存不等于完整候选状态已可恢复。新目标要考虑PQ筛选与有限精排后实际救回，不能仅预测区域原始遗漏数。

保持B32、区域补全和不补全为可选动作。先在合法校准角色选择数据集/K/L配置，只有异质性与额外费用值得时再研究逐query跳过或动作选择。在线不能读取GT；原公共test已曝光，校准与未参与选择的后续确认必须分开。流形/数据特征只可作为待验证线索，不替代净收益实测。

继续实现或实验时另立协议/目录，冻结控制、模型、预算、样本和停止条件，完整费用对照预算附近充分测量的更大L GT10；不利用稀疏网格或插值制造优势，不在旧test上调参到通过。本次交接不自动恢复实验。具体证据与读法见[接续说明]({NOTE})。

'''+s[b:];(REPO/'s-target.md').write_text(s)
    s=(REPO/'s-experiment.md').read_text();marker='## 最近研究与当前依赖'
    s=s.replace(marker,f'2026-10-28解释与接续补充：[单位新增召回的访问成本]({NOTE})。仅整理E187已有证据、未实施的省费方向和新对话入口，无新增实验编号或性能。\n\n'+marker,1);(REPO/'s-experiment.md').write_text(s)
    s=(REPO/'experiment_history/README.md').read_text();marker='## 全部详细卡片'
    s=s.replace(marker,'[2026-10-28费用结论与接续整理](_maintenance/20261028_completion_cost_handoff_v1/README.md)单独保留修改前快照、证据派生与验证；原E187 seal及当时验收收据不回写。\n\n'+marker,1);(REPO/'experiment_history/README.md').write_text(s)
    s=(REPO/'readme.md').read_text().replace(OLD,NEW);marker='## 实现与复现'
    s=s.replace(marker,f'[本次讨论的费用结论与新对话接续]({NOTE})：新区域法单位救回成本过高；Deep旧表另有有效候选不足。下一步先分段计时，再论证硬访问预算与成本感知补全，均未实施。\n\n'+marker,1);(REPO/'readme.md').write_text(s)
    start=f'''# ACSG 当前接续入口

更新于2026-10-28；工作区`/data/netg/ACSG`，分支`research/state-20261002`，核对HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–187及本次整理主要为本地未提交工作，HEAD/旧远端快照不包含这些完整产物；新对话应使用同一工作区。E187已完成，没有待恢复矩阵。

## 先读什么

1. [AGENTS.md](AGENTS.md)：文档职责、数据/历史保护及实际单线程约定。
2. [summary.md](summary.md) → [spec.md](spec.md) → [s-target.md](s-target.md) → [s-experiment.md](s-experiment.md)。
3. [本次费用结论与接续快照]({NOTE})：方法、关键数字、证据边界和未实施的下一步。
4. [E187报告](entry_method_exploration/20261028_adaptive_completion_pilot_v1/report_zh.md)、[六页PDF](entry_method_exploration/20261028_adaptive_completion_pilot_v1/ACSG_自适应残差补全_实验对比_20261028.pdf)、[52点](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/points.csv)、[预算对照](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/discrete_comparisons.csv)、[核验](entry_method_exploration/20261028_adaptive_completion_pilot_v1/reviews/results_audit.json)。旧方案从历史索引进原卡片、协议、配置、结果与修正。

## 本次讨论收敛的判断

**新区域方案能补到旧源外遗漏，但每增加一点召回，访问成本过高，未取得完整Recall–QPS改进。** 固定L200：COCO REG-R增Recall0.2349pp、平均完整耗时增29.30%；Deep增0.4821pp、耗时增62.60%。Deep救回4821个成员中4794个在旧训练残差源外，源外可达已有证据；Deep不使用学习模型的REG-NN仍增耗时54.60%。

旧B32有另一类限制：Deep只增Recall0.0021pp、耗时增3.51%；COCO增1.3715pp、耗时增5.70%。不能把全部残差问题归结为执行慢；需要同时看有效候选量和费用。耗时增幅按`QPS_GT10/QPS_method−1`算，不等于QPS降幅。

默认保留E99 GT10（WebVid soft-t1 / Yandex hard）。E187为原46点加6个独立冻结GT10控制，合计52点/156轮；18个区域点均有扩大L的GT10同时覆盖Recall与QPS。原窗口覆盖15点，另外3点使用后补控制，时间窗口/频率/缓存漂移限制保留。

## 哪些仍未做

已有完整wall与REG扫描/精算计数，尚未有粗路由、PQ扫描、精算等分段耗时，不能指定最大单项瓶颈。下一步优先讨论分段计时、硬访问预算、主搜索信息复用、成本感知实际救回目标、允许不补全；这些均未实施、未测试，不自动启动。

当前实现为全base1024区域/global PQ，GT10后从8个近区域选2个、完整扫码、最多96精算合并。REG-NN取最近、REG-Q看query/区域、REG-R加原结果摘要；没有完整统一动作选择器、硬扫描预算或显式流形估计。

E187仅COCO/Deep真实K100、历史曝光测试；无新盲确认，K1/其余五集未测该新来源。七集两K读E183，几何关联读E184/E185，不作流形因果或新数据净收益准入器。失败始终为单query Recall@100<10%（0–9命中），改善、脱离、成员救回分开。

## 可复制的接续提示词

```text
请接续/data/netg/ACSG。先只读核分支和HEAD，再读LOCAL_CODEX_START.md、AGENTS及四份主文档，沿入口读20261028_completion_cost_handoff_v1/conclusion_zh.md。
当前结论：E187新区域补全能救回旧训练残差源外目标，但单位新增召回成本过高；Deep旧B32另有有效候选不足。E187已完成52点/156轮，两集真实K100；18个区域点被更大L GT10覆盖，默认仍E99 GT10。测试已曝光，后补控制时间窗口不同，未做分段计时或完整动作开关。
请先总结证据与限制，再提出分段计时、硬访问预算、信息复用和成本感知补全的验证方案。保留严格Recall@100<10%的失败定义，完整单线程wall对照附近更大L。现阶段只读理解和方案讨论，不自动重跑、训练、恢复队列、修改默认或改写旧封存；后续按我在新对话中的明确任务继续。
```

## 交接维护

[本次快照与验证](experiment_history/_maintenance/20261028_completion_cost_handoff_v1/README.md)记录文档变化，无新ANN/GT/训练/QPS。E187旧交付收据中的根文档SHA只代表当时版本，本次更新另留收据；不要回跑旧finalize来覆盖封存身份。原大数据/GT/图/静态库/对象仍为本地重跑依赖。
'''
    (REPO/'LOCAL_CODEX_START.md').write_text(start)
    print('PASS synchronized cost conclusion and new-conversation handoff; no experiments')
if __name__=='__main__':main()
