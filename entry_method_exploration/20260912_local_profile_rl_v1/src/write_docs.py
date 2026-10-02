from shared import *
threads(8)
assert read(O/'reviews/training_verification.json')['status']=='PASS'
models=read(O/'results/training_analysis.json')['models'];gate=read(O/'results/method_gate.json');cost=read(O/'results/cost.json')
interpret=read(O/'reviews/interpretation.json');rel=str(O.relative_to(R));hist='experiment_history/32_local_profile_rl.md'
with (O/'results/feedback.csv').open() as f:feedback=list(csv.DictReader(f))
label={DS[0]:'WebVid',DS[1]:'Yandex'}
table='| 数据集 | 方法/seed | 选中步 | train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | monitor U |\n|---|---|---:|---:|---:|---:|---:|\n'
for m in models:
 table+=f"| {label[m['dataset']]} | {m['arm'].upper()}/{str(m['seed'])[-2:]} | {m['selected_step']} | {m['selected_train']['delta_recall_pp']:+.4f} | {m['selected_monitor']['delta_recall_pp']:+.4f} | {m['last_monitor']['delta_recall_pp']:+.4f} | {m['selected_monitor']['mean_U']:+.6f} |\n"
fbtable='| 数据集 | 方法/seed | 有命中变化的步/200 | 有命中变化候选/1600 | 更新hub数 | 每活跃hub更新中位数/最大 |\n|---|---|---:|---:|---:|---:|\n'
for m in feedback:
 fbtable+=f"| {label[m['dataset']]} | {m['arm'].upper()}/{m['seed'][-2:]} | {m['steps_with_hit_feedback']} | {m['candidates_with_hit_feedback']} | {m['active_hubs']} | {m['median_active_updates']}/{m['max_active_updates']} |\n"
wall=sum(d['seconds'] for d in cost['data']);rss=[d['peak_RSS_KiB']/2**20 for d in cost['data']]
cost_text=f"实际{cost['NSG']:,}次NSG（预留{cost['reserved_NSG']:,}/硬限2,200,000）、{cost['HNSW']:,}次HNSW、{cost['builds']:,}次普通构图，1600次更新。两个训练进程累计{wall:.3f}s，含加载/构图/反馈/写盘/验收；预检另计。峰值RSS约{rss[0]:.3f}/{rss[1]:.3f}GiB。CPU15、实际进程/OMP/BLAS/MKL1线程、方法及数据集串行。不是QPS。"
method='''固定E37 P/B/H和同train4096/monitor1024，独立H×16行系数：W_h=normalize(P_h+0.0625||P_hB||tanh(z_h)Bᵀ)，零参数直接复制原P字节。每次只改一行、其它当前画像不动。hub从原train三入口多重集合GT无关抽取，与uniform batch128独立；RL/ES同seed的hub/batch日程逐位相同。两臂σ.3、8候选、200步、原Adam步长，行局部计数作偏差修正。

每步真实重建当前图并run128，再逐个构建8个单行候选并run同128。奖励为原J的配对差，命中/总NDC/零命中/原漂移全部计入。8独立方向LOO-RL与4对方向ES同属高斯平滑黑箱目标，区别为估计器，不是两个不同模型族。共同当前J在两种梯度里抵消，单纯改名ΔJ不会改变估计器；新变量为局部动作与独立参数。E43自由度及额外当前基线成本都不同于E37，跨版本不是纯奖励消融。

checkpoint仍是确定均值，非采样最佳候选；每20步真实评估train512/monitor1024，按非零monitor U最高且graph NDC≤+1%选最早点。仅用monitor选择checkpoint，未按GT选hub或改变日程。最终输出是一份静态W/普通HNSW，线上仍原始query→一次HNSW top3→升序真实ID→原NSG，无在线优化模型。'''
validation='''双集预检恢复10240原基线输出，零参数/单行构造、共同baseline抵消、梯度/Adam和plain/原kernel通过。训练独立集合评分1,978,368个返回，核验12,800候选W hash、1600奖励/梯度/四分量/Adam更新、88完整checkpoint、16选中/末点模型及1024query三路parity。候选行用独立逐坐标公式核验，完整W由记录行字节重放，未调用ANN重训。原E37–E42/实际native/NSG依赖与query前冻结保持，根文档前件独立保存。无新GT和原validation/held-out读取/hash；保护旧隔离开发产物的字节读取不混为新开发。'''
status='COMPLETE_LOCAL_PROFILE_RL_'+('MONITOR_SIGNAL' if gate['status'].startswith('GO_') else 'STOP_MONITOR_GATE')
report=f'''# E43 固定背景的局部画像RL/ES

2026-09-12，状态`{status}`，门`{gate['status']}`。用户持续推进至20:00的总目标另由[下一阶段](../../s-target.md)跟踪；本阶段八次训练已完成。

{interpret['conclusion']}

## 实现与控制

{method}

[协议](protocol.md)、[锁定配置](config.locked.json)、[训练源码](src/train.py)、[缓存诊断补充](analysis_addendum.md)。两数据集/seed没有按结果增补epoch、σ或batch。

## 完整结果

{table}

正负及末点均保留。R为Recall@10，表中百分点相对当前GT10锚点；train512/monitor1024只是历史fit内分区，均有历史使用，非盲测或端到端性能验证。全G/L/失败/NDC见[质量CSV](results/quality.csv)。

![确定均值训练曲线](figures/learning_curves.png)

## 反馈及诊断

{fbtable}

{interpret['mechanism']}

![反馈与hub覆盖](figures/feedback_coverage.png)

候选梯度与确定更新不同：未对所有更新后的均值在该步原batch补测，不能从画像位移推断实际收益。逐query半批次/方差仅为固定方向条件分析，漂移项另列，不包括方向采样噪声；不能把分量范数相加当贡献百分比。

## 门与后续

预锁门要求每数据集RL与ES各至少一seed选中monitor ΔRecall>0、U>0且graph NDC≤+1%。实际[{gate['status']}](results/method_gate.json)。{interpret['next_step']}

默认保持WebVid GT10-soft-t1 / Yandex GT10-hard；旧E37开发门、E41局部+4无损和E42条件责任各自保留。本阶段无新cal/audit/QPS，不能由monitor正值推断RL额外价值或泛化优势。

## 成本、验证与原件

{cost_text}

运行期间为保持原余盘合同，曾在CPU8归档可再生成环境字节码；这是短暂辅助I/O，训练wall不作无干扰速度对比，见[资源记录](resource_note.md)。全部实验原件和源码保留。

{validation}

[完整训练模型](results/training_analysis.json)、[逐步反馈](results/steps.csv)、[实际调用](logs/jobs.json)、[成本](results/cost.json)、[独立重放](reviews/training_verification.json)、[完成审计](reviews/completion_audit.json)、[最终验收](reviews/final_audit.json)。所有已完成输出保留，runner拒绝覆盖。
'''
assert not (O/'report.md').exists();(O/'report.md').write_text(report)
# Retain the in-progress history and root documents before final synchronization.
snap=O/'reviews/docs_during_training';snap.mkdir()
for n in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md',hist]:shutil.copy2(R/n,snap/n.replace('/','__'))
history=f'''# 32. E43 固定背景的局部画像策略优化

2026-09-12，`{status}`，`{gate['status']}`。[协议](../{rel}/protocol.md)、[报告](../{rel}/report.md)、[配置](../{rel}/config.locked.json)、[验收](../{rel}/reviews/final_audit.json)。用户授权持续推进至20:00，本阶段八次真实训练与独立重放完成。

{interpret['conclusion']}

{method}

{table}

{fbtable}

{interpret['mechanism']}

{cost_text}

{validation}

{interpret['next_step']}

本阶段没有新开发/QPS或默认替换结论；旧E41局部信号与E42条件责任不被覆盖。原进行中版本在本阶段reviews/docs_during_training保存。[全质量](../{rel}/results/quality.csv)、[反馈](../{rel}/results/feedback.csv)、[逐步](../{rel}/results/steps.csv)、[独立核验](../{rel}/reviews/training_verification.json)、[预定门](../{rel}/results/method_gate.json)、[成本](../{rel}/results/cost.json)。
'''
(R/hist).write_text(history)
index=(R/'s-experiment.md').read_text();lines=index.splitlines()
lines=[f'| E43 局部画像RL/ES | 原P/B/H，一次一行系数动作，同日程/预算两臂双seed完成 | `{status}`；{interpret["index_result"]}，默认保持 | [32 局部画像](experiment_history/32_local_profile_rl.md) |' if l.startswith('| E43 ') else l for l in lines]
index='\n'.join(lines)+'\n';index=index.replace('最近完成记录已为E42责任控制','最近完成记录已为E43局部训练');(R/'s-experiment.md').write_text(index)
summary=f'''# ACSG 当前结果摘要

2026-09-12，最近完成E43局部画像RL/ES，`{status}`，门`{gate['status']}`。[报告]({rel}/report.md)、[历史32]({hist})、[验收]({rel}/reviews/final_audit.json)。用户20:00持续研究目标尚在推进，阶段完成不等于总目标结束。默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

## 当前结果

{interpret['conclusion']}

{table}

{interpret['mechanism']}

{fbtable}

所有值来自历史train/monitor，checkpoint由monitor选择；局部正值不构成泛化、独立性能或RL额外价值。具体G/L/零命中/NDC见[全质量]({rel}/results/quality.csv)。

## 执行与边界

{cost_text}

{validation}

共同当前J在LOO/ES梯度中抵消；本阶段实质改变为一次只改一行及H×16独立参数，不能将跨E37差异全部归因奖励。E42目标必要/充分与背景交互、E41 WebVid42091单改+4无损局部信号保留。当前无新cal/audit/validation/held-out/QPS；最近完整性能评测仍为E37。

{interpret['next_step']} 详细接续见[s-target](s-target.md)。
'''
(R/'summary.md').write_text(summary)
spec=(R/'spec.md').read_text().replace('E42被移除画像责任控制已验收','E43局部画像训练已验收').replace('局部画像策略优化（E43，已实现/预检通过，训练进行中）','局部画像策略优化（E43，完整训练与核验已完成）').replace('全部训练独立复算尚待训练终态，不能登记为已完成。','全部训练已完成并通过独立复算：1600更新、12,800候选W身份、88 checkpoint、16导出与完整返回均核验。')
spec+=f'''\n[独立审计]({rel}/src/audit_training.py)按保存的行字节重放整份W，以独立公式核验局部画像、GT集合评分、ΔJ、四分量/LOO/ES与局部Adam、日程/选点。额外条件query噪声分析只用原反馈，不更新模型或门。[汇总]({rel}/src/summarize.py)输出完整质量、反馈、预锁monitor门及图表。全部1992256 NSG/14510图/1600更新已完成，0新GT或本阶段开发/QPS；具体效果见summary。\n'''
(R/'spec.md').write_text(spec)
(O/'conclusion.md').write_text(interpret['conclusion']+'\n\n'+table+'\n'+interpret['mechanism']+'\n\n'+interpret['next_step']+'\n')
dump(O/'reviews/document_sync.json',dict(status='WRITTEN_PENDING_FINAL_AUDIT',stage_status=status,files=['summary.md','spec.md','s-experiment.md',hist],next_target_requires_update=True))
print('E43 report/history/current summary written; s-target remains to sync to the evidence-led next stage')
