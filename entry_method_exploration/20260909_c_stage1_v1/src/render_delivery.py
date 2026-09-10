#!/usr/bin/env python3
"""Render a human-readable delivery from frozen observed statistics; no ANN or GT reads."""
from pathlib import Path
import json
V=Path(__file__).resolve().parents[1]
r=json.loads((V/'results/analysis_v1/report.json').read_text());points=r['points']
def name(p):return ('WebVid' if p['dataset'].startswith('webvid') else 'Yandex-IP')+f" L{p['L']}"
def table(header,rows):return ['| '+' | '.join(header)+' |','|'+'|'.join(['---']*len(header))+'|']+['| '+' | '.join(map(str,row))+' |' for row in rows]
lines=['# C 第一阶段实际执行报告','',
 '**结论：C0、C1全部通过，C2完成后停止当前冻结C配置。** WebVid两点通过common-cap headroom门，Yandex两点仅+0.230/+0.140pp，低于预注册+0.5pp。最终 `NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`。不进入C3，不运行C4，不扩模型/候选/B，不联动A+B。','',
 '## 1. C0协议锁与实际范围','',
 'paired Fast20K、QGT seed20260828、原IP和冻结NSG；CPU-only单worker，OMP/BLAS1，最大允许16线程。每dataset在drl_train前10K中PCG64 seed20260909不放回取2000行；这属于历史开发池，与paired后20K画像fit隔离，但不是新鲜held-out。前128条只做GT-free成本校准，前16条做C1真实验收，前4条smoke；没有增加不同query。','',
 '锁定checkpoint为完成33/65次邻接扩展（L64/128），全局额外graph-NDC cap B=1856。起始入口来自direct HNSW top3；独立top7调用的后四槽生成候选，去重不补位。每候选分别做natural insert与force-expand；每个分支只动作一次。候选真实距离计入B，两个路由调用各自付费。原位continue是相同cap下的继续，**不能把它误标为无cap完整Fast**。','',
 '见[协议](protocol.md)、[锁定配置](config.locked.json)、[lock SHA](protocol_lock.json)、[C0独立审阅](reviews/c0_protocol_review.md)、[状态身份展开](inputs/state_identity_contract.json)。后者由已绑定的图/base SHA和索引头明确原IP语义；不修改任何原始state。','',
 '## 2. C1实现与验证','',
 '独立state保存L+1有序pool、flag、有效长度、cursor/rewind、visited/expanded、query/入口/身份、预算及partial-row offset、有界history。原search_new源码与库不改。reference机械提取自冻结源码，只增加外部observer，并先与真原kernel比对；不以两个手写实现相互佐证。','',
 '最终synthetic v2：180组合，5961组断言，960个partial-row案例、159个force/natural控制、3个tie fixture全部通过；显式手算用例覆盖pool拒绝、插入后淘汰、保留时的完整后继扩展顺序。两真实图各16query×2L，共64条记录，无cappause/clone/serialize/resume的ID、float bits、NDC、完整扩展与距离调用顺序一致。原plain/count/trace一致，分支无污染、共享search_L改变不影响state。独立补充测试实跑精确cap后零距离自然结束、DC错误query重新绑定、partial序列化与终态no-op。','',
 '第一版synthetic也通过；v2增加防御式shape检查与显式边界证据，未修改C0动作或预算。非法初始ID只在新API拒绝，不对原kernel执行未定义越界输入。C1结果：[gate](results/c1_gate.json)、[synthetic](results/c1_synthetic_v2.json)、[WebVid](results/c1_webvid_v2.json)、[Yandex](results/c1_yandex_v2.json)、[独立kernel审阅](reviews/kernel_final_review.md)。','',
 '## 3. C2主结果：无条件均值与校正区间','',
 '每点N=2000；所有early-finished、无合法候选、visited和no-op query均纳入。主oracle只在continue与四个合法force中选最大Recall，ties先continue再冻结槽序。20K query-paired bootstrap，Bonferroni4族95%（每项98.75%）；+0.5pp实质门用精确累计增命中≥100判断。四点区间均正，但Yandex没有达到实质门。','']
lines+=table(['点','continue R@10','oracle R@10','Δ pp','校正CI pp','新增命中','点gate'],[[name(p),f"{p['continue_recall']*100:.3f}%",f"{p['oracle_recall']*100:.3f}%",f"{p['primary']['mean']*100:+.3f}",'['+', '.join(f'{x*100:+.3f}' for x in p['primary']['ci_bonferroni4_family95'])+']',p['integer_gain_hits'],'PASS' if p['gate_pass'] else 'FAIL'] for p in points])
lines+=['','## 4. 覆盖与oracle动作比例','',
 'effective指扩展轨迹或最终retset改变，严格质量改善另列。它不等于正Recall收益；force仅改变轨迹亦可算effective。已visited槽均映射continue，无额外动作距离。','']
lines+=table(['点','early %','no eligible %','所有force均语义no-op %','至少一个有效force %','oracle严格增益 %'],[[name(p)]+[f"{p['coverage'][k]*100:.2f}" for k in ['early_finished_fraction','no_eligible_fraction','all_force_no_op_fraction','any_effective_force_fraction','oracle_strict_quality_gain_fraction']] for p in points])
lines+=['','以下比例分母均为全部2000query，F0–F3对应固定四候选槽。','']
lines+=table(['点','continue %','F0 %','F1 %','F2 %','F3 %'],[[name(p)]+[f"{p['oracle_action_fractions'][k]*100:.2f}" for k in ['continue','force_0','force_1','force_2','force_3']] for p in points])
lines+=['','## 5. 实际graph NDC与envelope','',
 '每query每branch满足`total=prefix+suffix`、`suffix<=1856`。共同上限不是相同实际工作。下表为全部query实际graph NDC；逐query envelope min/max及所有9动作完整分布保存在[JSON](results/analysis_v1/report.json)及aligned CSV。','']
lines+=table(['点','continue均值','oracle均值','oracle中位','oracleP95','oracle最大','continue自然结束 %'],[[name(p),f"{p['ndc']['branches']['continue']['graph_ndc']['mean']:.3f}",f"{p['ndc']['oracle_graph_ndc']['mean']:.3f}",f"{p['ndc']['oracle_graph_ndc']['p50']:.1f}",f"{p['ndc']['oracle_graph_ndc']['p95']:.2f}",f"{p['ndc']['oracle_graph_ndc']['max']:.0f}",f"{p['ndc']['branches']['continue']['natural_finished_fraction']*100:.2f}"] for p in points])
lines+=['','oracle相对continue的ratio-of-means graph-NDC变化依次为 '+', '.join(f"{p['ndc']['oracle_vs_continue_ratio_of_means_minus_one']*100:+.4f}%" for p in points)+'；不是逐query比值均值，也不是完整routing+graph成本。','',
 'Fast3与额外candidate top7两次调用各自平均routing NDC：WebVid各129.6415、Yandex各111.2445；即新候选路由成本必须额外支付。所有样本的direct top3与top7前三槽一致，但起始策略仍使用独立direct top3。','',
 '## 6. Force相对同候选natural的机制描述','',
 '以下每槽均用相同candidate的force−natural，单位pp，全2000query均值；属于描述性次比较，不冒充主族显著性。','']
lines+=table(['点','F0−N0 pp','F1−N1 pp','F2−N2 pp','F3−N3 pp','natural oracle−continue pp'],[[name(p)]+[f'{x*100:+.3f}' for x in p['mechanism']['per_slot_force_minus_same_natural_mean']]+[f"{p['mechanism']['natural_oracle_delta_vs_continue']*100:+.3f}"] for p in points])
lines+=['','按主force oracle所选同一candidate对比其natural分支，平均差依次 '+', '.join(f"{p['mechanism']['force_oracle_winner_minus_its_same_candidate_natural']*100:+.3f}pp" for p in points)+'。该赢家条件比较有GT选择偏差，不能证明在线可学性；force oracle与natural oracle可能选不同e，二者差也不称纯机制效应。','',
 '## 7. Clone/state成本及时间边界','',
 '以下为单线程诊断中实测均值，单位微秒；JSON保存完整分布。clone为每物理branch的深拷贝，序列化/恢复用于诊断持久化，不是未来线上必需操作。state初始化含前三入口距离，prefix resume包含图搜索；没有把差值假称纯bookkeeping开销。','']
lines+=table(['点','clone μs/branch','序列化 μs/query','恢复 μs/query','初始化 μs/query','prefix resume μs/query','state bytes均值'],[[name(p),f"{p['clone_seconds_physical_branches']['mean']*1e6:.2f}"]+[f"{p['bookkeeping'][k]['mean']*1e6:.2f}" for k in ['state_serialization_seconds','state_deserialization_seconds','prefix_init_plain_seconds','prefix_resume_plain_seconds']]+[f"{p['bookkeeping']['serialized_state_bytes']['mean']:.1f}"] for p in points])
lines+=['','无资格alias明确复用同一continue计时，其输出materialization成本单列。每个物理branch另用plain DC独立计时，与count/trace完整终态相等，GT/hash/JSON/DC分配/clone在branch timer外。候选/clone/prefix/suffix wall都是诊断分项；没有独立整批方法QPS、正式Recall–QPS或Pareto GO。','',
 '主raw运行：WebVid38.728秒，Yandex58.824秒（包含装载、路由、clone、两种branch执行、检查及I/O；不含后续GT评分）。WebVid一分钟前完成，Yandex约57秒时1936/2000，按实际吞吐预计余约2秒。持续资源采样、执行命令、stdout均保存；静态输入hash在搜索计时外。','',
 '## 8. 停止与未运行','',
 'C2触发的是**双数据集四点实质headroom门失败**；不能写成“完全无空间”或把WebVid正信号抹去。Yandex仅9/6条query被oracle严格改善，虽校正区间为正，均值仍不足+0.5pp。实际候选覆盖很高，因此当前记录也不能简单解释为全部候选都visited。该结论仅否决冻结checkpoint/B/Fast3/四候选配置，不推出所有同状态策略无效。','',
 'C3 learner、state×reuse训练、query-only对照学习、restart/merge析因、C4正式QPS、validation/held-out、全H动作、多checkpoint、多步RL均未运行。A+B仍设计未实施；没有联动或synergy证据。停止后只做评分复核、文档与provenance校验，不再运行ANN。','',
 '原E14强负证据继续保留；C2的WebVid有限oracle正值不挽救旧chooser，更不证明C可学。未来若两边分别通过，仍必须在最终deployed micro A+B诱导状态重新cross-fit后才做{Fast,AB}×{off,policy-specific C}，正交互才称协同。','',
 '## 9. 实际命令与证据','',
 '[完整实际命令](commands.md)、[机器argv/UTC/退出码](logs/commands.jsonl)、[状态](state.json)、[原始WebVid](results/c2_main_webvid_v1/)、[原始Yandex](results/c2_main_yandex_v1/)、[正式统计JSON](results/analysis_v1/report.json)、[gate](results/analysis_v1/gate.json)。`bin/*build.json`绑定源码/静态依赖/可执行SHA，`source_before`保留dirty工作区与旧根文档/源码快照。']
(V/'report.md').write_text('\n'.join(lines)+'\n')
# Actual child commands, with exact cwd/env in machine ledger. Do not suggest overwriting old outputs.
seen=set();commands=[]
for line in (V/'logs/commands.jsonl').read_text().splitlines():
 j=json.loads(line)
 if j['label'] in seen:continue
 seen.add(j['label']);commands.append(j)
import shlex
cmd=['# 实际执行命令','', '以下为本轮已执行命令；输出采用拒绝覆盖策略，不能原路径直接复跑。工作目录均为`/data/netg/ACSG`。长搜索以`setsid`脱离交互终端，保留独立stdout/资源日志。每项精确argv、环境、UTC、退出码见[commands.jsonl](logs/commands.jsonl)。','',
 '最初输入准备及C0构建发生在durable launcher建立前，原始调用如下；其逐进程资源时间未单独记录，不补造：','',
 '```bash','cd /data/netg/ACSG','.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/prepare.py prepare',
 'bash entry_method_exploration/20260909_c_stage1_v1/src/build.sh calibrate > entry_method_exploration/20260909_c_stage1_v1/logs/build_calibrate.log 2>&1',
 '.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/prepare.py lock',
 '.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/extract_reference.py',
 '```','', '下面逐条为实际child命令，其中`OMP_NUM_THREADS`、`OPENBLAS_NUM_THREADS`、`MKL_NUM_THREADS`、`NUMEXPR_NUM_THREADS`均为1：','']
for j in commands:cmd += [f"- `{j['label']}`：",'','```bash',shlex.join(j['argv']),'```','']
cmd+=['stage控制调用（负责启动独立进程、budget reservation、持久日志和状态门）如下：','','```bash',
 '.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c1-gate',
 '.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c2-run c2_smoke_webvid_v1 webvid2_5m_light_v1 4',
 '.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c2-run c2_smoke_yandex_v1 yandex_t2i_official10M_ip_v1 4',
 '.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py smoke-gate',
 '.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c2-run c2_main_webvid_v1 webvid2_5m_light_v1 2000',
 '.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c2-run c2_main_yandex_v1 yandex_t2i_official10M_ip_v1 2000',
 '```','', '执行入口外围实际采用`setsid ... > logs/<label>.launch.log 2>&1 < /dev/null &`；child与资源日志另存同label，不以脱离终端代替完成标记。']
(V/'commands.md').write_text('\n'.join(cmd)+'\n')
