from common import *
assert read(R/'analysis/stdlib_audit.json')['status']=='PASS_INDEPENDENT_STDLIB_RECALL_HASH_WALL_FRONTIER_AND_PRIOR_PARITY'
def readcsv(name):
    with open(R/'analysis'/name) as f:return list(csv.DictReader(f))
P=readcsv('points.csv');C=readcsv('comparisons.csv');M=readcsv('mechanisms.csv');facts=read(R/'analysis/summary_facts.json');cost=read(R/'analysis/cost_ledger.json');audit=read(R/'analysis/analysis_receipt.json')
prefix='entry_method_exploration/20261102_conditional_residual_policy_v1'
ref=lambda name:f'{prefix}/{name}'
lookup={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in P}
comp={(r['dataset'],r['window'],int(r['K']),int(r['L']),r['method']):r for r in C}
cache=[float(r['cache_QPS_gain_pct']) for r in P if r['method']=='OLD-CACHED384']
retention=[100*float(r['retention']) for r in M if r['retention']]
policy=[float(r['quality_threshold_QPS_gain_pct']) for r in C if r['method']=='POLICY']
summary=f'''# ACSG 当前结论

更新于2026-11-02。E198条件残差导航已完成1,480点/4,440完整单线程批次，默认E99 GT10保持（WebVid soft-t1、Yandex hard）。本轮范围COCO/WebVid，真实K100/L100、200、400及K1/L200；两曝光A/B窗口各512。无正在运行或待恢复矩阵。

**{facts['headline']}** 最终POLICY相对达到不低于其Recall的最快已测强控制，QPS变化为{min(policy):+.2f}%至{max(policy):+.2f}%；这是质量门槛比较，控制Recall可能更高，不能一概称严格同Recall。

14个有正增量的窗口中12个前置门仍全部放行；仅WebVid/K100/L400实质筛选，正增量保留80.55%/92.36%，一窗未达到cal90%目标。固定384级联相对最近单入口11正/1平/4负，但完整QPS全部慢11.8%–34.2%；不同种子的实际展开量也不同，不能全部归因模型推断。详见[机制结论]({ref('findings_zh.md')})。

已实现状态匹配的真实单seed效用监督、双塔蒸馏、至多6点教师重排、前置门及0/96/384预算选择。全部直接C始终保留，筛选只决定额外导航入口；不修图、不恢复主beam。完整说明见[方法]({ref('method_zh.md')})，无需重复解释GT10。

缓存共享特征的旧模型返回逐字节等价，完整QPS变化范围{min(cache):+.2f}%至{max(cache):+.2f}%；这证明有限工程省费，不自动证明达到强前沿。门相对无前置门ADAPT的正增量保留率（有正增量的窗口）为{min(retention):.2f}%至{max(retention):.2f}%；校准90%目标必须与正式实测分开，全关/全开不自动算识别成功。

| 数据 | 窗 | POLICY K100/L200 Recall / QPS | 质量门槛强控制 Recall / QPS |
| --- | --- | --- | --- |
'''
for ds,cn in [('coco','COCO'),('webvid2_5m_light_v1','WebVid')]:
    for w in ['A','B']:
        p=lookup[ds,w,100,200,'POLICY'];c=comp[ds,w,100,200,'POLICY'];bm,bl=c['quality_threshold_control'].split('/L');b=lookup[ds,w,100,int(bl),bm]
        summary+=f"| {cn} | {w} | {float(p['recall_pct']):.4f}% / {float(p['qps']):.2f} | {bm}/L{bl}: {float(b['recall_pct']):.4f}% / {float(b['qps']):.2f} |\n"
summary+=f'''
离线产生{cost['label_candidate_rows']:,}个候选行、两预算共{cost['executed_single_seed_actions']:,}个单seed动作标签；标签进程{cost['label_process_seconds']:.2f}秒，训练进程{cost['training_process_seconds']:.2f}秒。正式完整batch wall共{cost['formal_complete_batch_seconds']:.2f}秒；它包含于正式进程耗时，不能重复相加。模型文件量不是驻留RAM，辅助精算/邻接计数不是总NDC或全部访问，完整wall才是费用判据。

所有三轮返回/工作/决策一致，{audit['packet_hash_checks']}包、{audit['query_witness_fullsort_checks']}条query witness全排序和{audit['independent_model_decision_checks']}项独立策略决策检查通过；另有原生/NumPy全标签推断、stdlib整数/hash/wall/强前沿及旧兼容返回包核验。独审为同执行者不同实现。所有新证据持久化，旧科学文件和seal保留，根文档由source_before桥接，无新PDF。

学生fit2048、开发兼门fit512、独立cal512；Q8银行与模型角色沿E197分离，原画像监督交叠披露。开发阶段epoch/λ/门fit共享512，不称完全独立开发。正式两窗已曝光、单图/画像、有限预算与网格、K1稀疏事件、多比较描述区间限制保留。本轮未重做公开窗口GT穷举入口oracle；TEACHER384是学习预测器。

历史E197七集定位与E173/E191/E194条件有效的M5/B32/SQ继续保留原范围和费用；本轮局部结果不否定全部残差方法。参见[历史正面证据](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)。

当前停在固定验证与方法解释交付边界，不自动追加数据/参数或改默认。后继问题读[s-target](s-target.md)。证据：[完整报告]({ref('report_zh.md')}) · [全部点]({ref('analysis/points.csv')}) · [强控制]({ref('analysis/comparisons.csv')}) · [门]({ref('analysis/mechanisms.csv')}) · [交付核验]({ref('delivery_validation.json')})。
'''
(REPO/'summary.md').write_text(summary)
target=f'''# ACSG 后续研究问题

2026-11-02。用户授权的“验证新残差方法，并解释GT10之后的方法”已由E198完成1,480点/4,440完整T1。当前默认E99 GT10保持，无待恢复矩阵，不自动扩点、重训或生成PDF。可靠完整Recall–QPS仍是终点，训练成本不是单独的排除条件。

E198已经实现前置拒绝、双塔蒸馏、小名单精排和状态匹配的96/384预算选择，不能再把这四项泛称为尚未尝试的新建议。先读[实际结论]({ref('report_zh.md')})及[具体机制]({ref('method_zh.md')})，再判断是否有实质改进对象。

1. **区分选择损失和执行费用。** 固定同一C/单入口/预算，先查FAST、CASCADE、全C学习教师与距离选择的实测差异，再看完整强控制。教师所选ID的短名单保留率不是GT最优入口保留，也不是最终Recall上界。
2. **如继续研究门，先明确能省哪笔费用。** E198门已放在重模型之前，但仍付主搜索及全部C精算。需要在独立角色评估误拒、空动作、96/384分配与真实wall收益，不能仅减少启用数或换λ便宣称解决成本。
3. **更强导航监督或表示必须有新证据。** 进一步学习图/轨迹表示、以距离动作的实际收益为参照优化regret、直接预测强基线下的费用收益，均是本轮未验证的后继问题。预算比例惩罚不是实测wall模型，GT入口空间也不等于可学保证。
4. **若出现可靠局部优势，再确认。** 冻结模型、角色、预算、最强适用B32/SQ/距离/费用邻近控制和停止条件，在未参与开发的角色确认；当前两曝光窗口和有限网格不足以自动替换默认。不要求所有数据集全胜，也不追加窗口直到通过。

原主beam pause/resume、图修复、学习GNN等仍未实现。旧E197、E195/E196及理论设计各自保持原身份；历史条件有效M5/B32/SQ仍作为强参考。新研究需另建协议，本轮止于报告与方法解释。
'''
(REPO/'s-target.md').write_text(target)
specpath=REPO/'spec.md';spec=specpath.read_text()
old='具体结果和默认决定只读summary，后继强表示/前置拒绝尚未实现。'
spec=spec.replace(old,'具体结果和默认决定只读summary；E197收口时后继强表示/前置拒绝尚未实现，随后E198的具体实现另见4.13。')
section=f'''### 4.13 E198条件残差动作策略（已实现并验证）

[协议]({ref('protocol.md')})、[源码]({ref('src/benchmark.cpp')})及[策略]({ref('src/policy.inc')})在独立目录嵌入只重命名main、改绝对include的E197快照；原主核/图/metric不变。新DIST96/384为全C最近的单seed，与E195同名逐路由多seed语义不同；不能按同名混拼。完整C直接答案始终保留，辅助后端visited/seen/队列沿E195独立有界扩展，新增精算上限96/384、邻接槽上限64×预算，不恢复主beam。

COCO/WebVid每集四状态分别生成全C两预算真实净命中/救损/工作标签。Q8银行来自原前8K，后8K合法选定角色沿E197；2048学生fit、512epoch/λ开发兼门fit、512独立阈值/费用cal。原画像监督交叠及开发角色共享披露。每状态/预算HGB128轮/15叶/lr.08/L2=10；学生query25→64→两32头，node34→64→32，另23便宜候选线性特征，结合教师/真实收益回归与query内正收益排序，24epoch由开发收益选定。node32表示离线导出，线上query只编码一次。未训练GNN。

FAST在全C廉价选1；CASCADE每预算保留最近1＋学生前5（去重≤6），再用匹配教师重排；ADAPT选最大预测收益减λ×预算/384的正值，否则无动作。λ只选固定开发列表。POLICY先在12维便宜query/route/C/主返回摘要上运行深度3门，再决定是否付投影/学生/重排费用；门拒绝返回Q8直接答案。门仍付C精算，不能视作跳过全部补点。GT仅离线标签/评测读取，TEACHER384是部署可用预测器，非GT oracle。

共享query投影/范数/距离跨度等只计算一次。OLD-CACHED384与原MODEL1全query返回字节等价，强控制仍调用原GT10/OPT-B32/Q8-B32/SQ实现。完整matrix1,480点/4,440批次，CPU15实际T1、库线程1、单方法串行；计wall包括正常Batch创建、主搜、C、模型/门/扩展/合并、六数组复制销毁。加载/GT/持久化/hash/核验在外。工作邻接计数只覆盖辅助展开，不含主搜索和教师特征扫描，额外精算非总NDC，包内零NDC只是占位。

独立决策审计使用analyze_v2.py，将树比较输入提升float64以保持原生double阈值语义；首版NumPy隐式降精度导致的失败日志与原冻结源码保留，正式模型/返回/wall不改。首轮保存实际返回，另外两轮SHA、work、seed/budget/gate决策相同。native线性oracle、NumPy全排序、独立Python逐query预测/短名单/预算/门决策、stdlib整数/hash/wall/强前沿与旧兼容包核验通过；同执行者不同实现。标签源由labels_frozen.cpp精确桥接构建SHA，后续实现不回写它。新raw/work/决策/witness/特征witness按payload无损压缩并往返核验，持久storage为真目录，无RAM证据依赖；gzip包装字节不声明保留。源/模型/配置/角色/小输入SHA及继承大资产stat见[formal freeze]({ref('formal_freeze.json')})，结果、费用与边界只读summary/report。旧科学文件、seal、PDF不改，根文档由source_before桥接。

'''
assert '### 4.13 E198' not in spec
spec=spec.replace('## 5. 指标、计时与证据\n',section+'## 5. 指标、计时与证据\n');specpath.write_text(spec)
idx=REPO/'s-experiment.md';s=idx.read_text();start=s.index('更新于');end=s.index('2026-11-01设计汇报')
s=s[:start]+f'''更新于2026-11-02。最新完成E198条件残差导航（1,480点/4,440完整T1）；E197七集瓶颈分离及E195/E196保持原身份。当前结论读summary，实现读spec，后继读s-target。

E198：[验证报告]({ref('report_zh.md')}) · [方法具体说明]({ref('method_zh.md')})。{facts['headline']}无待恢复队列。

'''+s[end:]
s=s.replace('其后部分机制在E197独立实现/测量','其后部分机制在E197、E198分别实现/测量')
needle='| E197 |';pos=s.index(needle);s=s[:pos]+f"| E198 | 状态匹配监督、双塔短名单、前置门与0/96/384动作 | 完成1480/4440；{facts['learned_points']-facts['learned_uncovered_points']}/{facts['learned_points']}新学习窗口点被强控制覆盖，默认保持 | [卡片](experiment_history/198_conditional_residual_policy_v1.md) |\n"+s[pos:];idx.write_text(s)
history=f'''# E198 条件残差导航验证

2026-11-02。用户授权“验证吧，后面介绍方法具体是什么，GT10不用再讲”。固定COCO/WebVid四状态、A/B各512已曝光查询，完成1,480点/4,440完整CPU15/T1，默认保持，无新PDF。

## 动机与实现

E197显示有限候选里有入口空间，但全C重评分费用和拒绝位置受限。本轮保持Q8直接答案及单seed辅助后端，分别训练K100/L100、200、400和K1/L200两预算真实效用。HGB教师、双塔学生、最近1＋学生前5的短名单、前置深度3门和0/96/384动作全部实现；另保留完整B32/SQ、同池距离种子、原MODEL1和返回等价的共享特征缓存对照。新DIST96/384是全C最近单seed，不与旧同名多seed混淆。

角色2048fit、512开发兼门fit、512独立cal，Q8银行/选择器沿E197合法分离；画像监督交叠和开发共享披露。预算比例惩罚不是实测wall预测。正式点表由cal完整费用提出邻近GT10/OPT-B32控制并冻结，未用正式Recall追加点或调阈值。

## 结果与费用

{facts['headline']}

最终POLICY质量门槛强控制QPS变化{min(policy):+.2f}%至{max(policy):+.2f}%；相对ADAPT正增量保留{min(retention):.2f}%至{max(retention):.2f}%。旧MODEL1共享特征缓存返回字节等价，QPS变化{min(cache):+.2f}%至{max(cache):+.2f}%，工程省费不自动成为强前沿胜利。详细每窗Recall、QPS、救损、预算、门保留、短名单及失败查询在报告/CSV。

标签{cost['label_candidate_rows']:,}候选行、{cost['executed_single_seed_actions']:,}动作；标签进程{cost['label_process_seconds']:.2f}秒，训练进程{cost['training_process_seconds']:.2f}秒，正式batch wall{cost['formal_complete_batch_seconds']:.2f}秒。batch wall包含于正式进程，不重复相加。计数区分C/辅助精算和辅助邻接，非总NDC或全部扫描。

## 验证与边界

八状态全标签Python/native推断一致，三轮包/work/决策一致，native线性merge和NumPy全排序、独立Python策略、stdlib整数/hash/wall/强前沿及旧兼容包通过。同执行者不同实现，不独立人员复现。原标签源码与二进制有精确SHA桥接；原科学文件、seal和PDF只读保留，根文档修改前字节在本轮source_before。全部新证据持久化，无RAM依赖，无待恢复矩阵。

两集、单图/画像、固定单入口后端/预算、两曝光窗口、K1稀疏正例、共享开发和多比较描述区间均限制外推。未重做公开GT穷举入口oracle，学习教师不充当GT上界；未实现主beam续搜、图修复或GNN。历史条件有效M5/B32/SQ继续保留。新问题另建协议，不自动扩大本轮。

## 原始证据

[方法](../{ref('method_zh.md')}) · [报告](../{ref('report_zh.md')}) · [协议](../{ref('protocol.md')}) · [冻结](../{ref('formal_freeze.json')}) · [全部点](../{ref('analysis/points.csv')}) · [强控制](../{ref('analysis/comparisons.csv')}) · [门机制](../{ref('analysis/mechanisms.csv')}) · [成本](../{ref('analysis/cost_ledger.json')}) · [主核验](../{ref('analysis/analysis_receipt.json')}) · [stdlib](../{ref('analysis/stdlib_audit.json')}) · [交付](../{ref('delivery_validation.json')})。
'''
(REPO/'experiment_history/198_conditional_residual_policy_v1.md').write_text(history)
hp=REPO/'experiment_history/README.md';h=hp.read_text();a=h.index('更新于');b=h.index('\n\n',a)
h=h[:a]+'更新于2026-11-02。最新完成[E198](198_conditional_residual_policy_v1.md)条件残差导航验证；E197及所有前序记录保持各自身份。当前结论见[summary](../summary.md)，简要索引见[s-experiment](../s-experiment.md)。'+h[b:]
h+='\n- [E198 条件残差导航](198_conditional_residual_policy_v1.md)：状态匹配监督、双塔短名单、前置门和0/96/384动作，完成1480点/4440完整T1；默认保持，具体结论见卡片。\n';hp.write_text(h)
(REPO/'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

2026-11-02，工作区/data/netg/ACSG，HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62。最新E198条件残差导航完成1480点/4440完整T1，默认E99保持，无运行中或待恢复矩阵。先读AGENTS、summary、spec、s-target、s-experiment，再读[验证报告]({ref('report_zh.md')})、[具体方法]({ref('method_zh.md')})、[交付核验]({ref('delivery_validation.json')})。

{facts['headline']} 两集两曝光窗口的有限结论，不否定历史M5/B32/SQ正面场景。新方法已实现前置门、双塔、短名单教师和预算选择；不要再当成未实现方案。原主beam pause/resume、图修复和GNN仍未实现。

全部新证据在本轮storage持久目录，raw/witness按payload归档往返核验；旧科学文件/seal/PDF保留，根文档旧字节在source_before。不按旧PID/session重启，不自动扩点、重训、发布、改默认或生成PDF。E197关机恢复已独立收口，其持久来源和限制继续读原卡片与验收，不混拼旧QPS。
''')
print('SYNCHRONIZED_CURRENT_DOCUMENTS_AND_HISTORY',flush=True)
