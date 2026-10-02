# 下午原论文阅读与版本清单

这里记录团队本轮核读的**19项独立原工作相关章节**，以及沿用上午的3项有限图前作。不是19篇全文通读、不是19项首次发现，也不把一个工作的正文/补充/arXiv/会议版本重复计数。数学推导、原论文结论、当前实现及真实性能分别陈述；这些阅读没有产生实验。

各分稿含与本地历史的具体碰撞：[代理/前作审阅](theory_prior_and_falsifier_audit.md)、[决策/费用](decision_information_theory.md)、[有限搜索](finite_search_strengthening.md)、[整组拒收](certified_group_elision_theory.md)。表内来源为原会议/JMLR、作者或官方arXiv；第三方搜索结果只作发现线索，不作技术证据。

## 本轮核读的独立原工作

| ID | 论文与版本/作者 | 原文与实际阅读范围 | 本轮用途及限制 |
|---|---|---|---|
| P01 | *A Consistent Regularization Approach for Structured Prediction*，NIPS2016；Carlo Ciliberto、Alessandro Rudi、Lorenzo Rosasco | [原文](https://proceedings.neurips.cc/paper/2016/file/88a839f2f6f1427879fc33ee4acf4f66-Paper.pdf)，§3 Assumption1/Lemma1/Theorem2 | 正确loss embedding/条件mean与decoder；不证明当前GT10画像有该embedding |
| P02 | *Convex Calibration Dimension for Multiclass Loss Matrices*，JMLR2016；Harish G. Ramaswamy、Shivani Agarwal | [原文](https://www.jmlr.org/papers/volume17/14-316/14-316.pdf)，Example2/8、§4.1–4.3 | ordinal低维校准；rank(DΠ)线性值恢复维数不是一般校准维数 |
| P03 | *On Structured Prediction Theory with Calibrated Convex Surrogate Losses*，NIPS2017；Anton Osokin、Francis Bach、Simon Lacoste-Julien | [原文](https://proceedings.neurips.cc/paper/2017/file/38db3aed920cf82ab059bfccbd02be6a-Paper.pdf)，§3 | task loss/允许score空间/风险传递须同时声明 |
| P04 | *Risk Bounds and Calibration for a Smart Predict-then-Optimize Method*，NeurIPS2021；Heyuan Liu、Paul Grigas | [原文](https://proceedings.neurips.cc/paper_files/paper/2021/file/b943325cc7b7422d2871b345bf9b067f-Paper.pdf)，§2–4 | SPO+有具体分布/可行域前件，不直接给ANN/完整QPS保证 |
| P05 | *Learning to Search Better than Your Teacher*，ICML2015；Kai-Wei Chang、Akshay Krishnamurthy、Alekh Agarwal、Hal Daumé III、John Langford | [原文](https://proceedings.mlr.press/v37/changb15.pdf)，§2 Algorithm1、§3 Theorems1–4 | rollout终局相对cost与coverage；入口单次action不同于改主搜索policy |
| P06 | *Clustering on the Unit Hypersphere using von Mises-Fisher Distributions*，JMLR2005；Arindam Banerjee、Inderjit S. Dhillon、Joydeep Ghosh、Suvrit Sra | [原文](https://www.jmlr.org/papers/volume6/banerjee05a/banerjee05a.pdf)，§2.1–2.2、§3 Eq3.4–3.7 | resultant/vMF/MAP方向；不能从闭式形式反推当前责任或生成分布 |
| P07 | *Learning to Route in Similarity Graphs*，ICML2019；Dmitry Baranchuk、Dmitry Persiyanov、Anton Sinitsin、Artem Babenko | [原文](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)，§3.1–3.5 | graph-global表示、双映射及BFS teacher是直接前作；改变主图展开合同 |
| P08 | *Covariate Shift Adaptation by Importance Weighted Cross Validation*，JMLR2007；Masashi Sugiyama、Matthias Krauledat、Klaus-Robert Müller | [原文](https://www.jmlr.org/papers/volume8/sugiyama07a/sugiyama07a.pdf)，§2.1、§3 Lemma1 | 正确条件响应与density ratio；压缩query内shift及signed取消另需控制 |
| P09 | *Maximum Inner-Product Search Using Cone Trees*，KDD2012；Parikshit Ram、Alexander G. Gray | [作者原文](https://rithram.github.io/research/papers/2012/RG_KDD12.pdf)，§3.2/§3.2.1 Theorem3.1 | 经典MIPS球上界/pruning；不提供原native FP包络或实际在线机会 |
| P10 | *FINGER: Fast Inference for Graph-based Approximate Nearest Neighbor Search*，arXiv2206.11408v1，2022-06-22；Patrick H. Chen、Wei-cheng Chang、Hsiang-fu Yu、Inderjit S. Dhillon、Cho-jui Hsieh | [作者v1](https://arxiv.org/pdf/2206.11408v1)，§3.1–3.3/Alg1–3、Appendix A；独立审阅另读B/C/G | 邻接残差角/low-rank/分布匹配已有前作；平均L1 correction不等于逐点native安全上界，不继承SVD最优命题 |
| P11 | *High-Dimensional Approximate Nearest Neighbor Search: with Reliable and Efficient Distance Comparison Operations*，arXiv2303.09855v1，2023-03-17；Jianyang Gao、Cheng Long | [作者v1](https://arxiv.org/pdf/2303.09855v1)，§3.1–3.3 Lemma3.1–3.3/Theorem3.4、§4 Corollary4.1、§8 IP逐比较归约 | ADSampling的概率DCO/ANN同返回；原trace风险适配仍需FP/原batch合同，不是deterministic parity或线上收益 |
| P12 | *Consistent Estimators for Learning to Defer to an Expert*，ICML2020；Hussein Mozannar、David Sontag | [正文](https://proceedings.mlr.press/v119/mozannar20b/mozannar20b.pdf)/[补充](https://proceedings.mlr.press/v119/mozannar20b/mozannar20b-supp.pdf)，§3–5 Prop1/2/Thm1/2、supp C.1.2 | 正确expert cost与Bayes/一致surrogate；E25已引用，finite拟合和费用不可省 |
| P13 | *Convexity, Classification, and Risk Bounds*，JASA2006；Peter L. Bartlett、Michael I. Jordan、Jon D. McAuliffe | [原文](https://sites.stat.washington.edu/courses/stat527/s14/readings/Bartlett_etal_JASA_2006.pdf)，§2.1–2.4 Def1/Thm1/2/ψ-transform | calibration针对正确标签/目标，不把GT proxy变成真实utility |
| P14 | *Strictly Proper Scoring Rules, Prediction, and Estimation*，JASA2007；Tilmann Gneiting、Adrian E. Raftery | [作者原文](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf)，§2.1–2.2 Thm1、§3.1 Thm2/Brier/log/zeroone | elicitation不同于selected-policy值准确；较小有限MSE不保证动作改进 |
| P15 | *Selecting Computations: Theory and Applications*，UAI2012；Nicholas Hay、Stuart Russell、David Tolpin、Solomon Eyal Shimony | [作者原稿](https://aima.cs.berkeley.edu/~russell/papers/uai12-meta.pdf)/[arXiv存本v1](https://arxiv.org/pdf/1408.2048v1)，§1–3 Def1–3/6、Thm4/5/7/9/10 | metalevel VOI、真实联合结果/停止；cache/target访问不自动满足pure-info模型 |
| P16 | *Multicalibration: Calibration for the (Computationally-Identifiable) Masses*，ICML2018；Úrsula Hébert-Johnson、Michael P. Kim、Omer Reingold、Guy N. Rothblum | [正式原文](https://proceedings.mlr.press/v80/hebert-johnson18a/hebert-johnson18a.pdf)，§1–4 定义/Thm1–3/Algorithm1 | 选择组残差、组质量/泛化与membership费用；不能免费覆盖任意稀有组 |
| P17 | *Omnipredictors*，ITCS2022 DOI10.4230/LIPIcs.ITCS.2022.79；Parikshit Gopalan、Adam Tauman Kalai、Omer Reingold、Vatsal Sharan、Udi Wieder | [正式原文](https://drops.dagstuhl.de/storage/00lipics/lipics-vol215-itcs2022/LIPIcs.ITCS.2022.79/LIPIcs.ITCS.2022.79.pdf)，§3–6 Def1/3/5/8–14/17、Lemma4/10/11/15/20、Thm16/19；[full v1](https://arxiv.org/pdf/2109.05389v1)仅§6.3 | 正确比较类/损失族的决策保证；不是任意nonconvex/jointANN/time闭包，不是SODA版本 |
| P18 | *Accurate Sum and Dot Product*，SIAM JSC26(6):1955–1988，2005；Takeshi Ogita、Siegfried M. Rump、Shin’ichi Oishi | [作者原文](https://www.tuhh.de/ti3/paper/rump/OgRuOi05.pdf)，§1.2–2 舍入/underflow/γ_n、§3 FMA定义 | 经典误差模型；未证明当前CPU/kernel/FP环境满足或改算术免费 |
| P19 | *Convex Calibrated Surrogates for Low-Rank Loss Matrices with Applications to Subset Ranking Losses*，NIPS2013；Harish G. Ramaswamy、Shivani Agarwal、Ambuj Tewari | [原文](https://proceedings.neurips.cc/paper_files/paper/2013/file/a5cdd4aa0048b187f7182f1b9ce7a6a7-Paper.pdf)，§2–3 Theorem3及正文proof | 低秩loss的平方条件mean与对应decoder是直接前作；不提供ANN的target sufficiency或便宜可迁移query因子/完整wall |

## 上午已读并沿用/复核的有限图原工作

| ID | 论文与原文 | 使用范围 | 本地边界 |
|---|---|---|---|
| M01 | Liudmila Prokhorenkova、Alexander Shekhovtsov，*Graph-based Nearest Neighbor Search: From Practice to Theory*，ICML2020，[原文](https://proceedings.mlr.press/v119/prokhorenkova20a/prokhorenkova20a.pdf) | 上午§4.4，下午沿用引用边界 | 最近m点诱导图/进入条件，不是任意固定beam保证 |
| M02 | Yousef Al-Jazzazi、Haya Diwan、Jinrui Gou、Cameron Musco、Christopher Musco、Torsten Suel，*Distance Adaptive Beam Search for Provably Accurate Graph-Based Nearest Neighbor Search*，arXiv2505.15636v1（2025-05-21）[作者原文](https://arxiv.org/html/2505.15636v1)/[NeurIPS2025正式原文](https://proceedings.neurips.cc/paper_files/paper/2025/file/904fe070f484231aa26dbdb37816cd40-Paper-Conference.pdf) | 上午v1 §3–4/Claim2，下午复读v1与final §3.1–3.2/Algorithm1（final PDF4–5页） | ordered traversal/prefix已有；本地FIFO/full-row独立手证，不继承metric/navigability theorem或字面≤计数offbyone映射 |
| M03 | Yannick Bosch、Sabine Storandt，*Instance-based Approximation Guarantees for Graph-based Nearest Neighbor Search*，ICAPS2025，[原文](https://ojs.aaai.org/index.php/ICAPS/article/download/36113/38267/40186) | 上午Definition3–6/Theorem1，下午复核 | greedy/Voronoi响应区不自动推广任意native finite beam |

FINGER的WWW2023六作者版身份与本次实读五作者v1分别记录；ADSampling最终PACMMOD2023版本与本次17页v1不混正文/页数/原文定理版本。Hay arXiv2014是UAI2012存本；Omnipredictors full2021与正式ITCS2022属同一工作。未取得全文的Blackwell不记入实读；搜索中出现但未读原文的RaBitQ/AVQ等不计入本清单，也不靠其摘要作技术结论。

## 检索覆盖与研究贡献的限度

本轮补了现行query归属矩、有限pool/原native、actualjoint/真实完整费用之间的合同；多数基础机制在上述原工作和E04/E25/E36/E118/E133/E164已有直接前作。当前没有完成系统新颖性证明，不声称新的centroid/vMF、Bayes/VOI、loss embedding、calibration、beam失败、pruning或数值误差理论。19项核读是交接身份信息，不是综合性能进展的替代指标。
