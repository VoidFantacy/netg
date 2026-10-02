# 记录145的R100救回／损伤用语澄清

原145组内字段`rescues`和`damages`分别是每query净命中差的正／负累计。K100可在一条query上同时救回和损伤若干正确成员，旧字段会将这部分抵消；应称“每query净增加／净减少成员累计”。原净Recall、事件分解和停止结论保持，原代码／报告／JSON／seal均未修改。

本补充按正确返回成员集合差统计真实救回／损伤，另以带query编号的向量化ID编码逐query复核。以下展示原混合候选，全部方法对及near/away组均在results.json中保存。事件1为精确top3相同、实际入口改变；事件3为两者都改变。

| 原方法对 | 事件 | 旧净增加 / 净减少 | 真救回 / 真损伤 | 每侧被抵消 | 净差保持 |
|---|---:|---:|---:|---:|---:|
| Web HybridFixedTemperature / GT10-soft-t1 | 1 | 195 / 32 | 198 / 35 | 3 | +163 |
| Web HybridFixedTemperature / GT10-soft-t1 | 3 | 53 / 130 | 64 / 141 | 11 | -77 |
| Web HybridFixedTemperature / ApproxTarget10 | 1 | 76 / 5 | 77 / 6 | 1 | +71 |
| Web HybridFixedTemperature / ApproxTarget10 | 3 | 37 / 11 | 37 / 11 | 0 | +26 |
| Web HybridPilotTemperature / GT10-soft-t1 | 1 | 142 / 106 | 145 / 109 | 3 | +36 |
| Web HybridPilotTemperature / GT10-soft-t1 | 3 | 29 / 128 | 39 / 138 | 10 | -99 |
| Web HybridPilotTemperature / ApproxTarget10 | 1 | 5 / 64 | 7 / 66 | 2 | -59 |
| Web HybridPilotTemperature / ApproxTarget10 | 3 | 20 / 13 | 20 / 13 | 0 | +7 |
| Y HybridFixedTemperature / GT10-hard | 1 | 115 / 172 | 258 / 315 | 143 | -57 |
| Y HybridFixedTemperature / GT10-hard | 3 | 211 / 135 | 252 / 176 | 41 | +76 |
| Y HybridFixedTemperature / ApproxTarget10 | 1 | 131 / 79 | 235 / 183 | 104 | +52 |
| Y HybridFixedTemperature / ApproxTarget10 | 3 | 41 / 7 | 73 / 39 | 32 | +34 |

全部120个组单元、20项身份通过，计算1.738秒。K1不会在同query同时救回与损伤，原两类计数相同。本补充0新GT／NSG／ANN／模型／性能；没有改变任何旧标签、query或返回。新的158连接诊断已将真实成员差与每query净差分开存储。
