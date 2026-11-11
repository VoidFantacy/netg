#!/usr/bin/env python3
from pathlib import Path
import csv,json,re,hashlib
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];REL=R.relative_to(REPO).as_posix()
def rows(n):return list(csv.DictReader((R/f'analysis/{n}.csv').open()))
def main():
 guard=json.loads((R/"reviews/live_docs_binding.json").read_text())
 for name,digest in guard.items():assert hashlib.sha256((REPO/name).read_bytes()).hexdigest()==digest,"Concurrent document edit: "+name
 points=rows('points');paired=rows('paired');comp=rows('discrete_comparisons');p={(x['dataset'],x['method'],int(x['L'])):x for x in points};z={(x['dataset'],x['method'],int(x['L'])):x for x in paired};blocks=[x for x in comp if x['method'].startswith('BLOCK-')];dom=sum(bool(x['dominated_by_GT_L']) for x in blocks);speed=sum(float(x['target_speed_delta_pct'] or '-999')>=2 and x['target_speed_three_rounds_positive']=='True' for x in blocks);gain=sum(float(x['budget_recall_delta_pp'] or '-999')>=.05 for x in blocks);verdict=f'24个硬预算区域点中{dom}个被实测GT10同时覆盖Recall与QPS；速度筛选通过{speed}点、预算召回筛选通过{gain}点。'
 table=['| 数据 | 方法L200 | Recall@100 | 完整QPS | ΔRecall pp | 完整耗时增加 |','| --- | --- | --- | --- | --- | --- |']
 for ds,label in [('coco','COCO'),('deep10m_l2_v1','Deep10M')]:
  for m in ['GT10','B32','REG-R','OPT-R','BLOCK-R512','BLOCK-R2048','BLOCK-R8192','BLOCK-C2048']:
   a=p[ds,m,200];b=z.get((ds,m,200));table.append(f"| {label} | {m} | {float(a['recall_pct']):.4f}% | {float(a['qps']):.2f} | {float(b['recall_delta_pp']):+.4f}"+f" | {float(b['extra_time_pct']):+.2f}% |" if b else f"| {label} | {m} | {float(a['recall_pct']):.4f}% | {float(a['qps']):.2f} | — | — |")
 deep_old=z['deep10m_l2_v1','REG-R',200];deep_block=z['deep10m_l2_v1','BLOCK-R2048',200];a=p['deep10m_l2_v1','REG-R',200];b=p['deep10m_l2_v1','BLOCK-R2048',200]
 note=f"Deep L200：REG-R平均扫码{float(a['scanned_codes_per_query']):.1f}，BLOCK-R2048降至{float(b['scanned_codes_per_query']):.1f}；额外平均耗时{float(deep_old['extra_mean_us']):.2f}→{float(deep_block['extra_mean_us']):.2f}μs，Recall增量{float(deep_old['recall_delta_pp']):.4f}→{float(deep_block['recall_delta_pp']):.4f}pp。扫描减少与救回保留必须一起判断，不把访问次数下降当完整性能收益。"
 summary=f'''# ACSG 当前结论

更新于2026-10-28。**默认保留E99 GT10：WebVid GT10-soft-t1、Yandex GT10-hard。** 最新完成[E188补全费用与硬预算实验]({REL}/report_zh.md)：两集真实K100，正式100点/300完整单线程轮，另100点/300轮校准。预定矩阵已收口，无待恢复队列；可靠Recall–QPS研究目标尚未完成。

**{verdict}** 工程省费与硬预算的作用应分开看，当前不据此统一替换GT10。完整图表见[六页PDF]({REL}/ACSG_补全成本与硬预算实验_20261028.pdf)。

## 本轮实际结果：固定L200

{chr(10).join(table)}

QPS是本轮同一二进制的三轮中位数，包含正常分配、GT10路由/主搜、补全、六数组复制和销毁；不拼接旧绝对QPS。完整耗时增幅为QPS_GT10/QPS_method−1，不等于QPS降幅。

## 成本与有效候选

{note}

OPT-R两集三L全部10K的ID/score/route与原REG-R逐字一致；其速度差是工程实现收益，不自动成为对GT10的改进。分段诊断在校准L200上显示Deep扫描/堆维护较大，COCO粗路由较大。legacy诊断复用扫描临时缓冲，不能当原完整wall的严格拆解；正式QPS不包含阶段计时器。

BLOCK-C2048以预算内实际净救回和费用为目标；相同预算的BLOCK-R2048为对照，所有正负结果均见报告。原REG-R共同96个PQ候选，新块法每区域48，总共96，跨后端不能解释为纯扫码量因果。全库新来源与可靠净收益仍是两个判断。

## 校准角色修正与证据限制

原协议将旧16K B32放入末4K配置选择，但该4K已用于B32表训练，六项原选择均为B32并在Deep呈现强表内收益。正式矩阵前保留[原选择]({REL}/selection_freeze.json)，另冻[角色修正]({REL}/calibration_role_correction.md)与[修正选择]({REL}/corrected_selection_freeze.json)：B32继续作为正式参考，自动校准选择排除它。模型、预算和正式100点均未改。修正六项均选择更大L GT10，正式表现见[校准选择检验]({REL}/analysis/selected_validation.csv)。不能用这4K批准旧B32泛化或部署。

新模型前12K fit/后4K cal；旧GT10可能使用过合法fitquery。正式10K不参与本轮选择，但历史曝光，非新盲确认；三轮不是三份独立质量样本。仅COCO raw-IP/Deep squared-L2、真实K100，K1/其他五集未测本新方案，无逐query门控或完整主搜状态复用。

## 失败定义、核验与成本

失败始终是单query Recall@100<10%，即0–9命中。改善、脱离失败、成员救回/损伤、源外救回分别统计；不能用平均Recall提升替代严重失败修复。源为原完整16K训练遗漏并集，稀少尾部不作普遍规律。

全部timed返回/三轮SHA、真实主包补全oracle、逐query硬上限、旧包一致、第二份stdlib集合统计、原metric分数抽检和冻结身份核验已完成。第二实现由同一执行者完成，不称独立人员审查。原E187 689文件封存不变。块后端增加内存，benchmark同时装载两种布局；suite包含内部wall，不能相加；B32计数占位0不是0精算。详细成本与限制见[报告]({REL}/report_zh.md)。

## 既有证据与接续

七集两K综合证据仍为[E183](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)；E184/E185为几何关联诊断，不能给流形因果或免费在线净收益准入器。E187旧来源pilot保留历史原件。

[实现合同](spec.md) · [下一门](s-target.md) · [历史索引](s-experiment.md) · [100点]({REL}/analysis/points.csv) · [成对救损]({REL}/analysis/paired.csv) · [实际预算对照]({REL}/analysis/discrete_comparisons.csv) · [核验]({REL}/reviews/results_audit.json)。
'''
 (REPO/'summary.md').write_text(summary)
 target=f'''# ACSG 后续研究问题

更新于2026-10-28。目标仍为可靠Recall–QPS综合改进，默认E99 GT10保持。E188已完成正式100点/300轮及校准100点/300轮，没有待恢复矩阵。{verdict}

## 当前判断与停止边界

工程省费已通过返回逐字一致核验；硬预算确实限制了访问量，但需要同时付出候选覆盖/实际救回损失。完整结果见[summary](summary.md)和[E188报告]({REL}/report_zh.md)。本轮固定参数收口，不按曝光test继续改预算/块大小/模型到通过。旧E187及原E188选择文件保持历史身份。

原B32校准角色有训练重叠，已在正式矩阵前修正自动选择资格；不能用其表内收益决定未来部署。COCO旧B32的正式取舍与Deep固定表的来源不足仍须分别看，不将所有残差补全一律否定。

## 下一门（提案，未启动）

1. 先判断可否减少重复的辅助路由成本：研究利用GT10已产生的入口/主返回摘要，离线建立小范围的块候选关系，避免每次给全部1024粗代表评分；新来源应仍可覆盖旧ID表外目标。需同时测来源覆盖损失和完整wall，不假定复用信息免费。
2. 研究单位访问的实际救回密度。E188块内固定PQ筛选和每区48候选仍可能丢掉少数关键目标；任何新的排序/块组织须说明实质变化，固定预算并对照现有最强GT10/B32与E188，不能用更大扫码量换局部Recall冒充净收益。
3. 主搜索候选/距离缓存只有在现有接口和生命周期确认后才实现；已有R分数复用不等于完整可恢复状态。先衡量缓存维护代价，再判断收益。
4. 下一次自动选择B32必须使用新的合法校准角色，或另建未包含校准标签的表；旧16K表不能在自身训练遗漏上选择。继续保留不补全动作。逐query门控只有在收益异质性和低成本特征已有依据后再研究。

下一轮如执行须新协议/冻结身份、角色、预算和停止点，充分测量附近GT10 L，使用完整单线程wall。精确等Recall未测则写未测；实际离散阈值对照和插值描述分开。新确认角色不得参与选模型或追加预算。

## 泛化与指标

目前两集K100不能替代K1与其余五集，正式推广需覆盖SIFT/GIST/WebVid/Yandex/Flickr等反例。几何关联不是流形因果或净收益规则。失败继续严格为单query Recall@100<10%（0–9命中），成员/查询救损分开，稀少尾部不作普遍保证。

从[LOCAL_CODEX_START.md](LOCAL_CODEX_START.md)接续；本轮已有范围完成，不自动启动新队列。

<a id="2026-10-03-新对话接续入口"></a>
'''
 (REPO/'s-target.md').write_text(target)
 spec=REPO/'spec.md';s=spec.read_text().replace('### 4.2 已测费用与尚未实现的省费方案','### 4.2 E187费用边界与后续实现').replace('当前区域法固定选2区域并完整扫描','E187区域法固定选2区域并完整扫描').replace('上述省费方向均未实现，本次只在','这些方案在E187当时尚未实现，并在').replace('### 4.3 E188实验实现（已冻结，正式结果待出）','### 4.3 E188实验实现与实测合同')
 s=s.replace('当前进度见[state]','完成状态见[state]');anchor='## 5. 指标、计时与证据';s=s.replace(anchor,f'E188完成正式100点/300轮、校准100点/300轮。原B32包含末4K校准训练标签，原六项选择保留为角色失配诊断；正式前另冻[角色修正]({REL}/calibration_role_correction.md)，自动选择排除旧B32，正式参考仍保留它。未改变模型、预算或100点矩阵。新模型实际救回标签为单区域预算1024码/48候选的合并后GT100净增量，费用模型只估区域可变工作；固定粗路由/LUT等仍计完整wall。原REG-R诊断复用扫描工作缓冲，正式原REG-R调用旧路径。全部真实包、扫码/块代表/精算计数及三轮身份见[analysis]({REL}/analysis/)。\n\n'+anchor);spec.write_text(s)
 pth=REPO/'s-experiment.md';s=pth.read_text().replace('最新正式性能为E187两集K100来源pilot','最新正式性能为E188两集K100费用与硬预算实验');marker='| E187 |';s=s.replace(marker,f'| E188 | 补全分段费用、等价省费与硬访问预算 | 正式100点/300T1；硬预算{dom}/24点被GT10覆盖，默认不变；保留校准角色修正 | [卡片](experiment_history/188_completion_cost_budget_v1.md) |\n'+marker,1);pth.write_text(s)
 card=f'''# E188：补全费用、等价优化与硬访问预算

2026-10-28，用户在现状/费用方案讨论后授权“可以，开始实验吧”。独立目录实现并完成COCO raw-IP/Deep10M squared-L2真实K100：正式100点/300完整T1轮、校准100点/300轮；不改原base/图/GT10/metric/主核。默认E99 GT10保持。

{verdict}

{note}

分段诊断区分粗路由/特征/LUT/扫码/精算/合并；legacy诊断复用扫描缓冲，不能当原完整wall严格分解。OPT-R缓存模型/公共特征/工作空间，三L全部10K返回与REG-R逐字一致。块按PQ重构向量最大方差坐标递归划分，最多128点；每区域B/2码和48候选，B=512/2048/8192。BLOCK-C2048以12K实际预算内救回标签及非负费用模型选区，所有固定模型迁移L100/200/400。三档块法内部保持相同配额，原REG-R共同96对新每区48不属于纯扫码消融。

校准原六项均选B32，但旧16K表含末4K校准标签，属于角色设计缺陷；保留原协议/冻结/校准结果和选择，正式前另冻修正自动资格，B32仍正式参考，自动选择排除它。修正六项均选更大L GT10。没有按正式test调参或改矩阵，角色修正不包装成算法提升。

全部实际返回/三轮SHA、预算上限、旧包一致、真实主包合并oracle、stdlib二实现整数质量和float64原metric评分核验通过。E187 689文件seal保持。二实现为同一执行者，非独立人员审查。单图/模型、历史曝光test、训练角色局限和时间波动保留；无K1/其他五集新验证或逐query门控。

[完整报告](../{REL}/report_zh.md) · [六页PDF](../{REL}/ACSG_补全成本与硬预算实验_20261028.pdf) · [协议](../{REL}/protocol.md) · [角色修正](../{REL}/calibration_role_correction.md) · [冻结](../{REL}/freeze.json) · [核验](../{REL}/reviews/results_audit.json)。
'''
 (REPO/'experiment_history/188_completion_cost_budget_v1.md').write_text(card)
 pth=REPO/'experiment_history/README.md';s=pth.read_text().replace('最新正式pilot是[E187](187_adaptive_completion_pilot_v1.md)两集K100','最新正式实验是[E188](188_completion_cost_budget_v1.md)两集K100费用与硬预算');marker='| [187_adaptive_completion_pilot_v1.md]';s=s.replace(marker,'| [188_completion_cost_budget_v1.md](188_completion_cost_budget_v1.md) | E188：分段费用、等价省费与硬访问预算 |\n'+marker,1);pth.write_text(s)
 local=f'''# ACSG 当前接续入口

更新于2026-10-28；工作区`/data/netg/ACSG`，分支`research/state-20261002`，HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–188及整理主要是本地未提交工作，HEAD/旧远端不能代表这些完整产物。E188已完成，无待恢复矩阵。

## 阅读顺序

1. [AGENTS.md](AGENTS.md)；[summary](summary.md)→[spec](spec.md)→[s-target](s-target.md)→[s-experiment](s-experiment.md)。
2. [E188报告]({REL}/report_zh.md)、[六页PDF]({REL}/ACSG_补全成本与硬预算实验_20261028.pdf)、[100点]({REL}/analysis/points.csv)、[实际预算对照]({REL}/analysis/discrete_comparisons.csv)。
3. [校准角色修正]({REL}/calibration_role_correction.md)、[修正选择]({REL}/corrected_selection_freeze.json)、[正式选择检验]({REL}/analysis/selected_validation.csv)、[核验]({REL}/reviews/results_audit.json)。
4. 讨论旧方案从历史卡片进入原协议/源码/结果，不将旧状态当当前队列。

## 已收敛结论

{verdict} 默认E99 GT10保持。OPT-R返回与REG-R逐字一致，证明的是工程省费；块预算改变访问与候选取舍，必须对照完整wall和附近GT10 L。{note}

旧B32的末4K校准与16K训练表重叠，原选择存在角色缺陷；正式前修正选择资格，原件保持。原B32仍是正式参考，不能用表内校准收益批准泛化。测试历史曝光，两集真实K100，无K1/其他五集的新预算法证据。

## 可复制的接续提示词

```text
请接续/data/netg/ACSG，先只读核分支/HEAD及LOCAL_CODEX_START、AGENTS和四份主文档，再读E188报告与calibration_role_correction.md。
E188已完成正式100点/300轮及校准100点/300轮。默认E99 GT10保持，硬预算和等价工程优化的效果见真实CSV，不把扫码量下降或来源外救回等同可靠Recall–QPS改进。
旧B32包含末4K校准训练标签，原选择已保留，正式前另冻修正选择；无新盲确认。本轮模型/预算/矩阵已收口，不自动重跑、扩大预算、修改默认或改写旧seal。按我当前明确任务继续。
```

本轮修改前根文档在[E188 source_before]({REL}/source_before/)，科学与文档交付收据见[E188目录]({REL}/)。旧E187科学seal保持，旧根文档SHA只代表当时版本。
'''
 (REPO/'LOCAL_CODEX_START.md').write_text(local)
 print('PASS synchronized current docs and history')
if __name__=='__main__':main()
