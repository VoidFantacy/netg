from common import *
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
s=read(O/'results/selection.json')['datasets'];v=read(O/'reviews/verification.json');b=read(O/'results/build.json')['datasets']
history=R/'experiment_history/55_multimode_index.md';assert not history.exists()
text='# E66 GT10多画像单小索引\n\n2026-09-13，完整训练/历史辅助开发已执行，非最终wall。固定原真实H和GT10归属，每hub保留P加两模态；physical3H、search7slot去重为3真实hub。WebVid soft归属全部保留；固定20轮和父mass8/ESS16、子mass2/ESS8，不合格重复P。两个新增slot按子质量分raw prior1，总query质量保持，原P额外保存。旧E10是GT1硬盆、原top32内64点积重排；此处直接同一小图检索，不宣称新颖性。\n\n'
for bb in b:
    ds=bb['dataset'];x=s[ds];text+=f"{ds}：{bb['eligible_two_modes']}/{bb['total_hubs']}个hub有合格双模态；相对baseline fit净{x['fit_net_hits']:+d}、aux净{x['aux_net_hits']:+d} GT10命中，两半{x['aux_halves']}，aux失败净{x['aux_failure_net_change']:+d}；aux相对同容量duplicate控制净{x['aux_net_vs_duplicate']:+d}。预锁开发门{'通过' if x['passed'] else '失败'}，不把局部正值或NDC当完整性能。\n\n"
text+='画像全部冻结后测完整fit20K和aux7952；aux来自历史router_train[2048:10000]，两半均为选型训练反馈，不称盲集。fit含旧train/monitor，Fast30K/E10已有使用；E34最终validation与held-out未进入本轮。\n\n'
text+=f"实际337248 NSG、336960 HNSW、4新图构建；合成另1小图/15 HNSW。单线程CPU15，所有job实际退出后评分；167712开发返回及768预检独立集合评分，55904旧baseline恢复，288原kernelparity、7slot映射/去重、图bytes和模型质量/ESS/先验守恒通过。训练30.286秒，操作wall不当QPS。\n\n"
link='../entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/'
text+=' · '.join(f'[{title}]({link}{path})' for title,path in [('协议','protocol.md'),('完整结果/控制','report.md'),('冻结门','results/selection.json'),('逐query失败','results/failure_cases.csv'),('验收','reviews/verification.json')])+'。\n'
history.write_text(text)
p=R/'experiment_history/README.md';old=p.read_text();p.write_text(old.replace('|---|---|','|---|---|\n| [55 GT10多画像小索引](55_multimode_index.md) | E66：P+两模态直接3H小图、同容量重复P、7slot去重及完整开发 |',1))
p=R/'s-experiment.md';old=p.read_text();p.write_text(old.replace('| E65 今日候选开发集完整wall', '| E66 GT10多画像单小索引 | 固定3H画像/7slot去重、原P和duplicate3P控制、全fit/aux | `COMPLETE_MULTIMODE_DEVELOPMENT`；337248 NSG，原方法及局部正负/控制分开 | [55 多画像](experiment_history/55_multimode_index.md) |\n| E65 今日候选开发集完整wall',1).replace('当前根四文件、五十份详细卡片','当前根四文件、详细卡片'))
summary='# ACSG 当前结果摘要\n\n2026-09-13，第三串行会话完成E66多画像完整开发。真实入口仍815/821，画像容量3倍，原NSG/base/raw-IP不变。整日21:00目标未完成，E34最终validation今日仍待执行。\n\n'
for ds in DS:
    x=s[ds];summary+=f"{ds}：mode3P相对原P，fit净{x['fit_net_hits']:+d}、历史aux7952净{x['aux_net_hits']:+d}命中，aux两半{x['aux_halves']}，失败净{x['aux_failure_net_change']:+d}；相对同容量duplicate的aux净{x['aux_net_vs_duplicate']:+d}。开发门{'通过' if x['passed'] else '失败'}。完整损伤/救回与控制见[E66报告](entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/report.md)，尚未有本方法完整QPS。\n\n"
summary+='E66原A/P恢复、父子支持/先验守恒、全图bytes、七slot去重、167712开发集合评分、55904旧baseline及288原kernelparity通过。337248新NSG、336960新HNSW、4新3H图；合成另1图/15路由。所有ANN串行CPU15实际线程1，模型构造只用历史fit20K，无新GT。aux7952是历史已暴露选型训练，原cal/audit亦历史使用；E34最终与held-out未进入。\n\n'
summary+='E63的fit局部正值和cal净−1/−2未过门保持；E64 Web纯拓扑净+38但失败+2，Y真实端点均净负，best_all双集baseline。E65已完成45开发点225独立wall：Web相对匹配soft在4/5L上Recall小幅正、伴随失败增加，Y混合；全部QPS交叉范围跨零，无稳定改进结论。此前曲线与本轮不同，不拼接。\n\n[E65完整曲线](entry_method_exploration/20260913_until2100_v1/stage6_development_wall_v1/report.md) · [历史索引](s-experiment.md) · [下一阶段](s-target.md)。\n'
(R/'summary.md').write_text(summary)
p=R/'spec.md';old=p.read_text().replace('当前多画像3H仅设计，现有API仍一画像/真实hub，未实现多slot去重查询。','E65当时未实现多画像去重；继任E66接口见后节。')
old+='''\n\n## GT10多画像单小索引（E66，2026-09-13）

[独立builder](entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/src/build_modes.py)恢复原GT10 A/P，用全fit20K权重训练两个球面query模态；父/子mass和ESS门、raw prior按子质量分配、低支持重复P和原P首槽冻结。输出3H行W、唯一slot labels/tie_ids、重复真实hub mapping、分配bits及完整支持/聚合量。physical2445/2463与unique815/821分账，原kernel/metric/H未改。

[Policy](entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/src/benchmark_with_nsg.cpp)新增multi_profile开关、unique_hub_count，要求每真实hub恰3slot。原M16/efConstruction200/ef10小图取7slot，按distance/slot排序去重、前三真实ID升序入原NSG；不足/非法拒绝。所有源图和count重载逐行验证W bytes及slot或真实ID标签；原单画像/legacy路径保留。Decision另保存7slot和距离，plain/count按bits核对。

[evaluate](entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/src/evaluate.cpp)继承E34完整wall合同，新增显式input_total_rows形状检查后前N行消费，避免复制历史22048容器；容器后2048 cal/audit字节被读取但不查询/选择。原生GT仍在所有搜索后读取。E66本轮timing_repeats0，完整plain/count及原kernel16/点，独立集合/去重/图/旧baseline验收通过；该接口不代表多画像性能已通过，改变slot映射/画像/ef/图必须重新评测。
'''
p.write_text(old)
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-13，第三串行会话已完成E66单3H多画像开发。当前会话12:13:18前安全交接，唯一写入者串行，禁止并行CLI/子代理；整日目标未完成。

1. 按E66原始完整fit/aux与同容量duplicate控制判断下一步；保留模态信息与扩图损伤的区别。E66模型/门冻结，不回写结果、不扫其mode数/支持阈值/seed。若有明确表示或路由近似缺口，另立新协议和预算作有限机制控制，当前尚未冻结下一查询。
2. 任何实际新候选要有包含原NSG、Fast30K、GT10-hard和Web匹配soft的同批完整五L五轮wall，以及QPS–Recall、QPS–zero-hit失败率、按L三指标及逐query损伤。E65已有开发曲线，E66尚无完整QPS，不能以NDC/同LRecall/有限oracle给GO。
3. 20:00停新训练、20:40停新增查询、21:00完整交付。晚间仍须冻结best_all和今日实际best_new后在E34历史validation2000作最终同批对照，最终反馈不得回流训练/选型；held-out不自动打开。未找到稳定改进也要诚实报告实际新候选及损伤。

原base/raw-IP/NSG/GT/H固定，历史脏树/产物/封存保留；每阶段root source_before，新产物独立。现场free>=7GiB，每阶段按累计输出预留晚间空间。所有ANN CPU15/threads1/OMP、BLAS、MKL1，无同时训练或重分析；完整在线独立整批wall，GT/count/hash/JSON/build/load在外。

P-fit20K含旧train/monitor；cal/audit和aux7952均历史暴露，任何辅助动作/模型选择反馈计训练。Fast30K/E10已用前10K，不能称元数据余行为项目未观察。E34最终输入本会话未用于反馈，held-out未打开。

[E66报告](entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [上一会话交接，保留历史身份](entry_method_exploration/20260913_until2100_v1/handoff.md)。
''')
after=O/'reviews/root_after';after.mkdir()
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/name,after/name)
shutil.copy2(R/'experiment_history/README.md',after/'history_README.md')
state=read(C/'state.json');state.update(status='SESSION3_E66_COMPLETE_NEXT_STAGE_PENDING',stage='E66_COMPLETE',stage7_status='COMPLETE_MULTIMODE_DEVELOPMENT',total_new_NSG=943206+337248,
    total_HNSW=1828576+336960,total_builds=342+4,session3_synthetic_HNSW=15,session3_synthetic_builds=1,native_pids=[],day_goal_complete=False);dump(C/'state.json',state)
print('E66_DOCUMENTS_SYNCHRONIZED',flush=True)
