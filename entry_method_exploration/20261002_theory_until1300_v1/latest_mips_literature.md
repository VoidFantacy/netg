# 新补MIPS原论文：query scaling、PSP与MAG

2026-10-02补读，12:48前提交。只新增本文件；冻结理论、诊断协议、统计原件不修改。无真实ANN/NSG/GT、训练、构图或新向量评分。

**结论：逐q有限库可使某个精确top1解与缩放L2对齐；全排序与beam需要更强比较条件，这不免费给出当前完整轨迹或native保真。PSP改图、入口和停止；MAG改图并先L2后IP。它们是重要直接相关前作，没有提供固定现有IP主核的已测Recall–QPS替代。**

## 原文身份与实读范围

| 原始来源 | 作者/版本 | 本轮实际读到的部分 |
|---|---|---|
| [Maximum Inner Product is Query-Scaled Nearest Neighbor](https://arxiv.org/html/2503.06882v2) | Tingyang Chen、Cong Fu、Kun Wang、Xiangyu Ke、Yunjun Gao、Wenchao Zhou、Yabo Ni、Anxiang Zeng；v2，2025-07-23，PVLDB18(6)，DOI10.14778/3725688.3725705 | §3.1 Lemma1、Theorem1/2及Appendix A完整证明；§3.2 Theorem3/4及其假设；§4.1/4.2图、入口和AET |
| [Stitching Inner Product and Euclidean Metrics for Topology-aware Maximum Inner Product Search](https://arxiv.org/html/2504.14861v2) | Tingyang Chen、Cong Fu、Xiangyu Ke、Yunjun Gao、Yabo Ni、Anxiang Zeng；v2，2025-07-23，SIGIR25，DOI10.1145/3726302.3730088 | §3.2 Fact1/Proposition2；§4.1 Theorem2与近似构造；§4.2 ANMS；没有全篇首次性审查 |
| [MAG作者仓库](https://github.com/ZJU-DAILY/MAG) | 固定提交`cbabb2b7d06d0a2e7f171219686aa49b72edf4ea`，2025-08-23 | `include/index_mag.h`的Build、pruneEdge、Search_NN_IP；`test/test_mag.cpp`真实调用 |

先打开v1，随后核对最新版v2；以下采用v2，不依赖二手综述。两论文关联明确：MAG §3.2 Fact1引用query-scaled论文的缩放/搜索双性；作者仓库也直接链接PSP理论工作。

## 原文结论与实际改变

Query-scaled Theorem1证明有限库上逐q的top1对齐存在性；Theorem2/Appendix A按每步邻域的最佳节点统一选择，局部MIP ties另调整规则。Theorem3的效率假设包括SSG、足够大n、base/query同一零均值Gaussian且i.i.d.，不能直接赋给当前图/数据。实际PSP采用NSSG并添球面边，SN选入口，AET决策树提前停；当前“safe点最终必展开”不能跨AET继承。[原方法/证明](https://arxiv.org/html/2503.06882v2)

MAG的理想Theorem2依MRNG加dominator边；实际是近似K-MRNG/K-MAG、边比例控制，ANMS先m步Euclidean后IP。强连通、理想可达性和分布估计不等于当前预算Recall保证，也不证明加边对有限beam单调有利。[原方法/理论](https://arxiv.org/html/2504.14861v2)

作者固定源码的`Search_NN_IP`实际用L2 pool5自然扫描，再重置visited，初始化L个IP候选并重新评分；先生成随机数组，再用5个L2返回和norm列表覆盖，随后自然扫描，不能把初始化的随机内容视为必然残留。`pruneEdge`注释承认修改论文的边选择逻辑。故不能把论文的m步过程或理想图定理当源码逐行保真证明。[搜索与切换源码](https://github.com/ZJU-DAILY/MAG/blob/cbabb2b7d06d0a2e7f171219686aa49b72edf4ea/include/index_mag.h#L626)、[构图及剪枝](https://github.com/ZJU-DAILY/MAG/blob/cbabb2b7d06d0a2e7f171219686aa49b72edf4ea/include/index_mag.h#L458)、[实际调用](https://github.com/ZJU-DAILY/MAG/blob/cbabb2b7d06d0a2e7f171219686aa49b72edf4ea/test/test_mag.cpp#L96)

## 独立代数审查：哪些保证真正足够

以下是本轮自行从距离展开推导的条件及反例，不是原论文声称已建立的当前实现保证。设有限库、固定非零q、`s_i=q·x_i`，精确算术下

\[
e_i(\mu)=\|x_i-\mu q\|^2=\mu^2\|q\|^2+\|x_i\|^2-2\mu s_i.
\]

对`s_i>s_j`，L2也把i排在j前的充要条件为

\[
2\mu(s_i-s_j)>\|x_i\|^2-\|x_j\|^2.
\]

若所有IP分数严格不同，则取

\[
\mu>M(q):=\max\left(0,\max_{s_i>s_j}\frac{\|x_i\|^2-\|x_j\|^2}{2(s_i-s_j)}\right)
\]

足以保**全库严格排序**，因此保每个top-K/top-L，也保决策仅依节点排序的固定确定性beam中所有接受、cutoff、跨前沿排序和nearest-pending比较。还须同图、同实际seed、同visited、同自然停止、同tie规则；不能另含分数绝对阈值或距离ratio停止谓词。有限库只给该阈值存在；求它要全库norm/IP及最小margin，不是免费线上规约。更弱的版本只对一条实际trace全部比较对取最大阈值，再按分支归纳保该trace；已付出trace成本，不是访问前未知动作的免费标签。

**top1对齐不足以保剩余排序。**纯代数例`q=(1,0)`、`a=(3,0)`、`b=(2,10)`、`c=(1,0)`、μ=3：IP序a>b>c，平方L2值分别0、101、4，L2序a>c>b。top1已对齐，但top2/beam候选次序不同。该例只写精确数值，没有执行真实图搜索。本例严格top1对齐需μ>2（μ=2出现tie），全序需μ>51.5，说明局部最佳/全局top1条件不能替代本地beam全部比较合同；这不否认更大μ的存在。

IP ties时，等IP点的L2顺序由norm决定，有限μ不能消掉norm差；任意原生ID tie规则与此可能不同。q=0亦无严格序。因而“存在公共解”不能偷换成“所有tie解/有序ID数组一致”。

若主核仍是精确IP、图/实际seed及停止全部固定，正缩放只统一乘分数，不改变返回/展开/NDC；缩放本身没有新的Recall信号。native float32还要满足所有混合评分路径的实际顺序、finite/below-sentinel及舍入条件。L2共同项按μ²增长，比较间隔按μ增长：无限增大μ不能自动保证浮点分辨率，反可能产生ties/overflow；不能以精确存在性替代本轮的native区间条件。

## 精确排名与近似质量的差别

同样由上式独立推导：若只知道L2算法满足`e_x≤c² e_*`（c≥1），则

\[
s_x\ge c^2s_* -\frac{(c^2-1)\mu^2\|q\|^2+c^2\|x_*\|^2-\|x\|^2}{2\mu}.
\]

c>1时出现随μ增长的加性惩罚，不能直接得到固定乘性IP质量，更不能得到Recall@1/@100或完整wall。全序保真和某个metric近似因子是不同保证；导航图/分布条件仍须各自满足。此处是代数条件，不新增统计模型或实测。

直接的独立反例是1D `q=1`、库`{1,−1}`。精确MIP/缩放L2最近点始终是1；但任意固定c>1，只要μ≥(c+1)/(c−1)，点−1到μ的距离也满足c倍近似，因为(μ+1)/(μ−1)≤c。它的IP是−1，无法满足任意正ε的εMIPS。这说明即使精确排序已一致，L2相对近似合同仍允许质量完全错误的返回；没有运行算法。

## 与本次安全证明的关系

本次P_L安全闭包理论只需要固定图、共同严格序、合法去重seed≤L、自然完整展开，**不需要先把IP规约到L2**；query-scaled前作解释何时可以对照metric排序，但不能免费补齐未知P_L/GT-native一致性。

若采用PSP的AET，已发现safe点可能尚未展开即停止，故必展开与完整B_L等式的前件失效。若采用MAG的L2前缀/visited重置，应把IP重启实际消耗的全部候选当新S并收费，而非继承原三入口响应；上述作者初始化没有核实候选ID互异，不能直接套当前mode2去重合同。只有重新满足全部前件，才可针对该新固定执行推同类条件结论；不会给当前固定IP合同制造GO。

最终边界：PSP/MAG应登记为最新直接相关前作；其graph/metric/停止改变超出本轮入口固定主核优化。没有读取新真实数据、运行搜索、建图或性能，没有把论文加速数值搬到ACSG。
