"""Synchronize E25 facts while preserving all prior documents in source_before."""
import shutil
from common import ROOT, RUN, DATASETS, read, dump, identity, sha
from analyze import LABELS, METHOD_LABELS

STATUS='SELECTIVITY_NOT_GENERALIZED_NO_FORMAL_GO'
REL='entry_method_exploration/20260910_selective_profile_gate_v1'


def main():
    assert read(RUN/'reviews/immutable_integrity.json')['status']=='PASS'
    assert not (RUN/'reviews/doc_updates.json').exists()
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md']:
        assert sha(ROOT/name)==sha(RUN/'source_before'/name),name
    prior=RUN/'source_before/experiment_history/README.md';prior.parent.mkdir(exist_ok=True)
    assert not prior.exists();shutil.copy2(ROOT/'experiment_history/README.md',prior)
    r=read(RUN/'results/analysis.json')
    summary=f'''# ACSG 当前实验总结

> 更新至2026-09-10夜间。最近完成E25选择性保留E24改道。实现见[spec.md](spec.md)，接续见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。

## 当前总体结论

**E25未得到跨数据集稳定保留收益、减少损失并改善端到端性能的选择规则。WebVid有小幅质量修复，额外路由成本抵消了收益；Yandex主规则减少受损时丢掉了大多数有效改道。** 状态`{STATUS}`，本版本全部预定阶段已收口。

A0固定E24 matched Fast20K/GT1硬，A1固定E24按旧cal选定的WebVid GT10软T0.0162011385、Yandex GT10硬。BaseGate用旧路由7特征、按需再跑路由A1；DualGate固定两路13特征。二选一在主图搜索前完成，随后只执行一次原NSG，不在线probe或restart。

## 保留收益与避免损失

预设目标：有效query×L事件保留R≥75%、受损事件避免A≥25%，正命中保留Rh≥75%、负损失避免Ah≥25%，且净命中≥max(0,always-A1净命中)。下表合并L64/128，全部query保留分母。

| 数据集 / cal主规则 | 分段 | R | A | Rh | Ah | 净命中 vs A0 / always-A1 | 目标 |
|---|---|---:|---:|---:|---:|---:|---|
'''
    for ds in DATASETS:
        kind=r['datasets'][ds]['primary_frozen_on_cal']
        for stage in ['cal','audit','validation']:
            m=r['datasets'][ds]['splits'][stage]['gates'][kind]['pooled_L64_L128']
            ratio=' | '.join(f'{m[k]*100:.2f}%' for k in ['R','A','Rh','Ah'])
            summary+=f"| {LABELS[ds]} / {METHOD_LABELS[kind]} | {stage} | {ratio} | {m['net_delta_hits']:+d} / {m['always_A1_net_delta_hits']:+d} | {'PASS' if m['target_met'] else 'NOT_MET'} |\n"
    summary+='''
WebVid validation离25%门槛仅差约一个受损事件、两个命中损失单位，不能据此否定整个机制；主要问题是audit不稳定、质量增量小且付出时间。Yandex主规则在cal已失败，只按协议完成反证，不是部署推荐。

## 单线程五点的完整主结果

相对本轮同时重测的A1/E24；每点三次独立warm/plain，QPS报告中位数。

| 数据集 / cal主规则 | L | ΔRecall pp | ΔQPS % |
|---|---:|---:|---:|
'''
    for ds in DATASETS:
        kind=r['datasets'][ds]['primary_frozen_on_cal']
        rows=sorted([m for m in r['comparisons'] if m['dataset']==ds and m['method']==kind and m['reference']=='e24'],key=lambda m:m['L'])
        for m in rows:summary+=f"| {LABELS[ds]} / {METHOD_LABELS[kind]} | {m['L']} | {m['delta_recall_pp']:+.3f} | {m['qps_percent_change_medians']:+.2f} |\n"
    summary+=f'''
非主规则及NSG/Fast30K/Fast20K全部对照保留。两个门控×两数据集×五L相对A1的20项Recall差，描述性95%配对query bootstrap区间全部跨0；没有一点同时Recall提高且三轮对应QPS均提高。粗L网格的非支配点不直接转成等Recall加速结论。

## 机制与成本解释

- 8192 fit query中真正提供非零监督的只有WebVid1081、Yandex401；命中权重ESS约556.85/190.96。权重最高1% query贡献27.47%/57.79%的信号，尤其Yandex效应稀疏集中。
- WebVid DualGate weighted AUC从cal0.6132到audit0.4923、validation0.5693；Yandex BaseGate为0.5552→0.3754→0.4962。求解器已收敛；分段波动尚不能分离为抽样或分布变化的因果结论。
- fit若oracle允许按L分别选择，仅比固定query两L同一选择多98/30个命中，不能把主要失败归于模型不读L。免费oracle没有线上QPS。
- L128路由单测A1→Base/Dual：WebVid6.532→16.076/19.140μs/query，Yandex4.368→6.542/10.223。Base新增3次画像重评分且选新才再跑路由；Dual固定两路和6次重评分。所有计算计入独立端到端wall，分项不相加作QPS。

## 实际执行与验收

fit为router_train后20K固定抽8192；cal[2048,4096)、audit[4096,6144)各2048，配对L64/128。两数据集各30候选、合计12个凸模型，四规则及全部输入/候选/代码/binary在audit前冻结；audit只报告，随后才读历史validation前2000。E24画像见过fit query，各池有历史开发使用；held-out未打开。

六方法×五L×两数据集共60正式点、每点三次计时全部完成。124点219584个输出独立评分；四条原曲线80000个validation输出与E24的ID、距离bits、入口和route/graph NDC逐位相同。门控等于所选策略、全部新增收费、五L选择/logit/入口/微型图一致均通过。

真实调用1,089,152，修复预留0，另合成5144；全部查询实际线程1、CPU15。真实搜索进程1227.50s含加载/构建/预热/计数/I/O，最高RSS10.193GiB；不能换算QPS。63项上游hash、冻结文件与cal选择独立复核通过。原GT/QGT/NSG/E24从零成本未新测。

## 权威证据与接续

- [E25复盘](experiment_history/14_selective_profile_gate.md)、[完整报告]({REL}/report.md)、[全部原值]({REL}/results/tables.md)、[曲线]({REL}/figures/recall_qps.svg)、[收益保留图]({REL}/figures/retention_harm.svg)。
- [分析]({REL}/results/analysis.json)、[成本]({REL}/results/costs.json)、[选择冻结]({REL}/models/frozen_before_audit.json)、[审计]({REL}/reviews/immutable_integrity.json)。

用户另授权夜间深入分析并可适当探索，最终汇总从9月11日北京时间07:00开始。E25不扩模型或阈值；若做直接相关的单路画像收缩对照，须另立版本/协议/预算。2A等其它研究方向仍在s-target，旧C/probe大队列保持停止。E24局部画像信号保留[历史13](experiment_history/13_gt_topk_profiles.md)身份，所有旧资产保留。
'''
    spec=(ROOT/'spec.md').read_text()
    first=spec.splitlines()[2]
    spec=spec.replace(first,first.replace('固定H的GT-topK画像模块及双数据集60点单线程比较已完成验收','E25两固定画像的搜索前选择、真实配对监督及60点三次单线程计时已验收'),1)
    spec+=f'''

## 两固定画像的搜索前选择 v1（2026-09-10夜间）

独立[E25协议]({REL}/protocol.md)与实现不修改原Fast builder、E24画像或原ACSG kernel。A0/A1均为冻结的三个真实入口策略，选择只发生在主搜索前；以下接口不具备probe、restart或结果合并能力。

- [initialize.py]({REL}/src/initialize.py)绑定原资产hash与hub映射，生成fit-only hub表`[log1p ESS0, log1p ESS1, 1-cos(W0,W1)]`；导出fit8192/cal2048，audit及validation输入必须在模型冻结之后才准备。
- [gate_policy.hpp]({REL}/src/gate_policy.hpp)的`SelectivePolicy`包装冻结`Policy`；`inspect`返回13维GT-free特征与A0/A1三元组，`choose`返回完整所选路由、logit、选择bit及两路调用/特征内积计数。BaseGate只读前7维、选A1才调用新路由；DualGate每query两路。每query实际额外3/6次原IP distance重评分计入route NDC，raw query不改变原NSG metric。
- [train.py]({REL}/src/train.py)用真实配对命中差的P/N权重拟合线性logistic；fit全行标准化、clip±6、float64 Newton、截距不惩罚，三λ和五个fit阈值固定。JSON必须包含`feature_set/mean/scale/beta/bias/threshold`，预测按顺序float64求和并以`>=`选择A1。线上模型不读L或GT。
- [evaluate.cpp]({REL}/src/evaluate.cpp)支持`nsg/fast30k/fast20k/e24/base_gate/dual_gate`六种方法，单线程独立plain wall三次各自预热，全批count及前16条原wrapper在timer外。计时包含在线路由、特征、预测、排序、原kernel和预分配输出写入；GT在所有raw输出和计时结束后评分。L128的route-only/graph-only单测不相加为端到端wall。
- [jobs.py]({REL}/src/jobs.py)绑定源码/binary/config身份、CPU15、实际进程线程/RSS、进程时间、磁盘/输出和真实NSG调用上限；失败job保留完整预留。诊断point收费`2N+16`，三次wall点收费`7N+16`，L128分项额外`2N`；正常1,089,152、修复16,384、合成≤10,000。
- [verify_outputs.py]({REL}/src/verify_outputs.py)独立重评分、对照被选策略的ID/距离bits/graph NDC、复算全部路由收费和13维特征、比较C++与离线预测。[audit_report.py]({REL}/src/audit_report.py)只重建已缓存的两次真实搜索，不给反事实结果填写在线QPS。

Artifact包括逐query输入row IDs、GT100形状/来源、两路真实结果与特征、全部候选/优化轨迹、audit前冻结manifest、三次独立wall、派生门控输出与机制分析。A0/A1的W、H、metric、图、split或L身份变化会使相应配对标签/特征/模型/结果失效，必须独立重建；不得只改模型路径继续复用旧标签。只改离线分析解释不允许改冻结权重、阈值或原输出。

实现验收已通过：124点219584输出独立GT评分，四条原曲线80000个validation输出与E24逐位相同；门控选中策略/完整费用、五L决策及相应微型图一致、冻结/预算/线程/63项上游资产hash均通过。模型及方法效果见[summary](summary.md)与[E25报告]({REL}/report.md)，不由实现验收升级为性能GO。
'''
    target=(ROOT/'s-target.md').read_text();intro=target.splitlines()[2]
    target=target.replace(intro,f'2026-09-10夜间。最近E25已完整执行并收口，状态`{STATUS}`：WebVid局部修复未抵消双路成本，Yandex主规则丢失大多数有效改道。用户本轮要求夜间深入分析，9月11日北京时间07:00开始汇总，提前完成可适当探索；该授权只支持直接相关、有独立协议/目录/预算的小探索，不扩E25网格。E24第一方向仍保留其已完成身份；全部长期方向保留第4节，不是一张自动执行队列。',1)
    target=target.replace('## 1. 已完成第一方向给出的判断','## 1. 最近E25及第一方向给出的判断\n\nE25实际结果见[历史14](experiment_history/14_selective_profile_gate.md)和[完整报告]('+REL+'/report.md)。A0/A1三入口配对标签、两种低成本标量门控和两数据集60点三次单线程wall均完成；audit/validation未共同保住75%收益、避免25%损失，全部单点Recall差区间跨0。不能据此否定效用可学习，也不支持继续盲目加门控容量。\n\n直接相关的小探索可先检验离线收缩E24相对A0的画像偏移，让在线仍使用一套图/一次路由；此时会产生第三套入口，必须额外统计新产生的受损，不能套用E25二选一关系。当前仅提出独立版本边界，尚未自动执行；若实际启动，先锁定alpha候选、开发split、真实配对/墙钟预算和停止条件。',1)
    target=target.replace('## 3. 后续研究建议及进入边界','## 3. 后续研究建议及进入边界\n\nE25已封存，不修改lambda、阈值、样本或预算。下述2A是较长期研究建议；夜间授权的小型单路画像收缩若启动，单独建版本，不等于启动2A全H标签、重启旧utility residual/probe/C或自动执行其余队列。',1)
    target=target.replace('- 已完成第一方向：','- 最近完成E25：[协议]('+REL+'/protocol.md)、[固定选择]('+REL+'/models/frozen_before_audit.json)、[完整报告]('+REL+'/report.md)、[历史14](experiment_history/14_selective_profile_gate.md)。\n- 已完成第一方向：',1)
    experiment=(ROOT/'s-experiment.md').read_text()
    heading='| E24 固定H的GT-topK硬/软画像 |'
    row=f'| E25 两固定画像的选择性改道 | fit8192真实A0/A1三入口配对；Base/Dual门控、cal选/audit报、双数据集validation60点各三次单线程wall | `{STATUS}`；WebVid局部修复不抵双路成本，Yandex主规则丢失大多数收益；本版本收口 | [14 选择性改道](experiment_history/14_selective_profile_gate.md) |\n'
    experiment=experiment.replace(heading,row+heading,1).replace('当前最近实验已为E24','当前最近实验已为E25').replace('十三份详细卡片','十四份详细卡片')
    directory=(ROOT/'experiment_history/README.md').read_text().replace('\n\n| [13','\n| [13')
    anchor='\n## 写入规则'
    row='\n| [14 两固定画像的选择性改道](14_selective_profile_gate.md) | E25：真实配对监督、Base/Dual门控、全部60点三次单线程wall；未建立跨数据收益保留/损失减少与性能优势 |\n'
    directory=directory.replace(anchor,row+anchor,1)
    directory=directory.replace('\n\n| [14','\n| [14')
    updates={'summary.md':summary,'spec.md':spec,'s-target.md':target,'s-experiment.md':experiment,'experiment_history/README.md':directory}
    for name,content in updates.items():(ROOT/name).write_text(content)
    dump(RUN/'reviews/doc_updates.json',{'status':'WRITTEN_PENDING_LINK_AUDIT','files':[identity(ROOT/name) for name in updates],
         'original_root_documents_preserved':True,'new_history_card':identity(ROOT/'experiment_history/14_selective_profile_gate.md')})
    print('E25_DOCS_SYNCHRONIZED',flush=True)


if __name__=='__main__':main()
