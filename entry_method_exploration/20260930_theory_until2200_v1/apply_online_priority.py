import json,time,zipfile
from pathlib import Path
CAMP=Path(__file__).resolve().parent;ROOT=CAMP.parents[1]
names=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
old={n:(ROOT/n).read_text() for n in names}
with zipfile.ZipFile(CAMP/'root_docs_before_online_priority.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
    for n in names:z.write(ROOT/n,n)
    z.write(CAMP/'state.json','campaign_state.json')
with zipfile.ZipFile(CAMP/'root_docs_before_online_priority.zip') as z:
    for n in names:assert z.read(n)==(ROOT/n).read_bytes()
summary=old['summary.md'];title='# ACSG 当前结果摘要\n\n';assert title in summary
summary=summary.replace(title,title+'用户于2026-09-30 17:44明确：**主目标是完整端到端Recall–QPS综合提高，构建费用不是优化重点。** 下列构建费用收益只保留为附属事实，不视为主要目标完成。尚未执行的目标质量压缩诊断已取消；接下来回到廉价入口信息与真实线上效用，见[目标修订](entry_method_exploration/20260930_theory_until2200_v1/online_priority_steering.md)。\n\n',1)
(ROOT/'summary.md').write_text(summary)
target='''# ACSG 下一阶段目标

2026-09-30用户授权理论、论文与小实验研究至22:00，并于17:44明确：**构建成本不是优化重点，重点是完整端到端QPS和Recall综合提高。** 默认仍Web GT10-soft-t1/Yandex GT10-hard、生产E99。已完成记录141–163保留；费用下降、训练方向误差下降或数学条件核验都不等于主目标完成。[本次目标修订](entry_method_exploration/20260930_theory_until2200_v1/online_priority_steering.md)。

## 优先一：找到在线足够便宜、能迁移的入口决策信息

保持底图、主搜索、每个比较点的L、展开和停止规则。先从历史详细记录核对信息是否已用、动作是否相同、监督/工作预算是否对齐，再锁一个能被简单控制推翻的假设；不以新模型名字或oracle余量代替证据。

E117的六关系特征/四rank动作、E118全H打分、E121上层状态/全H静态ID表都有原负结果。更早E126四rank动作提案与E121的动作语义不同，但该区别本身尚不构成新收益依据。当前只审查原协议、完整缓存键与在线费用；不重跑旧runner、扩大候选/深度/阈值或追加测试直到通过。

## 优先二：用真实目标预算与完整wall验证综合改善

只在具体信息假设与最小控制明确后制定小实验。数据角色、方法、预算与结束边界在读反馈前冻结；只测真实Recall@1/@100，K100要求L≥100，CPU15实际单线程、方法串行、完整路由+主搜索+输出wall。训练/缓存中的graph-only时间、NDC、预测MSE和插值预算不能冒充线上QPS。

探索与默认替换分开。非劣区间未通过记为证据不足，不一票否决有实际价值的方向；同时保留明显损伤、跨来源/工作点差异和费用。旧版本门与结果不回改，新源一经观察不再参与后继选型。固定模型、同监督简单控制和独立实现核验先于负结果归因。[研究判定策略](entry_method_exploration/20260922_until2200_improvement_v1/research_decision_policy.md)。

## 优先三：理论解释服务于真实搜索效用

163已补全目标/温度→平均归属→归一化→评分间隔→实际路由→固定搜索的保真条件，不能由此推出超过默认的Recall或完整QPS。下一理论重点是廉价可见信息能否预测相对默认的救回−损伤，并支付全流程新增费用；通用统计/运输/球面均值工具明确注明前作。

单球/单hub证书162在两集各20K均无通过机会，固定版停止；Energy157在新源上相对同2048预算Uniform无稳定Recall改善，停止特征/深度/seed/温度/预算调参。141–160的低标签费用候选与全部数据保持，不作为当前首要优化路线。未执行的target_mass_compression_v1因目标纠正取消，不把取消当方法反证。

## 资源与交接

全部旧源码、模型、图、GT、日志、标签及seal保留；每项新工作独立版本与manifest。当前全日1GiB新增/空余6GiB预算继续检查，21:30后不启动可能超时作业，22:00结束并清空后台队列。正式性能期间无并发训练/标注/其他性能作业。当前没有新性能runner在运行。

[当前结果](summary.md) · [历史索引](s-experiment.md) · [实现合同](spec.md)。修订前完整目标保存在本日root_docs_before_online_priority.zip，原历史边界不丢失。
'''
(ROOT/'s-target.md').write_text(target)
state=json.loads((CAMP/'state.json').read_text());state.update(stage='online_joint_recall_qps_priority_review',primary_objective='joint_end_to_end_recall_qps_improvement',construction_cost_priority='secondary',active_process=None,last_updated_unix=time.time())
state.setdefault('cancelled_before_execution',[]).append('target_mass_compression_v1');(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
print('ONLINE JOINT RECALL QPS PRIORITY APPLIED',flush=True)
