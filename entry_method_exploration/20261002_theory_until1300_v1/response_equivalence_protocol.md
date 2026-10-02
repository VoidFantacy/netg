# 旧完整返回响应等价类：只读冻结协议

冻结时间：2026-10-02 12:09（UTC+8），第一次成功打开本诊断返回ID数组前。父代理授权该全点诊断；只能读取已曝光E166历史结果，不启动任何真实搜索、向量评分、GT读取/生成、训练或构图。此前一次默认python import numpy失败，尚未打开返回ID数组。

## 固定对象与全部比较

旧根目录：`/data/netg/ACSG/entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1`。

- 数据：WebVid/Yandex旧各4096个E105历史开发query；不打开query字节、不改变任何行、不生成新角色。
- Web全部六点：K1/L800、1000、1250；K100/L1120、1250、1400。
- Y全部六点：K1/L96、128、160；K100/L200、256、320。
- 三方法固定顺序：Default3、DefaultRank1、TargetBank1。
- 每点全三对：Default3–DefaultRank1、Default3–TargetBank1、DefaultRank1–TargetBank1；合计36个pair-point单元，正负全部保留。

允许读取旧`config.locked.json`、`results/analysis.json`、两集`score_arrays.npz`中的已保存hits，以及每方法/点的`ids.i32`、`graph_ndc.u64`、`route_ndc.u64`。不解引用config内query/GT/base/index/模型路径，不复制raw返回或大型输入，不读取pool/trace或补测缺失资料。

## 预声明统计与断言

1. 每方法返回shape为(4096,K)，little-endian int32；每行K个不同合法真实ID，无负pad。本数据若不满足则诊断停止并报告实际异常，不按结果删行。
2. hits shape=(4096,6,3)，每值为[0,K]整数；按原配置点/方法索引与旧analysis总hits对齐。graph/route NDC shape=(4096,)，按旧analysis均值对齐。
3. 记录相同**有序返回ID**行数、相同**K-ID集合**行数、相同已保存hits行数、hits相同但返回集合不同的行数。
4. 对满K集合记录每行成员替换数m=|A\B|=|B\A|，其均值、最大值、固定p50/p90/p99；记录由m/K得到的差分Recall绝对上界，检查旧hits差不超过m。不从这类后验上界推新方法收益。
5. 相同返回集合必须有相同旧hits；否则优先报标签/身份错误，不解释为方法机制。
6. 同返回集合时分别记录graph NDC相同/不同及total(route+graph) NDC相同/不同。NDC是旧工作计数，不是完整wall；没有逐query wall，不生成费用/QPS预测。
7. 所有输入在读取前hash/记录bytes，结束重新hash核对；脚本、协议身份记入结果。写小JSON统计及输入身份清单，不写raw数组副本。

## 解释边界

same K-return sets是终局响应相同，**不是same live-pool，也不是不同入口中途汇合率**；无法从旧终局输出判断命题三的状态汇合。same hits是更弱的当前GTK标签并列，不保证返回响应或其他可能GT上的并列。返回相同可与不同NDC/费用共存；无逐query完整wall，不作wall等价判断。

这里只检验旧已执行三个动作的响应关系，不代表未知MixedTarget、粗桶或memo已经执行，也不提供跨query可迁移教师/新模型信息。6点/3pairs不会据结果选子集、调定义或阈值；不选择新的方法或GO。

运行环境：既有`.venv_cpu/bin/python`，CPU0、OMP/BLAS/MKL/NumExpr/BLIS实际库线程均1；属于只读数组分析，运行seconds仅为此诊断脚本耗时，不是性能计时。输出由本代理独占：`response_class_check.py`、`response_class_check.json`、`response_class_input_identity.json`。
