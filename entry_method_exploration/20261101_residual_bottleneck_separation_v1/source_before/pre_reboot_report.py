from common import *
rows=list(csv.DictReader((R/'analysis/points.csv').open()))
comp=list(csv.DictReader((R/'analysis/comparisons.csv').open()))
stable=list(csv.DictReader((R/'analysis/stability.csv').open()))
room=list(csv.DictReader((R/'analysis/bottlenecks.csv').open()))
cost=read(R/'analysis/cost_ledger.json');audit=read(R/'analysis/analysis_receipt.json');second=read(R/'analysis/stdlib_audit.json')
decisions=read(R/'analysis/decision_audit.json')
idx={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in rows}
ci={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in comp}
names=dict(zip(DS,['COCO','Flickr','WebVid','Yandex','Deep10M','SIFT10M','GIST']))
def number(v,d=4):return '—' if v in ['',None] else f'{float(v):.{d}f}'
def table(head,data):return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in data)+'\n'
def rq(r):return f"{number(r['recall_pct'])}% / {number(r['qps'],2)}"
def p(ds,w,K,m,L=200):return idx[ds,w,K,L,m]
text=[]
text.append(f'''# E197：残差入口的候选、可预测性与执行方式详细实验报告

2026-11-01。按用户“更正主线然后继续实验”的授权完成固定范围；正式{cost['formal_points']}点、{cost['formal_batches']}个完整单线程批次。默认E99 GT10保持。训练费用不作为当前否决条件；判断分别落在入口质量、识别能力、执行方式和完整Recall–QPS，GT教师不当作可部署方法。

本报告使用本轮同窗口实际返回和完整wall。E195/E196与历史M5/B32/SQ保留原身份和正面场景，旧绝对QPS没有拼入新表。正式A/B沿E195曝光公共query、单图/画像；三轮只重复费用，不增加独立质量样本。本轮不作默认替换或全球最优结论。

## 1. 主线怎样更正并落实

原设计将学习强入口列为主线，现改成三个可分辨的问题：候选内有没有好入口、部署信息能否识别、路径限制/初始化方式是否是瓶颈。单点GT最好不证明可学习，零增量不等于永久坏节点，提前入口会改变初始集合与轨迹，不能简单归因于时机。

离线前8K合法query编独立Q8-B32，后8K固定2048入口fit/1024 cal；新表与选择器角色分离、排除完全相同向量。COCO/Flickr身份组跨新表/fit/cal及公共测试交集均0。旧GT10画像监督重叠披露；其余五集按原角色与行/向量身份核验，不声称语义IID。旧16K B32保留强参考，模型在Q8上训练/校准后固定迁移FULL，不冒称在FULL上重新校准过。

先生成全C、真实K1/K100、L200/384的实际单seed标签，比较24维ridge与104维固定128轮HGB；按合法cal选择模型/拒绝阈值。公共新响应前冻结所有模型、预算、控制和停止边界，未按正式质量调参或追加到通过。L100/400和完整16K表均为冻结迁移，未在相应状态重新拟合/校准；这些位置失效不能当成该状态下的可学习上限。
''')
text.append('## 2. 旧方法与本轮动作的具体区别\n\n'+table(
 ['方法','入口/答案选择','本轮隔离了什么'],[
 ['M5/B32','训练遗漏编直接候选，原metric精算合并','继续保留答案价值，旧16K OPT-B32为强控制'],
 ['E174/E195 DIST','逐路由行query-best最多3个seed','保留REF-DIST384；新增DIST1/FULL匹配单入口数量'],
 ['E195 NOVEL/REP','未访问邻居数/静态度数代表','不把度数/密度当准入证书；本轮按真实搜索标签识别'],
 ['MODEL1 / MODEL-FULL','每query全C预测净增量，选一个seed','与距离单seed同池/同预算比较；FULL为固定模型迁移'],
 ['MODEL-GATE / FULL','保留直接C，按冻结阈值允许不展开','核验每query完整包严格等于全开或直接返回'],
 ['CBRIDGE / SHARED','放开未选C或主评分未展开中间点','同适配层AUX384-FAST作控制，捕获空动作另测'],
 ['EARLY-MIX / ALL','仅用预先可用路由/残差表替换初始化入口','保持最多3入口合同；报告救回与损伤，不冒称同状态注入'],
 ['E193 / 旧Atlas','固定SQ整体开关/几何top8局部平均效用','当前是残差后置seed识别和执行干预，仍不代表所有学习器']]))
text.append('''完整C直接答案始终保留。种子来自已评分C或已付主评分集合，本轮没有新增独立代表精算；辅助新增来自后续路径。SHARED是保存实际分数后的独立辅助队列，原生产search_new没有完整pause/resume。GNN、组合教师、多个学习导航代表、修图均未在本轮实现。

## 3. 全C教师空间、模型兑现和路径支持

下面为FULL、L200、K100、两窗合计；各增量相对本轮同query的完整16K直接B32。均是追加Recall百分点，教师按GT逐query选最好单seed且可不执行；不包括识别代价。Shared教师同时改变队列并可加入主评分未展开候选前16个，范围有限，不能当全图最优。

''')
t=[]
for ds in DS:
 r=next(x for x in room if x['dataset']==ds and x['K']=='100' and x['bank']=='FULL');scale=100/(int(r['queries'])*100)
 t.append([names[ds],r['queries'],number(float(r['distance_single_gain'])*scale),number(float(r['model_gain'])*scale),number(float(r['gate_gain'])*scale),number(r['C_full_gain_pp']),number(r['shared_C_gain_pp']),number(r['shared_pool_gain_pp']),number(100*float(r['model_oracle_gain_fraction']),1) if r['model_oracle_gain_fraction'] else '无分母'])
text.append(table(['数据','query数','距离单seed','学习单seed','学习拒绝','GT最好C','GT最好共享C','GT共享扩源','模型/最好C%'],t))
text.append('[入口质量图](analysis/figures/quality_headroom.svg) · [Q8/FULL、两K完整瓶颈表](analysis/bottlenecks.csv) · [逐query诊断](analysis/query_diagnosis.csv.gz)\n\n')
text.append('## 4. 学习选择是否胜过同数量距离入口\n\n以下固定FULL/L200，实际完整Recall百分数/QPS；ΔR为相对DIST1-FULL的百分点，ΔQPS为完整费用比。每组只选一个seed、共同384预算。\n\n')
t=[]
for ds in DS:
 for K in [1,100]:
  for w in ['A','B']:
   model=p(ds,w,K,'MODEL-FULL');distance=p(ds,w,K,'DIST1-FULL')
   t.append([names[ds],K,w,rq(distance),rq(model),number(model['gain_vs_distance1_pp']),number(model['qps_gain_vs_distance1_pct'],2)])
text.append(table(['数据','K','窗','距离单seed R/QPS','学习单seed R/QPS','ΔR pp','ΔQPS%'],t))
text.append('''正的追加救回不自动等于模型学会选点；应同时看距离单seed、GT候选内差距和完整费用。K1新增事件稀疏；校准没有正收益时回退全关，不称识别成功。模型仅测试ridge/固定HGB和当前特征，不能外推所有神经模型、所有状态信息或所有候选支持。

## 5. 识别质量与更大L/强残差费用控制

下面固定MODEL-FULL/L200；控制选实际QPS不低于候选时Recall最高的GT10/OPT-B32/SQ点。它可以更快，不称精确同费用或同Recall。所有值来自本轮同窗口重测，预算插值只提出点表。

''')
t=[]
for ds in DS:
 r=next(x for x in room if x['dataset']==ds and x['K']=='100' and x['bank']=='FULL')
 t.append([names[ds],r['queries_any_C_gain'],r['selector_missed_available_positive_queries'],r['gate_enabled_queries'],
     number(100*float(r['gate_useful_precision']),1) if r['gate_useful_precision'] else '无分母',
     r['gate_wrong_reject_positive_queries'],
     number(100*float(r['gate_chosen_positive_gain_retention']),1) if r['gate_chosen_positive_gain_retention'] else '无分母'])
text.append('拒绝筛选另看FULL/K100/L200两窗：可用正入口query、选点漏失、实际启用、启用有用比例，以及误拒绝本来选中正入口造成的损失。保留率只在模型全开正收益有分母时定义，90%是cal约束，不能假定正式也达到。\n\n')
text.append(table(['数据','存在有用C的query','选择器未找对query','门启用query','启用有用%','误拒绝已选正入口query','正式正收益保留%'],t))
t=[]
for ds in DS:
 for w in ['A','B']:
  c=ci[ds,w,100,200,'MODEL-FULL'];r=p(ds,w,100,'MODEL-FULL')
  t.append([names[ds],w,rq(r),c['no_slower_control'],number(c['no_slower_control_recall']),number(c['no_slower_control_qps'],2),number(c['gain_vs_no_slower_pp']),c['covered']])
text.append(table(['数据','窗','模型R/QPS','不更慢控制','控制R%','控制QPS','模型ΔR pp','被覆盖'],t))
text.append('## 6. 队列限制与捕获管线的完整费用\n\n固定FULL/K100/L200，三种追加动作均按逐路由query-best最多3个seed。AUX384-FAST-FULL与旧REF-DIST384实际包相同，但使用与新动作相同的候选计划/适配层；因此费用差不全部归给队列。捕获Δus为SHARED-CAPTURE-FULL相对直接OPT-B32的完整批均query中位时间差，包含适配/分配，不是单次缓存写入单价。\n\n')
t=[]
for ds in DS:
 for w in ['A','B']:
  base=p(ds,w,100,'AUX384-FAST-FULL');cb=p(ds,w,100,'CBRIDGE384-FULL');sh=p(ds,w,100,'SHARED384-FULL');capture=p(ds,w,100,'SHARED-CAPTURE-FULL')
  t.append([names[ds],w,rq(base),number(cb['gain_vs_same_adapter_AUX_pp']),number(cb['qps_gain_vs_same_adapter_AUX_pct'],2),number(sh['gain_vs_same_adapter_AUX_pp']),number(sh['qps_gain_vs_same_adapter_AUX_pct'],2),number(capture['capture_pipeline_delta_us_vs_direct'],2)])
text.append(table(['数据','窗','AUX R/QPS','CB ΔR pp','CB ΔQPS%','共享 ΔR pp','共享 ΔQPS%','捕获Δus'],t))
text.append('''首次捕获核保留旧Trace统计，旧二进制/源码/cal原件全部保留。v2关闭无用统计，重新七集字节/缓存词/全部分支核验并完整费用校准，正式只用v2。SHARED仍包含分数保存、放开中间节点、过滤已展开节点等变化；未隔离每个内部因素，直接C也仍fresh精算，不能把该原型当一切状态共享的成本下界。

## 7. 提前入口的收益与损伤

以下FULL/K100/L200相对完整同L OPT-B32；保留全部直接残差候选。提前策略会替换原初始化入口，所以可能丢失原主搜索的成员；列救回/损伤及完整QPS变化。它不是相同入口集合、相同搜索状态下的时机单变量测试。

''')
t=[]
for ds in DS:
 for w in ['A','B']:
  baseline=p(ds,w,100,'OPT-B32')
  for m in ['EARLY-MIX-FULL','EARLY-ALL-FULL']:
   r=p(ds,w,100,m);t.append([names[ds],w,m,number(r['gain_vs_strong_pp']),r['rescued_vs_strong']+'/'+r['lost_vs_strong'],number((float(r['qps'])/float(baseline['qps'])-1)*100,2),ci[ds,w,100,200,m]['covered']])
text.append(table(['数据','窗','策略','ΔR pp','救回/损伤成员','ΔQPS%','被强控制覆盖'],t))
text.append('## 8. 严格失败尾部与拒绝\n\nK100失败严格定义为GT100命中0–9个，恰好10个排除。零分母不能报告修复率；尾部局部改善与完整Recall–QPS分开。\n\n')
t=[]
for ds in DS:
 for w in ['A','B']:
  vals=[p(ds,w,100,m) for m in ['GT10','OPT-B32','DIST1-FULL','MODEL-FULL','MODEL-GATE-FULL','SHARED384-FULL','EARLY-MIX-FULL']]
  gate=vals[4]
  t.append([names[ds],w]+[r['failed_lt10'] for r in vals]+[gate.get('actual_gate_enabled_queries',''),gate.get('escaped_lt10_vs_strong',''),gate.get('new_lt10_vs_strong','')])
text.append(table(['数据','窗','GT失败','B32失败','DIST1失败','模型失败','门失败','共享失败','提前失败','门启用query','门脱离/对B32','门新增失败'],t))
text.append('## 9. 跨窗覆盖和证据等级\n\n未被当前有限控制网格覆盖只表示保留观察，不等于默认替换。两窗稳定性按同一数据/K/L/方法配对；未通过不能一票否决所有相关路线。\n\n')
t=[]
for ds in DS:
 v=[x for x in stable if x['dataset']==ds]
 t.append([names[ds],len(v),sum(x['both_uncovered']=='True' for x in v),sum(x['both_uncovered']=='True' and x['both_positive_vs_no_slower']=='True' for x in v),sum(x['both_uncovered']=='True' and x['both_no_slower_CI_positive']=='True' for x in v)])
text.append(table(['数据','非GT/OPT/SQ配置','两窗未覆盖','同时两窗不更慢质量正','同时两窗描述CI正'],t))
text.append('''这些配置含距离/直接/捕获等控制，计数不是新算法成功数。所有逐点判断见[comparisons](analysis/comparisons.csv)，配对见[stability](analysis/stability.csv)。bootstrap按query配对1000次、描述性；多比较未作同时校正，std-lib独审没有独立重采样区间。A/B都曝光且同图，可靠默认替换仍需要具体适用场景的独立确认。

## 10. 实际费用与实现核验

''')
text.append(table(['阶段','实际费用/规模','解释'],[
 ['入口标签',f"{number(cost['actual_single_seed_label_invocations_seconds'],2)}秒",'实际单seed搜索，离线；不能当query QPS'],
 ['模型拟合进程',f"{number(cost['actual_model_training_invocations_seconds_including_failed_environment_launch'],2)}秒",'含失败系统Python启动；不以训练费否决'],
 ['旧捕获cal v1',f"{cost['previous_trace_capture_calibration_v1_points']}点 / {number(cost['previous_trace_capture_calibration_v1_batch_seconds'],2)}批次wall秒",'原件保留，不混入正式QPS'],
 ['精简捕获cal v2',f"{cost['calibration_points']}点 / {number(cost['calibration_batch_wall_seconds'],2)}批次wall秒",'事前选择费用邻近预算'],
 ['正式完整T1',f"{cost['formal_points']}点 / {cost['formal_batches']}批 / {number(cost['formal_batch_wall_seconds'],2)}秒",'正常完整batch生命周期'],
 ['候选/路径教师诊断',f"{number(cost['public_GT_privileged_candidate_diagnosis_native_process_seconds'],2)}秒",'GT特权、非部署、非正式QPS'],
 ['新增GT/主图构建','0','沿用原base/metric/GT/图，不重置历史投入']]))
text.append(f'''费用是嵌套口径：正式batch wall已包含在native进程时间内，整个public pipeline还包含诊断/归档/校验；不能相加称完整项目成本。全部查询比较CPU15、实际T1、库线程1、单方法串行，无并发训练/编译/其他性能任务。正常路由/主搜/C精算、状态保存、模型/选择、扩展、严格合并、输出分配/复制/销毁均计wall。加载、GT、hash、写盘和oracle在wall外。

首窗详细证据量触发存储峰值保护：COCO B一次运行在286.94秒停止，原始文件完整无损保留；随后复制24,856文件并逐一核对SHA/mtime，固定点表完整重跑B，不混入中断点。COCO A输出原在磁盘，其后输出在RAM暂存，均在query wall之外；比较以各同窗口共同条件为准，不把存储介质变化归为算法收益。所有新证据最后无损压缩并持久化，旧科学原件不动。中断实际进程费计入成本账；重启后的pipeline outer只覆盖最后一次调用，不冒称全程日历时长。[存储迁移](reviews/storage_RAM_staging.json)、[持久化证明](reviews/persistent_storage_delivery.json)。

本轮主分析核验{audit['point_packet_hashes_checked']}个实际点的三轮六数组hash，{audit['witness_queries']}条完整候选witness的ID/float字节与全排序，{audit['all_diagnostic_probes_recounted']}条公开诊断探针的GT hit-mask救损和教师选择。旧实际包对齐{audit['original_packet_parities']}点。14个选定模型的native/Python推断逐训练标签行检查；另对正式query重新无GT提取实际可用特征，核对{decisions['candidate_rows']}行推断及{decisions['query_K_L_bank_decisions']}组全开/拒绝实际选中ID。拒绝输出逐query核成全开或直接分支，FULL模型实际增量不超过同池单seed教师，两个Q8教师正式重放精确等于离线预期。

第二份std-lib实现独立核{second['formal_points']}点/{second['formal_batches']}批的GT整数、包hash、wall/费用覆盖、全部训练标签结构与原始query/GT行转换。它不导入主分析/NumPy；属于同执行者不同实现，不是独立人员审查，也未重跑所有图标签或独立bootstrap。详见[主核验](analysis/analysis_receipt.json)、[std-lib核验](analysis/stdlib_audit.json)、[成本账](analysis/cost_ledger.json)。

## 11. 交付与接续

- [全部实际点](analysis/points.csv)、[强控制比较](analysis/comparisons.csv)、[固定点表](analysis/frozen_formal_points.csv)、[冻结输入](formal_freeze.json)。
- [候选/模型/路径瓶颈](analysis/bottlenecks.csv)、[合法校准模型比较](analysis/model_calibration.csv)、[逐query诊断](analysis/query_diagnosis.csv.gz)、[逐点query命中](analysis/query_hits.npz)。
- [A窗完整费用图](analysis/figures/complete_wall_A.svg)、[B窗完整费用图](analysis/figures/complete_wall_B.svg)、[源/候选witness核验](analysis/witness_audit.csv)。
- [计量限制](measurement_boundaries.md)、[新无损存储](storage_format.md)、[原协议](protocol.md)、[历史有效残差索引](../../experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)。

旧科学文件、原始结果、PDF和seal不回写；本轮新timed raw字节与witness完整payload经SHA往返无损归档，原gzip容器字节不冒称保留。根文档以source_before桥接。无新PDF，默认E99保持。最终主线判断与具体有效/无效场景见[定位结论](findings_zh.md)，其范围限于本轮后端、候选、角色、K/L与曝光窗口。
''')
(R/'report_zh.md').write_text('\n'.join(text))
print('DETAILED_REPORT_TABLES_WRITTEN',flush=True)
