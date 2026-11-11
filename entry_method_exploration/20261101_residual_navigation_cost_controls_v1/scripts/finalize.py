from common import *
import re
assert read(R/'formal_complete.json')['points']==837
v=read(R/'analysis/validation.json');assert v['points']==837 and v['batches']==2511 and v['original_candidate_window_points']==102 and v['candidate_event_queries']==52008
assert(R/'findings_zh.md').exists()
for x in read(R/'formal_freeze.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
dump(R/'reviews/formal_freeze_after.json',dict(status='PASS_FROZEN_FILES_UNCHANGED',files=len(read(R/'formal_freeze.json')['files'])))
# All E195 scientific bytes remain; root contracts have explicit snapshots.
checked=bridged=0
for x in read(OLD/'delivery_manifest.json')['files']:
 p=Path(x['path']);rel=None
 try:rel=p.relative_to(REPO)
 except ValueError:pass
 bridge=R/'source_before'/rel if rel is not None else None
 if bridge is not None and bridge.is_file():assert sha(bridge)==x['sha256'],bridge;bridged+=1
 else:assert sha(p)==x['sha256'],p
 checked+=1
dump(R/'reviews/E195_seal_after.json',dict(status='PASS_ALL_E195_BYTES_OR_ROOT_BRIDGES',checked=checked,root_bridges=bridged,original_manifest_sha=sha(OLD/'delivery_manifest.json')))
for x in read(OLD/'input_freeze.json')['files']:
 p=Path(x['path']);s=p.stat();assert s.st_size==x['bytes']and s.st_mtime_ns==x['mtime_ns']and s.st_ino==x['inode'],p
 if 'sha256'in x:assert sha(p)==x['sha256'],p
dump(R/'reviews/input_after.json',dict(status='PASS_INHERITED_INPUT_IDENTITIES',records=len(read(OLD/'input_freeze.json')['files'])))
D=list(csv.DictReader((R/'analysis/dataset_summary.csv').open()));S=list(csv.DictReader((R/'analysis/stability.csv').open()));C=list(csv.DictReader((R/'analysis/candidate_comparisons.csv').open()));remaining=[x for x in S if x['both_not_covered']=='True'];globalremaining=[x for x in S if x['both_new_global_not_covered']=='True'];covered=sum(bool(x['GT_or_OPT_covers'])for x in C)
prefix=str(R.relative_to(REPO));oldprefix=str(OLD.relative_to(REPO));overview='\n'.join(f"| {a['dataset']} | {a['covered_window_points']} / {a['candidate_window_points']} | {a['both_not_covered']} / {a['configurations']} | {a['both_new_global_not_covered']} |"for a in D)
desc=f'E196费用邻近强控制完成837点/2511完整T1；重测E195的51个固定配置、102窗口点，其中{covered}个窗口点被当前强GT10/OPT-B32覆盖，{len(remaining)}个配置两窗均未被这组强控制覆盖，加入本轮其他重测导航后为{len(globalremaining)}个。均为有限曝光窗口证据，未覆盖不称成功或默认替换。'
(REPO/'summary.md').write_text(f'''# ACSG 当前结论

更新于2026-11-01。{desc}默认E99 GT10保持（WebVid soft-t1，Yandex hard），固定矩阵均已收口。

| 数据 | 被强控制覆盖窗口点 | 两窗未被强控制覆盖配置 | 两窗全方法未覆盖配置 |
| --- | --- | --- | --- |
{overview}

先读[E196定位结论]({prefix}/findings_zh.md)、[完整报告]({prefix}/report_zh.md)、[102比较]({prefix}/analysis/candidate_comparisons.csv)、[51配置]({prefix}/analysis/stability.csv)，再读[E195完整来源/导航定位]({oldprefix}/findings_zh.md)。E195原1260点/3780T1与837点控制是独立冻结阶段，不混拼绝对QPS、不回写旧结果。总2097正式点/6291完整批次；不是2097份独立质量样本。

E195源链显示COCO/Flickr/WebVid有较多重复遗漏支持，Yandex较弱，Deep/SIFT当前源只覆盖不到1%的K100/L200遗漏；GIST有来源/路由/容量多层损失。多数遗漏有来自已评分未展开集合的一步边，WebVid该比例较低；该集合包含被拒绝/淘汰点，不是可免费恢复的pending beam。本轮独立辅助队列只主动展开选中seed，后续跳过main visited及已评分C/代表，不代表所有状态共享。

当前度数/背景r8没有给出普遍可靠的导航准入规则；低度/密度不作为删正确答案规则。3952550个C评分事件中401354个此前主搜索已评分，均不能严格改善终止K阈值；这是直接补全的有限域省费证书，不是已实现优化或QPS收益。导航仍可使用已评分未展开的seed，不能据证书剔除入口资格。

历史M5/B32/SQ正面证据保留原身份和完整费用：[历史正面索引](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)。E194两个K100/L100 OPT-B32约2.2–2.5%等价省费、E173/E191有效场景不因新控制而抹去；E193有限门结果不否定所有残差/自适应。旧绝对QPS不拼入新窗口。

全部C1三轮真实包/工作相同，旧包字节对齐、原生线性oracle及NumPy/stdlib整数/hash/wall核验通过。A/B都是曝光公共query，单图/画像、固定窗口、小K1事件与有限L/容量限制保留；quality-threshold speed可对应更高Recall，不称精确等Recall。费用分段在wall外，完整wall权威。详见各报告和cost_ledger。旧科学文件/PDF/seal不回写，根文档由本轮source_before桥接；无新PDF。
''')
(REPO/'s-target.md').write_text(f'''# ACSG 后续研究问题

2026-11-01。E195七集详细定位和E196费用邻近对照均完成，固定范围无待恢复队列，默认E99 GT10保持。按数据/预算的判断和下一优先级读[E196定位结论]({prefix}/findings_zh.md)，机制细节读[E195定位]({oldprefix}/findings_zh.md)。

1. 保留实际有效的直接B32/M5/SQ；按E196强控制后的具体效应、损失和小计数决定后继，不把粗网格未覆盖记作成功。新控制仍有限，不能作为所有容量/图/查询政策的最优证明。
2. 直接补全可研究跳过已主评分C的省费，先保持原metric/有限域guard/到达顺序、完整包等价，再验证完整wall；当前只有证书未实现新优化。COCO/Flickr约24%/29%的C重算比例不等于相同QPS增幅；导航资格另判。
3. 导航/状态共享依据实际新增收益和选择费用，不按低度/密度删点。E195只测独立辅助队列，未穷尽已评分未展开状态利用；若导出评分/恢复淘汰节点，需要支付保存、访问及队列费用。先核实际路径/评分障碍，再条件性研究稀疏修图或主搜索便宜评分。原理论与前作边界沿[理论文稿](entry_method_exploration/20261030_residual_navigation_theory_v1/theory_zh.md)保留。

本轮曝光窗口不再自动加密或训练至通过。未来确认若有具体有效配置，另固定合法新查询/图、控制、效应量、成本和结束边界；真实K1/K100、单方法串行T1、完整wall、最强适用B32/GT10。下一轮依用户后续任务，不恢复旧runner、改默认或生成PDF。
''')
p=REPO/'spec.md';s=(R/'source_before/spec.md').read_text();at=s.index('## 5. 指标');s=s[:at]+f'''### 4.11 E196费用邻近控制（已完成）

[源码]({prefix}/src/benchmark.cpp)只嵌入重命名main的E195快照，新runner改变固定评测点表和三轮顺序，不改任何导航、图、metric、GT或模型。51个既定配置/102窗口点与GT10/OPT-B32控制共837点/2511完整T1。控制L由E195完整费用曲线的预先插值±2及原L+1提出；OPTB32旧L100绝对时间差只作预算估计，实际Recall/QPS重新测量。旧QPS不混拼。

全部新OPT-B32预算沿原Posting合并，原生全query线性oracle验证；原窗口包全query SHA对齐，三轮六数组/工作相同。NumPy全排序再核52008条候选事件，NumPy和stdlib整数/hash/完整wall复算全部837点；输入继承E195 identity，旧meta只读。timer沿E195完整生命周期，CPU15实际T1。两曝光窗口、有限L与单图限制保留；当前结果是对照收紧，不新增生产依赖/状态续搜/修图/评分器或新门。

固定配置/预算/二进制身份见[协议]({prefix}/protocol.md)、[选择]({prefix}/selection_freeze.json)、[freeze]({prefix}/formal_freeze.json)。大输出/data/acsg-e196-storage经storage链接；E195科学原件与seal不变，根文档由source_before桥接。

'''+s[at:];p.write_text(s)
p=REPO/'s-experiment.md';s=(R/'source_before/s-experiment.md').read_text();parts=s.split('\n\n');parts[1]=f'更新于2026-11-01。最新完成E196费用邻近强控制（837点/2511T1），前序E195七集详细来源与导航定位（1260点/3780T1）。当前实测与默认读summary，实现读spec，后继读s-target。原E173–195协议/结果/封存保留，不将历史“当前”当新执行队列。';s='\n\n'.join(parts);at=s.index('| E195 |');s=s[:at]+'| E196 | 费用邻近GT10/OPT-B32强控制 | 完成837点/2511T1；51固定配置成本复核，默认保持 | [卡片](experiment_history/196_residual_navigation_cost_controls_v1.md) |\n'+s[at:];p.write_text(s)
hist=f'''# E196 残差导航的费用邻近强控制

2026-11-01，按用户详细定位授权，E195完成后独立冻结，不更改原导航或追加到通过。{desc}

[协议](../{prefix}/protocol.md) · [冻结](../{prefix}/formal_freeze.json) · [固定837点](../{prefix}/analysis/frozen_point_list.csv) · [定位结论](../{prefix}/findings_zh.md) · [报告](../{prefix}/report_zh.md) · [全部点](../{prefix}/analysis/points.csv) · [51配置](../{prefix}/analysis/stability.csv) · [核验](../{prefix}/analysis/validation.json) · [费用](../{prefix}/analysis/cost_ledger.json)。

E195有78个两窗粗网格机会，加入其他导航后51个两窗全方法前沿候选进入本轮。旧成本只生成邻近L，控制和候选均重新完整计时，真实K1/K100、串行T1、三轮、实际包/工作一致和旧包字节匹配。原生线性及NumPy/stdlib核验通过。来源、几何与直接C证书仍属E195的独立事实，不因费用判断收紧而抹去。

有限曝光窗口/单图、小计数、预算估计和未穷尽L/容量/策略限制保留；三轮非独立质量样本，不称全局最优或精确等Recall。默认不改，固定范围收口；旧科学文件/PDF/seal保留，原根文档由source_before桥接。新增输出/data/acsg-e196-storage，无新PDF。
'''
(REPO/'experiment_history/196_residual_navigation_cost_controls_v1.md').write_text(hist)
p=REPO/'experiment_history/README.md';s=(R/'source_before/experiment_history/README.md').read_text();p.write_text(s+'\n- [E196 残差导航费用邻近强控制](196_residual_navigation_cost_controls_v1.md)：2026-11-01完成837点/2511完整T1，独立收紧E195机会的成本判断。\n')
(REPO/'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

2026-11-01，/data/netg/ACSG。E195七集详细定位与E196费用邻近对照均完成，默认E99 GT10保持，无待恢复矩阵。先读AGENTS、summary、spec、s-target、s-experiment，再读[E196定位结论]({prefix}/findings_zh.md)、[报告]({prefix}/report_zh.md)、[51配置]({prefix}/analysis/stability.csv)、[核验]({prefix}/analysis/validation.json)和[E195来源/导航定位]({oldprefix}/findings_zh.md)。

原1260点与后继837点分别冻结，不混拼QPS或回写旧原件。粗网格机会不记作成功；新控制仍是有限曝光窗口/单图证据。保留M5/B32/SQ历史正面场景。低度/密度不是删答案规则；直接已评分C无效重算证书不取消其导航资格；新跳过优化、完整续搜、修图/评分器仍未实现。

输出分别/root/acsg-e195-storage、/data/acsg-e196-storage，经storage链接。旧科学原件/PDF/seal和根文档快照保留。按用户后续任务继续，不自动扩大当前窗口、训练至通过、改默认或生成PDF。
''')
for path in [R/'README.md',R/'report_zh.md',R/'findings_zh.md',REPO/'LOCAL_CODEX_START.md',REPO/'summary.md',REPO/'s-target.md',REPO/'spec.md',REPO/'s-experiment.md',REPO/'experiment_history/196_residual_navigation_cost_controls_v1.md']:
 for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
  if link.startswith(('http:','https:','#')):continue
  link=link.strip('<>').split('#')[0];assert(path.parent/link).exists(),(path,link)
a=read(OLD/'analysis/cost_ledger.json');b=read(R/'analysis/cost_ledger.json');dump(R/'analysis/combined_cost.json',dict(E195_formal_batch_seconds=a['formal_batch_wall_seconds'],E196_formal_batch_seconds=b['formal_batch_wall_seconds'],combined_formal_batch_seconds=a['formal_batch_wall_seconds']+b['formal_batch_wall_seconds'],combined_formal_process_seconds=a['formal_process_seconds_including_load_warmup_performance_oracles_and_diagnosis']+b['formal_process_seconds_including_load_warmup_and_oracles'],formal_points=2097,formal_batches=6291,not_total_project_or_human_cost=True,nested_costs_not_additive=True))
dump(R/'state.json',dict(status='COMPLETED_DENSE_COST_CONTROLS_NO_DEFAULT_CHANGE',points=837,batches=2511,selected_configurations=51,both_windows_not_covered=len(remaining),both_windows_all_methods_not_covered=len(globalremaining),default_changed=False,pending_work=False,new_PDF=False))
dump(R/'postprocess_complete.json',dict(status='PASS_FULL_LOCAL_DELIVERY',final_findings_pending=False))
files=[ident(p)for p in R.rglob('*')if p.is_file()and '__pycache__'not in str(p)and p.name not in ['delivery_manifest.json','delivery_validation.json']]
files += [ident(p)for p in(R/'storage').rglob('*')if p.is_file()]
for name in ['AGENTS.md','LOCAL_CODEX_START.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/196_residual_navigation_cost_controls_v1.md']:files.append(ident(REPO/name))
dump(R/'delivery_manifest.json',dict(status='SEALED_E196_LOCAL_DELIVERY',files=files));dump(R/'delivery_validation.json',dict(status='PASS_E196_LOCAL_DELIVERY',points=837,batches=2511,files=len(files),bytes=sum(x['bytes']for x in files),E195_scientific_unchanged=True,formal_freeze_unchanged=True,default_changed=False,pending_work=False,new_PDF=False))
print('FINALIZED',len(files),len(remaining),flush=True)
