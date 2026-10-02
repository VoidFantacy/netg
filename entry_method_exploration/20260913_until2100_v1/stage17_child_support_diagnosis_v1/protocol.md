# E76 子模态支持与已有完整三入口收益：缓存诊断协议

2026-09-13，第6串行会话。E75原层级控制未胜compact，停止本版本；E73/E74局部信号保留。当前E69 Web exact-mode相对exact-P净−109，说明近似遍历不是全部损伤来源。新诊断只读E66训练support/画像/fit实际返回、E73 compact辅助返回和E69 exact辅助返回；0构图/0ANN/0NSG/0训练更新/0新GT/0QPS，最多120秒、16MiB、free>=7GiB。CPU15/数值库1线程，先锁源码/输入再分析，不读取最终validation/held-out。

固定三个已测比较：E66 fit20K mode−P；E73 aux7952 compact−P；E69 aux7952 exact-mode−exact-P。输入namespace/source rows逐项核对，GT仅独立复核旧返回集合。fit含旧train/monitor，aux/cal/audit历史暴露；本诊断用于下一方法设计，辅助反馈仍计训练。不能包装为盲集或新泛化结论。

每条query识别新三入口相对参照新增的hub；只在这些新增hub的三画像内用float64 raw-query分数查其最高slot，平局首slot。这解释完整画像表示，不冒充原SIMD路径或重跑全H排名。approx实际返回slot另存，可能与同hub最高slot不同。保存新增子slot的训练child mass、ESS、fraction rho、parent-child cosine、unit-query score lift；没有新增子slot的query单独标记。

前瞻固定二元cohort（each split separately）：是否有新增子slot；其中是否有child mass<8、ESS<16、fraction<0.25、parent-child cosine<0.9、unit-query lift>0.05。阈值只作描述（mass8/ESS16来自原父支持门），不根据新结果扫阈值。每个轴true/false分组完整划分该比较的所有query；不同轴相互重叠，禁止把多轴计数相加当独立样本。

报告各组query数、命中正负部/net、zero救回/新增以及原命中数分布；保留完整aligned特征和query源行，父子质量/ESS/方向集中度表。组效应只是已测完整三入口的事后关联，不能算单画像因果信用或可部署筛选器；没有新反事实标签，不模拟删子slot后搜索结果。只有明确关联且有可检验构造差异，才另锁后继表示控制；本诊断不导出模型、不选择final。

完成后历史65/索引/summary/s-target及新分析artifact合同同步，root_after封存。E75已封存原件不变。晚间E34最终对照仍待冻结后执行，本会话15:21:01前安全交接。
