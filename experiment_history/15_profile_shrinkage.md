# E26：单路画像收缩与损失迁移

2026-09-10夜间，状态`SHRINKAGE_DID_NOT_STABILIZE_SELECTIVITY_NO_FORMAL_GO`；全部预定阶段完成，无正式性能GO。独立版本`20260910_profile_shrinkage_v1`，不覆盖E25或旧E09。

## 动机、区别与固定方法

用户要求保留有效改道并减少受损查询，授权详细分析和直接相关的小探索。E25门控在WebVid有少量质量修复，但双路成本使QPS下降；Yandex收益保留不足。E26追问能否离线缩小画像位移，使在线仍是一份W/一个Micro-HNSW/一次原NSG。用户随后要求接近结束则当晚给短结论、明天继续，因此本轮完成后收口，不等待原07:00时间自动扩实验。

固定A0=E24 matched Fast20K/GT1硬，A1=E24冻结WebVid GT10软T0.016201138496398926、Yandex GT10硬；`Wα=normalize((1−α)W0+αW1)`，只有α0.25/0.50/0.75。float64混合归一化、float32导出，0/1端点bit复制。固定原base/raw-IP/NSG、seed20260828、H815/821、Micro-HNSW M16/efC200/ef10，三个唯一真实ID升序。Fast30K仍保留其旧30K/seed100/heap身份。

旧E09已使用top32真实single效用来聚合signed query残差；本轮仅插值E24既有几何画像，无新监督或训练，不复用旧residual/probe/C runner，不主张插值本身新颖。历史04及其原manifest/builder/结果已核对。

## 数据、冻结和统计合同

原E24 fit20K不变；新cal原router_train[6144,8192)共2048，audit[8192,10000)共1808，避开E25 cal/audit且不进入E24 fit。W、代码和cal输入先冻结，cal选定两数据集alpha及全部候选后再次全局冻结，再导出audit；audit只报告。随后原历史validation前2000，held-out不读取或hash。开发池有历史使用，validation已被E24/E25使用并启发本追问，不称盲测。

cal/audit每query配对A0/A1/三alpha，在L64/128真实运行原kernel。连续画像会产生第三套入口，故R/Rh只承认原收益保留，A_all/Ah_all计算包括新损伤的全部负事件/幅度减少。目标R/Rh≥75%、A_all/Ah_all≥25%，且净命中≥max(0,A1净命中)。cal若均不达标，按四项最差归一化比率S及净命中/受损/入口变化/小alpha ties选最接近者作反证；不把它升级为通过。

## 实际结果

两个数据集都选择alpha0.75，但三个候选在cal均未达联合目标；冻结主选择在audit和validation也未达标。合并L64/128的完整主结果：

| 数据集 | 分段 | R | Rh | A_all | Ah_all | 净命中 vs A0 / A1原净命中 |
|---|---|---|---|---|---|---|
| WebVid | cal | 70.94% | 73.27% | 24.67% | 31.56% | +151 / +67 |
| WebVid | audit | 63.55% | 61.55% | 21.59% | 22.53% | +8 / +66 |
| WebVid | validation | 64.62% | 61.07% | 14.02% | 9.28% | -28 / +91 |
| Yandex-IP | cal | 74.55% | 75.65% | 18.84% | 18.28% | -46 / -49 |
| Yandex-IP | audit | 64.18% | 61.86% | 21.13% | 12.91% | -118 / -87 |
| Yandex-IP | validation | 68.92% | 68.48% | 22.58% | 24.32% | +66 / +91 |

WebVid：原正命中619保留378，另产生73新/放大正命中；原负命中528避免153，但新增/加重104，最终损失479。
Yandex-IP：原正命中276保留189，另产生17新/放大正命中；原负命中185避免87，但新增/加重42，最终损失140。

损失恒等式逐query核对：原损失−避免原损失+新增/加重损失=新总损失。WebVid validation若只看“旧损失避免”可报28.98%，算上104个新增/加重损失后实际总损失只减少9.28%；Yandex从47.03%降至24.32%。不能只挑救回的旧坏query来称成功。

五L相对本轮同时重测A1/E24，Recall pp与QPS中位数变化：

| 数据集 | L | ΔRecall pp | ΔQPS % |
|---|---|---|---|
| WebVid | 64 | -0.495 | -0.85 |
| WebVid | 128 | -0.100 | -0.39 |
| WebVid | 256 | -0.170 | -0.21 |
| WebVid | 400 | -0.045 | -0.13 |
| WebVid | 800 | +0.005 | -0.20 |
| Yandex-IP | 64 | -0.055 | -0.14 |
| Yandex-IP | 128 | -0.070 | -0.38 |
| Yandex-IP | 256 | -0.065 | +0.31 |
| Yandex-IP | 400 | -0.105 | -0.90 |
| Yandex-IP | 800 | -0.060 | +0.08 |

十点九个Recall下降，唯一正值WebVid L800仅+0.005pp且QPS下降；没有同L Recall与三轮QPS都正。WebVid L64为−0.495pp，描述性配对query95%区间[−0.940,−0.085]，其余九点跨0；未经多重比较校正。相对matched Fast20K仍保留少数局部正值，但不能替代与A1的对照。所有基线、三次计时、每轮实测非支配点和三alpha开发负点完整保存。

## 机制与成本

插值保持画像连续，并不保证HNSW前三入口、主搜索命中或NDC单调。结果按same_both/A0_only/A1_only/third_entry_set分组；实际三入口相同的所有query，其返回ID/距离bits/命中和graph NDC均一致。第三套入口既会带来新收益也会制造新损伤；尚未分离精确排序变化和HNSW近似路径的因果贡献。

validation按任一L受损去重，WebVid原144→124条、Yandex45→33条；原有效query保留分别103/158、33/47。query跨L可同时有正负效应，这组诊断不替换协议事件口径。E25/E26只在相同原query/GT/A0/A1结果上连接质量分解，不跨轮混QPS或重新挑模型。

L128 A1→Shrink route-only：WebVid6.432→6.562μs/query、Yandex4.410→4.375；独立端到端wall约502.631→504.577、515.266→517.249μs/query。分项不相加作QPS。新三alpha及两端点复制产物构建WebVid0.0733s、Yandex0.0263s；部署一W一微型图，无门控/双路/额外特征。

E26真实调用897280、修复0、合成2268；8个真实job一次完成。搜索进程总计1000.25s、最高RSS10.038GiB，包含加载/构建/预热/计数/I/O，不能换算QPS。

正常调用分解：恢复1600、cal82240、audit72640、validation700800、L128分项40000。修复预留16384未用；单job1800s、查询进程合计7200s、RSS40GiB、新产物1GiB、free10GiB上限均满足。原GT/QGT/NSG/E24从零成本未重测，保留null，不把复用说成零。

## 验收、解释范围与接续

110点177760输出独立GT10评分；四条原validation曲线80000输出与E25的ID/距离bits/入口/route和graph NDC逐位回归。三次plain、count、前16query原wrapper、非法线程拒绝、实际CPU15/线程1、五L同图同入口、W数值/端点、选择ties及冻结先后均通过。115项原资产全hash验证保留，包括E25封存交付。

这是受限全局收缩反证，不是所有选择性路由不可行。尚无稳定低成本规则同时保留75%收益、减少25%损失并改善Recall–QPS。今晚不加密alpha/阈值、不加模型、不复跑旧队列；明日先判断正负改道是否有可区分证据，再决定是否新机制。长期2A/联合评分/效率等未执行分支保留在s-target。

## 原始证据

- [报告](../entry_method_exploration/20260910_profile_shrinkage_v1/report.md)、[所有原值](../entry_method_exploration/20260910_profile_shrinkage_v1/results/tables.md)、[分析](../entry_method_exploration/20260910_profile_shrinkage_v1/results/analysis.json)、[成本](../entry_method_exploration/20260910_profile_shrinkage_v1/results/costs.json)。
- [协议](../entry_method_exploration/20260910_profile_shrinkage_v1/protocol.md)、[用户时间更新](../entry_method_exploration/20260910_profile_shrinkage_v1/authorization_update.md)、[commands](../entry_method_exploration/20260910_profile_shrinkage_v1/commands.md)、[状态](../entry_method_exploration/20260910_profile_shrinkage_v1/state.json)。
- [cal前冻结](../entry_method_exploration/20260910_profile_shrinkage_v1/models/frozen_before_cal.json)、[audit前冻结](../entry_method_exploration/20260910_profile_shrinkage_v1/models/frozen_before_audit.json)、[完整性](../entry_method_exploration/20260910_profile_shrinkage_v1/reviews/immutable_integrity.json)、[最终验收](../entry_method_exploration/20260910_profile_shrinkage_v1/reviews/final_audit.json)。
- [收益和损失图](../entry_method_exploration/20260910_profile_shrinkage_v1/figures/gain_loss_decomposition.svg)、[Recall–QPS](../entry_method_exploration/20260910_profile_shrinkage_v1/figures/recall_qps.svg)、[损失迁移](../entry_method_exploration/20260910_profile_shrinkage_v1/reviews/validation_entry_transitions.json)、[跨版本质量](../entry_method_exploration/20260910_profile_shrinkage_v1/results/cross_experiment_quality_only.json)。
