from common import *
points=list(csv.DictReader((R/'analysis/points.csv').open()))
comp=list(csv.DictReader((R/'analysis/comparisons.csv').open()))
stable=list(csv.DictReader((R/'analysis/stability.csv').open()))
rooms=list(csv.DictReader((R/'analysis/bottlenecks.csv').open()))
names=dict(zip(DS,['COCO','Flickr','WebVid','Yandex','Deep10M','SIFT10M','GIST']))
idx={(r['dataset'],r['window'],r['K'],r['L'],r['method']):r for r in points}
def table(head,rows):return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)+'\n'
def f(x,d=4):return '—' if x in ['',None] else f'{float(x):.{d}f}'
def room(ds,K='100',bank='FULL'):return next(x for x in rooms if x['dataset']==ds and x['K']==K and x['bank']==bank)
text=['''# E197定位结论：有好入口，现有识别与拒绝还没有兑现完整收益

2026-11-02完成。默认继续E99 GT10（WebVid soft-t1、Yandex hard）。本轮七集、真实K1/K100、两窗、9434点/28302完整T1批次全部收口。**336个学习器窗口点全部被本轮同窗口GT10、OPT-B32或REUSE-SQ覆盖；不推荐当前学习器或门替换默认。** 这限定于本轮ridge/HGB、特征、候选、预算和曝光窗口，不是对所有学习方法或残差补全的否定。

我需要修正此前的建议：不能从“GT能挑到好入口”直接跳到“训练强模型即可突破”。本轮确认了候选内机会，也测出了识别落差、拒绝不稳定和在线评分开销。训练费用仍不作为当前排除条件，后继投入应验证可部署信息能否提高真实搜索效用。

## 1. 好入口并不少，但当前模型只兑现了一部分

以下为FULL、L200、单seed384预算、两窗合计。增量均相对同query完整16K直接B32，单位为Recall@100百分点；GT教师逐query选最好单入口并可不执行，识别费用未计，不能部署。WebVid等原固定表正面场景继续保留。

''']
t=[]
for ds in DS:
    r=room(ds);scale=1/int(r['queries'])
    t.append([names[ds],f(int(r['distance_single_gain'])*scale),f(int(r['model_gain'])*scale),
        f((int(r['model_gain'])-int(r['distance_single_gain']))*scale),f(r['C_full_gain_pp']),
        f(100*float(r['model_oracle_gain_fraction']),1),f(r['shared_pool_gain_pp'])])
text.append(table(['数据','距离单入口增量','模型增量','模型−距离','GT最好C','模型兑现教师%','GT共享扩源'],t))
text.append('''当前模型兑现约15.9%–34.0%的同池单入口教师增量。COCO、Flickr、GIST在两窗均比距离单入口选得好；WebVid、Yandex一窗正、一窗负；Deep、SIFT两窗均更差。两窗合并后的正值不能掩盖这个区别。

Deep/SIFT的有限C导航教师仍有约0.86/0.69pp增量。旧固定答案ID重复性弱，不能直接推出它们没有入口价值：入口可以沿图找到源表之外的新GT。零增量也只描述当前query、主搜索状态和预算，不能给节点贴永久坏标签。

全C教师明显强于距离前6个C内教师；前6仅保留约53%–69%的全C教师增量。不过即使前6的教师也高于当前模型，说明已有候选内的识别值得研究。共享中间点及增加已评分未展开前16个候选后，教师空间再提高约0.08–0.28pp；本有限池内，这小于当前模型与全C教师的差距。该差距不是可学习性的证明。

## 2. 入口质量的小幅改善没有抵消完整在线开销

以下均为A窗、FULL/L200/K100，完整Recall百分数/QPS。B窗和全部L见详细报告。单入口距离法与模型共用候选池、直接答案和384扩展预算。

''')
t=[]
for ds in DS:
    d=idx[ds,'A','100','200','DIST1-FULL'];m=idx[ds,'A','100','200','MODEL-FULL']
    t.append([names[ds],f(d['recall_pct'])+' / '+f(d['qps'],2),f(m['recall_pct'])+' / '+f(m['qps'],2),
        f(m['gain_vs_distance1_pp']),f(m['qps_gain_vs_distance1_pct'],2)+'%'])
text.append(table(['数据','距离 R%/QPS','模型 R%/QPS','模型ΔR pp','模型ΔQPS'],t))
text.append('''两窗中模型相对距离单入口的完整QPS下降约14.7%–44.2%。这是真实prototype完整费用，包含特征、预测、排序/选择、搜索和输出；不是神经模型或所有实现的成本下界。当前实现有可缓存的query级量及批量评分机会，但没有分段干预证明各因素分别贡献多少，不能把全部开销归给某个特征。

对照进一步加入同窗费用邻近的更大L GT10、强B32和SQ，全部336个学习器点被覆盖；只比同L GT10会高估新方法价值。GT教师的增量、模型选点的增量与完整Recall–QPS是三个不同结论。

## 3. 拒绝筛选有局部效果，泛化尚不可靠

以下FULL/K100/L200，两窗合计。保留率分母为模型全开时已选正入口的正收益总量；90%是cal约束，正式查询上需要重新检查。

''')
t=[]
for ds in DS:
    r=room(ds);n=int(r['queries'])
    t.append([names[ds],f(100*int(r['gate_enabled_queries'])/n,1),f(100*float(r['gate_useful_precision']),1),
        f(100*float(r['gate_chosen_positive_gain_retention']),1),r['gate_wrong_reject_positive_queries']])
text.append(table(['数据','实际启用%','启用有用%','正式正收益保留%','误拒已选正入口query'],t))
text.append('''COCO/Flickr/Yandex/SIFT保留约93%–96%的已选正收益，同时关闭约14%–18%的调用，但启用精度仍低。WebVid、GIST在K100完全启用，没有实现调用筛选。Deep关闭约57%调用，却仅保留58.2%正收益；Q8本身也只保留45.5%，因此不能把失败全归给FULL迁移。应单独验证校准、正例稀疏和状态变化，当前没有隔离出唯一原因。

当前门在全部C预测完成后才判断拒绝，能省展开，不能收回已经支付的评分费用。它也没有从表中删直接答案。K1正例在多集很稀疏：FULL两窗COCO/Flickr/Deep/SIFT/GIST的可用C正入口query仅4/1/5/1/13；全关和高准确率不代表学会拒绝。WebVid/Yandex为98/44，仍需与完整费用分别评价。

## 4. 放开路径和提前入口，结果怎样

CBRIDGE只放开未选C作为中间点，FULL/K100/L200增量接近零且部分为负。SHARED对同适配层AUX有约0.01–0.30pp新增Recall，完整QPS再降约3.5%–18.9%。应将真实救回保留为局部正面证据，但这些版本没有形成两窗均未被强控制覆盖的配置。此实现仍是带真实主评分缓存的独立辅助队列，生产主核没有完整pause/resume。

EARLY-MIX保留两个画像入口、换入最近C；它改变初始化集合和轨迹。Yandex的FULL/K100/L200两窗约+0.31/+0.25pp；WebVid却约−0.28/−0.31pp，救回267/410成员的同时损失410/570成员。提前入口不是普遍改进，也不是时机单变量的因果证明。不能只报救回。

严格低召回尾部（GT100命中0–9个）也有局部修复：WebVid两窗B32有3个失败，距离/模型为2个，SHARED为1个；Yandex B32为7个，模型为6个。其余五集在此L没有失败分母。这些少量事件不能替代完整Recall–QPS或推出普遍修复率。

## 5. 仍保留的两个观察配置

770个非GT/OPT/SQ配置对中，仅以下两个在A/B都未被有限强控制网格覆盖。不是新算法成功数或默认替换依据。

''')
t=[]
for m,K,L in [('DIST1-FULL','1','200'),('Q8-B32','100','100')]:
    for w in ['A','B']:
        r=idx[DS[2],w,K,L,m];c=next(x for x in comp if x['dataset']==DS[2] and x['window']==w and x['K']==K and x['L']==L and x['method']==m)
        t.append([m,K,w,f(r['recall_pct'])+' / '+f(r['qps'],2),c['no_slower_control'],
            f(c['gain_vs_no_slower_pp']),f(c['quality_threshold_qps_gain_pct'],2)+'%'])
text.append(table(['WebVid方法','K','窗','R%/QPS','不更慢控制','对该控制ΔR pp','质量阈值ΔQPS'],t))
text.append('''DIST1-FULL的配对query描述区间含0，不作稳定显著提升结论。Q8-B32相对GT10的不更慢控制区间为正，但相对质量更高的完整B32/L100，速度仅高约0.38%–0.50%，是很薄的费用取舍。质量阈值对照可有更高Recall，不叫精确同Recall加速。两者都保留作后继参考，不追加查询直到通过。

历史E173 M5、E191 B32/SQ及E194等价省费正面场景仍有效于各自原协议、窗口和实现；本轮结果不抹去它们，也不拼接它们的绝对QPS。

## 6. 新的改进方案：部署动作一致的效用监督、两段选择、前置拒绝

下面是建议，**未实现、未训练、未测试**。当前E197实现与这些后继建议分开。

1. **训练监督对齐实际动作和状态。** 用真实搜索的净新增命中、损伤和工作量，而非距离/度数代理；分别覆盖准备部署的K、L、候选表和后端。Q8→FULL、L200→其他L应明确作为迁移，不能假定校准可直接沿用。表拟合、入口fit、cal与确认query保持独立，需联合训练时用cross-fitting避免自己的直接答案进入监督造成偏移。
2. **以距离单入口为明确参照学习。** 训练query内成对排序和高收益错选的regret，评价比DIST1多救回多少、损伤多少。每query统一减去距离收益不会改变理想排序；关键是排序损失、动作选择和拒绝比较对象改变。允许直接B32、DIST1、学习入口三种动作，不能用额外模型开销换取已经由距离法取得的收益。
3. **离线强表示，在线两段排序。** 可投入更多训练到图/轨迹表示与实际效用教师，再蒸馏到廉价query–node打分；先低成本筛出小池，再用较强模型精排。距离前6是必要参照但会丢31%–47%全C教师空间，宜保留学习/结构来源的补充位置。小池只限制导航选择，直接C答案继续完整保留。
4. **先决定是否付评分费用，再决定是否展开。** 便宜的query/路由/主状态触发器放在重模型之前；再估计所选动作的增量、风险与预算。按数据/K/L/候选银行独立校准，增加正例覆盖并报告误拒收益、无效启用和完整wall。90%校准保留率是经验目标，不能当测试保证。
5. **按证据分配下一轮训练。** WebVid/K100教师空间最大但当前模型未稳定胜距离；COCO/Flickr/GIST已见两窗一致的选点信号，适合检验更好的表示能否增加收益。Deep/SIFT保留作重要反例与拒绝泛化检查，不因固定答案源弱而排除入口路径研究。任何新实现都继续与最强适用B32/SQ、DIST1和费用邻近GT10比较完整成本。

优先问题是“已有C里哪些收益能被部署信息识别，并以合理在线费用兑现”。若更强监督仍不能稳定超过距离参照，应据结果调整候选来源或动作，而不是把GT教师空间当作必能学会的收益。离线训练费不限制这项验证；本轮没有证明下一版会成功。

## 7. 本轮交付与证据限制

共3,485,197条真实单seed标签、28个候选拟合/14个选定模型；离线标签进程672.13秒，模型拟合117.40秒。正式完整batch wall合计16018.96秒；其他加载、校准、诊断、恢复与归档是不同嵌套口径，不相加称完整项目成本。重启后的SHA恢复额外3350.63秒；旧中断GIST完整耗时未知，保留下界。费用见账本。

主分析核9434点的真实包SHA、2,768,568条候选witness、5,403,128条探针；728点旧包字节对齐。第二份stdlib实现独立核全部GT整数、hash、wall和1624项费用提出检查。模型还通过无GT特征的native/NumPy逐候选与全开/拒绝ID核验。同执行者不同实现，不称独立人员审查；未独立重做bootstrap或全部图标签。

关机后的证据来源为1个原磁盘窗口、11个原计时包SHA恢复窗口、2个新GIST窗口。恢复只有六数组包逐点匹配原三轮SHA才复用原完整wall；work/seed/witness为重放来源，不声称丢失原件各自SHA已恢复。COCO60点/416份原件资格逐字节一致。所有窗口和最后分析资产已持久化，无RAM依赖，原日志以字节不变的稳定链接保留；旧科学seal/PDF不回写。

A/B均曝光、单图/画像、有限L/384预算、K1稀疏事件和Q8迁移限制保留。描述性bootstrap未作多比较同时校正。当前不改默认，不生成新PDF，不启动下一轮。

- [详细表格报告](report_zh.md) · [实际点](analysis/points.csv) · [强控制](analysis/comparisons.csv) · [跨窗配对](analysis/stability.csv)。
- [候选/识别/筛选](analysis/bottlenecks.csv) · [质量教师图](analysis/figures/quality_headroom.svg) · [完整费用A](analysis/figures/complete_wall_A.svg) · [完整费用B](analysis/figures/complete_wall_B.svg)。
- [主核验](analysis/analysis_receipt.json) · [stdlib核验](analysis/stdlib_audit.json) · [模型决策核验](analysis/decision_audit.json) · [成本账](analysis/cost_ledger.json)。
- [恢复依据](reviews/reboot_recovery_complete.json) · [持久化证明](reviews/persistent_storage_delivery.json) · [原协议](protocol.md) · [存储修正](storage_amendment_20261102.md)。
''')
(R/'findings_zh.md').write_text('\n'.join(text))
(R/'README.md').write_text('''# E197 残差入口瓶颈分离

2026-11-02完成七数据集、K1/K100、两窗、9434点/28302完整T1。默认E99 GT10保持；训练费用不作当前排除条件。先读[定位结论与新方案](findings_zh.md)，再读[详细表格报告](report_zh.md)。

本轮确认有限C入口的GT教师空间，模型实现局部选点改善，但336学习器窗口点均被同窗强GT10/B32/SQ覆盖，拒绝泛化不足。保留WebVid两个简单观察配置和历史M5/B32/SQ正面场景。新监督/两段选择/前置拒绝为未实现建议。

- 方法和角色：[协议](protocol.md)、[角色冻结](role_freeze.json)、[正式冻结](formal_freeze.json)、[源码](src/benchmark.cpp)。
- 数值：[全部点](analysis/points.csv)、[强控制](analysis/comparisons.csv)、[跨窗](analysis/stability.csv)、[瓶颈](analysis/bottlenecks.csv)。
- 核验：[主分析](analysis/analysis_receipt.json)、[stdlib](analysis/stdlib_audit.json)、[模型决策](analysis/decision_audit.json)、[成本](analysis/cost_ledger.json)。
- 图：[教师空间](analysis/figures/quality_headroom.svg)、[费用A](analysis/figures/complete_wall_A.svg)、[费用B](analysis/figures/complete_wall_B.svg)。
- 重启：[恢复资格](reviews/recovery_qualification.json)、[窗口恢复](reviews/reboot_recovery_complete.json)、[持久化](reviews/persistent_storage_delivery.json)、[存储修正](storage_amendment_20261102.md)。
- 收口：[交付核验](delivery_validation.json)、[文件身份](delivery_manifest.json)。

原timed包身份按1原持久/11原三轮SHA恢复/2新GIST区分；恢复窗动作witness为重放来源。公开A/B不是盲确认，不改默认、无新PDF、无待恢复矩阵。新输出在/root/acsg-e197-storage，部分已核验packet归档在/data/acsg-e197-durable-overflow，由稳定文件链接访问，均为持久磁盘。逐点JSON、raw与候选payload可按各archive manifest无损恢复；旧科学文件和seal保持原身份。
''')
print('FINDINGS_AND_READER_ENTRY_WRITTEN',flush=True)
