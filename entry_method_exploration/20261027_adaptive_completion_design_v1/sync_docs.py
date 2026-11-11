#!/usr/bin/env python3
"""Publish a theory-only design to current documentation, never execute it."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent;REPO=R.parents[1];REL=str(R.relative_to(REPO));LINK=REL+'/design_zh.md'
def edit(name,old,new):
    p=REPO/name;t=p.read_text();assert t.count(old)==1,(name,old)
    assert (R/'source_before'/name).exists();p.write_text(t.replace(old,new))
def main():
    assert json.loads((R/'state.json').read_text())['status']=='THEORY_ONLY_UNIMPLEMENTED_UNTESTED'
    edit('summary.md','更新于2026-10-24。','更新于2026-10-27。')
    edit('summary.md','## 当前方法和性能判断',
        '2026-10-27新增[E186适配不同遗漏特征的补全设计]('+LINK+')：保留ID表，并提出全base区域候选后端、主结果条件化及“不补全”选项；先验证新来源，再做选择器。**纯理论提案，未实现、未训练、未测试**；最新测量仍E185/E183，默认与现有补全代码不变。\n\n## 当前方法和性能判断')
    edit('spec.md','更新于2026-10-24。','更新于2026-10-27。')
    edit('spec.md','## 5. 指标、计时与证据',
        '### 4.1 尚未实施的适配设计\n\n[E186设计]('+LINK+')提出统一补全动作接口与“ID表/全base区域候选/不补全”，区域级训练遗漏标签、主结果条件化以及先来源后选择器的验证顺序。该接口、辅助索引、区域打分器和动作选择器**均未实现或测试**，不属于现有调用链；原search_new不因这份设计获得可暂停/恢复能力。当前源码/数据/metric/计时合同保持以上原状；若实施，辅助索引身份、RAM/离线构建、码扫描/精排与选择开销须另立版本登记。\n\n## 5. 指标、计时与证据')
    target='''# ACSG 后续研究问题

更新于2026-10-27。目标仍是相对当前默认的**可靠Recall–QPS综合改进**。GT10默认与E99共享核保持；E185/E184离线诊断、E183性能矩阵已完成。新的[E186适配补全设计](LINK)状态为**THEORY_ONLY_UNIMPLEMENTED_UNTESTED**，只记录本次讨论形成的方案与验证顺序，没有启动实验队列。

## 当前判断

当前固定ID表依赖遗漏目标在新query中重现、路由可取到和有限槽位可保留。E184显示Deep/SIFT源外主导，GIST还受路由/选择限制；E185支持局部几何连续性与遗漏共享有关，不支持简单“越低维越有效”，也没有给出净收益准入器。当前数值、费用和证据限制以[summary](summary.md)为准。

用户的失败定义保持单条Recall@100<10%，即0–9个GT100命中。该查询比例、平均Recall、成员救损和完整QPS分开；不以广义遗漏改善替代严重失败修复。

## 优先一：先证明一个新候选来源有成本优势

E186的主候选是：从独立覆盖整个base的几何分区/倒排后端检索候选，用合法训练query的**区域级遗漏**及主搜索真实返回摘要引导补查，最后按原metric精算合并。现有ID表作为基线与可保留动作。全base登记不等于有限扫描预算能覆盖全部目标；必须验证实际候选域。

提案先选COCO与Deep作正/负类型对照，真实K100、L=100/200/400，保留目标规模base和原图；比较GT10、固定B32、仅q区域选择与加入主结果R的区域选择。辅助分区/码本、额外RAM、扫描上限、独立角色和结束边界要在实施前冻结。候选域乐观覆盖不足以偿还开销时，停止该后端，不先训练复杂选择器。该pilot尚未运行。

## 优先二：证明主结果条件化优于简单区域检索

q-only与R-conditioned两策略必须用同后端、同成员来源/码本、同RAM及可选工作机会。主结果的区域数量不是正确GT数量；在线模型不能读取实际缺失、GT分离度、GT100局部PCA。若条件化没有额外收益，则保留简单策略或停止复杂主张。

E174/E175已有“残差候选作seed的一跳扩展”，E176已有PAIR/WIDE，旧理论也讨论return-ID键和预算器。新方案须实质改变候选来源；标准IVF/PQ与adaptive probing不作为创新本身。差异与前作见[E186](LINK)。

## 优先三：在独立query上选择动作，允许不补全

先在独立校准角色选固定数据集/K/L配置：ID表、区域补全或不补全。只有来源确有收益、且同一数据内query异质性值得额外费用时，再做逐query选择。输入限线上可取得且已计费的入口/分数/结果摘要、离线支持统计及区域摘要；校准证据不能替代未参与选择的确认。

原E185样本和旧公共query已曝光，不能充当新的盲确认。SIFT/GIST/Web/Y/Flickr保留为扩展与反例，不按结果剔除；后续正式评估仍须覆盖真实K1/K100，分别核质量与端到端费用。

## 进入与退出条件

统一单方法串行、实际threads=1。记录辅助路由/选择器/码扫描/访存/去重/原metric精算/合并/输出完整wall，另披露索引RAM与构建成本。新增候选数相同不等于费用相同。

相同完整耗时下比较实际Recall，或同目标Recall下比较速度；更大L的GT10必须在预算附近充分测量，不能利用稀疏网格或插值制造优势。最低实际效应、计时波动、质量不确定性、损伤与严格低召回尾部指标事前固定，不按确认反馈增加样本或改表到通过。

当前只有设计文档，没有已实现辅助后端、区域模型、动作选择器、确认角色或新性能。历史STOP/预算与旧runner保留原身份，不自动恢复。范数敏感路由等旧提案仍为[理论归档](entry_method_exploration/20261011_norm_aware_profile_theory_v1/theory.md)。

## 历史目标与接续

旧阶段期限/旧CAL与confirm前件全文见[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/s-target.md)，不是今天的执行队列。2026-10-27修改前的本文快照在[E186 source_before](entry_method_exploration/20261027_adaptive_completion_design_v1/source_before/s-target.md)。

<a id="2026-10-03-新对话接续入口"></a>

历史交接锚点仅兼容旧链接；当前接续从[LOCAL_CODEX_START.md](LOCAL_CODEX_START.md)开始。
'''.replace('LINK',LINK)
    (REPO/'s-target.md').write_text(target)
    edit('s-experiment.md','更新于2026-10-24。最新研究是E185局部几何探查；最新正式性能是E183。',
        '更新于2026-10-27。最新设计E186未实施；最新实测诊断E185；最新正式性能E183。')
    edit('s-experiment.md','| E185 |',
        '| E186 | 按遗漏特征适配补全来源/预算的设计 | THEORY_ONLY_UNIMPLEMENTED_UNTESTED；先验证全base区域候选，再做动作选择，无新性能 | [卡片](experiment_history/186_adaptive_completion_design_v1.md) |\n| E185 |')
    edit('readme.md','更新于2026-10-24。','更新于2026-10-27。')
    edit('readme.md','## 最新研究\n\n',
        '## 最新研究\n\n- [E186：不同遗漏特征的补全设计]('+LINK+')。拟比较ID表、全base区域候选与不补全；先来源、后选择器。**纯理论，未实施或测试**，默认不变。\n')
    edit('LOCAL_CODEX_START.md','更新于2026-10-24；','更新于2026-10-27；')
    edit('LOCAL_CODEX_START.md','E174–185及本次整理为本地工作；','E174–186及本次整理为本地工作（E186仅设计）；')
    edit('LOCAL_CODEX_START.md','## 当前结论与边界\n\n',
        '## 当前结论与边界\n\n[E186设计]('+LINK+')及[s-target](s-target.md)记录新的讨论方案：ID表/全base区域检索/不补全，先验证候选来源再做选择器；未实现、未训练、未测试。最近实测诊断仍为E185，正式性能仍为E183。\n\n')
    edit('LOCAL_CODEX_START.md','请报告当前默认、最新E185局部几何与E184诊断、E183实测Recall/QPS、费用、证据限制及尚未实施的下一问题。',
        '请报告当前默认、E185局部几何与E184诊断、E183实测Recall/QPS、费用、证据限制，以及E186尚未实施的适配设计和来源优先验证顺序。')
    edit('experiment_history/README.md','更新于2026-10-24。最新诊断是',
        '更新于2026-10-27。最新理论设计[E186](186_adaptive_completion_design_v1.md)未实施；最新诊断是')
    edit('experiment_history/README.md','| [185_manifold_residual_probe_v1.md]',
        '| [186_adaptive_completion_design_v1.md](186_adaptive_completion_design_v1.md) | E186：不同遗漏特征的补全来源与预算适配设计（纯理论） |\n| [185_manifold_residual_probe_v1.md]')
    card='''# E186：不同遗漏特征的补全来源与预算适配设计

2026-10-27，用户讨论“根据数据特征不同采用不同残差补全，改进适配不同数据集的新方案”。本轮完成理论设计与验证顺序，状态**THEORY_ONLY_UNIMPLEMENTED_UNTESTED**。没有新ANN/GT/训练/构图/QPS；默认E99 GT10保持，最新正式性能E183、离线测量E185不变。

设计收敛为两个候选来源与不补全：重复遗漏目标适合固定ID表；具体ID源覆盖不足时，提出独立全base几何分区/倒排后端，按q及主结果R预测值得补查的区域，在其中重新检索真实base点，原metric精算合并。区域级遗漏标签允许提出训练残差源外ID，但可迁移性和成本优势均待验证。全base收录不是无限预算覆盖承诺。

先验证新来源，再验证R条件化相对同后端q-only的增量，最后数据集级配置选择，逐query选择器后置。初步pilot提案COCO/Deep、K100、L100/200/400；SIFT/GIST/Web/Y/Flickr保留扩展反例，后续正式真实K1/K100。动作允许不补；完整费用对比附近更大L的GT10，不能以相同精算候选量冒充同费用。

历史差异：E174/E175从旧残差候选作种子在同NSG上一跳，E176细条件仍为固定ID表；新候选要求独立来源和区域内query检索。IVF/PQ、候选分类、adaptive probing已有前作，不主张组件本身新颖；实质研究对象是主结果条件化的剩余区域选择及可支付性。新接口、后端和选择器均未实现，也没有新未曝光确认角色或已分配运行预算。

'''
    card+='[完整设计](../'+LINK+') · [状态](../'+REL+'/state.json) · [修改前快照](../'+REL+'/source_before/) · [下一阶段目标](../s-target.md)。旧E174–185科学产物/失败记录与seal保持原件，不恢复旧runner。\n'
    (REPO/'experiment_history/186_adaptive_completion_design_v1.md').write_text(card)
    (R/'README.md').write_text('# E186：适配不同遗漏特征的补全设计\n\n[完整设计](design_zh.md) · [状态](state.json)。纯理论、未实现、未测试，无新训练/GT/ANN/QPS；当前默认不变。文档修改前快照在source_before，科学原件保护与链接核验见delivery_validation.json。\n')
    print('Synchronized E186 theory-only design; no experiments')
if __name__=='__main__':main()
