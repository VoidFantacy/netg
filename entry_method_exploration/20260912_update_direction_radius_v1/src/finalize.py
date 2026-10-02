from shared import *
import re,ast
threads(8);resources();check(O/'reviews/prequery_freeze.json');check(O/'reviews/protected.json');check(O/'reviews/native_dependencies.json');r=read(O/'results/analysis.json');v=read(O/'reviews/verification.json');cost=read(O/'results/cost.json');assert v['status']=='PASS' and cost['NSG_calls']==3416
status='COMPLETE_UPDATE_DIRECTION_RADIUS_DISCRETE_STEP_AND_DAMAGE'
tab='| 数据集 | 原M gain/loss/net | Adam r/4 | Adam r/2 | Adam r | 最佳候选方向1/4 | 最佳候选方向1/2 |\n|---|---:|---:|---:|---:|---:|---:|\n'
for ds in r['datasets']:
 tab+='| '+('WebVid' if ds['dataset']==DS[0] else 'Yandex')+' | '+' | '.join(f'{ds["tags"][t]["gain_hits"]}/{ds["tags"][t]["loss_hits"]}/{ds["tags"][t]["net_hits"]:+d}' for t in ['M','D25','D50','D100','B25','B50'])+' |\n'
core='''步长不足已有直接因果控制支持，但“统一放大”不是解决方案。WebVid原20状态的M全部质量空；在12个有原净正候选且M质量空的状态中，沿同一Adam方向放大成功9个，朝候选的中间点成功8个，其中7个两者都成功、2个只Adam方向、1个只候选方向、2个只有完整原候选端点成功。Yandex对应4个状态放大Adam全部成功，候选中间点成功2个。这是在原方向/原状态的真实干预，证明许多原确定步幅未跨搜索响应边界，不是完全没有局部机会。

代价也被直接测到：WebVid r/4累计gain15/loss30，r/2为35/32，r为50/28；Yandex r/4和r/2都是15/0，r却变19/33并新增3个零命中query。所有200系数控制均没有发生clip，因此不是边界裁剪制造了这些差异。不同状态/半径诊断合计不能成为一份新模型，有限半径成功或失败也不能外推所有方向。结论是需要按真实反馈接受/拒绝更新，不能仅凭此把学习率全局调大。
'''
next_text='''立即进入E52连续有限候选择优提交对照，独立协议已经写明：原RL两seed/两集/σ.3/200×8/full4096，原J在合法候选+不动中择优，真实重建提交图身份，下一状态重新route/补测。它明确是贪心局部搜索，不包装为RL，直接检验E50所见机会能否转成连续静态画像和新query收益。E50原接续门已通过，E51不另加门阻挡。

若连续对照有可用信号，可进一步独立检验带真实反馈步长接受的RL：保留原八候选梯度方向，只在预定r/4、r/2、r及不动之间选更新；需要新训练和完整成本，不把本轮三个反事实拼成结论。当前这一RL接受策略未实现/未训练。

用户最终比较仍必须落实：21:15前停止会延误最终窗口的新方法工作，冻结cal预选最佳候选，与NSG/Fast/FastGT10-hard同批五L五轮比较QPS/Recall/零GT10失败率，WebVid另保留soft匹配起点。21:35停止训练、21:40停止新查询、22:00收口。
'''
body=f'''# E51 固定状态的更新方向与半径

2026-09-12，`{status}`，40原E47 RL状态/200新反事实完成，0连续训练。

{tab}
表格为每集20固定状态累计gain/loss/net hits，不能当可部署Recall。

{core}
## 实际控制与验收

原两seed/step20/40/…/200全部状态，半径r为同状态原八Gaussian系数扰动L2范数中位数，GT无关；D沿实际Adam系数方向，B沿原J-best候选方向（明确有同状态GT择优），画像公式和普通HNSW builder/原NSG/IP/L128保持。C和M实际build/route并逐位恢复，五个未知反事实真实测量。280图状态，每状态完整train4096真实route，完整三入口不变才复用原C NSG；当次route NDC刷新。

实际3416 NSG=728变化返回+2688三路parity，HNSW1148672、普通build280；56代表物理图/896三路parity，WebVid/Yandex进程20.375/32.565s。独立1310720集合评分（含40原best端点）、327680 C/M位恢复、200半径/方向/画像scalar复核、全部缓存键/patch、物理图SHA与parity通过。0新monitor/cal/audit查询/评分、新GT、优化更新。复用原5120query文件/checkpoint物理上含历史monitor记录，不能声称文件只含train；范围澄清记录保留。

源/输入/E37–E50全SHA保护；默认仍WebVid GT10-soft-t1 / Yandex GT10-hard。最近完整性能E49未形成双集前沿增益，本控制不改写这一结论。

## 接续

{next_text}

[协议](protocol.md)、[200控制及端点](results/points.csv)、[40状态分类](results/contexts.csv)、[成本](results/cost.json)、[核验](reviews/verification.json)、[输入范围说明](reviews/input_scope_note.md)、[图](figures/direction_radius.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+next_text+'\n')
hist=body.replace('# E51 固定状态的更新方向与半径','# 40. E51 更新方向与半径');hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_update_direction_radius_v1/'+m.group(1)+')',hist);(R/'experiment_history/40_update_direction_radius.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E50 候选到均值转化');s=s[:i]+'| E51 更新方向/半径 | 原E47 RL40状态，Adam方向三半径与最佳候选方向两中间点 | `COMPLETE_UPDATE_DIRECTION_RADIUS_DISCRETE_STEP_AND_DAMAGE`；放大救回9/12与4/4空更新机会，最大半径也伤害Yandex；3416 NSG | [40 步长方向控制](experiment_history/40_update_direction_radius.md) |\n'+s[i:];p.write_text(s.replace('三十九份详细卡片','四十份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [40 更新方向与半径](40_update_direction_radius.md)：E51实测跨离散边界的机会与放大损伤，接续真实反馈接受控制。\n')
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E51，`{status}`。[报告](entry_method_exploration/20260912_update_direction_radius_v1/report.md)、[历史40](experiment_history/40_update_direction_radius.md)。

{tab}
{core}
实际3416 NSG/1148672 HNSW/280build/200新反事实，1310720集合评分/200半径方向核验通过。0连续训练；最近完整Recall–QPS仍E49，未形成双集前沿增益，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

接着E52同预算直接提交有效候选，协议已写明、尚未冻结训练。用户目标至22:00，并最终比较最佳候选与NSG/Fast/FastGT的QPS/召回/失败率，最终完整比较尚未执行，详见[s-target](s-target.md)。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E51完成，[历史40](experiment_history/40_update_direction_radius.md)。用户要求大胆假设、小心证明、持续至22:00，并最终比较最佳方法与NSG/Fast/FastGT三指标。

## 已有证据

{core}
E50全1600状态中，RL有净正候选而M质量空的比例Web86%/Yandex96%，J-best未放弃本批最佳净命中；直接提交控制门已通过。E48说明共享评分和邻接重建均有真实收益/损伤、两集主导不同，不能统一固定某因素解决。

## E52立即执行

[协议](entry_method_exploration/20260912_direct_candidate_commit_v1/protocol.md)已写，源码准备中、未冻结/未训练。4run（两集×原RL两seed）、原σ.3/200×8/full4096/原GT无关日程，合法候选+不动按原J择优，0Adam；所有新状态真实route/补测，提交W重新普通build验证拓扑身份。预计7212build/26276864 HNSW，NSG固定62976+真实候选变化；每run完整预留100000、总400000，不释放失败。新资源artifact256MiB/free8GiB，实际单线程CPU15/串行，启动按E47同RL时长保守估算，21:10前完成优先留最终窗口。原monitor选点规则保持，selected/last全物理图及完整checkpoint/parity审计，不能把E50反事实和当真实训练预期。

{next_text}
当前RL接受策略仅为后继设计，未实现；不得写成已有模块。最终[交付合同](entry_method_exploration/20260912_until2000_v1/final_comparison_contract.md)保持，Fast/GT身份已核对，当前E49 WebVid缺hard基线，不能宣称最终要求完成。
''')
p=R/'spec.md';s=p.read_text().replace('E51步长方向控制已冻结启动，连续提交尚未执行。','E51步长方向控制已完成验收，连续提交尚未执行。');s+='\nE51 [analyze_verify.py](entry_method_exploration/20260912_update_direction_radius_v1/src/analyze_verify.py)独立恢复200系数半径/方向与画像公式，1310720集合评分、327680 C/M端点位恢复及56物理图/896三路parity通过；实际3416 NSG/1148672 HNSW/280build。有限状态方向放大为因果控制，不是连续学习。E52直接提交控制仅协议完成，尚未训练；RL反馈步长接受仅后继设计，未实现。\n';p.write_text(s)
dump(O/'reviews/visual_review.json',dict(status='PASS',file='figures/direction_radius.png',method='Rendered gained/lost bars viewed, original mean and radius controls readable'))
dump(O/'state.json',dict(status=status,NSG_calls=3416,HNSW_calls=1148672,builds=280,optimizer_updates=0,campaign_complete=False))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/40_update_direction_radius.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(p.stat().st_size for p in files(O)),verification=v,cost=cost,campaign_complete=False))
freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots);print('E51 FINAL AUDIT PASS',flush=True)
