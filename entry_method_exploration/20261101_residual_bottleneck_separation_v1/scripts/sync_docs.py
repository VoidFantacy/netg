from common import *
import re,shutil
assert read(R/'reviews/persistent_storage_delivery.json')['status']=='PASS_ALL_NEW_EVIDENCE_PERSISTENT_NO_RAM_DEPENDENCY'
assert read(R/'analysis/stdlib_audit.json')['formal_points']==9434
base='entry_method_exploration/'+R.name
roots=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md',
       'experiment_history/197_residual_bottleneck_separation_v1.md']
snap=R/'source_before/root_before_completion'
for name in roots:
    p=snap/name;p.parent.mkdir(parents=True,exist_ok=True)
    assert not p.exists();shutil.copy2(REPO/name,p)
rooms=list(csv.DictReader((R/'analysis/bottlenecks.csv').open()))
names=dict(zip(DS,['COCO','Flickr','WebVid','Yandex','Deep10M','SIFT10M','GIST']))
tab='| 数据 | FULL单入口GT教师增量pp | 模型增量pp | 模型兑现教师% |\n| --- | --- | --- | --- |\n'
for ds in DS:
    r=next(x for x in rooms if x['dataset']==ds and x['K']=='100' and x['bank']=='FULL')
    tab+=f"| {names[ds]} | {float(r['C_full_gain_pp']):.4f} | {int(r['model_gain'])/int(r['queries']):.4f} | {100*float(r['model_oracle_gain_fraction']):.1f} |\n"
summary=f'''# ACSG 当前结论

更新于2026-11-02。E197七集候选支持、可预测性与执行方式分离已完成9434点/28302完整T1批次，默认E99 GT10保持（WebVid soft-t1、Yandex hard），无待恢复矩阵。**336个学习器窗口点全部被同窗GT10、OPT-B32或REUSE-SQ覆盖。** 当前prototype不作默认替换；这不否定所有学习器或残差补全。

主要定位：有限C里有可用入口，当前模型只兑现约15.9%–34.0%的同池单入口GT教师增量。下表为FULL、K100/L200、两窗合计，相对完整直接B32的百分点；教师用GT逐query选最好，不能部署，未付识别费用。

{tab}
在上述FULL/K100/L200比较中，COCO/Flickr/GIST两窗的模型选点均优于同数量距离单入口，WebVid/Yandex一窗正一窗负，Deep/SIFT两窗更差；完整QPS均慢约14.7%–44.2%。例如COCO A距离法97.2148%/1550.16 QPS，模型97.2871%/905.50 QPS；选点小幅增量没有抵消在线成本。更大L及强B32/SQ控制基于本轮实际完整wall，不能只比同L GT10。

筛选局部有效但不稳：FULL/K100/L200中COCO/Flickr/Yandex/SIFT保留约93%–96%的已选正收益；WebVid/GIST全部启用；Deep仅保留58.2%，Q8亦仅45.5%，低于cal的90%目标。门在全C预测后才拒绝，只省后续展开。K1多集正例稀疏，全关不等于学会识别。

CBRIDGE增量近零；SHARED在FULL/K100/L200对同适配层AUX追加约0.01–0.30pp，完整QPS慢约3.5%–18.9%；提前入口有救回也有损伤。三类动作均无两窗共同未被强控制覆盖的配置，仍不能外推完整状态续搜或所有实现。生产主核未实现pause/resume。

770个配置对仅保留两个简单观察：WebVid K1/L200 DIST1-FULL（A86.9141%/1134.02，B85.1563%/1140.67 QPS，描述区间含0）和K100/L100 Q8-B32（A64.2852%/2544.02，B63.8535%/2530.67，较更高质量B32仅快约0.38%–0.50%）。有限网格未覆盖不叫默认替换。历史M5/B32/SQ正面场景继续保留其原协议和费用，[历史索引](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)不因本轮结果失效。

后继建议改为部署状态一致的真实效用监督、以DIST1为参照的query内排序、离线强表示/在线两段选择及前置便宜拒绝；均未实现、未测试，详见s-target，不把教师空间当可学习保证。

证据：3485197标签、28候选拟合/14选定模型；全部9434包/28302轮、2768568候选witness、5403128探针、728旧包对齐及独立stdlib整数/hash/wall通过。正式batch wall16018.96秒，其他阶段为嵌套口径。关机后来源分1原持久/11原三轮包SHA恢复/2新GIST；恢复窗work/seed/witness为重放身份。所有证据均在持久磁盘，原日志字节不变、旧seal/PDF不回写，无新PDF。

先读[定位与新方案]({base}/findings_zh.md)、[详细表格]({base}/report_zh.md)、[跨窗]({base}/analysis/stability.csv)、[强控制]({base}/analysis/comparisons.csv)，再读[核验]({base}/delivery_validation.json)。A/B均曝光，单图/画像、有限预算、K1稀疏事件、Q8迁移和未校正多比较的描述区间限制保留。原E195/E196各自收口，不混拼旧绝对QPS。
'''
(REPO/'summary.md').write_text(summary)
target=f'''# ACSG 后续研究问题

2026-11-02。用户授权的“更正主线然后继续实验”已以E197瓶颈分离完成。当前默认E99 GT10保持；本页是后继候选问题，无正在运行或待恢复矩阵。训练费用仍不作当前排除条件，终点为可靠完整Recall–QPS。

E197已确认有限C教师空间、部分选点信号、拒绝泛化落差和完整成本问题。不能把GT选点机会自动转成可部署提升。先读[实测定位]({base}/findings_zh.md)和[全表]({base}/report_zh.md)，不回写旧学习设计的未实现身份。

1. **监督匹配准备部署的动作。** 对实际K/L、候选银行和后端生成真实净救回/损伤/成本标签；表fit、入口fit、cal和确认角色独立，需要联合时cross-fit。Q8→FULL、L200→其他状态明确按迁移处理。
2. **以距离单入口为参照提高识别。** 研究query内排序、收益regret和直接B32/DIST1/学习入口的动作选择。统一减去query常数不改变理想排序，需改变损失和动作准入对象。优先验证COCO/Flickr/GIST的既有信号、WebVid的大教师空间；Deep/SIFT保留作反例和泛化核验。
3. **离线强表示，在线两段选择。** 训练预算可投入图/轨迹效用教师和表示，再蒸馏廉价在线打分、仅小池精排。距离top6会丢约31%–47%全C教师空间，应测试补充来源。导航shortlist不删除完整直接答案。
4. **拒绝放到重评分之前。** 用便宜的query/路由/主状态触发器决定是否付重模型费用；再决定展开及预算，分状态校准正收益保留、误拒和无效启用。当前Deep在Q8也失守，不能只归因FULL迁移；WebVid/GIST K100全开不算筛选成功。
5. **以完整结果决定继续。** 新版本仍与最强适用B32/SQ、DIST1、费用邻近GT10比较完整T1 wall。教师有限池、单点未覆盖、少量尾部修复与可靠默认替换分开；不要求七集全胜，也不追加曝光窗口直到通过。

上述后继方案均THEORY_ONLY_UNIMPLEMENTED_UNTESTED，尚无新训练或实验编号。当前停在E197报告交付边界，不自动扩点、改默认、修图或生成PDF。历史有效M5/B32/SQ与当前简单观察保留为控制，后续具体协议应先冻结模型/角色/点表/计量和结束条件。
'''
(REPO/'s-target.md').write_text(target)
local=f'''# ACSG 当前接续入口

2026-11-02，工作区/data/netg/ACSG，HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62。E197七集瓶颈分离完成9434点/28302完整T1，默认E99 GT10保持，无待恢复矩阵。先读AGENTS、summary、spec、s-target、s-experiment，再读[定位结论]({base}/findings_zh.md)、[详细表格]({base}/report_zh.md)、[交付核验]({base}/delivery_validation.json)。

336学习器窗口点均被强GT10/B32/SQ覆盖；入口内有教师空间，识别和拒绝尚未兑现可靠完整收益。保留WebVid DIST1-FULL/K1/L200和Q8-B32/K100/L100两个有限观察及历史M5/B32/SQ正面场景。新强监督、两段选择和前置拒绝只是后继建议，不是已实现方法。

2026-11-02关机事件已收口：285冻结身份完好；1原持久窗口、11原三轮六数组包SHA恢复窗口、2新测GIST窗口。恢复动作witness为重放来源，旧中断GIST不拼入结果。所有新证据都已持久化：/root/acsg-e197-storage是真实目录，经storage链接；部分归档在/data/acsg-e197-durable-overflow，以持久文件链接访问。RAM只剩可重建临时内容，不是证据依赖。原日志字节不变，部分移动到持久root并保留原路径链接。

读[恢复与持久化]({base}/reviews/persistent_storage_delivery.json)、[恢复完成]({base}/reviews/reboot_recovery_complete.json)、[存储修正]({base}/storage_amendment_20261102.md)。不要按旧PID、旧session或运行中状态重启。原E195/E196/旧设计科学文件及seal保持，根文档以source_before精确桥接。无新PDF，不自动训练/重跑/发布或改默认。
'''
(REPO/'LOCAL_CODEX_START.md').write_text(local)

spec=(REPO/'spec.md').read_text();start=spec.index('### 4.12 E197');end=spec.index('\n## 5.',start)
section=f'''### 4.12 E197瓶颈分离与恢复合同（已实现并完成）

[协议]({base}/protocol.md)、[源码]({base}/src/benchmark.cpp)在独立目录复用只重命名main的E195快照。Q8-B32从旧合法16K教师token筛前8K，按嵌套greedy8/16/32编译；后8K固定2048入口fit/1024 cal，精确向量去重、COCO/Flickr身份组核验另存。旧16K B32保持强控制；GT10画像历史监督重叠披露。Q8模型向FULL、L200向L100/400为固定迁移。

ORACLE-C1/S1读取GT导出的入口mask，是不可部署诊断，GT选择费用不作为在线识别成本，不参与默认/部署比较。正常学习选择只用可部署特征，独立决策核验移除teacher mask。

真实K1/K100、L200、单seed384产生3485197标签。已实现24维ridge及104维固定128轮HGB（原坐标签名投影、前4有效有向出槽摘要等，非训练GNN），28候选拟合/14选定模型。MODEL1全C预测净增量选1入口；MODEL-GATE在评分后按合法cal阈值选0/1入口，完整C直接答案始终保留。DIST1/FULL为同池、同384单入口控制。已实现的门不能省掉已完成的全C评分。

CBRIDGE放开未选C中间点；SHARED用minimal_cached_search保存真实主评分及展开ID，允许已主评分未展开中间点并过滤其他已展开点，仍是独立辅助队列。SHARED-CAPTURE只付捕获并返回直接答案；AUX384-FAST使用同候选计划/适配层且包与原AUX逐字节一致。提前入口只用画像/残差表预评分，最多3槽，替换初始化集合；原GT10路由ID与实际early seed分别保存，不是时机单变量实验。生产search_new仍无完整pause/resume，未修图或改主搜索评分。

正式9434点/28302完整T1，CPU15实际线程1、库线程1、单方法串行。计wall包含正常Batch创建、路由/主搜/评分、特征与预测、状态保存、扩展/合并、六数组复制与销毁；加载、GT、写盘、hash/oracle在外。原/新完整native三轮返回/工作一致；原timed包按1原持久、11原三轮SHA恢复、2新GIST保留身份。四个保存数组加两组零NDC数组和形状构成包SHA；零NDC不是零距离计算，额外work不是总NDC。

恢复实现[recover_packets]({base}/src/recover_packets.cpp)只调用冻结搜索/Runner，必须逐点匹配原日志每轮六数组SHA才复用原wall；恢复时长不作query QPS。60点/416原持久payload资格字节一致。恢复窗work/seed/witness重放，不声称各自丢失原文件SHA已还原。GIST旧中断仅留时长下界，完整进程费未知；新A/B完整重测。285冻结文件和大资产stat、模型参数均不改。

[checkpoint_storage]({base}/scripts/checkpoint_storage.py)在native结束后无损归档raw/witness payload，长窗zstd重编码核整个tar SHA；逐点JSON入带member SHA的metadata tar，完整summary/config/environment仍可读。原gzip包装字节不声明保留。每窗复制/核对持久副本再进入下一窗。最终/root/acsg-e197-storage为真实持久目录，部分packet在/data持久卷，以稳定文件链接访问；原日志亦按字节不变的链接保留，无RAM依赖。[存储例外]({base}/storage_amendment_20261102.md)仅改内部预算，不改冻结协议字节。raw读取仍用原archive.load_packets，逐点JSON可按metadata manifest重建。

验证完成：1344初始捕获/原核调用、6074996缓存评分词、8064辅助线性合并；精简捕获再核并保持952旧运行包。正式分析核9434包、2768568候选witness、5403128GT探针，728旧包字节一致；逐候选native/NumPy模型选择及门分支、stdlib独立整数/hash/wall核验全部通过。独审是同执行者不同实现，不重跑所有图标签或独立bootstrap。恢复动作证据身份随前段注明。具体结果和默认决定只读summary，后继强表示/前置拒绝尚未实现。
'''
spec=spec[:start]+section+spec[end:];spec=spec.replace('更新于2026-11-01。','更新于2026-11-02。',1);(REPO/'spec.md').write_text(spec)

index=(REPO/'s-experiment.md').read_text();cut=index.index('2026-11-01设计汇报：')
index='# ACSG 实验与研究索引\n\n更新于2026-11-02。最新完成E197七集瓶颈分离（9434点/28302完整T1）；前序E196费用邻近控制（837/2511）与E195详细定位（1260/3780）保持原身份。当前结论与默认读summary，实现读spec，后继读s-target。\n\nE197结果：[定位与新方案]('+base+'/findings_zh.md)、[全表]('+base+'/report_zh.md)。336学习器窗口点均被强控制覆盖，保留两个简单观察；默认E99保持，无待恢复队列。\n\n'+index[cut:]
index=index.replace('新算法THEORY_ONLY_UNIMPLEMENTED_UNTESTED；只复算E195已有探针，无新训练/ANN/QPS或实验编号，最新完成实验仍E196。','该设计当时为THEORY_ONLY_UNIMPLEMENTED_UNTESTED，仅复算E195已有探针；当时最新完成E196。其后部分机制在E197独立实现/测量，旧设计封存不回写。')
index=index.replace('无新实验编号或性能，最新完成仍为E194；','该次无新实验编号或性能，当时最新完成为E194；')
index=re.sub(r'^\| E197 \|.*$', '| E197 | 候选支持、可预测性、执行路径/时机 | 完成9434/28302；336学习窗口被强控制覆盖，默认保持 | [卡片](experiment_history/197_residual_bottleneck_separation_v1.md) |',index,flags=re.M)
(REPO/'s-experiment.md').write_text(index)

history=f'''# E197 候选支持、可预测性与执行方式分离

2026-11-01启动，2026-11-02完成。用户授权更正主线并继续实验，训练费用不作当前否决条件。固定范围9434点/28302完整CPU15/T1批次已收口，默认E99 GT10保持，无新PDF。

## 动机与机制

原预设先训练强入口，现分开候选支持、收益可预测性及执行路径/初始化方式。前8K合法角色编Q8-B32，后8K固定2048 fit/1024 cal；COCO/Flickr身份组及精确向量排重，原GT10监督身份披露。旧16K B32作为强控制，学习器在Q8/L200拟合校准，FULL及其他L为固定迁移。

七集真实K1/K100全C单seed384标签3485197条；比较ridge/HGB并选14模型，门可不展开但保留全部直接C答案。与同数量DIST1、原3seed AUX、同适配层AUX-FAST、CBRIDGE、SHARED、捕获空动作、预先可用信息的EARLY初始化和强GT10/OPT-B32/SQ比较。GT逐query教师不可部署；SHARED不是主beam恢复，EARLY替换入口集合。

## 实测判断

336学习器窗口点全部被本轮强控制覆盖。FULL/K100/L200模型兑现同池教师约15.9%–34.0%；COCO/Flickr/GIST两窗选点胜距离，WebVid/Yandex交叉，Deep/SIFT更差，完整QPS均慢约14.7%–44.2%。门在COCO/Flickr/Yandex/SIFT保留约93%–96%已选正收益；WebVid/GIST全开，DeepFULL58.2%、Q845.5%，未达到cal90%目标。

{tab}
共享在固定距离seed上有真实追加救回，但当前完整费用未胜强控制；提前入口有损伤，WebVid负、Yandex局部正。770配置对仅WebVid DIST1-FULL/K1/L200、Q8-B32/K100/L100两窗未覆盖，前者描述区间含0，后者较更高质量完整B32只快约0.38%–0.50%；均不记默认替换。历史有效M5/B32/SQ不受此有限结果否定。

## 成本与恢复

离线标签进程672.13秒，模型拟合117.40秒（含失败环境启动）；正式batch wall16018.96秒。校准、构建、诊断、恢复与归档是嵌套口径，不相加成完整项目耗时。关机后包恢复额外3350.63秒；旧GIST中断进程完整时长未知。

首窗原始证据量触发存储保护，COCO B一次286.94秒尝试全部原字节单独存档后完整重跑。后续关机清空RAM，285冻结身份全保留；COCO A原磁盘包、11窗原三轮SHA恢复包、GIST两窗新测组成正式结果。恢复先以60点/416原件payload字节资格通过，再对全部恢复点匹配每轮六数组SHA；仅如此才复用旧wall。work/seed/witness为重放身份，不声称原丢失文件各自SHA已恢复。每窗验证并持久化后再继续，最终无RAM依赖，部分归档及原日志以持久文件链接访问。

## 验证与边界

原捕获1344调用、6074996评分词、8064线性合并；精简核全分支资格和952旧包对齐。最终9434包/28302轮、2768568候选witness、5403128探针和728旧包对齐；逐候选native/NumPy推断、门分支、stdlib全部GT整数/hash/wall与1624项费用提出检查通过。同执行者不同实现，不独立重采样bootstrap或重跑全部标签。A/B曝光、单图/画像、固定预算、K1少量事件、迁移和多比较限制保留。

后继状态一致监督、query内排序、离线强表示/在线两段选择及前置拒绝均未实现、未测试；本轮不自动扩大实验。旧E195/E196/设计科学文件、原PDF和seal保持，根文档按精确source_before桥接。

## 原始证据

- [定位与新方案](../{base}/findings_zh.md) · [详细报告](../{base}/report_zh.md) · [协议](../{base}/protocol.md) · [freeze](../{base}/formal_freeze.json)。
- [实际点](../{base}/analysis/points.csv) · [强控制](../{base}/analysis/comparisons.csv) · [跨窗](../{base}/analysis/stability.csv) · [瓶颈](../{base}/analysis/bottlenecks.csv)。
- [主核验](../{base}/analysis/analysis_receipt.json) · [stdlib](../{base}/analysis/stdlib_audit.json) · [成本](../{base}/analysis/cost_ledger.json) · [持久化](../{base}/reviews/persistent_storage_delivery.json) · [最终交付](../{base}/delivery_validation.json)。
'''
(REPO/'experiment_history/197_residual_bottleneck_separation_v1.md').write_text(history)
p=REPO/'experiment_history/README.md';t=p.read_text();t=re.sub(r'^- \[E197[^\n]*$', '- [E197 候选支持、可预测性与执行方式分离](197_residual_bottleneck_separation_v1.md)：2026-11-02完成9434点/28302完整T1；336学习窗口被强控制覆盖，默认保持，恢复来源与边界见卡片。',t,flags=re.M);p.write_text(t)
dump(R/'reviews/document_sync.json',dict(status='PASS_ACTUAL_RESULTS_AND_IMPLEMENTED_CONTRACT_DOCUMENT_SYNC',
    snapshots=str(snap),files=[dict(path=str(REPO/n),sha256=sha(REPO/n)) for n in roots],
    theory_proposals_separate=True,default_changed=False,old_scientific_files_not_rewritten=True))
print('ROOTS_AND_HISTORY_SYNCHRONIZED',flush=True)
