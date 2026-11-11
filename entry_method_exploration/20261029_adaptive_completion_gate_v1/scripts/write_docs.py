from common import *
C=read(R/'analysis/case_summary.json');V=read(R/'analysis/verdict.json');rel=R.relative_to(REPO);link=f'{rel}/report_zh.md'
def table(head,body):return '| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in body)
body=[]
for v in C:
 body.append([LABEL[v['dataset']]+'/'+str(v['K']),f"{v['sq_gain_pp']:.4f}",f"{100*v['ideal_on_rate']:.2f}%",f"{100*v['learned_on_rate']:.2f}%",'无增益' if v['learned_gain_retained'] is None else f"{100*v['learned_gain_retained']:.2f}%",f"{v['sq_qps']:.1f} / {v['ideal_qps']:.1f} / {v['learned_qps']:.1f}",'是' if v['learned_combined_cover'] else '否'])
tab=table(['数据/K','全开增益pp','理想启用','学习启用','学习保留增益','全开/理想/学习 QPS','学习被GT10或B32覆盖'],body)
summary=f'''# ACSG 当前结论

更新于2026-10-29。用户要求验证“优化残差后端＋自适应开关”两方向，E193已完成三集真实K1/K100、固定2048查询窗口的102点/306完整T1轮；另有36资格点和开发动作费用测量。默认E99 GT10保持：WebVid GT10-soft-t1、Yandex GT10-hard。无待恢复矩阵。

收益集中确实成立：E191七集旧实际包复核，Deep/SIFT K100/L200分别仅8.05%/7.42%查询有增益，COCO为71.7%。全开不划算不能否定选择性补全，E192对原全开费用的排除证书也不能外推门控后的费用。

本轮实际门在主搜索后复用route/main的廉价特征，不增加独立probe。合法末4K分成2K拟合、2K校准，模型与阈值在正式前冻结；旧GT10监督重叠保留披露。理想门用GT判断每条query是否有正净收益，真实付出条件执行费用，只作不可部署参考。

{tab}

以上每行Recall与QPS均来自相同2048查询，QPS为三轮完整wall中位数；保留比例针对补全新增正确成员。学习门{V['learned_GT10_or_B32_covered_cases']}/6组被GT10或已有B32在Recall和中位QPS同时覆盖。有增益的{V['positive_gain_cases']}组中，理想门均未被当前固定GT10/B32网格覆盖，只代表探索空间，不是默认替换证据；零增益两组的微小QPS差不计新潜力。Deep/SIFT K1无增益时模型回退全关，不算预测成功。

当前判断：后端费用/候选收益与开关识别能力应作为两项可分别验证的条件。收益集中已经确认；当前廉价模型仍有大量无效启用，尚未把理想开关空间变成可靠的净收益。不能把当前候选模型未过门说成所有自适应算法不可能，也不要求全开先胜出才准研究开关。各组理想门与GT10、B32的具体关系以报告的同窗口表为准。

E192的严格结论仍有效：新增正确成员必须在候选支持集中；固定训练遗漏ID源受遗漏交集上界约束。块法可以救回旧残差ID源之外的目标，所以“不共享目标ID则所有方法无用”不成立。完整旧结论读[E192报告](entry_method_exploration/20261029_sharing_necessity_v1/report_zh.md)，不将当前开关验证改称分布共享因果实验。

[详细报告]({link}) · [102点]({rel}/analysis/formal_points.csv) · [六组摘要]({rel}/analysis/case_summary.csv) · [动作费用]({rel}/analysis/action_cost.csv) · [冻结协议]({rel}/protocol.md) · [实现合同](spec.md) · [后继问题](s-target.md)。

证据边界：公共test历史曝光，一套图/画像、2048探索窗口，无新盲确认；同一执行者不同实现核验，非独立人员复现。正式GT不进可部署门；ORACLE明确知情。GT10/B32/SQ与E191同ID实际返回逐字节相同，所有门控分支/三轮包/访问计数核验通过。旧E191 PDF和E192科学原件/seal不回写；根文档旧字节保存于[E193修改前快照]({rel}/source_before/)，迁移映射见本轮reviews。新增产物/root/acsg-e193-storage经storage链接，无新PDF。
'''
(REPO/'summary.md').write_text(summary)
spec=(REPO/'spec.md').read_text();insert=f'''### 4.8 E193条件残差开关（已实现并完成pilot）

[源码]({rel}/src/benchmark.cpp)通过重命名main嵌入原E191实现，原文件不改；GT10/B32/REUSE-SQ直接复用旧调用，条件分支在真实原NSG主搜索之后执行同一SQ complete，原32块/2048码/96精算和metric不改。新Gate支持off/on、标准化ridge双头和深度3 CART双头；gain/cost得分与冻结阈值比较。特征仅来自原query范数、route profile摘要及当前主返回D摘要，ROUTE5项/POST12项；未新增独立预查询probe或读取GT的可部署特征。

开发取原合法16K残差角色相对[12000,14000)拟合、[14000,16000)校准，新块表前12K不重训。旧GT10监督可能用过16K，旧B32包含末4K标签所以只作正式参考。拟合2特征族×2模型×7阈值，校准保留>=90%正收益后最小估计费用，允许全开/全关回退；实际模型见[冻结]({rel}/formal_freeze.json)。推断预算0.5us仅为校准估计，实际QPS计真实调用。

真实三集两K、2048固定query、12个GT10 L与L200五个辅助方法，共102点/306轮；资格36点、开发12点另计。完整timer覆盖Batch生命周期、路由/主搜索、特征/模型/开关、条件complete和六数组复制。GATE-ORACLE预载GT导出的正收益mask，实际付开关与条件执行费用，严格诊断、不可部署。GATE-OFF用于观察条件核费用，不以微计时简单相加替代wall。另保存三次逐query complete微计时，仅动作费用选择用。

实际四数组、enabled.u8、access.u64、三轮wall/hash在storage保留；native全query全排序SQ oracle，Python核Recall/损伤/门分支/推断/访问量/hash，L200三旧方法与E191同query字节对齐。封存、数据角色和原E192根文档迁移映射均独立，不改旧seal；默认未改，结论见summary，完整证据见[报告]({link})。

'''
spec=spec.replace('## 5. 指标、计时与证据',insert+'## 5. 指标、计时与证据');spec=spec.replace('[本轮详细PDF]','[E191详细PDF]');spec=spec.replace('新块表末4K不参与本轮拟合或配置选择；','E191当时新块表末4K不参与其拟合或配置选择；E193现另将其划分为独立门拟合/校准角色；');(REPO/'spec.md').write_text(spec)
target=f'''# ACSG 后续研究问题

2026-10-29。E193固定验证已完成，无待恢复矩阵，默认E99 GT10保持。当前结论读[summary](summary.md)，实现读[spec](spec.md)，详细验证读[报告]({link})。以下是后续提案，未自动启动。

1. 对理想开关仍有固定网格空间的组，优先改善廉价识别：预测补全增量/费用；route-only查询前特征与主搜索后复用特征分开评估，不能把难查询等同于可补查询。合法训练/校准/确认集分离；稀少改善事件须报告数量与不确定性。当前ridge/浅树只是有限候选族，不据其负结果排除所有算法。
2. 对连全收益保留理想门也被更大L GT10覆盖的组，优先检查固定开关费用、动作费用、候选支持或收益；本轮未穷尽舍弃部分增益的其他oracle策略，不能作为所有门控无效的证明。固定源支持不足时扩大相同ID表不能突破集合上界；块法要同时检验覆盖、shortlist和精算容量。后端优化与开关研究允许并行，不要求全开先胜出。
3. 任何新门都必须比较GT10、全开、全关、理想参考和已有B32，并在相同查询窗口测完整T1 wall；省掉动作、救回成员、微计时下降均不能代替Recall–QPS证据。控制网格、模型、阈值和结束边界先冻结，不追加到通过。
4. 当前公共test和单图仅探索。若出现相对GT10/B32均有价值的完整点，再用合法新查询及必要的图/画像复核，满足实际收益后考虑默认。E191保留探索点、E192源上界/重配证据继续保留各自身份，不把不同窗口QPS和Recall拼成新点。

可按每组[理想/学习/控制摘要]({rel}/analysis/case_summary.csv)选择后继问题；本轮没有授权或启动这些后续矩阵。旧科学产物、PDF与seal保留。
'''
(REPO/'s-target.md').write_text(target)
p=REPO/'s-experiment.md';s=p.read_text();parts=s.split('\n\n');parts[1]=f'更新于2026-10-29。最新完成E193自适应残差开关验证（三集两K、102点/306T1）；E192保留共享必要条件与重配证据，E191保留七集综合矩阵和PDF。当前判断读[summary](summary.md)，实现读[spec](spec.md)，后继提案读[s-target](s-target.md)。历史卡片里的“当前/待执行”仅指原记录时点。';s='\n\n'.join(parts);s=s.replace('| E192 |', '| E193 | 自适应残差开关最小验证 | 完成102点/306T1；收益集中与理想/学习费用分开验证，默认不变 | [卡片](experiment_history/193_adaptive_completion_gate_v1.md) |\n| E192 |',1);p.write_text(s)
p=REPO/'experiment_history/README.md';s=p.read_text();parts=s.split('\n\n');parts[1]='更新于2026-10-29。最新正式实验是[E193](193_adaptive_completion_gate_v1.md)自适应残差开关验证；E192保留共享必要条件与受控重配，E191保留七集两K综合测试和PDF身份。当前结论见[summary](../summary.md)，简要索引见[s-experiment](../s-experiment.md)。';s='\n\n'.join(parts);s=s.replace('| [192_sharing', '| [193_adaptive_completion_gate_v1.md](193_adaptive_completion_gate_v1.md) | E193：收益异质性、理想开关与廉价门完整费用验证 |\n| [192_sharing',1);p.write_text(s)
card=f'''# E193 自适应残差开关最小验证

2026-10-29。用户在讨论“优化残差后端＋廉价自适应开关”后明确要求验证。区别于E192固定全开费用证书，本轮允许跳过部分查询的补全，测试全开失败是否仍有选择性空间。不是换名重跑旧全开方法。

范围：三集COCO/Deep10M/SIFT10M，各随机固定2048公共query，真实K1/K100，GT10固定12个L及L200五个辅助方法；102点/306完整T1轮、36资格点。旧七集实际包仅做收益异质性，不新增七集QPS。开发独立拟合2K/校准2K来自旧合法16K的末4K，残差块表仅前12K；旧GT10监督重叠披露，B32旧16K只作正式参考。线程1、CPU15、费用与落盘边界见协议。

{tab}

学习门被GT10或B32同时覆盖{V['learned_GT10_or_B32_covered_cases']}/6组；理想门在4个有增益组均未被当前固定网格覆盖；另两组K1无增益，其微小QPS差不计新潜力。比例保留针对残差新增成员而非主Recall，QPS为相同2048窗口三轮中位数。ORACLE使用GT导出的正收益mask并真实运行条件动作，非可部署、非全局最优定理。廉价门在主搜索后复用query/route/D特征，冻结ridge/浅CART预测增量/成本，只在校准选阈值；全关回退不当作识别成功。

结论：收益集中成立，全开不优不能否定选择性补全；理想潜力、可预测性、付费收益要分别证明。当前候选模型尚无相对GT10/B32的可靠替换依据，默认E99不改。不将有限模型的结果外推所有门控，后续依据每组理想门差距分别研究识别或后端动作费用/支持。

完整输入、模型、102点Recall/增益/损失/启用/扫描/精算/QPS和三轮范围见[详细报告](../{link})、[协议](../{rel}/protocol.md)、[冻结](../{rel}/formal_freeze.json)、[完整点表](../{rel}/analysis/formal_points.csv)。native全排序oracle、Python分支/推断/Recall/hash/旧实际字节核验通过。同执行者不同实现、一图/画像、旧公共test、小窗口，非盲确认。原E191/E192科学产物/PDF/seal不回写，旧根字节由source_before和迁移收据关联。固定矩阵已完成，无待恢复队列，无新PDF。
'''
(REPO/'experiment_history/193_adaptive_completion_gate_v1.md').write_text(card)
(REPO/'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

2026-10-29，/data/netg/ACSG。E193自适应残差开关固定验证完成，默认E99 GT10保持，无待恢复矩阵。分支/HEAD以git实际值为准，成果主要未提交。

先读AGENTS、summary、spec、s-target、s-experiment，再读[E193报告]({link})、[六组摘要]({rel}/analysis/case_summary.csv)、[协议]({rel}/protocol.md)、[正式冻结]({rel}/formal_freeze.json)、[状态]({rel}/state.json)。

收益集中成立，GT知情理想开关、真实廉价模型与完整费用分别评价；当前有限模型与保留>=90%校准增益的选择策略无默认替换依据。E192固定全开费用排除不适用于改变启用比例后的费用；固定源支持必要条件继续有效，身份共享不是所有块法必要条件。门在主搜索后复用状态，纯预查询probe未实施。

新三集真K1/K100共102点/306完整T1、36资格点。公共test曝光、每组2048窗口、一套图/画像，非新盲确认。数据/root/acsg-e193-storage经storage链接。E191 PDF与E192原件/seal不改，旧可变根字节映射到本轮source_before；原seal不得回写。

可复制接续：请先只读核HEAD与根文档，再读E193完整报告、冻结和完整wall比较。已完成固定矩阵，无待恢复队列。按我本次明确任务继续，区分增量可救性、理想参考、可部署特征和付费收益，不自动扩大矩阵或改默认。
''')
print('E193_ROOT_DOCS_SYNCHRONIZED')
