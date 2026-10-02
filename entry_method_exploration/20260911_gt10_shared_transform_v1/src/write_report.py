from setup import *
import csv,math,statistics
SHORT={DS[0]:'WebVid2.5M',DS[1]:'Yandex10M IP'}
def rows(name):return list(csv.DictReader((O/'results'/f'{name}.csv').open()))
def table(headers,data):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in data)
def f(x,n=3):return f'{float(x):.{n}f}'
def signed(x,n=3):return f'{float(x):+.{n}f}'
def main():
 allpoints=rows('all_points');dif=rows('validation_differences');interp=rows('interpolated_same_recall');dev=rows('development_diagnostics');training=rows('training_summary')
 verified=json.loads((O/'reviews/output_verification.json').read_text());modelcheck=json.loads((O/'reviews/model_verification.json').read_text());gates=json.loads((O/'results/performance_gate.json').read_text())
 selection={ds:json.loads((O/'models'/ds/'selection.json').read_text()) for ds in DS};teacher={ds:json.loads((O/'labels'/ds/'teacher.json').read_text()) for ds in DS};teacher_diag=json.loads((O/'results/teacher_diagnostics.json').read_text())
 profiles=['gt10_hard','linear','mlp','free'];stats=[]
 for ds in DS:
  dsname=SHORT[ds];anchors=[float(x['recall_pct']) for x in allpoints if x['stage']=='validation' and x['dataset']==dsname and x['method']=='gt10_hard']
  common=[]
  for r in anchors:
   if all(any(x['dataset']==dsname and x['method']==m and abs(float(x['recall_target_pct'])-r)<1e-8 for x in interp) for m in profiles[1:]):common.append(r)
  for m in profiles[1:]:
   xs=[x for x in interp if x['dataset']==dsname and x['method']==m and any(abs(float(x['recall_target_pct'])-r)<1e-8 for r in common)];gm=math.exp(statistics.mean(math.log(1+float(x['delta_qps_pct'])/100) for x in xs))-1 if xs else None
   ds_dif=[x for x in dif if x['dataset']==dsname and x['method']==m]
   stats.append(dict(dataset=dsname,method=m,common_anchor_recalls=common,geomean_interpolated_qps_delta_pct=None if gm is None else gm*100,min_interpolated_delta_pct=min(float(x['delta_qps_pct']) for x in xs) if xs else None,max_interpolated_delta_pct=max(float(x['delta_qps_pct']) for x in xs) if xs else None,positive_same_L_points=sum(float(x['delta_recall_pp'])>0 and float(x['delta_qps_pct'])>0 for x in ds_dif)))
 shared_go=[x['method'] for x in gates['methods'] if x['method'] in ['linear','mlp'] and x['dual_dataset_GO']]
 status='LOCAL_DUAL_DATASET_GATE_PASSED_REQUIRES_FRESH_VALIDATION' if shared_go else 'SHARED_TRANSFORM_EXPLORATION_COMPLETE_NO_FORMAL_GO'
 conclusion=dict(status=status,shared_GO=shared_go,common_anchor_comparison=stats,not_new_blind_validation=True,heldout_opened=False)
 dump(O/'results/report_conclusion.json',conclusion)
 out=['# GT10 共享入口变换：真实检索比较与方法判断\n']
 if shared_go:out.append('本轮有共享变换通过预设的本地双数据必要门槛，但测试切片具有历史使用，仍需要新的独立验证。下文报告完整曲线、负点与成本，不把局部实验升级为论文或部署结论。\n')
 else:out.append('本轮没有建立共享线性或小 MLP 优于原 GT10 画像的稳定双数据证据。默认保留原已冻结的 GT10 路线；下列实测曲线用于区分不同数据集、召回区间和方法的局部变化。模型已经训练并完成真实检索，结论不依赖训练损失或教师上界代替查询结果。\n')
 out.append('研究固定原始 query→一次 microHNSW top3→三个真实 hub→原 NSG。线性和 MLP 都只在离线生成入口向量；在线没有神经网络前向。测试覆盖两数据集、9个方法、5个 L，共90个正式点，每点3次完整 warm/plain 单线程端到端 wall。\n')
 out.append('文献部分提供机制和新颖性判断的依据；实测矩阵由这里列出的9种配置组成。硬件为Intel Xeon 6982P-C，16个逻辑CPU、约123GiB内存，正式查询固定CPU15/实际单线程；环境版本见[machine.json](reviews/machine.json)。\n')
 out.append('## 1. 主比较图\n\n![四个主方法的完整 Recall–QPS 曲线](figures/recall_qps_main.png)\n')
 out.append('点为实际 L64/128/256/400/800 的测试；QPS 取三次独立批次的中位数，误差线为最小/最大值。连线只连接测试点，纵轴为对数刻度；三次 wall 不增加 Recall 样本量。完整原始数值见 [all_points.csv](results/all_points.csv)，所有图表的工作簿见 [chart_data.xlsx](chart_data.xlsx)。\n')
 out.append('## 2. 哪个方法更好：分数据集和召回区间回答\n')
 out.append('先列L128的实际值作量级参照；选择方法仍需结合整条曲线。\n')
 out.append(table(['数据集','模型','Recall@10','QPS中位数','三次QPS范围'],[[x['dataset'],x['method'],f(x['recall_pct'])+'%',f(x['qps'],1),f(x['qps_min'],1)+'～'+f(x['qps_max'],1)] for x in allpoints if x['stage']=='validation' and x['L']=='128' and x['method'] in profiles]))
 out.append('下面以原 GT10 hard 的实测 Recall 点为参照，仅保留四个主方法共同覆盖的点，在线性 Recall–log QPS 坐标内插值，并计算速度比的几何平均。它用于概括本次粗网格的相对位置，是事后描述；既不是新增选择规则，也不是额外实测的等 Recall 点。区间之外不外推。\n')
 out.append(table(['数据集','方法','共同参照点数','插值QPS几何平均变化','这些点的变化范围','同L质量/速度同时提高'],[[x['dataset'],x['method'],len(x['common_anchor_recalls']),'无覆盖' if x['geomean_interpolated_qps_delta_pct'] is None else signed(x['geomean_interpolated_qps_delta_pct'],2)+'%','无覆盖' if x['min_interpolated_delta_pct'] is None else signed(x['min_interpolated_delta_pct'],2)+'% ～ '+signed(x['max_interpolated_delta_pct'],2)+'%',str(x['positive_same_L_points'])+'/5'] for x in stats]))
 out.append('\n本轮的具体推荐是继续保留WebVid原冻结GT10 soft、Yandex GT10 hard。共享linear在WebVid共同参照点的插值平均变化约+0.52%，在Yandex约−1.44%；MLP分别约+0.59%与−1.76%，没有形成双数据统一优势。free也没有提供更好的整体证据。\n')
 out.append('MLP的WebVid高召回局部信号值得单独保留：L400实测Recall为85.350%，比GT10 hard高0.240pp，QPS约持平；在GT10 hard的85.110%召回参照处，曲线插值速度比约+2.64%。这与L64双降、Yandex中间几个点下降同时成立，不能写成MLP整条曲线最好。\n')
 out.append('\n![相对GT10的插值速度差](figures/interpolated_speed.png)\n\n色带为三次对应插值速度比的范围，不是统计置信区间。原始完整曲线与此图一起读取，避免重叠曲线掩盖小幅变化。\n')
 out.append('\n预设门要求两数据集在0.90/0.95/0.98中至少两个共同覆盖的召回点上达到≥3%插值中位QPS提升、三次对应比值均>1，并无约定的明显前沿退化。覆盖不足时记录“未建立”，不更换目标点来补一个通过结论。全部门结果见 [performance_gate.json](results/performance_gate.json)，插值点和三次比值见 [interpolated_same_recall.csv](results/interpolated_same_recall.csv)。\n')
 out.append(table(['方法','数据集','可覆盖预设点','达到速度条件的点','明显退化点'],[[g['method'],d['dataset'],d['covered_targets'],d['passing_targets'],d['material_frontier_regressions']] for g in gates['methods'] for d in g['datasets']]))
 if any(not g['gate_applicable'] for g in gates['methods']):out.append('\n**门设计的覆盖限制：** 至少一个数据集的原GT10曲线没有覆盖两个预设目标，因此这一统一门在本轮不可充分检验。不能将它的“不通过”作为模型无效的证据，也没有事后改目标点。方法推荐另依据上面实际共同覆盖区间的比较、全部实测点和波动范围；本轮没有完成新的精确等Recall测量。\n')
 out.append('\nGT10 hard 是新模型的共同锚点；历史按 cal 冻结的正式画像仍分别是 WebVid GT10 soft、Yandex GT10 hard。下图保留 soft、GT1 hard、原 Fast30K 和 NSG，避免只在几个新模型里选一个相对不差者。原 Fast30K 的30K输入、seed100和旧入口顺序身份单列。\n\n![全部原基线与新模型](figures/recall_qps_all.png)\n')
 out.append('## 3. 完整五个 L 的增减与不确定性\n')
 out.append('以下所有差值均相对本批次 GT10 hard；pp 表示百分点。QPS 为同 L 的中位数之比，与等 Recall 加速不同。Recall 区间采用相同 query 的2000次配对 bootstrap，未做多重比较校正，也不包含不同图、训练种子或机器的不确定性。\n')
 for ds in DS:
  out.append('### '+SHORT[ds]+'\n')
  out.append(table(['L','方法','ΔRecall pp','95%区间','Δ同L QPS','Δgraph NDC','获益/受损query'],[[x['L'],x['method'],signed(x['delta_recall_pp']),'['+signed(x['ci_low_pp'])+', '+signed(x['ci_high_pp'])+']',signed(x['delta_qps_pct'],2)+'%',signed(x['delta_graph_ndc_pct'],2)+'%',x['improved_queries']+'/'+x['harmed_queries']] for x in dif if x['dataset']==SHORT[ds] and x['method'] in ['linear','mlp','free']]))
 out.append('\n![逐query配对 Recall 差](figures/recall_differences.png)\n\n正、负 query 同时保留，净命中恒等式为 gained_hits−lost_hits。新增零命中、挽救零命中和入口改变比例也保存在差值CSV中；没有用一个净正数隐藏其它查询受损。\n')
 out.append('## 4. 教师空间、模型拟合与实际检索\n')
 out.append('每个 fit query 的候选为两条原硬画像实际 HNSW3 并集补齐八个入口，枚举56个真实三入口搜索。教师先最大GT10 hits，再最小graph NDC。这是 GT 参与的 C8 内选择；既不是全H上界，也不能部署，更不构成等工作或QPS收益。\n')
 out.append(table(['数据集','原GT10 fit Recall','教师Recall','教师增量pp','原graph NDC','教师graph NDC','存在正命中空间的query'],[[SHORT[ds],f(teacher[ds]['baseline_gt1_gt10'][1]['hits']*10),f(teacher[ds]['teacher_hits']*10),signed((teacher[ds]['teacher_hits']-teacher[ds]['baseline_gt1_gt10'][1]['hits'])*10),f(teacher[ds]['baseline_gt1_gt10'][1]['ndc'],1),f(teacher[ds]['teacher_ndc'],1),f(teacher[ds]['improved_hits_fraction']*100,2)+'%'] for ds in DS]))
 out.append('\n训练后另作教师分组诊断，不增加搜索，也不用于改选择。下表区分有额外命中空间与原GT10已经达到C8最大命中的query；教师可能仍为了同命中下更低NDC而改变三入口。它说明标签构成，不能证明哪一组导致最终性能变化，因果区分需要新的控制实验。\n')
 out.append(table(['数据集','query组','行数','占fit比例','教师改变集合','平均同最高hits集合数','教师平均hit增量','平均每query相对NDC变化'],[[SHORT[x['dataset']],'有Recall空间' if x['group']=='recall_headroom' else '无Recall空间',x['queries'],f(x['fraction']*100,2)+'%',f(x['teacher_entry_set_change_fraction']*100,2)+'%',f(x['mean_max_hit_ties'],1),f(x['mean_hit_gain'],3),signed(-x['mean_graph_ndc_gain_pct'],2)+'%'] for x in teacher_diag['groups'] if x['group']!='all']))
 out.append('\n无额外命中空间的query占78.83%/89.20%，其中教师仍为63.69%/57.50%更换集合；这些行平均有51.7/54.4个集合达到相同最高hits，监督很大一部分来自成本tie-break。真正增加命中的组平均每query相对graph NDC反而增加10.33%/16.41%。因此总体平均NDC下降不意味着质量收益无成本，组内相对变化均值也不同于总体均值之比。\n')
 out.append('\n三族各用λ10/100，cal在L64/128平均Recall上选择；精确同分依总NDC和较强正则打破ties。两集最终配置如下，audit与validation结果均未用于改动它们。\n')
 out.append(table(['数据集','模型','冻结配置'],[[SHORT[ds],m['model_name'],m['selected_variant']] for ds in DS for m in selection[ds]['selected']]))
 fitrows=[]
 for ds in DS:
  for m in selection[ds]['selected']:
   x=next(x for x in modelcheck['models'] if x['dataset']==ds and f"{x['family']}_r{x['lambda_anchor']}"==m['selected_variant'])
   tr=next(t for t in training if t['dataset']==SHORT[ds] and t['family']==m['model_name'] and int(t['lambda_anchor'])==x['lambda_anchor'])
   fitrows.append([SHORT[ds],m['model_name'],f(tr['initial_CE'],3)+'→'+f(tr['final_CE'],3),f(x['baseline_exact_teacher_overlap']*100,2)+'%→'+f(x['teacher_entry_overlap']*100,2)+'%',f(x['teacher_exact_set_match']*100,2)+'%',f(x['predicted_set_outside_C8']*100,2)+'%'])
 out.append(table(['数据集','模型','fit集合CE','教师入口重合度 原→新','教师集合完全匹配','新精确集合超出C8'],fitrows))
 out.append('\n训练侧入口重合度用float64全H精确评分统计，分母为每query三个教师入口；集合匹配则要求三个全对。共享模型的CE下降没有带来重合度提升，因此不能把当前结果简单解释为“只差一点优化工程”。这也不证明所有共享模型都无效：本轮只有一种教师压缩、温度、宽度、种子和固定80轮优化。自由向量提供更大表容量参考，但相同训练轮数不等于相同收敛程度。\n')
 out.append('![全部训练损失与漂移](figures/training_curves.png)\n\n同一λ内可比较三族目标；不同λ改变了目标定义，跨λ损失值不直接排序。最终梯度范数、参数量、漂移和全部训练曲线都保留，没有按验证结果挑选某一epoch。\n')
 out.append('## 5. 开发段差异与微型HNSW的影响\n')
 out.append('下表是L128的真实检索Recall。fit probe只取训练集前256行，cal/audit各1024行，validation各2000行；不同段的绝对难度不同，不能把列间差异都叫作泛化损失。比较应看每段内同一query的模型与GT10差。\n')
 dsrows=[]
 for ds in DS:
  for m in profiles:
   vals=[]
   for stage in ['fit_probe','cal','audit','validation']:
    name=m
    if stage=='cal' and m!='gt10_hard':name=next(x['selected_variant'] for x in selection[ds]['selected'] if x['model_name']==m)
    x=next(x for x in allpoints if x['dataset']==SHORT[ds] and x['stage']==stage and x['method']==name and x['L']=='128' and x['exact']=='False');vals.append(f(x['recall_pct']))
   dsrows.append([SHORT[ds],m]+vals)
 out.append(table(['数据集','模型','fit probe','cal','audit','validation'],dsrows))
 exactrows=[]
 for ds in DS:
  for m in profiles:
   ms=[x for x in allpoints if x['dataset']==SHORT[ds] and x['stage']=='audit' and x['method']==m and x['L']=='128'];a=next(x for x in ms if x['exact']=='False');b=next(x for x in ms if x['exact']=='True');exactrows.append([SHORT[ds],m,f(a['recall_pct']),f(b['recall_pct']),signed(float(b['recall_pct'])-float(a['recall_pct']))])
 out.append('\naudit的精确画像top3诊断如下。精确画像评分只消除入口小图的近似，不能消除画像评分与有限L搜索效用的不一致；它可能提高或降低最终Recall。\n')
 out.append(table(['数据集','模型','HNSW3 Recall','exact3 Recall','exact−HNSW pp'],exactrows))
 out.append('## 6. 在线和离线成本\n')
 costrows=[]
 for x in allpoints:
  if x['stage']=='validation' and x['L']=='128' and x['method'] in profiles:
   costrows.append([x['dataset'],x['method'],f(1e6/float(x['qps']),2),f(x['route_us'],2),f(x['graph_us'],2),f(float(x['route_us'])/(1e6/float(x['qps']))*100,2)+'%',f(x['graph_ndc'],1)])
 out.append(table(['数据集','模型','端到端μs/query','route单测μs','graph单测μs','route/独立总wall','graph NDC'],costrows))
 out.append('\n分项wall是另外的测量，不相加当作总wall。模型前向已经离线完成，但入口几何会改变microHNSW访问和后续NSG路径，故“在线没有MLP开销”不代表所有模型QPS相同。NDC只计距离操作，不能代表访存、分支或全部运行时间。\n')
 out.append(table(['数据集','模型','λ','参数量','训练秒','导出秒','最终梯度范数'],[[x['dataset'],x['family'],x['lambda_anchor'],x['parameters'],f(x['seconds'],2),f(x['export_seconds'],4),f(x['final_grad_norm'],5)] for x in training]))
 labeljobs=json.loads((O/'logs/label_jobs.json').read_text());evaljobs=json.loads((O/'logs/evaluation_jobs.json').read_text());labels=[json.loads((O/'labels'/ds/'complete.json').read_text()) for ds in DS]
 total_label=sum(x['physical_calls'] for x in labels);parity=sum(x['parity_calls'] for x in labels);evaluation=sum(x['reserved_calls'] for x in evaljobs);total=total_label+parity+evaluation
 out.append(f'\n整个研究实际新增NSG调用 **{total:,}** 次：新标注{total_label:,}、标注核验{parity:,}、开发/正式评测{evaluation:,}；另{sum(x["reused"] for x in labels):,}个逻辑三元组复用兼容缓存。修复搜索0、合成搜索0，未借用历史剩余额度。两集标注进程合计{sum(x["seconds"] for x in labeljobs if x["stage"]=="label"):.2f}s（16线程且带计数，包含加载等），12次训练合计{sum(float(x["seconds"]) for x in training):.2f}s（8线程）。这些离线吞吐不能和单线程在线QPS比较。\n')
 out.append('候选生成另有80,000次纯microHNSW路由与32,720,000个精确画像分数计算，均为fit候选准备；不计作NSG调用，也不混进正式查询wall。\n')
 out.append('精确训练GT、QGT hub、原GT10画像、主图和base均为既有依赖；本轮没有重新测从零构建总成本。模型导出和microHNSW构建单独保存，但不能据此声称完整系统构建只需这些时间。若未来有稳定同Recall加速，仍需按额外离线成本和每query节省的wall计算摊销规模。\n')
 out.append('## 7. 验收、限制与研究建议\n')
 out.append(f'原始ID独立GT评分覆盖{verified["total_points"]}个开发/正式点、{verified["total_query_outputs"]:,}个query输出；其中6条原对照×2数据集×5L的120,000个输出回归历史E24，ID、入口、graph NDC、hits和mask一致。每点plain/count结果、16条原wrapper结果及正式三轮结果逐位对齐；同一模型五个L入口一致。模型的NumPy独立前向和概率归一化重算通过。最终资产/预算/链接核验见 [final_audit.json](reviews/final_audit.json)。\n')
 out.append('本轮只有一个既有hub/图构建，历史fit/cal/audit/validation均已多轮使用；cal选λ之后冻结并不能把这些切片变成新的盲测。bootstrap只描述固定模型下的query波动；三次wall仅描述本机重复范围。没有访问或hash held-out，没有额外调参、追加L、换种子或训练更大网络。\n')
 out.append('现阶段应把后续优先级放在“真实联合教师怎样被压缩成可靠的静态top3评分”，而不是首先扩大MLP。当前教师确有候选范围内空间，但共享模型的损失改善与教师入口命中没有同步，这是可核验的监督/压缩问题。若继续该方向，下一独立版本应先固定一个比本轮更贴近top3错误的目标，检验训练侧和开发侧的真实三入口收益；只有这一步成立，再讨论更强非线性、结构特征或新的未使用测试集。这些建议尚未执行，不自动开启新预算。\n')
 out.append('GT10原来的局部正信号与本轮共享变换的结果分开保留；一个增强失败不推翻先验本身。作为论文方向，GATE式离线表示加小图已有明确先例，MLP组件、成对线性变换和固定大小集合似然本身都不构成新颖性证明。可检验的贡献候选在于联合搜索监督、固定部署约束下的压缩机制和可重复端到端收益。\n')
 out.append('## 8. 证据与复现入口\n\n- [冻结协议](protocol.md)、[选择与冻结](models/frozen_before_validation.json)、[执行账](logs/evaluation_jobs.json)。\n- [全部数据工作簿](chart_data.xlsx)、[全部点CSV](results/all_points.csv)、[配对差值](results/validation_differences.csv)、[插值表](results/interpolated_same_recall.csv)。\n- [训练源码](src/train.py)、[原生标注](src/label.cpp)、[评测器](src/evaluate.cpp)、[完整构建参数](bin/evaluate.build.json)。\n- [标注核验](reviews/label_verification.json)、[模型核验](reviews/model_verification.json)、[输出核验](reviews/output_verification.json)、[修改前文档](source_before/summary.md)。\n\n本目录脚本使用冻结绝对输入路径，拒绝覆盖已有训练和搜索输出。重跑真实实验需要新的独立目录、相同依赖身份和新的预算；不能直接在本已完成目录执行原训练命令。原始来源和方法推导如下。\n')
 research=(O/'research.md').read_text();research=research[research.index('## 1.'):];research=research.replace('## 1. 研究对象与部署约束','## 9. 方法依据：研究对象与部署约束',1)
 # Keep a single title and globally unique numbered section headings.
 for old,new in [(2,10),(3,11),(4,12),(5,13),(6,14),(7,15)]:research=research.replace(f'## {old}.',f'## {new}.',1)
 out.append('\n'+research)
 (O/'report.md').write_text('\n'.join(out))
 dump(O/'results/report_numbers.json',dict(stats=stats,total_real_calls=total,training_seconds=sum(float(x['seconds']) for x in training),verification=verified,conclusion=conclusion))
 print(json.dumps(conclusion,indent=2))
if __name__=='__main__':main()
