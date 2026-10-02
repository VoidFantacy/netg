from shared import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

threads(8);assert read(O/'reviews/verification.json')['status']=='PASS'
g=read(O/'results/gate.json');cost=read(O/'results/cost.json');rows=g['datasets']
(O/'figures').mkdir(exist_ok=True)
fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
names=['WebVid','Yandex'];colors=['#2563eb','#d97706']
axes[0].bar(names,[x['supported_states'] for x in rows],color=colors)
axes[0].axhline(10,color='#991b1b',linestyle='--',label='Preregistered continuation gate')
axes[0].set(ylim=(0,40),ylabel='Supported states / 40',title='Auxiliary support')
axes[0].legend(fontsize=7)
for i,r in enumerate(rows):axes[0].text(i,1,f"{r['supported_states']}/40",ha='center')
for k,name in enumerate(names):
    a=axes[k+1];s=rows[k]['diagnostic_step_sums'];xs=np.arange(2)
    a.bar(xs-.16,[s[f'{p}_transfer_gain_hits'] for p in ['original','constrained']],.32,label='Gained hits',color='#16a34a')
    a.bar(xs+.16,[-s[f'{p}_transfer_loss_hits'] for p in ['original','constrained']],.32,label='Lost hits',color='#dc2626')
    a.axhline(0,color='#6b7280',linewidth=.6);a.set(xticks=xs,xticklabels=['Original J','Aux constraint'],ylabel='Hit events across fixed states',title=name+' historical transfer')
    a.legend(fontsize=8)
    a.set_ylim(-6,10)
    if all(s[f'{p}_transfer_gain_hits']==s[f'{p}_transfer_loss_hits']==0 for p in ['original','constrained']):a.text(.5,.55,'All selected-action hit changes = 0',transform=a.transAxes,ha='center',fontsize=8)
fig.suptitle('E60: Fixed-action diagnostic; historical development data; no combined model or QPS',fontsize=11)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'support_and_transfer_v2.{ext}',dpi=170)
plt.close(fig)
table='\n'.join(f"| {n} | {r['supported_states']}/40 | {r['eligible_actions']}/120 | {r['auxiliary_quality_null_actions']}/120 | {r['transfer_quality_null_actions']}/120 | {r['constrained_transfer_positive_states']}/{r['constrained_transfer_negative_states']}/{r['constrained_transfer_null_states']} |" for n,r in zip(names,rows))
trtable='\n'.join(f"| {n} | {arm} | {r['diagnostic_step_sums'][p+'_aux_gain_hits']}/{r['diagnostic_step_sums'][p+'_aux_loss_hits']} | {r['diagnostic_step_sums'][p+'_transfer_gain_hits']}/{r['diagnostic_step_sums'][p+'_transfer_loss_hits']} | {r['diagnostic_step_sums'][p+'_transfer_rescued']}/{r['diagnostic_step_sums'][p+'_transfer_new_failures']} |" for n,r in zip(names,rows) for arm,p in [('原J','original'),('辅助约束','constrained')])
text=f'''# E60：固定动作辅助支持与迁移诊断

2026-09-13，独立评分与实现验收通过。状态 `{g['status']}`。

两数据集的固定40状态支持数分别为 {rows[0]['supported_states']} 和 {rows[1]['supported_states']}，门槛为各10/40。本阶段没有生成一条新的连续训练轨迹，也没有可部署方法或新的正式QPS结论。默认仍为 WebVid GT10-soft / Yandex GT10-hard。

## 数据和实际改变

固定E53两seed各step10/20/…/200动作前状态及原D25/D50/D100，共80状态、240动作；没有按新增反馈挑状态或方向。新实现把原J合法性与辅助正净命中、无新增零命中约束组合，逐状态比较与原接受决定的差异。该辅助反馈用于决定是否接受，属于选择训练信息。迁移组只记录固定规则的结果，不回改规则。

原P拟合router_train10000:30000，含旧train4096和monitor1024全部行。辅助是旧cal0:1024；迁移是旧audit1024:2048，两者早已历史使用，Fast30K更曾拟合全部router_train。已逐行核验当前query/GT与原源文件；没有宣称任何一组为项目盲集。E34最终validation输入和反馈均未用于本实验，不将不同源namespace的数值ID相同误判为数据重叠。

## 支持与损伤实测

| 数据集 | 支持状态 | 合格动作 | 辅助命中全空动作 | 迁移命中全空动作 | 约束选中动作迁移正/负/全空 |
|---|---:|---:|---:|---:|---:|
{table}

“命中全空”表示相对同状态C每query的命中数完全不变，不表示查询本身零命中。失败另定义为返回top10与exact GT10集合交集为0；hits=1不算失败。

WebVid辅助组有9个净正动作，但与原train-J不降条件的交集为空：7个损失训练命中，2个训练命中不变而成本/漂移使J略负。9个均没有新增零命中。因此不能把WebVid的0/40概括为完全没有辅助正动作；它是本次固定动作中两个条件不能同时满足。Yandex辅助净正动作本身就是0。仅据这些有限动作不能声称整个表示空间不可兼容，也不事后放宽阈值继续训练。

| 数据集 | 接受规则 | 辅助增益/损伤命中 | 迁移增益/损伤命中 | 迁移救回/新增失败 |
|---|---|---:|---:|---:|
{trtable}

上述是40个固定历史状态的一步事件总和，可重复计同query，不能当一份模型的Recall增量。候选来自原train优化状态；辅助和迁移都有历史暴露。有限状态不通过支持门只约束本动作机制的连续扩大，不是整个画像空间或RL不可能改善的证明。约束动作少时，损伤下降可能只是大量选择不动，必须同时查看收益保留。

## 成本与验收

实际新增 NSG {cost['NSG_calls']:,} 次、HNSW {cost['HNSW_calls']:,} 次、普通小图构建 {cost['builds']} 次；完整三入口相同时复用了 {cost['reused_NSG_outputs']:,} 行NSG返回。双集原生阶段（含加载，排除启动前身份hash）共 {cost['native_process_seconds']:.3f} 秒，构建/路由/新增NSG/缓存重构/评分/写盘分项见cost.json。没有新GT、optimizer更新或正式QPS点。图像构建与搜索计数耗时不等于部署纯wall，缓存比例不等于端到端加速。

两集CPU15、进程及OMP/BLAS/MKL/NumExpr/BLIS实际1线程串行。659488行新输出独立集合评分；655360行完整缓存键/patch重构；240确定半径/画像独立计算；34物理图的全部画像与多层有序邻接解析、576行count/plain/原kernel parity通过。原base/图/query/GT与旧源码/轨迹身份检查通过。新输出不覆盖历史文件。

## 接续

若任一数据集未过支持门，停止相同局部动作的连续预算扩张。下一步需要扩大有依据的动作支持，不能只增加随机方向、步数或在线固定池选型器。备选为用完整P-fit20K上冻结基线实际遗漏的GT10成员调整原画像归属，并以同query相同遗漏数量的随机目标身份控制区分作用；必须另立协议、先恢复lambda0，并核对E08/E09/E22历史差异。该备选在本E60中未实现或运行。

[协议](protocol.md)、[数据角色审计](reviews/data_exposure_audit.json)、[逐动作](results/actions.csv)、[逐状态两规则](results/states.csv)、[门与完整汇总](results/gate.json)、[条件交集分解](results/support_breakdown.json)、[实际成本](results/cost.json)、[独立验收](reviews/verification.json)、[支持与迁移图](figures/support_and_transfer_v2.svg)。图v1保留，v2只修正零柱标注和整数事件轴范围，未更改数据或规则。
'''
(O/'report.md').write_text(text)
print('REPORT_READY',g['status'])
