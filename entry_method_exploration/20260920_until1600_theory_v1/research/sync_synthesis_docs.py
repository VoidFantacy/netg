import json,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
rel='entry_method_exploration/20260920_until1600_theory_v1'
def prepend(name,text):
 p=ROOT/name;old=p.read_text();head,body=old.split('\n\n',1);assert text not in body;p.write_text(head+'\n\n'+text+'\n\n'+body)
assert (R/'reviews/synthesis_source_before.json').exists()
summary=f'''2026-09-20 **限时理论综合：阶段完成，待16:00截止验收**。E107–E111未找到稳定GT10替换，原Web soft/Y hard及生产E99保持。GT10是固定GT权重下的闭式方向估计；自适应H入口已经贡献明显系统收益，画像还影响小图可检索性，有限池多入口没有一般单调保证。真实区域覆盖翻倍未转成Web召回收益，首展开修复未稳定超过单入口，排名核心证书跨数据覆盖不足。另4次合成调用验证固定几何、改变图可反转入口效用；补充分层同分条件，原GT/Recall及E111的15条同query违例不改。本限时段2,797,056真实NSG、6合成、4路由小图、0新GT/底图/梯度训练/held-out；E108提供54配置/162轮完整wall，未形成跨集质量速度替换。[综合报告]({rel}/report.md) · [理论与条件]({rel}/research/learning_objective_and_search_contract.md) · [综合记录107](experiment_history/107_timebox_theory_synthesis.md)。'''
prepend('summary.md',summary)
prepend('spec.md',f'''2026-09-20限时研究工具已实现且与生产隔离：E107初始化因素、E108普通小图完整wall、E109完美代理门、E110首展开fork、E111排名核心标签及完整违例审计。新增[四次合成图依赖核验]({rel}/research/graph_dependence_v1/verify.cpp)复用冻结E107内核，0真实数据搜索；[综合表生成器]({rel}/research/build_synthesis_tables.py)只读取冻结CSV/日志，输出报告表与成本JSON。真实指标仍K1/K100、CPU15/线程1，生产API、GT、底层图和默认不变。E111同分条件文字修正及前件见[修正记录]({rel}/reviews/theory_scope_correction.json)；这是数学范围补充，未改搜索或评分。''')
prepend('s-experiment.md',f'''2026-09-20 **E107–E111理论综合已交付阶段报告**，截止验收待16:00；没有新增E112性能试验。固定几何的两图反例4合成调用通过，K1 ID与核心保留条件分层修正，所有原阶段与负点封存。累计2,797,056真实NSG/6合成/4路由小图/0新GT或训练，默认保持。[综合记录107](experiment_history/107_timebox_theory_synthesis.md) · [报告]({rel}/report.md)。''')
p=ROOT/'s-target.md';parts=p.read_text().split('\n\n');assert parts[1].startswith('E111[');assert parts[2].startswith('2026-09-20当前用户授权');assert parts[3].startswith('E109已完成')
parts[1:4]=[f'''2026-09-20当前用户目标持续到北京时间16:00。E107–E111阶段检验、图依赖反例、理论范围修正与[综合报告]({rel}/report.md)已完成；当前只做证据审查、文档和截止验收，15:50禁止新搜索，16:00交付。没有待运行训练/ANN/GT/构图队列；原Web soft/Y hard与生产E99保持。''',f'''后继研究优先回答：固定大图和真实raw-IP有限预算下，什么不依赖在线GT的信息，能预测可索引入口的净搜索收益，并保留基线质量及完整wall？先给可检验的图/查询/预算条件、反例与跨数据覆盖，再判断同监督的简单模型和MLP/双塔/RL。E109两个区域代理、E110首展开候选、E111当前m64/100证书均按门停止，不降低门槛、不扩m/路径/seed/ef或转选单个数据集继续。E106及旧WFree/QMLP版本也不重启。[理论证据与边界]({rel}/research/learning_objective_and_search_contract.md) · [前作条件]({rel}/research/literature_scope.md)。后文为历史接续，当前状态以这两段为准。''']
p.write_text('\n\n'.join(parts))
history=ROOT/'experiment_history/107_timebox_theory_synthesis.md';assert not history.exists()
history.write_text(f'''# 107｜E107–E111限时理论综合

2026-09-20，13:05:42–16:00的理论→方法→冻结核验研究；阶段结果已完成，最终截止状态以[父状态](../{rel}/state.json)为准。本条是跨阶段综合，不是E112或新正式性能试验。

GT10固定权重方向目标有闭式最优解；当前证据将H自适应入口、画像精确质量、普通小图恢复能力和有限池多入口竞争分开。没有稳定替换原默认。E109完美区域代理未过跨数据门，E110首展开修复未稳定超过单入口，E111保守证书在Yandex覆盖不足。

后续四次冻结内核合成执行表明，相同几何和GT在两张强连通有向图上可出现入口优劣反转；范围限任意有向图，不宣称toy是NSG构图产物，也不否定固定图上的可学习性。图中包含两个合成cycle，不计为数据集索引构建。

E111后数学审查修正：核心与外部严格分离仅保证成员保留，指定GT1 ID返回还需内部第一名无并列或GT一致的并列规则。原文前件与理由保存，冻结阶段报告、GT、Recall及15条违例保持；这些违例都来自同一条query的逐字重复向量。不能用0.024414pp的单query边界解释大部分旧失败。

本限时段2,797,056真实NSG、6次合成kernel调用、4张普通路由小图，0新底层图/GT/梯度训练/held-out/生产或默认变更。E111生成图派生诊断标签；E108有54配置/162轮单线程完整在线wall。含加载搜索进程累计2888.65秒，编译/准备/派生/分析另计，历史输入成本未知部分不置零。

默认仍Web GT10-soft-t1、Yandex GT10-hard及生产E99；E103仍是最新完整五数据集前沿。截止后无自动训练、补网格或部署队列。

[完整报告](../{rel}/report.md) · [成本台账](../{rel}/results/cost_ledger.json) · [图依赖反例](../{rel}/research/graph_dependence_v1/report.md) · [理论修正](../{rel}/reviews/theory_scope_correction.json) · [最终验收](../{rel}/reviews/completion_audit.json)。
''')
p=ROOT/'experiment_history/README.md';text=p.read_text();needle='| [106 排名核心证书]';assert needle in text;p.write_text(text.replace(needle,'| [107 限时理论综合](107_timebox_theory_synthesis.md) | E107–E111综合、图依赖反例及同分范围修正；默认保持，非新性能试验 |\n'+needle,1))
(R/'research/working_notes.md').write_text('''# 限时理论研究工作记录

2026-09-20 13:05:42–16:00（北京时间）。E107–E111及综合推导均已完成；当前仅证据审查与截止验收，没有在运行的搜索或训练。最终时间边界以[父状态](../state.json)为准。

[综合报告](../report.md)将GT10的闭式方向目标、H自适应入口收益、画像的小图可检索性、多入口首展开竞争与实际Recall分开。没有稳定新方法替换，原Web soft/Y hard及生产E99保持。

| 阶段 | 当前结果 |
|---|---|
| [E107](../stages/e107_initialization_factorial/report.md) | 初始化因素144点完成；单位H入口已有明显收益，多入口无一般单调保证 |
| [E108](../stages/e108_unit_hub_online/report.md) | 三控制54点/162轮完整wall；UnitHub无跨数据替换 |
| [E109](../stages/e109_perfect_proxy_gate/report.md) | fit完美代理未过跨数据门，不训练 |
| [E110](../stages/e110_first_expansion_intervention/report.md) | 同三入口首展开干预有机制信号，未稳定超过单入口，停止候选 |
| [E111](../stages/e111_rank_core_certificate/report.md) | 条件证书覆盖不足；同query重复向量ID边界完整保留，停止监督 |

新增[图依赖合成反例](graph_dependence_v1/report.md)4次原kernel调用通过，不读取真实数据；原E107的2次另保留。核心保留与指定GT1返回所需同分条件已[分层修正](retained_target_reachability.md)，原文和冻结E111原件均保留。

理论入口：[学习目标与搜索合同](learning_objective_and_search_contract.md)、[概率解释](probabilistic_profile_interpretation.md)、[目标几何](target_geometry_derivation.md)、[区域后验](coverage_posterior_derivation.md)、[保分数导航等价性](score_preserving_navigation_equivalence.md)、[文献条件](literature_scope.md)。这些基础推导未声称论文首次性，尚未形成新的可部署方法。

累计2,797,056真实NSG、6合成调用、4普通路由小图；0新GT/底层图/梯度训练/held-out/生产变更，E111有图派生标签。4M/2GiB上限、15:50禁止新搜索、16:00交付保持。不因剩余时间扩m/路径/seed/ef或更换网络继续试。
''')
manifest=R/'reviews/synthesis_document_update.json';assert not manifest.exists();manifest.write_text(json.dumps(dict(created_unix=time.time(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),root_files=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/107_timebox_theory_synthesis.md'],deadline_closeout_pending=True),ensure_ascii=False,indent=2)+'\n')
print('Synthesis documents synchronized; deadline closeout remains pending.')
