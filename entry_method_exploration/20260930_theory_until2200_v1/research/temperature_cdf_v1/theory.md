# 少量真值校准训练总体的温度

记有限总体大小N，固定精确gap为y_i，近似gap为z_i，S为m个不放回均匀样本，f=m/N。每个固定阈值t的估计为

\[
\widetilde F(t)=N^{-1}\sum_i1\{z_i\le t\}+m^{-1}\sum_{i\in S}(1\{y_i\le t\}-1\{z_i\le t\}).
\]

对抽样设计取期望，E Ftilde(t)=F_y(t)，且Var Ftilde(t)=(1-f)S_r²(t)/m，r_i(t)=1{y_i≤t}-1{z_i≤t}。普通样本CDF的方差是(1-f)S_y²(t)/m；因此固定阈值下的方差比为S_r²/S_y²。这里全体近似值是固定已知总体，不再加独立未标注样本的方差项。常系数lambda时残差换为I_y-lambda I_z，oracle最优lambda=Cov(I_y,I_z)/Var(I_z)；本次只用预定lambda=1，不拿全真值求部署系数。

中位数附近，若连续总体近似成立、真分布局部可微且密度g(T)>0，正规根选择的首阶误差约为-(Ftilde(T)-0.5)/g(T)。这只是局部渐近桥，离散有限总体、非单调曲线、多根和网格并列均需另外处理。CDF逐点无偏不意味着温度无偏，也不意味着归一化画像或Recall改善。

对任意有限网格G，令T_hat使|Ftilde(t)-1/2|最小，delta_G=min_G|F_y(t)-1/2|。若G上sup|Ftilde-F_y|≤epsilon，直接三角不等式给

\[
|F_y(T_{hat})-1/2|\le 2\epsilon+\delta_G.
\]

该界只控制CDF残差；平坦区可使温度误差大，必须有逆分布的局部稳定性才能转成数值误差。网格本身依赖样本时，逐点方差式仍针对固定t；不能直接把它代入随机所选T_hat声称覆盖率。实验用固定真中位点检查方差，16个样本误差只作描述性诊断。

近似标签若本来准确预测阈值两侧，指示残差比标签本身方差小，少量精确值就能纠偏；只接近连续gap却跨错中位点也可能无效。因此本次同时报告真实中位点的配对类别表和打乱配对控制，而非只看gap相关系数。

这是已有方法的适配：[Prediction-Powered Inference](https://arxiv.org/abs/2301.09633)已提出预测加标签校正的推断框架；[官方ppi_quantile_pointestimate源码](https://ppi-py.readthedocs.io/en/latest/_modules/ppi_py/ppi.html#ppi_quantile_pointestimate)明确使用校正CDF和网格最近分位点。上面的不放回有限总体方差及离散数值约定单独推导，不能套用官方独立两样本CI。没有新的统计方法或ANN质量定理主张。
