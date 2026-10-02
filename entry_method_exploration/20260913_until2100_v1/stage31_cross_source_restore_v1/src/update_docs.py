from common import *
threads();resources();cost=read(O/'results/cost.json');assert not read(O/'results/gate.json')['wall_measurement_allowed'];assert read(O/'reviews/verification.json')['status']=='PASS'
rel=str(O.relative_to(R));history=R/'experiment_history/79_cross_source_parent_restore.md'
history.write_text('# 79｜双来源支持的局部父画像恢复（E90）\n\n固定E89原fit通过的13/8个动作，不扩候选/调强度；aux前3976加入训练，对各动作真实NSG支持筛选，保留5/0个。支持3976和fit20K都重测合并，后3976只评估预冻整体模型；所有aux历史暴露，接受不是盲验证。它检验E89损益能否跨来源保留，和E60的40背景稀疏小半径RL不同，跨源支持概念本身不新。\n\nWeb支持单项和51→实并49（3非加性query），fit71→61（13非加性），失败−5/−8；随机支持+30/fit+60。接受后半对compact+21命中、救回4/新增3；对P−22、24/26；对E89+7、4/2；对随机+4、1/2。完整门FAIL，P损失与随机/分半不稳保留。Y0个通过筛选，两模型逐字等于compact；接受相对P+81/失败−8全部继承compact，非新方法收益。两集停止固定筛选规则，不据接受反馈重选。\n\n新增163858NSG=1938训练+161920辅助，616304HNSW=454704训练+161600辅助。4物理导出含2非零Web、2零更新Y；2离线效用筛选拟合，0构图/编译/梯度/GT/QPS。准备0.188s、训练42.228s、辅助130.915s含load/count/cache/I/O，不作QPS；继承P/GT总成本未知。所有ANN串行CPU15、实际及库1线程。\n\n完整缓存来源、source row、21动作、真实合并与随机、非向量图bytes、plain/count/原kernel、支持前缀/旧P与compact和E89逐字回归、全部集合/mask和7slot入口核验。421失败并集/185状态变化/2105五配置单元保存，角色逐行区分。P-fit含旧train/monitor，辅助全部历史暴露；E34最终query/GT/row及held-out未打开。\n\n[报告](../'+rel+'/report.md) · [协议](../'+rel+'/protocol.md) · [源代码](../'+rel+'/src/train.py) · [门](../'+rel+'/results/gate.json) · [成本](../'+rel+'/results/cost.json) · [训练核验](../'+rel+'/reviews/training_verification.json) · [辅助核验](../'+rel+'/reviews/verification.json)\n')
p=R/'s-experiment.md';s=p.read_text();at=s.index('| E89 局部父画像恢复');s=s[:at]+'| E90 双来源父画像恢复 | E89固定13/8动作，另3976训练支持筛选5/0，实际双源合并与后半接受 | 双集门FAIL；Web接受对compact+21/失败−1，仍对P−22/+2，Y零更新；163858NSG/0QPS | [79 双来源恢复](experiment_history/79_cross_source_parent_restore.md) |\n'+s[at:];s=s.replace('当前最近完成记录为E89局部父画像恢复','当前最近完成记录为E90双来源父画像恢复');p.write_text(s)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [79 双来源父画像恢复（E90）](79_cross_source_parent_restore.md)：Web双源训练收益部分迁移但未过完整门，Y零更新。\n')
p=R/'summary.md';p.write_text('''# ACSG 当前结果摘要

2026-09-13第10串行会话E89/E90已完成，双集完整门均FAIL，默认未替换。整日21:00目标未完成，E34最终完整矩阵仍待执行。

| 阶段/数据 | 训练实际合并收益 | 接受区对compact命中/失败变化 | 对P | 判断 |
|---|---|---|---|---|
| E89 Web | fit20K +224，失败−27 | aux7952 +18/−6 | −41/+5 | 局部修复未胜P/随机 |
| E89 Y | fit20K +114，失败−10 | aux7952 −39/+5 | +81/−8 | 损失compact增益 |
| E90 Web | fit20K +61；支持3976 +49 | 后3976 +21/−1 | −22/+2 | 部分迁移，完整门仍FAIL |
| E90 Y | 0动作/零更新 | 后3976 0/0 | +81/−8 | 逐字compact别名，无新改善 |

E89固定同hub两个子画像恢复父P、32候选真实NSG筛选13/8，再实测并图。E90只用这些13/8固定动作，另3976行训练支持筛选5/0个，两个来源均重测合并，后3976接受完整预冻模型。原1771/2067slot、815/821真实入口、图全部非向量bytes保持；线上仍单小图七slot去重三入口与原NSG。

局部收益与损伤并存：E89 Web31/32、Y26/32动作同时救与伤，事件命中正负部1334/1274与610/625；筛选后单项和297/125，实际合并224/114。E90 Web接受对随机+4命中但多1失败，分半也未稳定。停止这些固定版本，不从接受反馈扫阈值/子集/幅度。训练收益与计数变化不作性能结论。

本会话这两阶段新增346556NSG/3578928HNSW，10物理导出含8非零向量安装/2零更新副本，4离线筛选拟合；0普通构图/梯度/GT/QPS。实际训练104.978s、辅助260.991s操作wall，E89编译13.194s；操作含load/count/cache/I/O，不是QPS，继承GT/P总成本未知。CPU15，实际进程及各库1线程，查询串行。

E90完整421失败并集/185变化、E89 427/193分别保留，不把两批并集数直接相加。P-fit含旧train/monitor；E90支持区明确训练，全部aux/cal/audit历史使用，后半不是盲验证。E34最终query/GT/row和held-out未打开。E89原因表查询后从预冻输入补录；训练图为独立封存补充，原结果不改。

旧正信号保留：E84 Web对compact+42/失败−4仍未及P；E73/E74 Y五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0，五轮QPS范围跨零。最近完整QPS仍E74，不能将本次质量点拼入旧曲线。

[E90报告](entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/report.md) · [E89报告](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/report.md) · [E89训练损益补充](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/supplement_training_v1/report.md) · [最近完整QPS](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。
''')
p=R/'s-target.md';p.write_text('''# ACSG 下一阶段目标与接续

第10唯一串行会话，2026-09-13 19:21:48前安全交接；整日目标仍进行中，不开子代理或并行CLI。

1. E89/E90固定版本均停止：单组父画像恢复有训练收益，E90另源支持确实筛掉不迁移动作，但Web仍未胜P/随机完整门，Y0更新。不要继续扫这些动作子集/阈值/幅度。若有明确新机制，先从历史78/79进入原逐query损益与图路由证据，另立版本和预算。
2. 当前优先完成最终评估工具参数化与候选目录同步，只读取已暴露开发结果和模型/配置元数据。最终best_all/best_new尚未选择；不得把目录、工具测试或历史2048数据当最终矩阵。需冻结实际候选池资格、选择规则/得分/ties及W/graph/mapping/ef/variable，再打开E34历史validation2000；最终反馈不可回流，held-out不打开。
3. 20:00停新训练，20:40停新增query，21:00交付。最终同批含原NSG、Fast、GT10-hard/Web匹配soft及实际新方法；五L五轮CPU15/实际及库1线程，完整wall、集合评分、zero失败全表与QPS–Recall/QPS–失败/按L三指标。E73 evaluator不支持E72 distinct回调，不能静默忽略；2000不能套旧2048分析硬编码。旧局部门不等于最终选型，也不自动禁止独立前瞻最终对照。

资源：session10全部新输出192MiB，另留晚间64MiB/交接8MiB，floor6.45GiB；已完成E89/E90全部文件累计计入，大文件只/data，不清理封存。新工具输出计入后续资源版本。

[E90报告](entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/report.md) · [campaign state](entry_method_exploration/20260913_until2100_v1/state.json) · [前会话最终准备](entry_method_exploration/20260913_until2100_v1/session9_final_preparation/readme.md) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
''')
p=R/'spec.md';p.write_text(p.read_text()+'''

## E90 双来源父画像恢复（2026-09-13）

[trainer](entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/src/train.py)复用E89 Routes helper和E69原NSG注入。每个dataset分别建立support3976、fit20000独立query-key缓存，source0/1/2为同角色P/compact/E89完整恢复，source3为本阶段缺失完整三入口新响应；角色/源行不同不能交叉命中缓存。每新键plain/count实际测量，16/32原kernel三方基线回归。

固定13/8候选在原compact背景测支持效用；合格5/0名单与固定随机同数量名单先冻结再合并，并在两源都实际查询。物理W/graph复制同父P，全部非向量bytes保持；零候选导出是compact逐字别名，不能称新模型。原E73 evaluator载入五配置，7952原值分为支持3976与接受3976及接受子半1988；全部已历史暴露，完整接受门只用后半，支持前缀与训练输出逐字回归。

[分析](entry_method_exploration/20260913_until2100_v1/stage31_cross_source_restore_v1/src/analyze.py)保存角色标注失败并集、集合/mask评分、各参考损益、训练单项和与实际并图交互；routeNDC不从缓存继承。无新线上接口或kernel变化、0本阶段QPS。变更候选/来源/合并模型须独立协议与新响应，不能从旧加和代替联合测量。
''')
for f in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 p=O/'root_after'/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,p)
s=read(C/'state.json');assert s.get('stage31_status')!='COMPLETE_CROSS_SOURCE_RESTORE_NO_GATE';s.update(status='E90_COMPLETE_SAFE_STAGE_BOUNDARY',stage31_status='COMPLETE_CROSS_SOURCE_RESTORE_NO_GATE',stage='E90_complete',total_new_NSG=s['total_new_NSG']+cost['NSG'],total_HNSW=s['total_HNSW']+cost['HNSW'],session10_NSG=s['session10_NSG']+cost['NSG'],session10_HNSW=s['session10_HNSW']+cost['HNSW'],session10_training_aux_operation_seconds=s['session10_training_aux_operation_seconds']+cost['training_operation_seconds']+cost['aux_native_operation_seconds'],native_pids=[],offline_pids=[],next_action='Prepare parameterized final tooling; actual selection and final matrix remain pending.');dump(C/'state.json',s)
freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file()]);print('E90_DOCUMENTED_SEALED')
