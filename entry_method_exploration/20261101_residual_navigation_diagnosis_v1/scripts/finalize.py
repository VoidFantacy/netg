from common import *
import re
assert read(R/'formal_complete.json')['points']==1260
assert read(R/'analysis/loss_receipt.json')['status'].startswith('PASS')
assert read(R/'analysis/C_reuse_certificate.json')['checked_C_events']>0
assert read(R/'analysis/source_chain_receipt.json')['rows']==42864
assert read(R/'analysis/stdlib_audit.json')['points']==1260
assert read(R/'analysis/geometry_receipt.json')['status'].startswith('PASS')
for x in read(R/'geometry_freeze.json')['files']:assert sha(x['path'])==x['sha256']
analysis=read(R/'analysis/analysis_receipt.json');assert analysis['points']==1260 and analysis['auxiliary_candidate_audit_points']==504
assert analysis['auxiliary_candidate_audit_queries']==257184
changes=[]
input_checked=0
for x in read(R/'input_freeze.json')['files']:
    pp=Path(x['path']);st=pp.stat()
    assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns'] and st.st_ino==x['inode'],pp
    if 'sha256' in x:assert sha(pp)==x['sha256'],pp
    input_checked+=1
dependency=[]
for x in read(E194/'formal_freeze.json')['files']:
    pp=Path(x['path'])
    if pp.suffix in ['.cpp','.hpp','.h','.a','.o']:
        assert sha(pp)==x['sha256'],pp;dependency.append(x)
dump(R/'reviews/input_dependency_after.json',dict(status='PASS_INPUT_IDENTITIES_AND_INHERITED_SOURCE_LIBRARY_SHA',input_records=input_checked,dependencies=dependency))
for x in read(R/'formal_freeze.json')['files']:
    assert sha(x['path'])==x['sha256'],x['path']
dump(R/'reviews/formal_freeze_after.json',dict(status='PASS_ALL_FROZEN_FILES_UNCHANGED',files=len(read(R/'formal_freeze.json')['files'])))
before=read(R/'reviews/E194_scientific_before.json');verified=0
for x in read(E194/'delivery_manifest.json')['files']:
    p=Path(x['path'])
    if str(p).startswith(str(E194)+'/') or str(p).startswith('/root/acsg-e194-storage/'):
        assert sha(p)==x['sha256'],p;verified+=1
assert sha(E194/'delivery_manifest.json')==before['manifest_sha']
dump(R/'reviews/E194_scientific_after.json',dict(status='PASS_E194_SCIENTIFIC_AND_MANIFEST_UNCHANGED',verified=verified))
summary=list(csv.DictReader((R/'analysis/dataset_summary.csv').open()));stable=list(csv.DictReader((R/'analysis/stability.csv').open()));pts=list(csv.DictReader((R/'analysis/points.csv').open()))
good=[x for x in stable if x['both_positive_net']=='True' and x['both_not_existing_covered']=='True'];nav=[x for x in pts if x['method'] in NAV]
prefix='entry_method_exploration/'+R.name
index_line=' | '.join([])
overview='\n'.join(f"| {x['dataset']} | {x['points_positive_vs_B32']} / {x['navigation_points']} | {x['points_existing_covered']} / {x['navigation_points']} | {x['both_positive_and_not_existing_covered']} / 36 |" for x in summary)
conclusion=(f'完成七集、两曝光公共窗口、真实K1/K100的1260正式点/3780完整T1批次；另140新资格点和56旧二进制控制点，42对应包逐字节一致。504个导航点中{sum(float(x["gain_vs_B32_pp"])>0 for x in nav)}个同L相对B32净Recall正、{sum(bool(x["existing_covers"]) for x in nav)}个被同窗GT10/B32/OPT-B32/SQ覆盖。252个方法/K/L配置中{len(good)}个两窗均正且未被已有离散网格覆盖。默认E99 GT10保持。')
old=R.parent/'20261030_residual_optimization_stability_v1'
text=f'''# ACSG 当前结论

更新于2026-11-01。E195七集残差来源与导航增量详细定位完成：{conclusion}当前无待恢复矩阵。

| 数据 | 导航同L净增益正点 | 被已有方法覆盖点 | 两窗正且未覆盖配置 |
| --- | --- | --- | --- |
{overview}

分数据解释与后继见[定位结论]({prefix}/findings_zh.md)。完整结论见[E195报告]({prefix}/report_zh.md)、[全部点]({prefix}/analysis/points.csv)、[机制]({prefix}/analysis/mechanisms.csv)、[两窗一致性]({prefix}/analysis/stability.csv)。本轮六种导航动作保留完整B32直接C，比较一跳、距离多步、未访问邻居选点和真实入邻居静态代表；不是原search_new续搜，不修改主图或训练新门。诊断逐query复制核与原主搜索ID/距离字节一致，Python全排序另核504点全部候选事件/最终返回，详见analysis_receipt。

遗漏分为已评分未返回、未评分但邻接已评分未展开集合、无该一步边。后者不等于全图不可达；边界包含被拒绝或淘汰节点，不是终止beam的pending状态。七集全图均无零入度节点，低入度/出边/密度仍需与实际有限动作区分，不能据此删直接正确答案。逐query/GT事后相关与单seed机会不能冒充部署收益或联合beam结果。

A/B源行不重叠，均为曝光公共测试；一套图/画像、固定小窗口、离散控制和K1小计数限制保留。有限未覆盖不等于全局最优；三轮只重复费用。所有正式QPS计完整正常生命周期、选择和扩展；分段微计时在wall外，不相加代替完整wall。成员损伤/严格K100<10%尾部保留原定义。

历史有效M5/B32/SQ继续保留：[历史正面证据](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)。前序[E194]({old.relative_to(REPO)}/report_zh.md)的COCO/WebVid两窗口、256点/768T1及两集K100/L100 OPT-B32约2.2–2.5%等价省费仍成立；B32为强参照。E191 COCO/K1 SQ L400的99.64%/1072.26对GT10 L693的99.64%/817.09属于原窗口，不能混拼新QPS。E193有限学习门失败不否定所有残差/自适应。旧科学文件、PDF、seal不回写；根文档原字节由E195 source_before及前序理论桥接保留。
'''
(REPO/'summary.md').write_text(text)
target=f'''# ACSG 后续研究问题

2026-11-01。用户授权的[E195七集详细定位]({prefix}/protocol.md)已完成固定范围，无待恢复队列，默认E99 GT10保持。实际结果读[summary](summary.md)和[E195报告]({prefix}/report_zh.md)。

## 根据定位保留的分支

分数据解释、有效配置与下一问题见[定位结论]({prefix}/findings_zh.md)。

按数据/K/预算评价直接补全、导航增量和完整费用。具体两窗正且未被本轮已有网格覆盖的配置见[stability]({prefix}/analysis/stability.csv)，属于探索候选；未通过的实际效应和成员损伤保留，不能一票否决所有后端或所有数据集。后续不自动追加当前曝光窗口调参。

1. 来源不足时先研究更便宜的新支持；固定源不含目标，池内评分不能创造该目标。区域/块可访问源外，但须看路由覆盖、短名单和完整费用。保留强B32和历史M5/SQ具体有效配置。
2. 导航研究以本轮实际新增/损失和选择费用为基础。直接C保留，真实代表/种子只承担有限动作价值；入度/出度/未访问邻居是特征或静态基线，GT相关不是可部署规则。E195已实现独立辅助多步扩展，原search_new仍无完整续搜接口；更多seed或独立命中并集不保证共享beam改善。
3. 稀疏修复和主搜索便宜评分仍是条件性提案，尚未在E195实现或验证。要先识别实际路径或评分费用障碍；改主图必须重绑教师/表/响应/计时，压缩/guard/精排均支付完整费用。RoarGraph/NGFix及旧M2/FINGER/LeanVec/RaBitQ/PAG的前作边界沿原[理论]({R.parent.relative_to(REPO)}/20261030_residual_navigation_theory_v1/theory_zh.md)保留。

## 进退与稳定性

后继按具体数据集的效应、成本和小计数保留候选，先明确需要改善的是来源、动作还是信息；不用更复杂模型代替新信息。未来新模型/图/查询角色和预算须另冻协议，正式仍为真实K1/K100、串行T1、完整wall、强GT10/B32同窗比较。当前A/B已曝光，不称盲确认。E194的两个OPT-B32条件性工程配置保留；E193原门控和E174原一跳结果保持历史身份。

本次详细验证固定矩阵与分析已收口；下一轮具体实现与确认按用户新指令，不恢复旧runner或自动扩大当前窗口。
'''
(REPO/'s-target.md').write_text(target)
p=REPO/'spec.md';s=p.read_text().replace('更新于2026-10-30。','更新于2026-11-01。',1)
s=s.replace('均为THEORY_ONLY_UNIMPLEMENTED_UNTESTED，未新增入口/续搜API、连通性统计、过滤器、图边或评分器；若将来实施，需独立定义状态/预算、GT离线角色、metric/并列语义、完整wall和依赖重绑。本次只同步合同边界，默认与代码保持原实现。','该文稿当时为THEORY_ONLY_UNIMPLEMENTED_UNTESTED；E195现已另实现全图静态统计、独立辅助扩展和导航代表基线，见4.10。原完整状态续搜、修图和主搜索新评分仍未实现，默认保持。')
at=s.index('## 5. 指标')
section=f'''### 4.10 E195详细定位与独立辅助导航（已实现并完成）

[独立源码]({prefix}/src/benchmark.cpp)嵌入只重命名main的E194快照，GT10/B32/SQ调用沿旧原实现；新六种动作在原主搜索后保留全部B32 C及原metric分数，再选择最多3个seed并沿原图一跳或独立有界多步扩展。DIST96/384用逐路由行query-best，NOVEL96/384在距离前12个C中按相对主visited和已选邻接的新覆盖贪婪选择，REP384使用全图真实h→C入邻居的静态度数代表。代表评分计入384，C评分另计；物理辅助访问≤64×额外精算预算。原visited只读、辅助seen/队列独立；已选seed可主动展开，后续main visited及全部C/已评分节点跳过精算和新入队，未选C不自动展开。该限制见implementation_boundary.md，不代表所有状态共享/续搜策略。不恢复原beam，不改主图或生产核。

Meta按唯一非自环有效边计算入度/出度，保留N×4/N×2数组及C→代表映射；这些全N数组用于离线/诊断，REP在线只需映射，GT10/B32不新增依赖。共同benchmark加载SQ/度数不等于默认部署RAM。局部replay.inc由原search_on_graph_new复制，仅加评分/展开/拒绝ID记录，七集两窗两K三L全42864条调用与原主包ID/距离字节核对；不是完整可恢复状态API。

正式1260点/3780T1，资格140、旧二进制控制56（42对应包），两曝光公共窗口各512、GIST500。正常完整Batch生命周期、路由/主搜/C评分/选择/扩展/合并/六数组复制销毁计wall。所有三轮输出/工作一致；504个辅助点的257184条query候选事件由原生线性oracle和Python全排序核最终ID/距离字节。单seed384探针及GT相关仅wall外诊断，不是线上规则或联合beam证明。冻结、来源/预算、计数语义见[协议]({prefix}/protocol.md)与[formal_freeze]({prefix}/formal_freeze.json)；旧科学文件、PDF和seal不改。仍未实现原状态续搜、修图、新主搜索评分或新门。

'''
s=s[:at]+section+s[at:];p.write_text(s)
p=REPO/'s-experiment.md';s=p.read_text().replace('更新于2026-10-30。','更新于2026-11-01。最新完成E195七集残差来源与导航详细定位（1260点/3780完整T1），六种独立辅助动作及完整费用；具体判断见summary。前序：',1);needle='| E194 |';at=s.index(needle);s=s[:at]+'| E195 | 七集残差来源、搜索轨迹与导航增量 | 完成1260点/3780T1；分数据/预算保留实际效应，默认不变 | [卡片](experiment_history/195_residual_navigation_diagnosis_v1.md) |\n'+s[at:];p.write_text(s)
hist=f'''# E195 七集残差来源与导航增量详细定位

2026-11-01用户授权“定位吧，不一定要最小验证，详细验证，不同的数据集有价值就都研究研究”。本轮建立新协议，未恢复旧runner。{conclusion}

[协议](../{prefix}/protocol.md)、[源码](../{prefix}/src/benchmark.cpp)、[正式冻结](../{prefix}/formal_freeze.json)、[完整报告](../{prefix}/report_zh.md)、[全部点](../{prefix}/analysis/points.csv)、[机制与阶段](../{prefix}/analysis/mechanisms.csv)、[两窗配置](../{prefix}/analysis/stability.csv)、[第二实现](../{prefix}/analysis/analysis_receipt.json)、[费用](../{prefix}/analysis/cost_ledger.json)。

七集原图/metric/GT10/B32/SQ不变，两个公共查询窗口各512（GIST500），真实K1/K100。GT10/B32 11档L、SQ四档、OPT-B32一档、六导航三档固定完成。直接C保留，一跳/距离多步/未访问邻接选择/真实入邻居代表分别测试。独立辅助扩展不是原API续搜，GT只在wall外评价。

轨迹复制核42864条调用与原主返回ID/距离字节相同，导航504点/257184条query通过原生线性oracle和NumPy全排序。A/B源行不重叠但均已曝光，非跨图/独立人员复现；常数特征相关无定义，单seed并集不当共享beam。成员损伤、严格<10%尾部、完整QPS和旧正面证据保留。

旧E194科学与manifest保持，根文档原字节由source_before桥接；旧E173–194协议/失败/原始结果/PDF/seal不回写。大产物/root/acsg-e195-storage经storage链接。固定矩阵及分析收口，无自动追加范围或默认替换。
'''
(REPO/'experiment_history/195_residual_navigation_diagnosis_v1.md').write_text(hist)
p=REPO/'experiment_history/README.md';s=p.read_text();s+='\n- [E195 七集残差来源与导航详细定位](195_residual_navigation_diagnosis_v1.md)：2026-11-01完成1260点/3780完整T1，默认保持；详情与边界读卡片。\n';p.write_text(s)
(REPO/'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

2026-11-01，/data/netg/ACSG。E195七集残差来源与导航详细定位已完成1260点/3780完整T1，无待恢复矩阵；默认E99 GT10保持。先读AGENTS、summary、spec、s-target、s-experiment，再读[E195报告]({prefix}/report_zh.md)、[逐集]({prefix}/analysis/dataset_summary.csv)、[全部点]({prefix}/analysis/points.csv)、[机制]({prefix}/analysis/mechanisms.csv)、[两窗]({prefix}/analysis/stability.csv)、[状态]({prefix}/state.json)。

六种辅助动作保留B32直接C，分别测试一跳、距离多步、新邻接选择和真实入邻居代表。独立辅助扩展不是原search_new续搜。轨迹诊断与GT事后关联不等于可部署收益；低度/密度不是删答案规则，单seed并集不当联合beam。A/B均曝光公共窗口，一图/画像；原GT和近并列/成员损伤不改。

保留E173/E191/E194条件性M5/B32/SQ正面证据和E194两个OPT-B32工程配置。旧科学原件/PDF/seal保留，原根文档经E195 source_before桥接。大产物/root/acsg-e195-storage。按用户下一任务继续，不自动扩大当前测试到通过、训练/修图、改变默认或生成PDF。
''')
dump(R/'state.json',dict(status='COMPLETED_DETAILED_SEVEN_DATASET_RESIDUAL_NAVIGATION_DIAGNOSIS_NO_DEFAULT_CHANGE',formal_points=1260,formal_batches=3780,qualification_points=140,legacy_control_points=56,default_changed=False,pending_work=False,new_PDF=False,two_window_positive_nondominated_configurations=len(good)))
dump(R/'analysis/decision.json',dict(default_changed=False,formal_points=1260,navigation_points=504,covered_navigation_points=sum(bool(x['existing_covers']) for x in nav),two_window_positive_nondominated_configurations=good,scope='finite-grid exploratory; no blind/cross-graph/default replacement claim'))
# Check local relative links in changed root/entry docs without resolving historical web links.
for path in [R/'README.md',R/'report_zh.md',REPO/'LOCAL_CODEX_START.md',REPO/'summary.md',REPO/'s-target.md',REPO/'spec.md',REPO/'s-experiment.md',REPO/'experiment_history/195_residual_navigation_diagnosis_v1.md']:
    for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if link.startswith(('http:','https:','#')):continue
        link=link.strip('<>').split('#')[0]
        assert (path.parent/link).exists(),(path,link)
dump(R/'postprocess_complete.json',dict(status='PASS_ANALYSIS_SOURCE_GEOMETRY_AUDIT_REPORT_AND_FINDINGS',human_findings_and_document_sync_pending=False))
files=[]
for p in R.rglob('*'):
    if p.is_file() and '__pycache__' not in str(p) and p.name not in ['delivery_manifest.json','delivery_validation.json']:files.append(ident(p))
# rglob does not traverse the storage symlink; include artifacts through explicit storage enumeration.
for p in (R/'storage').rglob('*'):
    if p.is_file():files.append(ident(p))
for name in ['AGENTS.md','LOCAL_CODEX_START.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/195_residual_navigation_diagnosis_v1.md']:
    files.append(ident(REPO/name))
dump(R/'delivery_manifest.json',dict(status='SEALED_E195_LOCAL_DELIVERY',files=files))
dump(R/'delivery_validation.json',dict(status='PASS_E195_LOCAL_DELIVERY',formal_points=1260,formal_batches=3780,files=len(files),bytes=sum(x['bytes'] for x in files),old_E194_scientific_unchanged=True,formal_freeze_unchanged=True,default_changed=False,pending_work=False,new_PDF=False))
print('FINALIZED',len(files),len(good),flush=True)
