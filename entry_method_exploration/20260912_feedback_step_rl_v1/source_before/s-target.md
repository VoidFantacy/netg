# ACSG 下一阶段目标与接续

2026-09-12，E52四训练及独立审计完成，[历史41](experiment_history/41_direct_candidate_commit.md)。用户要求持续至22:00，大胆假设、小心证明，并最终比较最佳方法与NSG/Fast/FastGT的QPS、召回率、失败查询率。

## 当前证据

连续提交已经把部分已见候选机会转成真实静态画像收益，说明E50的更新转化缺口可以实际改善。WebVid两seed选中monitor +0.3125/+0.2051pp，高于原E47 RL对应+0.0781/+0.0098pp；第一seed末点完整训练池+0.6250pp，第二seed末点+0.6543pp。但这是不同状态逐步分岔后的完整算法对照，不是固定状态因果消融，直接证据仍由E50/E51提供。

损伤和种子不稳定也真实存在：Yandex第一seed选中monitor +0.0586pp，第二seed−0.0977pp、末点−0.1270pp，而原E47 RL第二seed选中为+0.0781pp。两seed末点完整训练池均上涨（+0.2515/+0.2734pp），不能据此声称独立query稳定提升。预锁双集“至少一个可行正monitor候选”门通过，只说明候选信号存在；不是四seed稳定性、开发或性能GO。该方法是贪心局部搜索对照，不包装成RL。

E50证明候选反馈到确定均值转化缺口，E51同方向放大救回9/12与4/4机会，也测到最大半径伤害。E48区分评分和邻接的局部质量响应，两集机制不同，不可统一固定一项解决。

## 立即接续E53

下一阶段E53保留原RL八候选LOO梯度和Adam方向，以GT无关的候选中位半径r，在r/4、r/2、r三个真实确定点与不动之间按原J选择；Gaussian候选只估计方向，不可直接提交。m/v和局部计数每步推进，实际均值接受后真实恢复图身份与缓存。其依据来自E51放大机会和最大半径损伤的固定控制；协议在E52完整结果之前写定，源码和独立审计已准备，尚未冻结训练。

E53四run预计9612build/36107264 HNSW，NSG固定62976+实际变化、每run预留150000/总600000，0新开发反馈。用E52实测时长保守估算，须预计21:10前完成；用户最后最佳候选对NSG/Fast/FastGT的QPS/Recall/零GT10失败率比较必须在21:15前进入准备窗口，21:40停止新查询，22:00收口。当前尚未执行最终完整比较。

[E53协议](entry_method_exploration/20260912_feedback_step_rl_v1/protocol.md)、[训练源码](entry_method_exploration/20260912_feedback_step_rl_v1/src/train.py)、[独立审计源码](entry_method_exploration/20260912_feedback_step_rl_v1/src/audit_training.py)均已准备，冻结/训练尚未执行。完整训练池/监控选点/画像公式/实际线程和源保护保持；新资源artifact384MiB/free8GiB，各dataset≤2400s。原E47和E52对照完整保留，不按新结果换旧seed。

如果模型形成可用局部信号，完整学成W/G的评分/邻接四格可作为额外机制问题；它不同于E48单行小动作，当前仅设计思路，不能当已测结果或提前替换默认。不得因此延误最终性能矩阵。

## 最终交付

[最终合同](entry_method_exploration/20260912_until2000_v1/final_comparison_contract.md)：冻结cal预选最佳候选，对NSG、原Fast30K（GT1/seed100/legacy堆）、FastGT10-hard（E24/20K/seed20260828），WebVid另soft匹配起点，同机CPU15实际1线程五L五轮比较完整QPS/Recall/GT10零命中失败率。全部点/五轮范围/配对失败转换/图与独立核验，最终audit不得回流选模型。E49 WebVid缺hard基线，最终要求尚未完成。21:15前留最终窗口、21:35停止训练、21:40停止新查询、22:00收口。
