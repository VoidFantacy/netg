# E187：全base区域残差补全的来源与费用pilot

2026-10-28，用户授权开始实验并给出提升。实施E186的首轮候选来源pilot：COCO raw-IP 118272×512、Deep10M squared-L2 10M×96，真实K100，原base/NSG/GT10保持。原46点/138单线程10K批次完成，另以独立冻结协议增加6个GT10控制/18轮（合计52点/156轮），不扩展K1/其他五集或动作选择器。

**本轮区域补全尚未建立可支付的Recall–QPS提升，保留GT10默认，停止该固定后端进入动作选择器。** 区域补全18点中，18点被本轮某个实测L的GT10在Recall和中位QPS两项同时覆盖；达到事前速度筛选的点0个，达到预算筛选的点0个。

| 数据 | 方法L200 | Recall@100 | 完整QPS | 对GT10 ΔRecall pp / ΔQPS |
| --- | --- | --- | --- | --- |
| COCO | GT10 | 95.3444% | 1906.51 | — |
| COCO | B32 | 96.7159% | 1803.71 | +1.3715 / -5.39% |
| COCO | REG-NN | 95.5523% | 1511.32 | +0.2079 / -20.73% |
| COCO | REG-Q | 95.5102% | 1483.92 | +0.1658 / -22.17% |
| COCO | REG-R | 95.5793% | 1474.49 | +0.2349 / -22.66% |
| Deep10M | GT10 | 97.0780% | 1785.59 | — |
| Deep10M | B32 | 97.0801% | 1725.05 | +0.0021 / -3.39% |
| Deep10M | REG-NN | 97.5345% | 1154.98 | +0.4565 / -35.32% |
| Deep10M | REG-Q | 97.5599% | 1106.34 | +0.4819 / -38.04% |
| Deep10M | REG-R | 97.5601% | 1098.14 | +0.4821 / -38.50% |

原模型/原46点不改；读出原结果后为排除L网格错觉，单独冻结COCO408/432/464及Deep101/201/401，仅GT10六点。补充为测试曝光后的保守费用核验，不是盲确认；时间窗口差异与漂移限制保留，原分析在analysis_original_v1。

三种区域对照：REG-NN最近2区域；REG-Q只q/区域特征；REG-R加入原R摘要。同后端1024区域、global PQ M16×8bit、top8选2，完整扫描后96精算严格合并。候选来自全base，与E174/E175从残差seed作同NSG一跳有实质区别；IVF/PQ本身不作创新主张。R是否有效及源外救回详见实际CSV，不从几何相关推导净收益。

合法16K训练中12K fit/4K cal（cal不选参数）；B32为原16K冻结参考。原test已历史曝光，无新盲确认。原L200教师模型固定用于L100/200/400；GT10密集11个L，三轮轮转顺序，不改配置到通过。

计时CPU15/实际1线程，所有库1线程；完整Batch分配初始化、原路由/主搜、区域选择/扫描/精算/合并、六数组复制及正常销毁。预热/加载/保存/hash/GT/oracle在外；coco正式内部wall 644.09s，suite 671.56s；deep10m_l2_v1正式内部wall 744.13s，suite 931.05s。内部wall包含在suite中，不能相加；额外区域数组和构建费用见报告。B32原计数0为未插桩，第二实现重构实际候选数。

核验52点/156轮实际包、成员/查询救损与严格<10%尾部；三轮bit/SHA、冻结输入、大资产stat、实际主包补全oracle、旧程序128query前缀位一致、全base分区及4096编码抽查通过。stdlib第二实现20.136s。提前启动资格汇总造成的FileNotFoundError保留过程说明，随后等待完成原脚本通过；不回写失败或旧科学产物。

默认E99 GT10不变；不宣称完整E186接口/动作开关已实现，不从两集pilot推出流形因果或跨集净收益准入器。更多方法/预算若继续须另立冻结协议。E186设计原件继续保留当时纯理论身份。

[完整报告](../entry_method_exploration/20261028_adaptive_completion_pilot_v1/report_zh.md) · [PDF](../entry_method_exploration/20261028_adaptive_completion_pilot_v1/ACSG_自适应残差补全_实验对比_20261028.pdf) · [协议](../entry_method_exploration/20261028_adaptive_completion_pilot_v1/protocol.md) · [冻结](../entry_method_exploration/20261028_adaptive_completion_pilot_v1/freeze.json) · [核验](../entry_method_exploration/20261028_adaptive_completion_pilot_v1/reviews/results_audit.json)。
