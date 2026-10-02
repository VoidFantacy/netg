from common import *
import csv
assert read(O/'reviews/objective_checker_correction.json')['status']=='PASS_V2_ORIGINAL_FROZEN';v=read(O/'reviews/joint_objective_verification.json');assert v['status']=='PASS'
with (O/'results/paired.csv').open() as f:pairs=list(csv.DictReader(f))
p=O/'report.md';assert '独立检查器更正与局部信号' not in p.read_text();lines=['','## 独立检查器更正与局部信号','', '第一次独立目标检查在F字节digest处失败，旧检查源/失败记录保留。v2恢复训练输入的目标gather、n×10 rank矩阵copy布局及逐rank A归约后，原严格F digest与独立初末范数全部通过；未放松原哈希、未改模型/训练/查询/门，0额外ANN。没有分别隔离这些检查器布局改动的贡献，不将其说成模型错误。首次检查耗时未在失败前写出，成本为未知；v2耗时另记。','']
for r in v['datasets']:lines.append(f"- {r['dataset']}：{r['all_hub_trajectories']}条21步J轨迹通过；12固定hub初末两视角独立求和最大误差{r['max_norm_error']:.3g}。J总变化{r['total_J_increase']:+.6f}，query视角{r['query_norm_change']:+.6f}，条件目标视角{r['target_norm_change']:+.6f}。Web最小步差约−1.8e−15在预锁1e−9浮点容差内；不是完整20轮重放。")
lines+=['', 'E81保留旧compact正收益Web601/820、Y396/545，E80条件目标分别仅356/820、183/545：联合分组确实更能保留原分组的已测收益。但它也少修复旧损失，不能只按保留率选型。Web相对compact丢失219旧正命中，新增210收益，避免228旧损失却新增/放大238损失，合计−19；Y对应−149+134+120−167=−62。', '', 'Yandex相对P多58命中且少11失败，相对条件目标多70命中且少8失败，属于局部修复信号。它相对compact仍少62命中、多2失败，而且对P两半并非同时非负；因此不通过原门，不启动E81 enhancement wall，也不把等权附近的权重作为隐含新搜索。Web仍对P−78命中/+8失败。联合几何目标单调上升未保证真实搜索受益；这不证明所有目标表示或所有离线学习都无效。','', f"独立v2检查操作wall {v['seconds']:.3f}s，[更正记录](reviews/objective_checker_correction.json)和[目标核验](reviews/joint_objective_verification.json)保留。"]
p.write_text(p.read_text()+'\n'.join(lines)+'\n');print('E81_INTERPRETATION_APPENDED')
