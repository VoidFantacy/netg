from common import *
assert read(R/'analysis/stdlib_audit.json')['status']=='PASS_STDLIB_INTEGERS_HASH_WALL_BRANCHES_AND_FRONTIER'
assert read(R/'reviews/pdf_visual_review.json')['status']=='PASS_ACTUAL_PDF_VISUAL_REVIEW'
def rows(name):
    with open(R/'analysis'/name) as f:return list(csv.DictReader(f))
facts=read(R/'analysis/summary_facts.json');cost=read(R/'analysis/cost_ledger.json');G=rows('gate_aggregate.csv');D=rows('pre_post_summary.csv');A=rows('aggregate.csv');ref=lambda p:'entry_method_exploration/20261104_gate_timing_cost_v1/'+p
cn={'coco':'COCO','flickr30k':'Flickr','webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex'}
headline=f"E199四个多模态数据集的门时机与精排成本实验已完成736点/2208完整单线程批次；主门策略{facts['primary_gate_points']}个窗口点中{facts['primary_covered']}个被同期强控制覆盖。"
summary=f'''# ACSG 当前结论

更新于2026-11-04。{headline} 当前默认E99 GT10保持；无运行中或待恢复矩阵。 唯一未覆盖的主门点为WebVid A/K1，速度差仅+0.0254%、三轮范围重叠、B窗未复现；没有两窗共同未覆盖的新门配置。用户本轮明确要求PDF，已交付[详细PDF]({ref('E199_残差门控时机与精排成本_20261104.pdf')})，并提供[结论解释]({ref('findings_zh.md')})和[文字/表格报告]({ref('report_zh.md')})。

本轮三层决策：STATIC按dataset/K/L离线固定开关；PRE在query/route可用、主搜索前预测；POST在相同完整主搜索后预测。PRE-LATE复用完全相同PRE模型/阈值，只移动执行位置，返回、动作和工作量一致。PRE/POST不是主搜索循环内早停，主搜索总是完整执行。

F语义控制整段C＋CASCADE384，关闭返回主结果；N语义始终保留全部C答案，只控制追加导航，并有利用C摘要的CPOST。两种off语义分别比较，不能把删除直接补点带来的省费当成门位置单变量。完整耗时和校准正增量保留必须同时评估。

| 数据 | K | 语义 | PRE90 Recall/QPS | POST90 Recall/QPS |
| --- | --- | --- | --- | --- |
'''
for r in D:
    summary+=f"| {cn[r['dataset']]} | {r['K']} | {r['family']} | {float(r['pre_recall']):.4f}% / {float(r['pre_qps']):.2f} | {float(r['post_recall']):.4f}% / {float(r['post_qps']):.2f} |\n"
summary+=f'''
表为A/B各512的合并描述：Recall按命中合并，QPS由平均每query时间取倒数；不是新独立确认。逐窗原值与门误拒、无效启用、正增量保留、强前沿见[门表]({ref('analysis/gates.csv')})、[完整点]({ref('analysis/points.csv')})和[强控制]({ref('analysis/frontier.csv')})。75%/90%只为独立cal目标，测试结果另核；零正增量记NA，全开/全关不自动算识别成功。

精排成本已分为重特征、树预测和实际扩展；FAST384/同池距离/短名单CASCADE384/全C教师均同期测量。[精排表]({ref('analysis/rerank_costs.csv')})保留最终召回、完整增加µs、局部特征/模型费用与入口改变后的实际工作差。门特征可被后续复用，分段归属变化不等于同额新增开销；cal全关时当前PRE/POST仍构造特征再关闭，STATIC免去这笔费用，是可优化实现差异。

正式路径无阶段插钟，完整wall含Batch创建、全部查询工作、六数组复制与销毁。另行profile逐条返回/动作对齐，阶段均值/条件均值/P50/P95为诊断，不能拼成正式QPS；其batch边界亦不含正式六数组复制销毁；基线分段使用返回等价逐query适配层，非原优化batch严格分解。正式batch wall共{cost['formal_complete_batch_seconds']:.2f}秒，包含于正式进程{cost['formal_process_seconds']:.2f}秒。COCO/WebVid复用E198，Flickr/Yandex本轮新标签/模型成本分别{cost['new_label_process_seconds']:.2f}/{cost['new_model_training_process_seconds']:.2f}秒；继承债未清零。

四集raw-IP、原图/画像、固定Q8来源、单入口384/L200、两旧曝光窗口、K1稀疏事件、共享开发512和多比较限制保留。未实现主循环早停、pause/resume或修图。历史E173/E191/E194条件有效M5/B32/SQ与E198返回等价缓存优化保持原身份；本轮不否定全部残差方法。所有旧科学文件/seal/PDF保留，根文档由source_before桥接，全部新证据持久化。[交付核验]({ref('delivery_validation.json')})。
'''
(REPO/'summary.md').write_text(summary)
target=f'''# ACSG 后续研究问题

2026-11-04。用户授权的四多模态集PRE/POST残差门对照、成本/精排分析与PDF由E199完成。736点/2208完整T1已收口；当前默认保持，无待恢复队列。

后继先读[具体结论]({ref('findings_zh.md')})和[报告]({ref('report_zh.md')})，不能再把PRE/POST、同门移位、F/N语义、阶段成本或精排成本作为尚未测量的建议。原E198仍是其独立两集学习策略验证。

1. **只为有实际收益的状态继续。** 若某状态在两窗有值得保留的质量/费用取舍，冻结模型、阈值与适用Recall要求，再在未参与开发的合法角色确认；不以合并表或有限网格未覆盖直接替换默认。
2. **门位置与省费对象保持一致。** F可以跳过整个残差但会放弃直接C；N保留C就不能宣称省掉其评分。进一步前移需要明确新增可用信号和答案语义，不能仅移动相同模型便期待减少主搜索量。
3. **精排研究以完整增益和实测分段支持。** 分清重特征、模型预测、选点后的扩展量和阶段外费用；更少候选/扫描不自动变成完整加速。更便宜模型、收益/实际费用联合监督等仍需独立新证据。
4. **确认角色与判断规则先冻结。** 继续保留强B32/SQ/距离控制、真实K1/K100与完整T1；三轮wall非独立质量样本，不追加曝光窗口直到通过。

主图循环内动态早停、原beam续搜、图修复和新GNN均未在E199实现。历史有效残差配置继续保留。当前边界为本轮报告/PDF交付，不自动扩大实验。
'''
(REPO/'s-target.md').write_text(target)
sp=REPO/'spec.md';s=sp.read_text();assert '### 4.14 E199' not in s
section=f'''### 4.14 E199门时机、F/N语义与精排成本（已实现并验证）

[协议]({ref('protocol.md')})、[benchmark]({ref('src/benchmark.cpp')})及[kernel]({ref('src/kernel.inc')})在独立目录嵌入只重命名main/绝对include的E198快照。四多模态集原raw-IP/base/图/router不变。COCO/WebVid复用冻结E198 L200模型，Flickr/Yandex按相同方案新建匹配K1/K100模型；Q8银行和3072角色沿E197，2048学生fit、512开发兼门fit、512独立cal，原画像交叠和开发共享披露。

STATIC按状态cal正增量选全开/全关。PRE22在路由后主搜前预测；POST28再用主Top-K摘要，在C精算前预测；N-CPOST12使用已评分C摘要。门为深度3/min_leaf32树，fit512，阈值只由独立cal按75%/90%正增量保留选择。PRE-LATE使用同PRE模型/阈值只改执行位置，返回、动作、工作量完全一致。主搜索始终完整，无主循环内动态早停或pause/resume。

F门off返回主结果、on调用相同Q8＋CASCADE384；N门off返回完整Q8直接答案、on追加同CASCADE384。固定单seed384、物理辅助邻接≤64×384。FAST384、最近DIST384、全C TEACHER384及完整B32/SQ强控制均同期测量；候选bank/后端/预算一致。原模型与主核未改。

736正式点/2208完整T1，CPU15实际线程1与库线程1；正常路径通过模板关闭所有阶段时钟，完整Batch创建、全部处理、六数组复制销毁计wall。另行profile记录route/main/gate-features/gate-predict/C/student-shortlist/rerank-features/rerank-predict/expansion/merge及query总量，逐条与normal包/工作/决策核对。profile batch缺少正式六数组复制销毁并含阶段时钟，边界不同；分段和、P50/P95和profile差额都是诊断，不替换正式QPS。基线GT10/OPT-B32/Q8分段采用返回等价逐query适配路径，分配/调度不同于原优化batch，不是严格拆解；门normal/profile沿同一模板查询逻辑。门特征可能复用，阶段迁移不是同额新开销。

辅助work保留原8字段；decisions.i32每query7字段为action-enabled/seed-ID/cap/rerank-rows/rerank-neighbor-slots/gate-position/gate-enabled。profile.f64每query11字段顺序见environment.stage_names。ALWAYS的selection witness保存22+28+12门输入及全C104维特征，用于Python独立门/学生/教师决策；其他自定义点保存main+events线性合并witness。实际首轮四数组加两组零NDC和形状形成包SHA，三轮返回/work/决策一致；零NDC非无计算。

全开/全关、同门移位、normal/profile、旧动作包资格通过；正式native线性merge、NumPy全排序/树double阈值与学生推断、门分支、stdlib整数/hash/wall/前沿和旧兼容包核验通过。独审为同执行者不同实现。raw/work/决策/profile/witness按payload无损归档并往返核验，证据持久化，无RAM依赖；gzip容器字节不声明保留。模型/源/配置/角色/小输入SHA及继承大资产stat见[冻结]({ref('formal_freeze.json')})。详细PDF已实际渲染核查，旧科学文件/seal/PDF保持，根文档由source_before桥接。

'''
s=s.replace('## 5. 指标、计时与证据\n',section+'## 5. 指标、计时与证据\n');sp.write_text(s)
idx=REPO/'s-experiment.md';s=idx.read_text();a=s.index('更新于');b=s.index('2026-11-01设计汇报');s=s[:a]+f'''更新于2026-11-04。最新完成E199四多模态集残差门时机与精排成本（736点/2208完整T1），交付详细PDF；前序E198/E197及全部历史保持原身份。当前结论读summary，实现读spec，后继读s-target。

E199：[结论]({ref('findings_zh.md')}) · [报告]({ref('report_zh.md')}) · [PDF]({ref('E199_残差门控时机与精排成本_20261104.pdf')})。{headline} 无待恢复队列。

'''+s[b:];pos=s.index('| E198 |');s=s[:pos]+f"| E199 | 四多模态集STATIC/PRE/POST门、F/N语义与精排分段 | 完成736/2208，详细PDF；主门{facts['primary_covered']}/{facts['primary_gate_points']}被强控制覆盖 | [卡片](experiment_history/199_gate_timing_cost_v1.md) |\n"+s[pos:];idx.write_text(s)
card=f'''# E199 搜索前/查询阶段残差门与精排成本

2026-11-04。用户授权四多模态集实验、成本分析、精排成本与PDF。{headline} 默认保持，固定矩阵已收口。

## 实验问题与机制

STATIC离线固定开关，PRE用query/route22维在主搜前预测，POST增加主返回摘要共28维，在C评分前预测；PRE-LATE使用同PRE模型/阈值只移动位置，结果/动作/工作量相同。没有图循环内早停。

F控制整段Q8＋CASCADE384、off主结果；N保持直接C答案，只控制追加导航，另测CPOST12。固定单入口384预算，学生top5＋最近1去重≤6、104维HGB重排；FAST/DIST/全C教师与B32/SQ均作控制。两拒绝语义独立报告。

四集真实K1/K100、主研究L200与预定强控制L网格、A/B各512旧曝光query。沿E197合法角色，2048学生fit/512开发兼门fit/512独立cal，75/90保留目标正式前固定；COCO/WebVid模型复用E198，Flickr/Yandex同方案新建。画像交叠和共享开发披露，未按正式结果调参。

## 实际结果、成本与边界

具体保留/停止结论读[findings](../{ref('findings_zh.md')})。完整Recall/QPS及阶段/精排实际数字读[report](../{ref('report_zh.md')})和[PDF](../{ref('E199_残差门控时机与精排成本_20261104.pdf')})，合并表仅描述两曝光窗口，不替代逐窗确认。

新标签/模型进程{cost['new_label_process_seconds']:.2f}/{cost['new_model_training_process_seconds']:.2f}秒；门标签/拟合{cost['gate_label_process_seconds']:.2f}/{cost['gate_fit_process_seconds']:.2f}秒。正式batch wall{cost['formal_complete_batch_seconds']:.2f}秒，包含于正式进程{cost['formal_process_seconds']:.2f}秒，不重复相加。继承图/router/SQ及E198成本未清零；模型文件大小非RSS。

normal不插阶段时钟，含完整Batch生命周期；profile另行测分段并核输出/动作一致，profile batch缺六数组复制销毁且含时钟，不能以阶段和替代QPS或把差额全归给插钟。门特征可复用，入口改变后的扩展量与模型费用分开。辅助精算/邻接与重特征槽分别计，不是总NDC。

资格、三轮包/work/决策、profile、native/NumPy合并与模型/门分支、stdlib整数/hash/wall/强前沿/旧兼容包通过，同执行者不同实现。详细PDF实际渲染核查；所有新证据持久化，旧科学文件/seal/PDF保留，根文档旧字节在source_before。

单图/画像、Q8来源、单入口384/L200门研究、两曝光窗口、K1稀疏事件、共享开发和多比较限制保留。历史有效M5/B32/SQ不被本轮有限结果否定。未做原beam续搜/修图/GNN，未扩大固定矩阵，无待恢复队列。

## 原证据

[协议](../{ref('protocol.md')}) · [冻结](../{ref('formal_freeze.json')}) · [全部点](../{ref('analysis/points.csv')}) · [门](../{ref('analysis/gates.csv')}) · [阶段成本](../{ref('analysis/stage_costs.csv')}) · [精排成本](../{ref('analysis/rerank_costs.csv')}) · [同门位置](../{ref('analysis/placement.csv')}) · [强前沿](../{ref('analysis/frontier.csv')}) · [核验](../{ref('delivery_validation.json')})。
'''
(REPO/'experiment_history/199_gate_timing_cost_v1.md').write_text(card)
hp=REPO/'experiment_history/README.md';h=hp.read_text();a=h.index('更新于');b=h.index('\n\n',a);h=h[:a]+'更新于2026-11-04。最新完成[E199](199_gate_timing_cost_v1.md)四多模态集残差门时机与精排成本，交付详细PDF。E198及全部前序卡片保持各自身份；当前结论见[summary](../summary.md)，简要索引见[s-experiment](../s-experiment.md)。'+h[b:];h+='\n- [E199 门时机与精排成本](199_gate_timing_cost_v1.md)：四多模态集736点/2208完整T1，独立成本剖析与详细PDF完成，默认保持。\n';hp.write_text(h)
(REPO/'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

2026-11-04，工作区/data/netg/ACSG，HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62。最新E199四多模态门时机/精排成本完成736点/2208完整T1及详细PDF；默认保持，无运行中或待恢复矩阵。

先读AGENTS、summary、spec、s-target、s-experiment，再读[结论]({ref('findings_zh.md')})、[报告]({ref('report_zh.md')})、[PDF]({ref('E199_残差门控时机与精排成本_20261104.pdf')})和[交付]({ref('delivery_validation.json')})。STATIC/PRE/POST、PRE-LATE、F/N两语义与阶段/精排成本已实现测量，不能再当成未试建议。

两窗口已曝光，固定单入口384/L200、K1稀疏和共享开发限制保留；历史M5/B32/SQ正面场景及E198缓存优化保留。全部新raw/witness/profile按payload归档并持久化；旧科学文件/seal/PDF保留，根文档由source_before桥接。不要按旧PID/session重启；不自动扩点、重训、发布或改默认。原主beam续搜、图修复、GNN仍未实现。
''')
print('SYNCHRONIZED_E199_CURRENT_DOCUMENTS_AND_HISTORY',flush=True)
