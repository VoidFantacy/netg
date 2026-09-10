# 执行前实现澄清（真实模型训练/评估尚未开始）

以下补充不改变已冻结的学习方法、数据划分、标签或评价目标。

1. 原 `benches/test.cpp:139,353` 和 `benches/bench_per_query_recall.cpp:88,120` 的历史Fast采用HNSW默认seed100，direct top3按heap弹出次序（远→近）注入；Fast30K基准恢复这两个细节。matched Fast20K与学习模型共享其QGT构建seed作为Micro-HNSW seed，top3沿E20的近→远次序。全部重新计时，旧串行QPS不拼接到本次16线程结果。
2. 拟合hard接受使用已折叠W的float32 GEMM；soft梯度用缓存QP0+QVZ。部署使用原SIMD/1-IP分数。模型冻结后增加calibration_check，仅检查这种编译/浮点差异，不重选或重训；audit再做每个单入口hit/NDC与标签逐项重放。
3. `joint`表格是预限定新checkpoint中的校准最优者；`joint_selected`另报告允许原Fast1 fallback的选择结果。若根本没有新checkpoint则必须标明identity，不能称为新方法提升。
4. 连续proposal实现为每个温度最多20轮，每轮最多5个epoch、初始尝试加最多5次回退；首次hard增益或hard相等且soft下降即接受。校准仅选已接受checkpoint，不参与梯度、mapping或hard接受。分阶段对照在允许Fast fallback的W-only校准选择后做一次fit mapping。
5. QPS统计为三构建各三轮独立full-batch QPS的算术均值，同时保存全部原wall与构建差异；主四点统计比较为新joint vs恢复旧调用语义的Fast30K-3，paired Fast20K-3为同训练量对照。
6. synthetic benchmark只验收输出、plain/count、真实入口映射和计时边界；其中QPS不用于性能结论。没有读取validation/held-out或据其改变配置。
