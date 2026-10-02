# E72 按真实hub计宽的小图搜索控制

2026-09-13，第5串行会话。原P/duplicate/mode各普通ef10与distinct10，固定原图/W/H/NSG/raw-IP；没有新画像训练或实际图构建。历史aux7952/L128及固定3976两半，全部选择反馈计训练，非最终validation。

| 数据 | distinct mode 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |
|---|---|---:|---:|---|---|---|
| WebVid | baseline10 | -21 | -0.0264 | 44/48 | [-7, -14] | +28.77/+1.76 |
| WebVid | mode3P10 | +85 | +0.1069 | 12/3 | [31, 54] | +23.45/+1.47 |
| WebVid | mode3P30 | -27 | -0.0340 | 12/11 | [9, -36] | -31.26/-3.32 |
| Yandex | baseline10 | +73 | +0.0918 | 40/34 | [10, 63] | +57.85/+2.10 |
| Yandex | mode3P10 | +24 | +0.0302 | 6/4 | [24, 0] | +31.17/+1.20 |
| Yandex | mode3P30 | -4 | -0.0050 | 4/5 | [2, -6] | -25.43/-1.76 |

预锁完整wall接续门：WebVid未通过, Yandex未通过。这是历史辅助质量与路由费用门，不是性能GO；E66/E70原门、原默认保持。

回调只按external label映射的实际引用数计hub，不使用移除回调中不可靠的距离或影子堆。返回internal ID显式转换；singleton保留原堆截k子集，mode按完整候选distance/slot去重前三真实入口。每query状态复位，完整候选长度及最多30槽全部保存，未把前7槽当完整结果。

完整画像前三一致率及候选占位：
- WebVid baselineD10: agreement 86.38%，平均10.00槽，范围10–10，10不同hub。
- WebVid duplicate3PD10: agreement 81.05%，平均29.14槽，范围28–30，10不同hub。
- WebVid mode3PD10: agreement 85.06%，平均16.02槽，范围10–30，10不同hub。
- Yandex baselineD10: agreement 93.61%，平均10.00槽，范围10–10，10不同hub。
- Yandex duplicate3PD10: agreement 91.49%，平均29.01槽，范围28–30，10不同hub。
- Yandex mode3PD10: agreement 93.80%，平均18.06槽，范围10–28，10不同hub。

实际194304 NSG/193920 HNSW/0实际图build；合成另4图/512 HNSW/0NSG。原生四job 149.135s、编译16.616s。24 plain与24 count源图加载、0图副本；route-only/graph-only未单测为null，不换算QPS。

独立96960集合/mask评分，主批63616原控制及singleton返回/距离bits/入口/两NDC恢复，全部plain/count与384原kernel对照、完整候选距离/映射/去重及预检前缀通过。80103同三入口结果恢复E69。合成覆盖tie、非同一内外ID、引用增减/忽略移除dist、复位和重复候选；真实运行要求10hub、至少3入口，不足则拒绝。

strict failure=GT10集合零命中。GT成员找回/丢失与逐query净命中正负部独立记账，所有失败转换保存source namespace/row/三入口。所有原始aligned返回ID/距离/入口、hits/mask和路由/图NDC保留。GT在原生搜索后读取，双集工具terminal0后才分析。CPU15与进程/OMP/BLAS/MKL1核验；E34最终及held-out未进入。

[完整配对](results/paired.csv) · [原值与成本](results/cost.json) · [失败转换](results/failures.csv) · [排名/占位](results/ranking.csv) · [图](figures/distinct_control.png) · [门](results/gate.json) · [协议](protocol.md) · [验收](reviews/verification.json)。
