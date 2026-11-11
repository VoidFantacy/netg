# ACSG 后续研究问题

2026-11-01。E195七集详细定位和E196费用邻近对照均完成，固定范围无待恢复队列，默认E99 GT10保持。按数据/预算的判断和下一优先级读[E196定位结论](entry_method_exploration/20261101_residual_navigation_cost_controls_v1/findings_zh.md)，机制细节读[E195定位](entry_method_exploration/20261101_residual_navigation_diagnosis_v1/findings_zh.md)。

1. 保留实际有效的直接B32/M5/SQ；按E196强控制后的具体效应、损失和小计数决定后继，不把粗网格未覆盖记作成功。新控制仍有限，不能作为所有容量/图/查询政策的最优证明。
2. 直接补全可研究跳过已主评分C的省费，先保持原metric/有限域guard/到达顺序、完整包等价，再验证完整wall；当前只有证书未实现新优化。COCO/Flickr约24%/29%的C重算比例不等于相同QPS增幅；导航资格另判。
3. 导航/状态共享依据实际新增收益和选择费用，不按低度/密度删点。E195只测独立辅助队列，未穷尽已评分未展开状态利用；若导出评分/恢复淘汰节点，需要支付保存、访问及队列费用。先核实际路径/评分障碍，再条件性研究稀疏修图或主搜索便宜评分。原理论与前作边界沿[理论文稿](entry_method_exploration/20261030_residual_navigation_theory_v1/theory_zh.md)保留。

本轮曝光窗口不再自动加密或训练至通过。未来确认若有具体有效配置，另固定合法新查询/图、控制、效应量、成本和结束边界；真实K1/K100、单方法串行T1、完整wall、最强适用B32/GT10。下一轮依用户后续任务，不恢复旧runner、改默认或生成PDF。
