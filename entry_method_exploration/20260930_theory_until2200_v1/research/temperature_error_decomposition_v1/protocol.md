# 温度与标签误差的条件分解

2026-09-30，在读取本阶段分解结果前固定；fresh_transfer_v1已锁模型/查询并运行，本阶段不得改变其比较。待全部性能作业终止后才计算，避免并发污染。只用旧曝光训练资料与已经生成的合力v，不用新确认query、GT、入口或增损结果。

目标：说明2048替换固定温度时的有限总体风险公式，为何不能直接适用于同一批样本估计温度的全流程；定量拆出固定r0的标签项、温度项和二者内积。此为解释性诊断，不重新选择温度公式、种子、m或shrinkage系数。

Web以记录141的全真值合力V(T*)为参照，T*为原全20K GT1中位数。A=原ApproxTarget10；F=记录144的HybridFixedTemperature；P=HybridPilotTemperature；另纳入记录150的HybridRectifiedCDF及HybridApproxMedian。各模型原始v已保存，均先独立确认unit(v).float32恢复其冻结W。定义E_label=F−V、E_temp=M−F、E_total=M−V，M取P/CDF/ApproxMedian，严格检查加法同一性。

分别在原始向量、按真合力范数加权向量、真方向切空间三种度量报告||E_total||²=||E_label||²+||E_temp||²+2<E_label,E_temp>，同时列实际归一化chord²和最小径向合力。按hub报告贡献分布，不从事后正负hub挑子模型。该交叉项来自一个固定样本，不称抽样协方差或因果份额。

解析温度导数只在F的原T*处计算一次：保留同一混合目标与样本，按float32分数/float64softmax计算dV/dlogT和P dV/||V||。不输出新W或图。预测已冻结P/CDF/ApproxMedian相对F的位移，报告一阶余项相对实际位移，不以余项选温度。温度本身由全局目标打分影响全部20K权重；固定lambda风险公式的条件和随机温度共享样本的依赖需明确。

CPU0–7池8，≤5分钟、输出≤10MiB；0新GT/NSG/ANN/候选/图/性能。对导数用预定小型合成softmax中心差分核验，实数据另用显式每hub投影检查能量与交叉恒等。若float32实现与理想光滑模型有细小数值差，只作误差说明，不改变冻结参数。
