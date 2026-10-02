from shared import *
import re,ast
threads(8);resources();started=time.monotonic()
check(O/'reviews/prequery_freeze.json');check(O/'reviews/prequery_freeze_v2.json');check(O/'reviews/protected.json');check(O/'reviews/native_dependencies.json')
assert read(O/'reviews/verification.json')['status']=='PASS'
cost=read(O/'results_v2/cost.json');gate=read(O/'results_v2/gate.json');assert gate['status']=='PASS_EXACT_FEEDBACK_CACHE_AND_TRAINING_PROJECTION'
status='COMPLETE_EXACT_FEEDBACK_CACHE_FULL_RECOVERY'
core='''精确反馈复用通过：180张固定图的737280行完整返回五字段与E44逐位一致，20个全池奖励/梯度恢复。候选655360配对只新增1333次NSG（WebVid971/Yandex362），为完整候选调用的0.2034%；全部HNSW路由仍真实执行，当前route NDC没有复制旧值。只在三个升序真实入口与query/原NSG/L/K/metric/kernel身份完全一致时复用完整ID/距离/graph NDC，入口变化则新搜索；没有GT引导筛选或未知补0。

20份当前C种子复用E44已支付的81920次完整反馈，若全部新冷启动则正常NSG为83253次；1333仅为候选补测，不能据此宣称整条链99.8%加速。新真实NSG共3061（正常1333+parity1728），HNSW742528、构图181，其中包含失败尝试的4096路由/1图。两个成功进程共34.410s，含14.711s加载；新NSG约0.578s、route约4.117s、含检查的build约9.821s，查表/复制及I/O另列。计数进程成本不是线上QPS。

冻结状态下的保守训练投影为2951.912s（约49.2分钟，已含1.5倍余量和600s加载/monitor/导出/审计），通过截止门。它不保证学习中入口变化率不增长；新训练仍须实时限制调用、输出与19:35截止。E45的小单步正值可据此进入一次真正的完整反馈RL/ES对照，而不是再改相关性采样。
'''
next_text='''下一步E47保持E43原P/B/H/局部行参数化、σ.3、200步、两臂双seed及hub/ε日程；唯一反馈变化是每候选使用完整train4096。每次确定均值更新后也真实route全池、补测入口变化并替换当前缓存，杜绝过期C。初始全池结果实际重算并计费；轨迹保存完整route NDC和新增返回patch、原状态/方向/梯度/Adam/身份，独立重放全部逻辑反馈。按原monitor门决定后续，不扩大epoch或幅度。当前E47尚未运行，准备完成并核对剩余时间后直接执行。'''
body=f'''# E46 完整三入口身份的精确反馈复用

2026-09-12，`{status}`，门`{gate['status']}`。实现/成本验收通过，不是新学习或性能GO。

{core}
## 实现与验证

[cache_environment.cpp](src/cache_environment.cpp)包含冻结E37 environment，新增e46_route（真实全池HNSW）和e46_search（显式合法升序三入口的原NSG），原kernel/库/旧binary不变。有效封装为[native_cached_v2.py](src/native_cached_v2.py)与[run_v2.py](src/run_v2.py)。当前C种子有完整query/图身份；候选重构完成后才打开旧候选raw做验收。保存全部raw、变化行/新返回、完整拓扑和每图时间；首末context36物理图×16query三路parity通过。

独立集合评分737280条、全部cache identity和raw bits、20个LOO梯度、180图身份、576条三路parity通过，8个非法输入批次在零NSG前拒绝，空增量返回正确类型空数组。奖励包含新的route NDC、原graph NDC、命中/失败/漂移，无代理标签。有效分析为[analyze_verify_v3.py](src/analyze_verify_v3.py)。

首attempt在首C空patch返回时触发ctypes NULL错误，原现场保留；新增NSG0、HNSW4096、build1由trace/控制流重建，未捕获该进程最终native计数。失败4000预留保留，两个修复job各2000，总预留8000/硬限10000。v2只修零长度输出，原二进制不变。分析v2完成数值核验后因NumPy bool JSON失败，v3只改标量类型与派生目录；无新查询。详见[空增量修正](empty_delta_repair.md)、[分析修正](analysis_serialization_repair.md)，原件不覆盖。

CPU15实际进程/OMP/BLAS/MKL1、串行；编译/分析CPU8。E37–E45及实际native/NSG/链接依赖保护，根文档前件保存。0 optimizer/新GT/monitor/cal/audit/validation/held-out/QPS。

## 接续

{next_text}

默认保持WebVid GT10-soft-t1 / Yandex GT10-hard；E43、E44失败门与E45小正值保留。阶段完成不结束20:00持续研究目标。

[协议](protocol.md)、[配置](config.locked.json)、[逐图成本](results_v2/points.csv)、[完整成本](results_v2/cost.json)、[门](results_v2/gate.json)、[独立核验](reviews/verification.json)、[图](figures/exact_feedback_cache.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+next_text+'\n')
hist=body.replace('# E46 完整三入口身份的精确反馈复用','# 35. E46 完整三入口精确反馈复用');hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_exact_feedback_cache_v1/'+m.group(1)+')',hist)
(R/'experiment_history/35_exact_feedback_cache.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E45 确定均值单步完整反馈');s=s[:i]+'| E46 完整三入口精确反馈复用 | 180图全池路由，仅入口变化新NSG；全部原E44返回/奖励/梯度恢复 | `COMPLETE_EXACT_FEEDBACK_CACHE_FULL_RECOVERY`；候选补测1333/655360，种子/路由另计；3061新NSG、0训练，可进入完整反馈对照 | [35 精确反馈复用](experiment_history/35_exact_feedback_cache.md) |\n'+s[i:];s=s.replace('三十四份详细卡片','三十五份详细卡片');p.write_text(s)
p=R/'experiment_history/README.md';s=p.read_text();s+='\n- [35 完整三入口精确反馈复用](35_exact_feedback_cache.md)：E46全部原始输出与奖励/梯度恢复，完整反馈训练的调用成本具备实测依据。\n';p.write_text(s)
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E46，`{status}`。[报告](entry_method_exploration/20260912_exact_feedback_cache_v1/report.md)、[历史35](experiment_history/35_exact_feedback_cache.md)、[验收](entry_method_exploration/20260912_exact_feedback_cache_v1/reviews/verification.json)。用户持续研究至20:00，并要求大胆假设、小心证明；当前默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

{core}
当前研究假设是完整质量反馈能缓解局部画像学习失效，而非预先认定表示没有空间。E45同状态单步WebVid净0→+1、Yandex−2→+3（主要避开5命中损伤），各9/10全池更新仍无质量响应，信号小。E44原入口分层失败（方差比1.074/0.978）仍成立；E43未过Yandex monitor门，WebVid ES局部+0.0781pp保留。最近完整Recall–QPS仍E37，无RL额外优势或默认替换。

{next_text} 详细协议与进退条件见[s-target](s-target.md)。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E46精确反馈复用已验收，[历史35](experiment_history/35_exact_feedback_cache.md)、[报告](entry_method_exploration/20260912_exact_feedback_cache_v1/report.md)。用户20:00持续研究授权并强调大胆假设、小心证明，总目标继续。

## 当前假设与直接检验

假设：局部画像RL失效的重要瓶颈是小批次遗漏质量反馈；完整反馈可以改善实际学习。E44全池诊断和E45小单步正值支持继续检验，并未证明这一假设充分。E46已将原655360候选query反馈精确恢复为1333新增NSG，路由和初始反馈完整计费；保守投影约49.2分钟。直接用真正训练对照检验，不追加采样网格。

{next_text}

## E47冻结要求与判断

两数据集RL/ES双seed20260921/22、200更新、原σ.3/Adam/单行参数和原hub日程。候选ε按相同seed重放，query反馈改为全4096。当前W完整反馈随每次均值更新刷新；同三入口复用需完整query/NSG身份，所有新route NDC付费。选中/末点仍静态W/普通HNSW，线上没有策略网络。

预期8次训练、1600更新；每次初始化完整4096真实查询，monitor1024每20步实际查询，train512由当时全池缓存提取。保存候选和均值的变化行/完整返回patch、全route NDC、动作前状态/ε/奖励/梯度/Adam、完整checkpoint及静态导出；独立重放当前缓存、全部奖励与更新，不能只验selected点。新版本预锁NSG/HNSW/build/输出预算与19:35截止，启动时按真实时间再次校验投影。

原monitor门保持：每数据集每arm至少一seed非零checkpoint ΔRecall>0、U>0、graph NDC≤+1%，双集均通过才考虑独立冻结后的开发控制；否则停止本完整反馈版本预算扩展，保留局部正值并分析未转化的候选机会。不用不同context或同L Recall充当QPS前沿。

## 次优先和截止

若时间/预算不允许完整训练，不开注定超时的大任务，转缓存中的共享冲突/评分与邻接机制。若训练完成但未过门，先解释质量反馈频次、每hub暴露和采样/均值差，不扩σ/epoch。19:35停止训练，19:40停止新查询，20:00收口；默认与E37–E46原件保留。当前无遗留query进程。

> 读四主文档和AGENTS，从历史35进入有效native_cached_v2/run_v2/analyze_verify_v3及两次修正；全部737280返回和20梯度已恢复，不重跑E46。独立冻结E47完整反馈训练，复用合法三入口语义，每个均值更新也刷新全池缓存，按原双集monitor门检验假设，20:00前收口。
''')
p=R/'spec.md';s=p.read_text().replace('E45确定均值单步控制已验收','E46精确反馈复用已验收').replace('后继route-only/精确三入口反馈复用尚未实现，不能写成现有能力。','继任route-only/精确三入口反馈复用已在E46实现，见下节。');s+='''

## 完整三入口精确反馈复用（E46，已验收）

[cache_environment.cpp](entry_method_exploration/20260912_exact_feedback_cache_v1/src/cache_environment.cpp)包含原E37 environment，新增e46_route真实全池HNSW与e46_search显式三入口原NSG。后者批次先验证query行、升序唯一合法H成员再搜索；route-only仍计HNSW及route NDC，原kernel/build/run/verify保持。有效Python接口[native_cached_v2.py](entry_method_exploration/20260912_exact_feedback_cache_v1/src/native_cached_v2.py)对零长度原生输出返回类型正确空数组。

[run_v2.py](entry_method_exploration/20260912_exact_feedback_cache_v1/src/run_v2.py)对E44固定C+八候选实际route4096，完整三入口不变者仅复用C的IDs/距离bits/graph NDC，变化者调用原NSG；当前route NDC永不复用。query/图/metric/L/K/kernel和完整入口身份均为标签键。全部重构后才打开旧候选raw验收，保存全raw/变化patch/拓扑/费用，36代表物理图三路parity。

[analyze_verify_v3.py](entry_method_exploration/20260912_exact_feedback_cache_v1/src/analyze_verify_v3.py)完成737280集合评分/五字段bits/复用身份、20奖励/梯度、180拓扑及576条parity核验。实际3061 NSG、742528 HNSW、181图含首失败0/4096/1（由trace控制流重建）；失败预留保留，两个v2 job后总预留8000≤10000。初始C种子81920历史调用单列，候选新增1333不能声称全流程99.8%加速。两个修正与原件保留，0optimizer/新GT/QPS；E47连续训练尚未实现。
''';p.write_text(s)
dump(O/'reviews/visual_review.json',dict(status='PASS',files=['figures/exact_feedback_cache.png'],method='Viewed PNG: log counts and separately charged seed column readable'))
dump(O/'state.json',dict(status=status,gate=gate['status'],NSG_calls=3061,optimizer_updates=0,campaign_complete=False))
jobs=read(O/'logs/jobs.json');assert len(jobs)==3 and jobs[0]['status']=='FAILED' and all(x['status']=='COMPLETE' for x in jobs[1:]);assert sum(x['reserved'] for x in jobs)==8000
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/35_exact_feedback_cache.md']]
links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
rec=dict(status='PASS',NSG_calls=3061,HNSW_calls=742528,builds=181,optimizer_updates=0,protected_files=len(read(O/'reviews/protected.json')['files']),
 local_links=links,artifact_bytes=sum(x.stat().st_size for x in files(O)),independent_verification=read(O/'reviews/verification.json'),campaign_complete=False,seconds=time.monotonic()-started)
dump(O/'reviews/final_audit.json',rec);dump(O/'reviews/completion_audit.json',dict(status='PASS',stage_complete=True,campaign_complete=False,next='E47 full-feedback RL/ES training, planned unrun'))
freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots);print(json.dumps(rec,indent=2),flush=True)
