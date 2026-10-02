from pathlib import Path
import json,hashlib,shutil,time
C=Path(__file__).resolve().parents[1];R=C.parents[1];O=C/'stage29_proposal_rank_diagnosis_v1'
assert not O.exists();O.mkdir()
for d in ['src','inputs','results','reviews','source_before','figures']:(O/d).mkdir()
for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/f,O/'source_before'/f)
(O/'protocol.md').write_text('''# E88｜已测提议边的排名与响应诊断（前瞻，0新查询）

独立新版本；E86/E87停止门保持。只读E87已冻结fit20K提议事件、W/mapping/tie、原七slot、实际单边route/完整NSG变化patch。fit含旧4096train/1024monitor；辅助/cal/audit历史暴露；本版不读辅助响应、E34最终输入/GT或held-out，不拟合或选新方法。

固定问题：P独有hub提出的目标，按原compact打分能否进入既有七slot所代表的前三hub；实际单边是否使目标返回/被选及完整三入口/命中变化。全1951事件保留，只有已实际测量的53/9候选拥有单边响应，其他事件不能填成零效果。

固定排名参照：对原返回七slot与目标的并集计算float64 query内积，按分数降序、tie ID升序、slot升序排序，再取前三不同真实hub。这是固定返回集插入参照，不是完整HNSW反事实，也不能推断访问/扩展。原第三不同hub分数和目标分差并存；abs(gap)<=1e-5*max(1,norm(query))标近界，结果不靠该界选边。实测目标返回、目标hub选中、入口三元组变化、hit差由原保存patch复原。全fit每边区分支持事件所在query与其他query的收益/损失，边事件与唯一query不能混数。

核验：实际完整三入口变化必须和已有edge_statistics一致；重新集合评分原/变化返回；事件权重/来源与原提议一致；逐项复算固定排序；无新增调用原生库、训练、图、GT、QPS。输出完整事件CSV、每边CSV、汇总JSON、图/报告；不新增调参或性能GO。离线单进程CPU15/库1线程，预计<120秒，上限8MiB。会话合计192MiB、晚间64MiB+交接8MiB预留、磁盘6.55GiB底线不变。
''')
(O/'state.json').write_text(json.dumps(dict(status='PROTOCOL_FROZEN_ANALYSIS_PENDING',epoch=time.time(),NSG=0,HNSW=0,builds=0,fits=0,GT=0,QPS=0,day_goal_complete=False),indent=2)+'\n')
print('E88_PREPARED',O)
