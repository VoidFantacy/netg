# 固定温度风险到随机温度全流程之间的缺项

记unit查询u_i、固定hub先验h_j、样本S。a_ij(T)、b_ij(T)分别是精确/近似目标top10的hub软分配。固定混合系数c_ij(T,S)=1{i∈S}a_ij(T)+1{i∉S}b_ij(T)，合力

\[
V_j(S,T)=h_j+\sum_i c_{ij}(T,S)u_i,\qquad w_j=V_j/\|V_j\|.
\]

以全真值与固定T*为参照，误差的精确分解为

\[
V_j(S,\widehat T)-V_j^{exact}(T_*)
=\underbrace{V_j(S,T_*)-V_j^{exact}(T_*)}_{E^{label}_j}
+\underbrace{V_j(S,\widehat T)-V_j(S,T_*)}_{E^{temperature}_j}.
\]

第二项不是仅影响S的局部修改，它通过T影响每行softmax。对任一固定线性度量L_j（恒等、按参照合力缩放、参照切向投影），令e=L E，有恒等式

\[
\sum_j\|e^{total}_j\|^2=\sum_j\|e^{label}_j\|^2+\sum_j\|e^{temperature}_j\|^2
+2\sum_j\langle e^{label}_j,e^{temperature}_j\rangle.
\]

同一批S同时决定标签替换和温度估计，最后一项不应默认为0。即使对固定阈值CDF校正无偏，也不能抹去此交叉项，或把固定T的偏差—方差公式直接称为整个管线的风险公式。更不应把固定样本内积叫作抽样协方差。

设tau=logT，对某个目标的原分数s_j，p_j=softmax(s/T)_j，微分为

\[
\frac{\partial p_j}{\partial\tau}=p_j\left(\sum_l p_l\frac{s_l}{T}-\frac{s_j}{T}\right),\qquad
\frac{\partial w_j}{\partial\tau}=\frac{(I-w_jw_j^T)}{\|V_j\|}\frac{\partial V_j}{\partial\tau}.
\]

top10平均和查询合力按线性运算传递导数。平移所有s_j不改变p或导数；实现先减最大分数以稳定指数。对于未归一化合力的温度项，可以沿tau积分精确表示；归一化路径只要||V_j||有正下界，方向弧长给出chord变化的上界。某一端点的一阶导数只能作局部近似，不能未经余项控制外推很大的温度区间。

单个softmax满足||dp/dtau||_1=E_p|s/T−E_p(s/T)|≤(max s−min s)/(2T)。该分布范围界正确但对全部20K累加会很松；实际投影导数可衡量本地敏感性，却不是免费部署的真值误差证书。非正/近零合力、排序小间隔、小图近似与有限beam效用仍可能使“温度更准”无法变成“召回更好”。

上述为softmax微分、归一化微分和平方范数展开的应用，不主张新普遍定理。本日新源测试只负责验证冻结模型的真实R1/R100和wall；本分解不能改写已冻结温度或选择最好的一组结果。
