# E195 七集残差来源与导航增量详细定位

2026-11-01用户授权“定位吧，不一定要最小验证，详细验证，不同的数据集有价值就都研究研究”。本轮建立新协议，未恢复旧runner。完成七集、两曝光公共窗口、真实K1/K100的1260正式点/3780完整T1批次；另140新资格点和56旧二进制控制点，42对应包逐字节一致。504个导航点中341个同L相对B32净Recall正、319个被同窗GT10/B32/OPT-B32/SQ覆盖。252个方法/K/L配置中78个两窗均正且未被已有离散网格覆盖。默认E99 GT10保持。

[协议](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/protocol.md)、[源码](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/src/benchmark.cpp)、[正式冻结](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/formal_freeze.json)、[完整报告](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/report_zh.md)、[全部点](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/points.csv)、[机制与阶段](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/mechanisms.csv)、[两窗配置](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/stability.csv)、[第二实现](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/analysis_receipt.json)、[费用](../entry_method_exploration/20261101_residual_navigation_diagnosis_v1/analysis/cost_ledger.json)。

七集原图/metric/GT10/B32/SQ不变，两个公共查询窗口各512（GIST500），真实K1/K100。GT10/B32 11档L、SQ四档、OPT-B32一档、六导航三档固定完成。直接C保留，一跳/距离多步/未访问邻接选择/真实入邻居代表分别测试。独立辅助扩展不是原API续搜，GT只在wall外评价。

轨迹复制核42864条调用与原主返回ID/距离字节相同，导航504点/257184条query通过原生线性oracle和NumPy全排序。A/B源行不重叠但均已曝光，非跨图/独立人员复现；常数特征相关无定义，单seed并集不当共享beam。成员损伤、严格<10%尾部、完整QPS和旧正面证据保留。

旧E194科学与manifest保持，根文档原字节由source_before桥接；旧E173–194协议/失败/原始结果/PDF/seal不回写。大产物/root/acsg-e195-storage经storage链接。固定矩阵及分析收口，无自动追加范围或默认替换。
