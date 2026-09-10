#!/usr/bin/env python3
"""Publish this completed experiment's measured handoff; does not run experiments."""
from common import DATASETS, ROOT, RUN, dump, read, sha

assert read(RUN/'reviews/result_verification.json')['status']=='PASS'
assert read(RUN/'state.json')['status']=='RESULTS_VERIFIED_REPORT_PENDING'
result=read(RUN/'results/summary.json')
short={'webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex-IP'}
status='EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN'
prefix='entry_method_exploration/20260910_three_entry_rank_v1'
summary=f'''# ACSG 当前实验总结

> 更新至2026-09-10。当前最近实验为E23三入口收益排序探索。实现见[spec.md](spec.md)，接续边界见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 当前结论

**E23已完成：小幅Recall正信号，尚无明确整体QPS优势。** 固定真实入口，匹配Fast三个互异入口，用真实三入口条件收益训练Fast锚定完整W，并与同目标rank8对照。两数据集各validation2000、一个QGT构建、L64/128/256/400/800、单线程，NSG/Fast30K3/Fast20K3/Full3/Rank8-3共50点全部完成。状态`{status}`，不自动追加模型、rank、seed或计时。

完整W的固定训练目标优化到位，且目标值低于同λ的rank8，但未取得一致的最终搜索优势；Yandex五点Recall均是rank8高于完整W。不能把更低训练损失直接写成方法性能更好，也没有依据丢弃低秩或直接加MLP。

## 相对matched Fast20K-3的五点变化

每格为ΔRecall百分点 / ΔQPS百分比；每点一次独立plain wall，小幅差异不作稳定加速或显著性解释。匹配相同20K画像输入、H、三个入口、HNSW参数/seed和入口消费顺序。

| 数据集 | L | Full-3 | Rank8-3 |
|---|---:|---:|---:|
'''
for ds in DATASETS:
    for L in [64,128,256,400,800]:
        cells=[]
        for family in ['full','rank8']:
            x=next(x for x in result['comparisons'] if x['dataset']==ds and x['family']==family and x['baseline']=='fast20k_3' and x['L']==L)
            cells.append(f"{x['delta_recall_pp']:+.3f} / {x['delta_qps_percent']:+.2f}%")
        summary+=f'| {short[ds]} | {L} | {cells[0]} | {cells[1]} |\n'
summary+=f'''
L128原值：WebVid Fast20K→Full为74.260%/1997.81QPS→74.420%/2009.57QPS，零命中54→52；Yandex Fast20K→Rank8为89.720%/1960.73QPS→90.010%/1958.90QPS，零命中38→34。原Fast30K和NSG始终另列；例如WebVid Full对原Fast30K的+0.430pp包含matched Fast20K本身的+0.270pp，新增学习为+0.160pp，不能全部归于学习器。

## 实际执行与证据边界

- 原raw-IP/NSG不变，QGT seed20260828；一向量对应一真实hub，在线raw query→HNSW direct3→原kernel。matched Fast20K与学习模型按真实ID升序消费三入口，原Fast30K保留原heap顺序。模型不输入L，每query入口跨五L完全不变。
- fit20K×24个逻辑组合：两数据集合计96万逻辑标签，缓存后88万实际标注搜索，另2304次parity。Full/rank8各三个λ，共12候选；cal1024选λ，audit1024不参与选择；双数据集全部模型冻结后才读取validation2K。该开发池是历史开发数据，held-out未打开。
- Full在WebVid/Yandex均选λ=10/0.1，rank8相同。两数据集cal都选新候选；audit中Full均小幅正值，Yandex rank8小幅负值；最终validation结果全部保留，没有按validation换模型。
- 全部100000个validation输出独立GT评分、单线程及原kernel/plain/count验收通过；NSG/Fast30K共40000个query输出、入口与距离bits和E22逐位相同。
- 标签子进程58.89秒、训练137.45秒、fit-probe/cal95.68秒、audit29.05秒、最终五点比较381.64秒。均含各自过程工作，不能称查询QPS。完整W六个模型核心拟合约7.35秒、rank8约125.78秒。
- 本轮复用旧全H single标签提出候选；按当前提议器从零复现还依赖3272万份single标签。88万新增联合标注不是完整从零成本；exact GT/QGT/原图和single子集专属重建成本未新测。
- graph NDC变化很小，Yandex路由NDC略增。fit中观察到同一query的a/b偏好随另外两个入口改变，说明条件排序标签存在不能同时满足的部分；未将它定量归因为全部性能差距。一个构建、validation2K、单次wall不支持正式性能GO。

## 权威证据

- [E23详细复盘](experiment_history/12_three_entry_rank_exploration.md)、[完整报告]({prefix}/report.md)、[全部50点原值]({prefix}/results/tables.md)、[Recall–QPS图]({prefix}/figures/recall_qps.svg)。
- [结果JSON]({prefix}/results/summary.json)、[指标CSV]({prefix}/results/metrics.csv)、[配对比较CSV]({prefix}/results/comparisons.csv)、[成本账]({prefix}/results/costs.json)。
- [输出核验]({prefix}/reviews/result_verification.json)、[模型冻结]({prefix}/models/frozen_before_validation.json)、[最终审计]({prefix}/reviews/final_audit.json)。

E22保留`EXPLORATORY_NO_OVERALL_FAST_GAIN`历史身份，原大矩阵不恢复；C仍按E21停止，无C联动。所有原源码、图、GT、标签、模型和结果保留。
'''
(ROOT/'summary.md').write_text(summary)
(ROOT/'s-target.md').write_text(f'''# ACSG 当前状态与接续边界

2026-09-10。用户授权的E23三入口排序探索已完成；实测结果见[summary.md](summary.md)，实现见[spec.md](spec.md)，详细证据见[E23复盘](experiment_history/12_three_entry_rank_exploration.md)。

## 当前判断

`{status}`：相比matched Fast20K三入口，有小幅Recall增益；完整W没有一致胜过rank8，QPS未形成明确整体优势。特别是Yandex，rank8五L Recall都高于Full，也都高于matched Fast20K，但多数点QPS基本持平或略低。该版本已完成并收口，不将它作为已验证的Fast替代品。

## 已完成的授权范围

[协议]({prefix}/protocol.md)：双数据集fit20K、cal1024、audit1024；96万逻辑真实三入口标签、88万实际标注调用；Full/rank8各三λ、共12个候选；按cal选择后冻结；validation各2K、单构建、NSG/Fast30K3/Fast20K3/Full3/Rank8-3、五L、单线程、每点一次warmup/独立plain wall和timer外完整NDC/输出核对。50点及100000个query输出验收完成，held-out未打开。

一份模型适用于全部五L。训练标签在L128下产生，模型本身不输入L；所有方法每query入口跨L一致。cal选中Full/rank8在WebVid均λ10、Yandex均λ0.1，validation没有参与重新选择。

## 若继续研究，先解决什么

当前实验已把三个问题分开：完整W固定目标能够充分优化；低秩虽目标较高却在Yandex最终搜索更好；真实联合收益到静态top3分数的代理仍有差距。下一步优先检查联合收益目标与最终top3选择的对应关系，以及训练/部署的泛化差异。已观察到同一query、同一a/b的偏好随context反转，但未证明这是全部差距的原因。

保留Full作优化参考、rank8作正则化对照。共享hub端MLP会改变参数共享和优化，但对固定H仍导出固定W，不能自动消除这些条件偏好冲突；query端MLP或策略梯度也尚无本轮实证。任何后续选择需说明针对哪项已观测问题、与E23的实质区别及小型验证范围，再建立新协议；本轮不自动增加MLP、rank、λ、seed、标签或计时。

今后比较继续优先单构建、小validation与必要对照；正式查询始终单线程，显式OMP/OpenBLAS/MKL=1并核验实际线程，一次只运行一个被测方法。最终结论取完整Recall–QPS，NDC、训练损失或少量同L Recall仅作诊断。完整从零离线成本还需包含当前候选提议依赖的旧single标签，不能只报88万新增联合调用。

旧E22大矩阵、额外基线队列均不恢复。C继续`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`，不做C3/C4或联动；D和效用树不自动切换。原数据、源码、图、标签、模型、日志和结果不清理或覆盖。
''')
spec=ROOT/'spec.md';text=spec.read_text()
text=text.replace('新增独立三入口排序模块，标注与合成验收通过，训练运行中','独立三入口排序模块已完成双数据集五点单线程探索验收')
text=text.replace('合成五L/精确top3/三唯一入口和多线程配置拒绝验收已通过；真实最终评测状态见summary。',
    '合成五L/精确top3/三唯一入口和多线程配置拒绝验收已通过；真实50点的100000个query输出独立GT复核通过，四个路由模型在五L下序列化HNSW图及逐query入口均一致。NSG/原Fast30K的40000个query输出与E22逐位回归通过。cal诊断v1的warmup计数元数据错误由独立evaluate_v2修正，数值结果/模型选择不变，原件保留；正式validation使用v2。实测性能与范围见summary。')
spec.write_text(text)
index=ROOT/'s-experiment.md';text=index.read_text()
old='| E23 真实三入口收益排序 | 固定真实入口，原kernel联合标签，Fast锚定完整W/rank8同目标；双数据集88万实际标注搜索及独立全标签评分完成 | 训练运行中；尚无新性能结论，后续cal选择与validation2K五点比较范围已锁定 | [12 三入口排序](experiment_history/12_three_entry_rank_exploration.md) |'
new=f'| E23 真实三入口收益排序 | 固定真实入口，88万实际组合标注、Full/rank8各三λ；双数据集validation2K五L、五方法、单线程50点全部完成 | `{status}`；Full目标更优但最终未胜rank8，Yandex rank8五L Recall均高于matched Fast；未形成明确QPS优势，本版本收口 | [12 三入口排序](experiment_history/12_three_entry_rank_exploration.md) |'
assert old in text;text=text.replace(old,new)
text=text.replace('`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`；没有新标签、训练、ANN或评测；不能将推荐当作已验证改进',
    '该只读原件保留`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`；后续用户另授权继任实验E23，不能将后续执行回写为原研究已运行')
index.write_text(text)
print('HANDOFF_UPDATED',flush=True)
